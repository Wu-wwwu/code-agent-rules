# 专项方法路由

本表只识别候选方法；适用条件、快速路径和执行要求由对应方法自裁决。多信号同时出现时按依赖顺序加载覆盖当前动作所需的最小方法集合；不得用一个方法替代另一个方法的强制义务；义务完成即退出。

**轻量路径**（保持 agent.md 守则即可）：已有新鲜适用的方法上下文；任务局部、直接可验证且无风险升级或方案选择；仅一般解释、不需专项判断/证据链/方案/风险结论。用户已给出决策可缩短探索，但**不得跳过任何已命中方法规定的验证、隔离、迁移、回退或确认门禁**——尤其数据删除/覆盖、权限与安全、配置覆盖、外部副作用、金额语义、公开契约变更。

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
| T13 | 新功能、计划、跨模块、上下文恢复、需建立/移交任务环境或实现路径不清 | `methods/project-context.md` |

**读写目标项目 `documents/*.md`**：由已加载的方法继续加载 `methods/project-documents.md`；写入需模板时再加载 `methods/templates.md`。

**路由裁决**：Bug 以 T9 为主，仅当目标/范围/模块边界/实现路径不足以支持诊断时先 T13 补缺口再回 T9，不重复扫描。权限修改命中 T1；权限/角色语义不明确时同时命中 T3，两者不得互相替代。

**转引**：方法执行中发现破坏性/金额/数据安全信号时，由当前方法自行加载 `methods/destructive-analysis.md` 或 `methods/business-rules.md`，不回查本表；级联加载的方法义务完成后同样退出。
