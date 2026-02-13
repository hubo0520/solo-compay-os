# Solo Company OS (一人公司 Agent / Agent Company-in-a-Box)

> **一个可运行的学习型开源产品**：把“软件公司工作流”装进你的电脑。  
> 你只需要下发 Mission（目标），系统会用 **Agent Skills（SKILL.md）** 组织一个极简团队（PM / Tech Lead / Engineer / QA / Coach），生成可读、可改、可复现的产物（PRD、工单、架构、代码、测试、复盘）。

---

## 你能用它做什么？

- ✅ **练手 Agent/LLM**：规划（Plan）→ 执行（Act）→ 校验（Check）→ 复盘（Reflect）
- ✅ **练手 Agent Skills**：如何写一个可复用的 `SKILL.md`，如何做 discovery / validation / activation
- ✅ **练手工程化**：结构化输出（JSON）、Trace（jsonl）、可复现运行（runs/<id>）
- ✅ **展示 AI coding 水平**：清晰架构 + 可跑 demo + 文档齐全 + 可扩展

> 项目定位：**不需要注册公司、不强调盈利**。它更像一个“可部署的练手项目 / 教学产品”，帮助更多人把 agent 这套东西跑起来、理解透、改得动。

---

## 为什么现在做这个很合适？

1) **Agent Skills 标准正在成为事实标准**  
   Skill = 一个目录 + `SKILL.md`（YAML frontmatter + Markdown 指令）+ 可选 resources。它强调按需加载、可移植、可审计。  
   规范细节见：`agentskills.io/specification`（本 repo 也做了基础校验）。

2) **SkillsMP 正在把“技能”变成可搜索、可复用的生态**  
   SkillsMP 聚合了大量来自 GitHub 的现成 skills，并提供搜索与 REST API。你可以从 marketplace 里直接“拿来即用/即改”。  
   （本项目内置 `solo-company skillsmp search` 命令，支持在你提供 API Key 的情况下搜索。）

> 换句话说：你在做的是一个 **顺势而为的“技能驱动型 agent 产品”**，很容易长成爆款。

---

## 30 秒快速体验（无需任何 API Key）

> 默认使用 `MockProvider`（离线、确定性输出），确保“开箱即跑”。

```bash
# 1) 安装
pip install -e ".[dev]"

# 2) 跑一个 Mission（纯文本）
solo-company run "Build a runnable demo web/API project for learners."

# 3) 或者直接传 mission 文件（推荐，便于复现）
solo-company run scenarios/missions/landing_fastapi.yaml
```

运行完成后，你会看到一个新的 run 目录：

```
runs/<run_id>/
  plan.json
  trace.jsonl
  RUN.md
  workspace/
    docs/
      PRD.md
      BACKLOG.md
      ARCHITECTURE.md
      RETRO.md
    app/
      main.py
    tests/
      test_app.py
    requirements.txt
    pyproject.toml
    README.md
```

---

## 用真实模型跑（OpenAI-compatible）

> 真实模型的输出质量会明显更好（PRD 更像 PRD、代码更像可交付代码）。

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="..."
# 可选：export OPENAI_BASE_URL="https://api.openai.com/v1"

solo-company run "Write a PRD for a minimal note-taking app" --provider openai
```

⚠️ 说明：

- 本项目的 openai provider 是**最小实现**：使用 OpenAI-compatible 的 `/v1/chat/completions`。
- 不同供应商对该接口的兼容性可能不同；如果遇到 JSON 解析失败，会在 `RUN.md` 和 `trace.jsonl` 中记录 warnings。

---

## 项目核心概念（建议你先读完这一段）

### Mission → Work Orders → Artifacts

- **Mission**：用户一句话目标（输入）
- **Work Orders**：Supervisor 规划出来的工单列表（中间态）
- **Artifacts**：最终落到 workspace 里的文件（输出）

对应到运行流程：

```
Mission
  -> Plan (JSON)
    -> WorkOrders (JSON)
      -> Execute each WorkOrder with one Skill (JSON)
        -> Write files into workspace
          -> Run report + Trace
```

### “技能”是内容层，“调度器”是执行层

- Skill（SKILL.md）负责：岗位 SOP、输出格式、质量门槛
- Orchestrator 负责：发现技能、生成计划、逐工单执行、写产物、写 trace

这会让你的项目非常“像产品”：
- 增加新技能 = 加文件夹，不用写一堆框架代码
- 复用别人技能 = 从 SkillsMP 复制目录即可

---

## Repo 结构

```
src/solo_company_os/
  cli.py                    # Typer CLI：solo-company
  core/
    skill.py                # 解析 SKILL.md（frontmatter + body）
    skill_index.py          # 扫描 skills 目录，做校验与索引
    orchestrator.py         # Plan -> Execute -> Write -> Report
    providers/
      mock.py               # 离线确定性 provider（CI 也用它）
      openai_compatible.py  # OpenAI-compatible chat/completions provider
    trace.py                # trace.jsonl 事件记录

.agents/skills/             # 本 repo 自带示例 skills
scenarios/missions/         # 示例 mission（可复现）
docs/                       # 详细说明文档
AGENTS.md                   # 给 AI coding agents 的贡献指南
```

---

## Skills（Agent Skills）怎么写？

你可以把 skill 理解成“岗位 SOP 的可复用模块”。

### 一个最小 skill 长这样

```
my-skill/
  SKILL.md
```

SKILL.md 顶部必须有 YAML frontmatter：

```yaml
---
name: my-skill
description: What this skill does and when to use it.
---
```

然后 body 部分写 SOP 指令、例子、输出要求。

### 本 repo 的强约束：所有 skills 都要输出 JSON

我们要求 skills 输出：

```json
{
  "files": [{"path": "...", "content": "..."}],
  "summary": "short summary",
  "warnings": ["optional"]
}
```

原因：
- 产物需要稳定写入 workspace
- 后续 eval / dashboard 才能可靠消费

### 创建新 skill 的推荐方式

1) 复制模板：

```bash
cp -r .agents/skills/skill-template .agents/skills/<your-skill-name>
```

2) 修改 `.agents/skills/<your-skill-name>/SKILL.md` 的 frontmatter：
- `name:` 必须和目录名一致（kebab-case）
- `description:` 写清楚“做什么 + 什么时候用”，并包含触发关键词

3) 校验：

```bash
solo-company skills validate
```

---

## 如何从 SkillsMP 获取现成 skills？

SkillsMP 是一个 marketplace（聚合来自 GitHub 的 skills）。你可以：

- **方式 A（最简单）**：网页搜，复制 skill 目录到 `.agents/skills/`  
- **方式 B（进阶）**：用 SkillsMP REST API 搜索（需要 API key）

本 repo 提供 CLI：

```bash
export SKILLSMP_API_KEY="sk_live_..."
solo-company skillsmp search "fastapi"
solo-company skillsmp search "how to create a web scraper" --ai
```

更多说明见：
- `docs/04-how-to-add-skills-from-skillsmp.md`

---

## Trace / Debug：为什么这个项目“适合学习”？

每次运行都会写：

- `plan.json`：Supervisor 的工单计划（可复现）
- `trace.jsonl`：每一步请求/响应/写入文件（可复盘）
- `RUN.md`：运行报告（产物清单 + warnings）

你可以把它当成一个“透明的 agent 工作流录像”。

---

## 文档导航

- `docs/00-background.md`：背景与意义
- `docs/01-quickstart.md`：快速开始
- `docs/02-architecture.md`：架构说明
- `docs/03-how-skills-work.md`：Skills 机制
- `docs/04-how-to-add-skills-from-skillsmp.md`：从 SkillsMP 获取技能
- `docs/05-how-to-write-missions.md`：写 Mission
- `docs/06-evals-and-scenarios.md`：Evals 规划
- `docs/07-roadmap.md`：Roadmap
- `docs/08-security.md`：安全注意事项

---

## 让 AI 帮你实现这个项目：推荐工作方式

如果你要用 AI 来持续实现功能（你在做“AI coding 作品集”），建议这样组织：

1) **把约束写进 AGENTS.md**  
   - 哪些命令必须始终可跑
   - 输出 contract（JSON）
   - 目录结构不要乱

2) 每次只让 AI 做一个小 PR（小步快跑）
   - “新增 `solo-company eval` 子命令”
   - “新增一个 skill：xxx”
   - “给 orchestrator 增加重试和 timeout”

3) 给 AI 明确验收标准（Definition of Done）
   - 例如：“`pytest` 全绿 + `solo-company run ... --provider mock` 可跑 + docs 更新”

本 repo 已经提供 `AGENTS.md` 作为 AI coding agent 的贡献指南。

---

## 安全提醒（非常重要）

- Marketplace skills 本质上来自开源仓库  
- 如果 skill 携带 scripts / 命令：**默认不要自动执行**  
- 安装 skill 前先 review，就像装任何依赖一样

更多见：`docs/08-security.md`

---

## 可视化（Dashboard）

> 提供本地 Web Dashboard，用于实时查看任务提交、历史运行、Agent 分工与执行过程。

### 启动方式

```bash
solo-company dashboard
```

默认访问地址：`http://127.0.0.1:8000`

### 功能概览

- **任务提交页**：输入 Mission，一键提交运行
- **历史任务页**：查看所有运行记录与状态
- **实时执行视图**：流式展示 Agent 接受指令、执行步骤、产物写入与协作信息流

### 适合场景

- 复盘完整的 Agent 工作流
- 对比不同 Mission 的产出质量
- 观察各 Agent 的角色分工与执行轨迹

---

## License

MIT

---

## Acknowledgements / References

- Agent Skills spec: see `agentskills.io/specification`
- Skills marketplace: SkillsMP (skillsmp.com)