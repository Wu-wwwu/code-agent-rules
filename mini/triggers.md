# 专项方法路由

本表只识别候选方法；详细适用条件、快速路径和执行要求在对应方法中确认。多个信号同时出现时只加载覆盖当前动作所需的最小方法集合，义务完成后退出。

以下情况保持 agent.md 轻量路径：已有新鲜且适用的方法上下文；任务局部、直接可验证且无风险升级或方案选择；仅作一般解释且不需要专项判断、证据链、方案或风险结论。用户已给出决策可以缩短流程，但不能跳过破坏性、安全、金额或契约验证。

| # | 候选信号 | 加载方法 |
|---|---------|---------|
| T1 | 数据删除/覆盖、权限修改、配置覆盖或有副作用的外部操作 | `methods/destructive-analysis.md` |
| T2 | 公开 API、Schema 或共享数据契约变更 | `methods/destructive-analysis.md` |
| T3 | 金额、货币、支付/退款/结算，或状态/权限/角色业务语义 | `methods/business-rules.md` |
| T4 | 需要回查历史技术决策或既有约定 | `methods/decision-recall.md` |
| T5 | 依赖 major 升级、弃用到期或上游移除 | `methods/dependency-upgrade.md` |
| T6 | 代码生成器、构建/格式化/编译工具或 CI/CD 变化 | `methods/toolchain-scope.md` |
| T7 | 值得拆分的独立子任务、跨模块并行调查或专业审查 | `methods/multi-agent.md` |
| T8 | 技术栈不明确、新项目选型或技术方向可能改变系统边界 | `methods/technology-selection.md` |
| T9 | 竞态/时序/非确定性/跨模块 Bug，或无法稳定复现 | `methods/bug-diagnosis.md` |
| T10 | 性能、容量、延迟、吞吐或资源消耗是目标或方案依据 | `methods/performance-evidence.md` |
| T11 | 新增抽象/设计模式/分层，提取公共代码或重构结构 | `methods/neutral-design.md` |
| T12 | 从代码/Schema/表识别实体、关系或表示变换 | `methods/data-entity-analysis.md` |
| T13 | 新功能、计划、跨模块、上下文恢复或实现路径不清 | `methods/project-context.md` |

准备读取或写入目标项目的 `documents/*.md` 时，由已加载的方法继续加载支持方法 `methods/project-documents.md`。
