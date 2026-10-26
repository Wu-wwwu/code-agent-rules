# Lite 规则体系

三层结构：`agent.md`（常驻基础规范）→ `triggers.md`（每任务短路由）→ `methods/`（按需加载，含 `templates.md` 仅写入时加载）。

## 定位

- `agent.md` 保留执行循环、证据、安全和完成条件。
- `triggers.md` 只负责把当前任务信号路由到对应方法。
- `methods/` 提供自包含的专项方法；命中时加载，义务完成后退出。
- `project-documents.md` 与 `templates.md` 支持按需创建项目长期记忆；安装时不预置根 `documents/`。
- `methods/security.md` 提供认证、输入、命令、路径、凭据和测试隔离的通用安全要求；它不能替代破坏性分析或平台权限控制。

`py lite/check_references.py` 检查路由集合、方法文件和跨方法引用是否有效。

## 维护约定

- 安全方法（security、destructive-analysis、business-rules、dependency-upgrade、bug-diagnosis）压缩不得删减判定与确认语义：分级判定条件、授权/确认分支、数据安全语义、诊断阶段必须完整保留
- 示例（neutral-design 正反例、bug-diagnosis 日志、performance-evidence 格式）属于 few-shot 价值，不删除
- 跨文件重复原则一律引用 agent.md，不在方法内重述
- 新增或扩展方法时保持路由清晰、按需加载和版本自包含
