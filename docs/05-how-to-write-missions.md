# 如何写 Mission？

你可以直接在命令行写一句话：

```bash
solo-company run "Build a minimal landing page with FastAPI"
```

也可以用文件（推荐，便于复现和评测）：

```bash
solo-company run scenarios/missions/landing_fastapi.yaml
```

## Mission 文件格式（v0.1）

```yaml
mission: |
  这里写你的目标，支持多行。
notes:
  audience: 谁来用
  constraints:
    - 想要哪些限制（例如必须离线、必须小而美）
```

当前 orchestrator 只读取 `mission` 字段，其余字段作为备注。
