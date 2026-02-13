# Roadmap

## v0.1（当前）
- [x] Skill discovery + validation（SKILL.md）
- [x] Orchestrator：plan -> execute -> artifacts
- [x] MockProvider：离线可跑 + CI 友好
- [x] OpenAI-compatible provider（最小 chat/completions）
- [x] Trace：trace.jsonl + plan.json + RUN.md
- [x] 示例 skills + 示例 missions

## v0.2（建议）
- [ ] `solo-company eval`：场景评测命令
- [ ] 更好的 plan schema（支持依赖、并行、重试策略）
- [ ] 工具层（filesystem/git/shell）抽象
- [ ] 安全沙箱：脚本执行白名单 + 人类确认（HITL）

## v0.3（可选）
- [ ] Web Dashboard：Kanban + Trace + Artifact explorer
- [ ] GitHub Issues integration（把 backlog 同步到 Issues）
- [ ] SkillsMP “一键安装”到 `.agents/skills/`
