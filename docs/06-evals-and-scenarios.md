# Scenarios & Evals（规划）

为什么要做 eval？

很多 agent 项目只能“跑通一次”，但学习型项目需要能反复跑、能回归。

v0.1 先提供：
- 示例 mission 文件（scenarios/missions）
- `MockProvider` 端到端跑通 + pytest

后续可以加：
- `solo-company eval run <mission>`：判断生成的文件是否满足预期
- 更严格的 judge：比如 PRD 必须包含 Acceptance criteria 等

如果你想实现 eval，可以从：
- 读取 mission 文件
- 运行 orchestrator（mock 或真实）
- 检查 workspace 是否包含必需文件
- 对文件内容做最小规则校验（regex / json schema / markdown section）
开始。
