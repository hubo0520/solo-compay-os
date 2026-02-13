# Architecture

## 目标：让“公司运转”变成一个可复现的 pipeline

核心闭环：

```
Mission
  -> Plan (work orders)
    -> Execute each work order with a skill
      -> Write artifacts into workspace
        -> Run Report + Trace
```

## 关键模块

- SkillIndex
  - 扫描多个技能目录（`.agents/skills/` 等）
  - 解析 `SKILL.md` frontmatter 做验证
  - 需要时才加载 body

- Orchestrator
  - 用 Provider 生成 Plan（JSON）
  - 逐个 WorkOrder 激活对应 skill 执行（JSON）
  - 写入 workspace，并记录 trace

- Provider
  - MockProvider：离线确定性输出（CI 也用它）
  - OpenAICompatibleProvider：用于真实模型跑

- Trace
  - `trace.jsonl` 记录每个步骤请求/响应/写入文件

## 为什么这样设计？

- **教育**：每一步都有产物和 trace，易于学习和调试
- **可扩展**：增加 skill 不需要改 orchestrator 太多
- **可评测**：结构化输出 + 场景脚本 = 可回归
