# Quickstart

> 你可以先用 `mock` provider 跑通全流程（无需任何 API Key），再切换到真实模型。

## 1) 安装

```bash
git clone <your-repo-url>
cd solo-company-os
python -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"
```

## 2) 运行一个 Mission（离线 mock）

```bash
solo-company run "Build a runnable demo web/API project for learners."
```

或者直接传 mission 文件：

```bash
solo-company run scenarios/missions/landing_fastapi.yaml
```

运行成功后会生成：

- `runs/<run_id>/plan.json`
- `runs/<run_id>/trace.jsonl`
- `runs/<run_id>/RUN.md`
- `runs/<run_id>/workspace/`（你的产物都在这里）

## 3) 切到真实模型（OpenAI-compatible）

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="..."
# 可选：export OPENAI_BASE_URL="https://api.openai.com/v1"

solo-company run "Write a PRD for a minimal note-taking app" --provider openai
```

> 注意：不同供应商对 OpenAI-compatible 接口的支持程度不同。本项目的 openai provider 只实现了最小的 `/v1/chat/completions` 调用。
