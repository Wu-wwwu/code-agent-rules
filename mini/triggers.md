# 专项路由

本表只决定加载路径，不包含执行规则。每次只加载当前动作命中的最少方法；多项同时命中则取并集，任何方法都不能替代另一方法的门禁。先检查会影响安全、权限、数据、公开契约、共享状态、外部副作用或回退代价的信号。义务完成即退出。

路由不要求任务在单一模式中择一。分析视角可以叠加；只有输出结构发生冲突时才指定一个主视角。路由标签和输出前缀不是默认要求，除非下游系统明确解析它们。

| 信号 | 方法 |
|---|---|
| 删除/覆盖数据、改权限或安全、覆盖配置、外部副作用、公开 API/Schema/共享契约变化 | `methods/destructive-analysis.md` |
| 金额/支付/结算，或状态/权限/角色的目标业务语义 | `methods/business-rules.md` |
| 历史技术决策可能约束当前方案 | `methods/decision-recall.md` |
| major 升级、弃用到期或上游移除 | `methods/dependency-upgrade.md` |
| 生成器、构建/格式化/编译工具、CI/CD 或生成物变化 | `methods/toolchain-scope.md` |
| 子任务有独立完成标准且不依赖未产生的前序结果，并适合只读并行、隔离写入或独立专业复核 | `methods/multi-agent.md` |
| 技术栈不明、新项目选型或技术方向改变系统边界 | `methods/technology-selection.md` |
| 竞态/时序/非确定性/跨模块 Bug，或无法稳定复现 | `methods/bug-diagnosis.md` |
| 性能、容量、延迟、吞吐或资源消耗用于目标、选型或完成结论 | `methods/performance-evidence.md` |
| 新增抽象/分层/模式、提取公共代码或结构重构 | `methods/neutral-design.md` |
| 需从代码/Schema/表识别实体、关系或表示变换 | `methods/data-entity-analysis.md` |
| 新功能、计划、跨模块、上下文恢复、需建立或移交任务环境，或实现路径/验证接缝不清 | `methods/project-context.md` |

## 分析视角映射
本表只帮助已命中的方法选择分析关注点，不单独触发方法加载。局部且直接可验证的任务未命中上表信号时仍直接执行。
| 分析视角 | 典型信号 | 优先复用的方法 |
|---|---|---|
| 全局拓扑 | 多步骤、跨模块、资源调度、迁移计划 | `methods/project-context.md`、`methods/destructive-analysis.md`、`methods/multi-agent.md` |
| 局部影响 | 局部修改、接口调用、具体文案、工具操作 | 无默认方法；仅按上表实际信号加载 |
| 发散探索 | 根因未知、需求模糊、技术方向未定 | `methods/bug-diagnosis.md`、`methods/technology-selection.md` |
| 状态变迁 | 状态、数据、并发、事务、生命周期、回滚 | `methods/bug-diagnosis.md`、`methods/data-entity-analysis.md`、`methods/destructive-analysis.md` |
| 职责与表示 | 需在数据访问、业务模型、算法结构或边界契约之间选择贴合代码职责的分析方式 | 无默认方法；按代码实际职责选择证据、表示和验证接缝 |
仅在已加载方法准备实际读写目标项目的 `documents/*.md` 时，再加载 `methods/project-documents.md`。Bug 优先走诊断；只有上下文不足以诊断时才补项目上下文。权限执行风险走破坏性分析；权限目标语义不明时再叠加业务规则。
