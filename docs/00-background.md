# 背景与意义

## 这是什么？

**Solo Company OS** 是一个“可部署的一人公司（Agent Company-in-a-Box）”练手项目：

- 你给一句话 Mission（目标）
- 系统模拟一个极简的软件团队（PM / Tech Lead / Engineer / QA / Coach）
- 通过 **Agent Skills（SKILL.md）** 把每个岗位的 SOP 固化成可复用模块
- 最终在本地 workspace 里生成可查看、可运行的产物（文档 / 代码 / 测试 / 复盘）

它的目标不是注册公司或商业化，而是：

- 让更多人能 **一键部署** 并反复练习 Agent + LLM 的核心技术栈
- 让作者通过“工程化、可复现、可扩展”的实现展示 AI coding 水平

## 为什么用 Agent Skills？

Agent Skills 是一个开放标准：一个 skill 就是一个目录 + `SKILL.md`（含 YAML frontmatter + Markdown 指令），可选 scripts / assets / references。  
优点：

- **按需加载（progressive disclosure）**：只把必要的信息放进上下文
- **可移植**：同一个 skill 可以被不同的 agent/IDE/CLI 工具复用
- **可审计**：skill 的 SOP 就是文本文件，可 review、可 version control

这也解释了为什么 SkillsMP（skillsmp.com）这样的 marketplace 会出现：它聚合了大量来自 GitHub 的现成 skills，方便大家直接拿来用、改、组合。

## 项目能帮你学到什么？

- Skills discovery：扫描 skill 目录、解析 frontmatter、按需加载 body
- Orchestration：Supervisor 规划 → Worker 执行 → 产物落盘
- Structured output：把 LLM 输出约束成 JSON，保证可解析、可评测
- Trace：每一步写入 trace.jsonl，可复盘、可调试
- Eval/Scenario（后续）：把“能跑通一次”升级成“可复现/可回归”

