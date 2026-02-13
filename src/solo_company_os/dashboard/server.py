from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
from threading import Thread

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from rich.console import Console

from ..core.orchestrator import run_mission
from ..core.providers.mock import MockProvider
from ..core.providers.openai_compatible import OpenAICompatibleProvider
from ..core.skill_index import DEFAULT_SKILL_DIRS, SkillIndex, discover_skills
from ..core.utils import new_run_id


def create_app(run_root: Optional[Path] = None) -> FastAPI:
    app = FastAPI(title="Solo Company OS Dashboard")
    app.state.run_root = run_root or Path("runs")

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        return HTMLResponse(_render_submit())

    @app.get("/submit", response_class=HTMLResponse)
    def submit_page() -> HTMLResponse:
        return HTMLResponse(_render_submit())

    @app.get("/history", response_class=HTMLResponse)
    def history_page() -> HTMLResponse:
        return HTMLResponse(_render_index())

    @app.get("/api/runs")
    def list_runs() -> Dict[str, Any]:
        run_root = _run_root(app)
        return {"runs": _collect_runs(run_root)}

    @app.get("/api/runs/{run_id}")
    def get_run(run_id: str) -> Dict[str, Any]:
        run_dir = _resolve_run_dir(_run_root(app), run_id)
        return {
            "run_id": run_id,
            "mission": _extract_mission(run_dir),
            "plan": _read_json(run_dir / "plan.json"),
            "report": _read_text(run_dir / "RUN.md"),
        }

    @app.get("/api/runs/{run_id}/trace")
    def get_trace(run_id: str) -> Dict[str, Any]:
        run_dir = _resolve_run_dir(_run_root(app), run_id)
        return {"events": _read_trace(run_dir / "trace.jsonl")}

    @app.post("/api/runs/execute")
    def execute_run(req: RunRequest) -> Dict[str, Any]:
        run_root = _run_root(app)
        run_id = new_run_id()
        run_dir = run_root / run_id
        workspace = run_dir / "workspace"
        run_dir.mkdir(parents=True, exist_ok=True)
        workspace.mkdir(parents=True, exist_ok=True)

        skill_index = _build_skill_index(req.skill_dir)
        provider = _build_provider(req.provider, req.model)

        Thread(
            target=_run_background,
            args=(req.mission, skill_index, provider, run_dir, workspace),
            daemon=True,
        ).start()
        return {"run_id": run_id}

    @app.get("/api/runs/{run_id}/stream")
    def stream_trace(run_id: str, since: int = Query(0, ge=0)) -> StreamingResponse:
        run_dir = _resolve_run_dir(_run_root(app), run_id)
        trace_path = run_dir / "trace.jsonl"
        return StreamingResponse(
            _iter_trace_stream(trace_path, since),
            media_type="text/event-stream",
        )

    @app.get("/api/runs/{run_id}/files")
    def get_files(run_id: str) -> Dict[str, Any]:
        run_dir = _resolve_run_dir(_run_root(app), run_id)
        workspace = run_dir / "workspace"
        if not workspace.exists():
            raise HTTPException(status_code=404, detail="workspace not found")
        return {"root": workspace.name, "tree": _build_tree(workspace, workspace)}

    @app.get("/api/runs/{run_id}/file")
    def get_file(run_id: str, path: str = Query(..., min_length=1)) -> Dict[str, Any]:
        run_dir = _resolve_run_dir(_run_root(app), run_id)
        workspace = run_dir / "workspace"
        file_path = (workspace / path).resolve()
        if workspace.resolve() not in file_path.parents and file_path != workspace.resolve():
            raise HTTPException(status_code=400, detail="invalid path")
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="file not found")
        if file_path.stat().st_size > 200_000:
            raise HTTPException(status_code=413, detail="file too large to preview")
        return {"path": path, "content": file_path.read_text(encoding="utf-8", errors="ignore")}

    return app


class RunRequest(BaseModel):
    mission: str = Field(..., min_length=1)
    provider: str = Field("mock")
    model: Optional[str] = None
    skill_dir: List[str] = Field(default_factory=list)


def _run_root(app: FastAPI) -> Path:
    return app.state.run_root


def _resolve_run_dir(run_root: Path, run_id: str) -> Path:
    run_dir = run_root / run_id
    if not run_dir.exists() or not run_dir.is_dir():
        raise HTTPException(status_code=404, detail="run not found")
    return run_dir


def _collect_runs(run_root: Path) -> List[Dict[str, Any]]:
    if not run_root.exists():
        return []
    runs = []
    for item in sorted(run_root.iterdir(), reverse=True):
        if not item.is_dir():
            continue
        runs.append(
            {
                "run_id": item.name,
                "mission": _extract_mission(item),
                "updated_at": item.stat().st_mtime,
                "has_plan": (item / "plan.json").exists(),
                "has_trace": (item / "trace.jsonl").exists(),
            }
        )
    return runs


def _extract_mission(run_dir: Path) -> Optional[str]:
    trace_path = run_dir / "trace.jsonl"
    mission = _mission_from_trace(trace_path)
    if mission:
        return mission
    run_md = _read_text(run_dir / "RUN.md")
    if not run_md:
        return None
    for line in run_md.splitlines():
        if line.strip().startswith("Mission:"):
            return line.split("Mission:", 1)[-1].strip() or None
    return None


def _mission_from_trace(trace_path: Path) -> Optional[str]:
    if not trace_path.exists():
        return None
    for raw in trace_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            evt = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if evt.get("type") == "mission.start":
            mission = (evt.get("payload") or {}).get("mission")
            if isinstance(mission, str):
                return mission
    return None


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _read_text(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_trace(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _load_env() -> None:
    load_dotenv(dotenv_path=Path(".env"), override=False)


def _build_skill_index(extra_dirs: List[str]) -> SkillIndex:
    roots = list(DEFAULT_SKILL_DIRS) + extra_dirs
    report = discover_skills(roots=roots, console=Console())
    idx = SkillIndex(report.skills)
    if not idx.skills:
        raise HTTPException(status_code=400, detail="no skills found")
    return idx


def _build_provider(provider: str, model: Optional[str]) -> Any:
    _load_env()
    if provider == "mock":
        return MockProvider()
    if provider == "openai":
        return OpenAICompatibleProvider.from_env(model=model)
    raise HTTPException(status_code=400, detail="provider must be mock or openai")


def _run_background(
    mission: str,
    skill_index: SkillIndex,
    provider: Any,
    run_dir: Path,
    workspace: Path,
) -> None:
    try:
        run_mission(
            mission=mission,
            skill_index=skill_index,
            provider=provider,
            run_dir=run_dir,
            workspace=workspace,
            console=Console(),
        )
    except Exception as exc:
        (run_dir / "RUN_ERROR.txt").write_text(str(exc), encoding="utf-8")


def _iter_trace_stream(path: Path, since: int) -> Any:
    last_index = max(since, 0)
    yield "retry: 1000\n\n"
    while True:
        if path.exists():
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            for idx in range(last_index, len(lines)):
                try:
                    evt = json.loads(lines[idx])
                except json.JSONDecodeError:
                    continue
                payload = {"index": idx, "event": evt}
                data = json.dumps(payload, ensure_ascii=False)
                yield f"id: {idx}\ndata: {data}\n\n"
            last_index = max(last_index, len(lines))
        time.sleep(0.6)


def _build_tree(root: Path, base: Path) -> List[Dict[str, Any]]:
    nodes: List[Dict[str, Any]] = []
    for item in sorted(root.iterdir()):
        rel = str(item.relative_to(base))
        if item.is_dir():
            nodes.append(
                {
                    "type": "dir",
                    "name": item.name,
                    "path": rel,
                    "children": _build_tree(item, base),
                }
            )
        else:
            nodes.append(
                {
                    "type": "file",
                    "name": item.name,
                    "path": rel,
                    "size": item.stat().st_size,
                }
            )
    return nodes


def _render_index() -> str:
    return """<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Solo Company OS Dashboard</title>
  <style>
    :root { color-scheme: light; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; background: #f6f7fb; color: #1f2430; }
    header { padding: 16px 24px; background: #111827; color: #fff; font-weight: 600; display: flex; align-items: center; justify-content: space-between; }
    header nav a { color: #cbd5f5; text-decoration: none; margin-left: 12px; font-size: 13px; }
    header nav a.active { color: #fff; font-weight: 600; }
    .layout { display: grid; grid-template-columns: 280px 1fr; height: calc(100vh - 56px); }
    aside { background: #0f172a; color: #cbd5f5; padding: 16px; overflow-y: auto; }
    aside h3 { margin: 0 0 12px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.08em; }
    .run { padding: 10px 12px; border-radius: 10px; cursor: pointer; margin-bottom: 8px; background: #1e293b; }
    .run.active { background: #3b82f6; color: #fff; }
    main { padding: 20px 24px; overflow-y: auto; }
    .grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
    section { background: #fff; border-radius: 14px; padding: 16px; box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08); }
    pre { background: #0f172a; color: #e2e8f0; padding: 12px; border-radius: 8px; overflow-x: auto; font-size: 12px; }
    .tag { display: inline-block; padding: 2px 8px; border-radius: 999px; background: #e2e8f0; font-size: 12px; }
    .tree ul { list-style: none; padding-left: 16px; }
    .tree li { margin: 4px 0; }
    button { border: 0; background: #3b82f6; color: #fff; padding: 6px 10px; border-radius: 6px; cursor: pointer; }
    .muted { color: #94a3b8; font-size: 12px; }
    table { width: 100%; border-collapse: collapse; font-size: 12px; }
    th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #e2e8f0; }
    .status-badge { display: inline-flex; align-items: center; gap: 6px; padding: 2px 8px; border-radius: 999px; font-size: 11px; }
    .status-running { background: #fde68a; color: #92400e; }
    .status-thinking { background: #bfdbfe; color: #1d4ed8; }
    .status-done { background: #bbf7d0; color: #166534; }
    .status-skip { background: #e2e8f0; color: #475569; }
    .status-error { background: #fecaca; color: #991b1b; }
  </style>
</head>
<body>
  <header>
    <span>Solo Company OS Dashboard</span>
    <nav>
      <a class="active" href="/submit">任务提交</a>
      <a href="/history">历史任务</a>
    </nav>
  </header>
  <div class="layout">
    <aside>
      <h3>Runs</h3>
      <div id="runList" class="muted">Loading...</div>
    </aside>
    <main>
      <section>
        <h2 id="runTitle">请选择一个 Run</h2>
        <p class="muted" id="runMeta"></p>
        <span class="tag" id="runMission">Mission</span>
      </section>
      <div class="grid" style="margin-top:16px;">
        <section>
          <h3>Agents 状态</h3>
          <div style="max-height:280px; overflow:auto;">
            <table>
              <thead><tr><th>Agent</th><th>状态</th><th>工单</th><th>更新时间</th></tr></thead>
              <tbody id="agentBody"></tbody>
            </table>
          </div>
        </section>
        <section>
          <h3>协作流</h3>
          <div style="max-height:280px; overflow:auto;">
            <table>
              <thead><tr><th>ID</th><th>Skill</th><th>标题</th><th>状态</th><th>产物</th></tr></thead>
              <tbody id="flowBody"></tbody>
            </table>
          </div>
        </section>
        <section>
          <h3>Plan</h3>
          <pre id="plan">-</pre>
        </section>
        <section>
          <h3>Trace</h3>
          <div style="max-height:300px; overflow:auto;">
            <table>
              <thead><tr><th>时间</th><th>事件</th><th>摘要</th></tr></thead>
              <tbody id="traceBody"></tbody>
            </table>
          </div>
        </section>
        <section>
          <h3>Files</h3>
          <div class="tree" id="fileTree">-</div>
        </section>
        <section>
          <h3>File Preview</h3>
          <pre id="filePreview">选择文件查看内容</pre>
        </section>
      </div>
    </main>
  </div>
<script>
const runListEl = document.getElementById('runList');
const runTitleEl = document.getElementById('runTitle');
const runMetaEl = document.getElementById('runMeta');
const runMissionEl = document.getElementById('runMission');
const planEl = document.getElementById('plan');
const traceBodyEl = document.getElementById('traceBody');
const fileTreeEl = document.getElementById('fileTree');
const filePreviewEl = document.getElementById('filePreview');
const agentBodyEl = document.getElementById('agentBody');
const flowBodyEl = document.getElementById('flowBody');
let currentRunId = null;
let eventSource = null;
let traceEvents = [];
let agentState = {};
let workOrders = {};
let refreshTimer = null;
let fileRefreshTimer = null;
const REFRESH_INTERVAL = 2000;
const FILE_REFRESH_INTERVAL = 3000;

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function formatTime(ts) {
  if (!ts) return '-';
  try { return new Date(ts).toLocaleString(); } catch { return ts; }
}

function statusClass(status) {
  if (!status) return 'status-badge';
  if (status.includes('思考')) return 'status-badge status-thinking';
  if (status.includes('执行') || status.includes('响应')) return 'status-badge status-running';
  if (status.includes('完成')) return 'status-badge status-done';
  if (status.includes('跳过')) return 'status-badge status-skip';
  if (status.includes('失败')) return 'status-badge status-error';
  return 'status-badge';
}

function resetLiveState() {
  traceEvents = [];
  agentState = {};
  workOrders = {};
  renderAgents();
  renderFlow();
}

function setAgent(name, status, workOrderId, title, ts, detail) {
  if (!name) return;
  const orderTitle = title || (workOrders[workOrderId] ? workOrders[workOrderId].title : '') || '';
  agentState[name] = {
    name,
    status,
    workOrderId,
    title: orderTitle,
    updatedAt: ts,
    detail,
  };
}

function updateFromEvent(evt) {
  traceEvents.push(evt);
  const type = evt.type;
  const payload = evt.payload || {};
  const ts = evt.ts;

  if (type === 'plan.request') {
    setAgent('supervisor', '规划中', null, '生成计划', ts, null);
  }
  if (type === 'plan.response') {
    setAgent('supervisor', '规划完成', null, '生成计划', ts, null);
  }
  if (type === 'work_order.start') {
    workOrders[payload.id] = {
      id: payload.id,
      skill: payload.skill,
      title: payload.title,
      status: '执行中',
      files: [],
    };
    setAgent(payload.skill, '执行中', payload.id, payload.title, ts, null);
  }
  if (type === 'skill.exec.request') {
    setAgent(payload.skill, '思考中', payload.work_order, null, ts, null);
  }
  if (type === 'skill.exec.response') {
    setAgent(payload.skill, '已响应', payload.work_order, null, ts, null);
  }
  if (type === 'skill.exec.parse_error') {
    setAgent(payload.skill, '解析失败', payload.work_order, null, ts, payload.error);
  }
  if (type === 'work_order.done') {
    const item = workOrders[payload.id] || { id: payload.id, skill: payload.skill };
    item.status = '完成';
    item.files = payload.files || [];
    item.summary = payload.summary || '';
    workOrders[payload.id] = item;
    setAgent(payload.skill, '完成', payload.id, item.title, ts, payload.summary);
  }
  if (type === 'work_order.skip') {
    const item = workOrders[payload.id] || { id: payload.id, skill: payload.skill };
    item.status = '跳过';
    item.reason = payload.reason || '';
    workOrders[payload.id] = item;
    if (payload.skill) {
      setAgent(payload.skill, '跳过', payload.id, item.title, ts, payload.reason);
    }
  }
}

function renderAgents() {
  const entries = Object.values(agentState);
  if (!entries.length) {
    agentBodyEl.innerHTML = '<tr><td colspan="4" class="muted">暂无 Agent 事件</td></tr>';
    return;
  }
  agentBodyEl.innerHTML = '';
  entries
    .sort((a, b) => (a.name || '').localeCompare(b.name || ''))
    .forEach((agent) => {
      const tr = document.createElement('tr');
      const status = agent.status || '-';
      const workOrderLabel = agent.workOrderId
        ? `${agent.workOrderId}${agent.title ? ' · ' + agent.title : ''}`
        : agent.title || '-';
      tr.innerHTML = `<td>${agent.name}</td><td><span class="${statusClass(status)}">${status}</span></td><td>${workOrderLabel}</td><td>${formatTime(agent.updatedAt)}</td>`;
      agentBodyEl.appendChild(tr);
    });
}

function renderFlow() {
  const orders = Object.values(workOrders);
  if (!orders.length) {
    flowBodyEl.innerHTML = '<tr><td colspan="5" class="muted">暂无工单</td></tr>';
    return;
  }
  flowBodyEl.innerHTML = '';
  orders
    .sort((a, b) => (a.id || '').localeCompare(b.id || ''))
    .forEach((order) => {
      const files = order.files && order.files.length ? order.files.join(', ') : '-';
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${order.id || '-'}</td><td>${order.skill || '-'}</td><td>${order.title || '-'}</td><td>${order.status || '-'}</td><td>${files}</td>`;
      flowBodyEl.appendChild(tr);
    });
}

function renderRuns(runs) {
  if (!runs.length) {
    runListEl.textContent = '没有找到 run 目录';
    return;
  }
  runListEl.innerHTML = '';
  runs.forEach((run) => {
    const div = document.createElement('div');
    div.className = 'run' + (run.run_id === currentRunId ? ' active' : '');
    div.innerHTML = `<div>${run.run_id}</div><div class="muted">${run.mission || '无 Mission'}</div>`;
    div.onclick = () => selectRun(run.run_id);
    runListEl.appendChild(div);
  });
}

function applyRunSummary(run) {
  if (!run) return;
  runTitleEl.textContent = run.run_id || '-';
  runMetaEl.textContent = run.mission ? 'Mission 已解析' : 'Mission 未解析';
  runMissionEl.textContent = run.mission || '无 Mission';
  planEl.textContent = run.plan ? JSON.stringify(run.plan, null, 2) : '-';
}

async function refreshRuns() {
  try {
    const data = await fetchJSON('/api/runs');
    renderRuns(data.runs || []);
    if (currentRunId && !data.runs.some((r) => r.run_id === currentRunId)) {
      currentRunId = null;
    }
  } catch (err) {
    console.warn('refresh runs failed', err);
  }
}

async function refreshCurrentRun() {
  if (!currentRunId) return;
  try {
    const run = await fetchJSON(`/api/runs/${currentRunId}`);
    applyRunSummary(run);
  } catch (err) {
    console.warn('refresh run failed', err);
  }
}

async function refreshFiles() {
  if (!currentRunId) return;
  try {
    const files = await fetchJSON(`/api/runs/${currentRunId}/files`);
    fileTreeEl.innerHTML = buildTree(files.tree || []);
    fileTreeEl.querySelectorAll('button[data-path]').forEach((btn) => {
      btn.onclick = async () => {
        const file = await fetchJSON(`/api/runs/${currentRunId}/file?path=${encodeURIComponent(btn.dataset.path)}`);
        filePreviewEl.textContent = file.content || '';
      };
    });
  } catch (err) {
    console.warn('refresh files failed', err);
  }
}

function renderTrace(events) {
  traceBodyEl.innerHTML = '';
  if (!events.length) {
    traceBodyEl.innerHTML = '<tr><td colspan="3" class="muted">无 trace</td></tr>';
    return;
  }
  events.slice(-200).forEach((evt) => {
    const tr = document.createElement('tr');
    const summary = evt.payload && typeof evt.payload === 'object'
      ? JSON.stringify(evt.payload).slice(0, 120)
      : '';
    tr.innerHTML = `<td>${formatTime(evt.ts)}</td><td>${evt.type}</td><td>${summary}</td>`;
    traceBodyEl.appendChild(tr);
  });
}

function buildTree(nodes) {
  if (!nodes || !nodes.length) return '<div class="muted">无文件</div>';
  const items = nodes.map((node) => {
    if (node.type === 'dir') {
      return `<li><strong>${node.name}</strong>${buildTree(node.children)}</li>`;
    }
    return `<li><button data-path="${node.path}">${node.name}</button> <span class="muted">${node.size}B</span></li>`;
  });
  return `<ul>${items.join('')}</ul>`;
}

function startStream(runId, since) {
  if (eventSource) {
    eventSource.close();
  }
  eventSource = new EventSource(`/api/runs/${runId}/stream?since=${since}`);
  eventSource.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data);
      if (payload && payload.event) {
        updateFromEvent(payload.event);
        renderAgents();
        renderFlow();
        renderTrace(traceEvents);
      }
    } catch (err) {
      console.error('SSE parse error', err);
    }
  };
}

function getQueryRunId() {
  const params = new URLSearchParams(window.location.search);
  return params.get('run');
}

async function selectRun(runId) {
  currentRunId = runId;
  resetLiveState();
  renderRuns(await fetchJSON('/api/runs').then((r) => r.runs));
  const run = await fetchJSON(`/api/runs/${runId}`);
  applyRunSummary(run);

  const trace = await fetchJSON(`/api/runs/${runId}/trace`);
  (trace.events || []).forEach((evt) => updateFromEvent(evt));
  renderAgents();
  renderFlow();
  renderTrace(traceEvents || []);

  const files = await fetchJSON(`/api/runs/${runId}/files`);
  fileTreeEl.innerHTML = buildTree(files.tree || []);
  fileTreeEl.querySelectorAll('button[data-path]').forEach((btn) => {
    btn.onclick = async () => {
      const file = await fetchJSON(`/api/runs/${runId}/file?path=${encodeURIComponent(btn.dataset.path)}`);
      filePreviewEl.textContent = file.content || '';
    };
  });

  startStream(runId, traceEvents.length);
}

async function init() {
  const data = await fetchJSON('/api/runs');
  renderRuns(data.runs || []);
  const queryRun = getQueryRunId();
  if (queryRun) {
    try {
      await selectRun(queryRun);
      return;
    } catch (err) {
      console.warn('failed to load query run', err);
    }
  }
  if (data.runs && data.runs.length) {
    selectRun(data.runs[0].run_id);
  }

  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(() => {
    refreshRuns();
    refreshCurrentRun();
  }, REFRESH_INTERVAL);

  if (fileRefreshTimer) clearInterval(fileRefreshTimer);
  fileRefreshTimer = setInterval(() => {
    refreshFiles();
  }, FILE_REFRESH_INTERVAL);
}

init().catch((err) => {
  runListEl.textContent = '加载失败：' + err.message;
});
</script>
</body>
</html>"""


def _render_submit() -> str:
    return """<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Solo Company OS - 任务提交</title>
  <style>
    :root { color-scheme: light; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; background: #f6f7fb; color: #1f2430; }
    header { padding: 16px 24px; background: #111827; color: #fff; font-weight: 600; display: flex; align-items: center; justify-content: space-between; }
    header nav a { color: #cbd5f5; text-decoration: none; margin-left: 12px; font-size: 13px; }
    header nav a.active { color: #fff; font-weight: 600; }
    main { padding: 32px 24px; max-width: 860px; margin: 0 auto; }
    section { background: #fff; border-radius: 14px; padding: 20px; box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08); }
    .form-grid { display: grid; gap: 12px; grid-template-columns: 1fr 140px 180px auto; align-items: center; }
    .form-grid input, .form-grid select { width: 100%; padding: 8px 10px; border-radius: 8px; border: 1px solid #e2e8f0; font-size: 13px; }
    .form-grid button { border: 0; background: #3b82f6; color: #fff; padding: 8px 14px; border-radius: 8px; cursor: pointer; }
    .muted { color: #94a3b8; font-size: 12px; }
  </style>
</head>
<body>
  <header>
    <span>Solo Company OS Dashboard</span>
    <nav>
      <a class="active" href="/submit">任务提交</a>
      <a href="/history">历史任务</a>
    </nav>
  </header>
  <main>
    <section>
      <h2>提交新的 Mission</h2>
      <p class="muted">输入任务后系统会立即执行，并自动跳转到历史任务页面查看执行过程。</p>
      <form id="runForm" class="form-grid">
        <input id="missionInput" type="text" placeholder="输入你要执行的任务" required />
        <select id="providerSelect">
          <option value="mock">mock</option>
          <option value="openai">openai</option>
        </select>
        <input id="modelInput" type="text" placeholder="Model (可选)" />
        <button type="submit">开始执行</button>
      </form>
      <p class="muted" id="runFormHint">支持直接输入任务文本</p>
    </section>
  </main>
<script>
const runFormEl = document.getElementById('runForm');
const runFormHintEl = document.getElementById('runFormHint');
const missionInputEl = document.getElementById('missionInput');
const providerSelectEl = document.getElementById('providerSelect');
const modelInputEl = document.getElementById('modelInput');

function resetHint() {
  runFormHintEl.textContent = '支持直接输入任务文本';
}

window.addEventListener('pageshow', resetHint);
resetHint();

runFormEl.addEventListener('submit', async (event) => {
  event.preventDefault();
  const mission = missionInputEl.value.trim();
  if (!mission) {
    runFormHintEl.textContent = '请输入 Mission 后再执行';
    return;
  }
  runFormHintEl.textContent = '正在提交任务...';
  try {
    const payload = {
      mission,
      provider: providerSelectEl.value,
      model: modelInputEl.value.trim() || null,
      skill_dir: [],
    };
    const res = await fetch('/api/runs/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error(await res.text());
    }
    const data = await res.json();
    missionInputEl.value = '';
    runFormHintEl.textContent = '已开始执行，正在跳转历史任务...';
    window.location.href = `/history?run=${encodeURIComponent(data.run_id)}`;
  } catch (err) {
    runFormHintEl.textContent = '执行失败：' + err.message;
  }
});
</script>
</body>
</html>"""