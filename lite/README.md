# 规则集说明与 token 预算

三层结构：`agent.md`（常驻基础规范）→ `triggers.md`（每任务短路由）→ `methods/`（按需加载，含 `templates.md` 仅写入时加载）。

## Token 预算表（防回归）

> 预算为硬约束：新增内容必须从本文件或他处删减抵消，不得突破上限。

| 文件 | 现状 ≈token | 预算上限 | 加载时机 |
|------|-----------|---------|---------|
| agent.md | ≈1 400 | 1 500 | 常驻 |
| triggers.md | ≈1 000 | 1 100 | 每任务校准 |
| methods/destructive-analysis.md | 1 534 | 1 600 | T1/T2 命中 |
| methods/project-context.md | ≈1 600 | 1 750 | T13 命中 |
| methods/project-documents.md | 1 507 | 1 600 | 读写 documents 时 |
| methods/business-rules.md | 1 277 | 1 400 | T3 命中 |
| methods/multi-agent.md | ≈700 | 800 | T7 命中 |
| 其余 7 个方法 | 300–700 | ≤800/个 | 对应触发命中 |
| methods/templates.md | 853 | 1 000 | 仅写入 documents 时 |
| **全库合计** | **≈13 700** | **14 500** | — |

## 典型场景预算（含常驻）

- 轻量任务：≈2.4k（agent + triggers）
- 破坏性任务：≈3.8k
- 业务规则×破坏性：≈5.1k
- 最重路径（br+da+pc+pd）：≈7.5k

## 维护约定

- 安全方法（destructive-analysis、business-rules、dependency-upgrade、bug-diagnosis）压缩不得删减门禁语义：分级判定条件、授权/确认分支、数据安全语义、诊断阶段必须完整保留
- 示例（neutral-design 正反例、bug-diagnosis 日志、performance-evidence 格式）属于 few-shot 价值，不删除
- 跨文件重复原则一律引用 agent.md，不在方法内重述
- 预算核查：使用目标模型 tokenizer 时以实测为准；无 tokenizer 时用字符统计作近似，超出预算即回退或重构
