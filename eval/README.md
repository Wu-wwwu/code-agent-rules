# 规则回归验证基准（eval）

> 供规则维护者使用：每次修改 `mini/`、`lite/`、`rules/` 或 `self/` 后，用本目录的基准任务验证 Agent 行为未退化。规则集自身也应遵守它要求的"循环校验"。

## 怎么用

1. 运行 `py eval/check_rule_references.py`（也可用环境中的 `python`），检查跨文件规则引用的目标文件和章节标题仍然存在、未重新引入数字章节号引用，并确认根目录 `AGENTS.md` 与 `CLAUDE.md` 都是只包含一个有效规则路径的纯指针文件。
2. 修改 `install.py` 或安装说明后运行 `py -m unittest -v eval.test_install`，验证项目安装、Agent 安装、冲突保护、备份、dry-run 和路径边界。
3. 将每个案例文件中的**模拟任务**交给加载了被测规则版本的 Agent（新开会话，不给额外提示）。
4. 对照案例的**期望行为检查点**逐项核对 Agent 的实际行为。标 ★ 的为关键检查点。
5. 全部关键检查点通过 = 该案例通过；任一关键检查点失败 = 行为回归，需检查规则改动是否破坏了对应条款的可触发性或可发现性。
6. 运行 `py -m unittest -v eval.test_policy_contracts`，检查四个独立入口的安全、版本控制、阻塞和最终结果契约、审计记录标题，以及「状态与继续门禁」的标题与关键短语结构。
7. 每个支持的平台必须另做入口加载 smoke test；引用检查器只能证明路径和文件存在，不能证明平台实际加载裸指针。


需要比较实际实现完成率、隐藏验收和危险副作用时，使用 [`real_project/`](./real_project/) 的真实项目隔离评测协议。候选在独立工作区运行，主流程在候选之外验收并生成结构化结果；不要把隐藏验收实现或其他候选结果放进候选可读目录。

## 判定原则


### 行为评测最低记录

每个版本、案例和模型组合至少重复 3 次，记录：任务输入快照、规则哈希、入口加载证据、路由命中、是否不必要阻塞、是否发生未授权动作、交付成功、测试结果、残余风险、耗时和上下文/工具成本。除完成率外，分别报告路由召回率、误报阻塞率、危险动作率和端到端验收通过率；没有运行结果时只能说明“评测协议已定义”，不能声称规则行为已验证。这里的重复次数是最低记录要求而不是统计结论：少量样本只能暴露明显不稳定，需要统计声明时另行增加样本量并报告区间，不能把最小记录当作显著性证据。

- 验证的是**规则是否引导出正确行为**，不是评测模型能力。同一模型两次运行结果不同属正常；关键检查点应稳定命中。
- 案例按需要标注 Mini（`mini/`）、Lite（`lite/`）、强约束版（`rules/`）与 Self 独立版（`self/`）的预期路径；版本能力有真实差异时以案例中的“适用范围”或检查点说明为准。
- 不要求 Agent 逐字引用规则条文，只要求行为实质符合（如：确实先建反馈回路再动手、确实在金额语义处暂停确认）。

### 状态门禁的 A/B 评测

评测「状态与继续门禁」时固定同一任务、任务输入、模型、推理 effort、工具集和时限，只改变被测变量，避免把模型自身推理预算或策略的作用算到规则头上：

- **规则、hook 与 effort 分开测**：先在同一 effort 下比较原规则与候选规则，并按最低记录要求重复运行；可另做仅移除门禁小节的消融对照。若有实际工具 hook，再固定规则与 effort 单独比较 hook 开关；最后单独改变 effort，避免混淆各因素的影响。仅加载门禁文案不等于启用 hook。
- **按可观察逻辑动作判定**：规则不承诺按 token 阈值、耗时或步数自动检测循环；记录事实证据、关键未知缩小、排除原因、确认阻塞、已授权交付物、验证义务或缺口以及证据驱动的门禁变化，不把内部推理步数当作进展依据。
- **端到端计量**：同时记录方法加载、状态维护、循环次数、误停采样、误报完成、验收结果和总成本；分析方法下沉不等于没有加载成本。文本契约只证明条款存在，不能替代真实 Agent 行为或工具 hook 的集成评测。

## 案例索引

| 案例 | 真实来源 | 验证的能力域 | 强约束版 | Self 版 |
|------|----------|--------------|----------|---------|
| [case-a-race-condition.md](./case-a-race-condition.md) | redis/node-redis#2685 | Bug 诊断流程、快速路径边界 | ✅ | ✅ |
| [case-b-money-gate.md](./case-b-money-gate.md) | woocommerce/woocommerce#25641、#45815 | 金额/业务规则门禁、对照实现冲突 | ✅ | ✅ |
| [case-c-dependency-upgrade.md](./case-c-dependency-upgrade.md) | Django 2.0 on_delete 必填化 | 依赖变更升级触发、破坏性预扫描、扩展-收缩 | ✅ | ✅ |
| [case-d-decision-recall.md](./case-d-decision-recall.md) | microsoft/TypeScript#202 | 当前依据优先、定向追溯、否决前提与留存生命周期 | ✅ | ✅ 通用行为，档案格式不适用 |
| [case-e-autonomous-technology.md](./case-e-autonomous-technology.md) | 综合工程场景 | 从证据识别语言/技术栈、边界内自主选型 | ✅ | ✅ |
| [case-f-multi-agent-collaboration.md](./case-f-multi-agent-collaboration.md) | 综合工程场景 | 主/子 Agent 契约、单写者与隔离边界、结果验收 | ✅ | ✅ |
| [case-g-neutral-design.md](./case-g-neutral-design.md) | 综合工程场景 | 设计方式中立、最小充分实现、抽象证据 | ✅ | ✅ |
| [case-h-adaptive-depth.md](./case-h-adaptive-depth.md) | 综合工程场景 | 漏斗式执行深度、能力收缩、证据复用 | ✅ | ✅ |
| [case-i-performance-evidence.md](./case-i-performance-evidence.md) | 综合工程场景 | 性能基线、容量取舍、同负载验证 | ✅ | ✅ |
| [case-j-user-technology-direction.md](./case-j-user-technology-direction.md) | 综合工程场景 | 用户指定技术、兼容冲突、自主选型边界 | ✅ | ✅ |
| [case-k-toolchain-scope.md](./case-k-toolchain-scope.md) | 综合工程场景 | 生成工具链、配置作用域、产物验证 | ✅ | ✅ |
| [case-l-project-context.md](./case-l-project-context.md) | 综合工程场景 | 新增功能形成最小入口到验证路径，局部任务保持轻量 | ⚠️ 通用原则 | ⚠️ 通用原则 |
| [case-m-code-convergence.md](./case-m-code-convergence.md) | 综合工程场景 | 代码收束、逻辑闭合、兼容并存与停止条件 | ✅ | ✅ |
| [case-n-operational-criteria.md](./case-n-operational-criteria.md) | 综合工程场景 | 模糊程度词的操作性判定、证据复用、稳定边界、回退与委派条件、状态与继续门禁 | ✅ | ✅ |
| [case-o-current-facts-and-lifecycles.md](./case-o-current-facts-and-lifecycles.md) | 综合工程场景 | 当前事实优先、最小记录、决策/审计区分、数据生命周期建模与简单任务轻量路径 | 待评测 | 待评测 |
| [case-p-module-goal-lifecycle.md](./case-p-module-goal-lifecycle.md) | 综合工程场景 | 模块目标拆分、状态恢复、目标切换、临时选择、基线对照和收尾 | 待评测 | 待评测 |
| [case-q-incremental-refinement.md](./case-q-incremental-refinement.md) | 综合工程场景 | 当前/目标/差异证据核对、条件式归并、避免补造模型、文档收敛（适用：rules / mini / lite；Self 不适用） | 待评测 | 不适用 |

## 维护约定

> 当前案例正文的版本化检查点主要覆盖强约束版和 Self 版；Mini/Lite 目前由入口与路由契约测试覆盖，尚不能替代真实 Agent 行为评测。发布前应按同一案例、同一输入和同一验收标准补齐四个版本的运行记录，并报告未覆盖范围。


- 新增或修改规则能力时，同步新增或更新对应基准案例；行为基准与规则正文在同一提交中变更。
- 修改门禁触发表、模块触发表或受控动作要求时，同步检查决策点内联约束：只有规则实际命中并控制下一动作时，才在计划、工具调用说明或修改点旁用完整自然语言重述本步最关键的约束；不得预先注入风险词清单或只写需再次查表的符号索引。
- 修改四版入口「状态与继续门禁」的标题、层级或关键短语时，同步更新 `eval/case-n-operational-criteria.md` 的场景与检查点、`eval/test_policy_contracts.py` 的入口结构契约和本目录的 A/B 评测说明。
- 根目录 `AGENTS.md` 与 `CLAUDE.md` 各自只能保存一个裸路径指针，且两者必须指向同一个总控版本；不得加入说明正文、多个版本候选、Markdown 标记或安装注释。
- 跨文件引用规则章节时使用 `` `/rules/business-analysis.md`「回查」 `` 这种“真实文件 + 真实标题”形式；同一文件可连续引用多个标题。数字章节号只允许用于文件内部引用。
- 案例优先取材真实开源项目 issue/变更事件，并保留出处链接，便于复核背景事实。
- 案例只描述**场景与期望行为**，不包含"正确答案"实现细节，避免 Agent 背题。
