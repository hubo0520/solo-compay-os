# 如何从 SkillsMP 找现成技能？

SkillsMP 是一个 agent skills marketplace，聚合了大量来自 GitHub 的 SKILL.md skills。

## 方式 A：网页搜索（最简单）

打开：

- https://skillsmp.com/search
- https://skillsmp.com/categories

找到合适 skill 后，一般会给出安装指令（例如复制到 `.claude/skills/` 或 `~/.codex/skills/`）。

## 方式 B：用本项目的 CLI 搜索（需要 API key）

SkillsMP 提供 REST API（需要 API Key），支持 keyword search 和 AI search。

1) 获取 API Key
- 参考 SkillsMP 文档：https://skillsmp.com/docs/api

2) 配置环境变量

```bash
export SKILLSMP_API_KEY="sk_live_..."
```

3) 搜索

```bash
solo-company skillsmp search "fastapi"
solo-company skillsmp search "how to create a web scraper" --ai
```

> 说明：SkillsMP 返回 JSON 的具体字段可能随版本变化，本项目目前以“打印 JSON”为主，后续可逐步做更漂亮的表格渲染。
