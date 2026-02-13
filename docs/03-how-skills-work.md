# Skills 是怎么工作的？

## 目录结构

一个 skill 是一个目录，至少包含：

- `SKILL.md`（必须）
- `assets/`（可选：模板、静态资源）
- `references/`（可选：长文档）
- `scripts/`（可选：脚本）

本 repo 的示例 skills 在：

- `.agents/skills/<skill-name>/SKILL.md`

## SKILL.md 最重要的两件事

1) YAML frontmatter（name + description 必须）  
2) Markdown body（给 agent 的 SOP 指令）

本项目会校验：
- `name` 必须是 kebab-case 且与目录名一致
- `description` 必须非空

## 为什么强调输出 JSON？

因为我们想让下游（orchestrator / eval / dashboard）稳定消费产物。  
所以 repo 内的示例 skills 都要求输出：

```json
{
  "files": [{"path": "...", "content": "..."}],
  "summary": "...",
  "warnings": ["..."]
}
```

你也可以把这个当成写 skills 的“工程化最佳实践”。
