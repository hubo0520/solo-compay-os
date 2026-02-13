# Security Notes

Skills（尤其是来自 marketplace 的 skills）可能包含 scripts 或建议执行命令。

本 repo 的默认策略：
- v0.1 不会自动执行 skills 的脚本
- 只生成文件
- 如果未来加入脚本执行：
  - 必须提供 sandbox（隔离目录、限制命令）
  - 必须提供白名单/黑名单
  - 默认需要人类确认（HITL）
  - 所有执行写入 trace

把 skills 当作任何开源代码：安装前先 review。
