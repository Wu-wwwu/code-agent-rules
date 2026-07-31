# 专项路由

本表只决定加载路径，不包含执行规则。每次只加载当前动作命中的最少方法；多项同时命中则取并集，任何方法都不能替代另一方法的门禁。义务完成即退出。

| 信号 | 方法 |
|---|---|
| 删除/覆盖数据、改权限或安全、覆盖配置、外部副作用、公开 API/Schema/共享契约变化 | `methods/destructive-analysis.md` |
| 金额/支付/结算，或状态/权限/角色的目标业务语义 | `methods/business-rules.md` |
| 历史技术决策可能约束当前方案 | `methods/decision-recall.md` |
| major 升级、弃用到期或上游移除 | `methods/dependency-upgrade.md` |
| 生成器、构建/格式化/编译工具、CI/CD 或生成物变化 | `methods/toolchain-scope.md` |
| 独立子任务并行调查或专业复核确有净收益 | `methods/multi-agent.md` |
| 技术栈不明、新项目选型或技术方向改变系统边界 | `methods/technology-selection.md` |
| 竞态/时序/非确定性/跨模块 Bug，或无法稳定复现 | `methods/bug-diagnosis.md` |
| 性能、容量、延迟、吞吐或资源消耗用于目标、选型或完成结论 | `methods/performance-evidence.md` |
| 新增抽象/分层/模式、提取公共代码或结构重构 | `methods/neutral-design.md` |
| 需从代码/Schema/表识别实体、关系或表示变换 | `methods/data-entity-analysis.md` |
| 新功能、计划、跨模块、上下文恢复，或实现路径/验证接缝不清 | `methods/project-context.md` |

仅在已加载方法准备实际读写目标项目的 `documents/*.md` 时，再加载 `methods/project-documents.md`。Bug 优先走诊断；只有上下文不足以诊断时才补项目上下文。权限执行风险走破坏性分析；权限目标语义不明时再叠加业务规则。
