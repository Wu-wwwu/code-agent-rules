# 规则回归验证基准（eval）

> 供规则维护者使用：每次修改 `mini/`、`rules/` 或 `self/` 后，用本目录的基准任务验证 Agent 行为未退化。规则集自身也应遵守它要求的"循环校验"。

## 怎么用

1. 运行 `py eval/check_rule_references.py`（也可用环境中的 `python`），检查跨文件规则引用的目标文件和章节标题仍然存在、未重新引入数字章节号引用，并确认根目录 `AGENTS.md` 仍是只包含一个有效规则路径的纯指针文件。
2. 修改 `install.py` 或安装说明后运行 `py -m unittest -v eval.test_install`，验证项目安装、Agent 安装、冲突保护、备份、dry-run 和路径边界。
3. 将每个案例文件中的**模拟任务**交给加载了被测规则版本的 Agent（新开会话，不给额外提示）。
4. 对照案例的**期望行为检查点**逐项核对 Agent 的实际行为。标 ★ 的为关键检查点。
5. 全部关键检查点通过 = 该案例通过；任一关键检查点失败 = 行为回归，需检查规则改动是否破坏了对应条款的可触发性或可发现性。

需要比较实际实现完成率、隐藏验收和危险副作用时，使用 [`real_project/`](./real_project/) 的真实项目隔离评测协议。候选在独立工作区运行，主流程在候选之外验收并生成结构化结果；不要把隐藏验收实现或其他候选结果放进候选可读目录。

## 判定原则

- 验证的是**规则是否引导出正确行为**，不是评测模型能力。同一模型两次运行结果不同属正常；关键检查点应稳定命中。
- 案例按需要标注 Mini（`mini/`）、强约束版（`rules/`）与 Self 独立版（`self/`）的预期路径；版本能力有真实差异时以案例中的“适用范围”或检查点说明为准。
- 不要求 Agent 逐字引用规则条文，只要求行为实质符合（如：确实先建反馈回路再动手、确实在金额语义处暂停确认）。

## 案例索引

| 案例 | 真实来源 | 验证的能力域 | 强约束版 | Self 版 |
|------|----------|--------------|----------|---------|
| [case-a-race-condition.md](./case-a-race-condition.md) | redis/node-redis#2685 | Bug 诊断流程、快速路径边界 | ✅ | ✅ |
| [case-b-money-gate.md](./case-b-money-gate.md) | woocommerce/woocommerce#25641、#45815 | 金额/业务规则门禁、对照实现冲突 | ✅ | ✅ |
| [case-c-dependency-upgrade.md](./case-c-dependency-upgrade.md) | Django 2.0 on_delete 必填化 | 依赖变更升级触发、破坏性预扫描、扩展-收缩 | ✅ | ✅ |
| [case-d-decision-recall.md](./case-d-decision-recall.md) | microsoft/TypeScript#202 | 决策回查、rejected 决策重提条件 | ✅ | ⚠️ 不适用（见案例说明） |
| [case-e-autonomous-technology.md](./case-e-autonomous-technology.md) | 综合工程场景 | 从证据识别语言/技术栈、边界内自主选型 | ✅ | ✅ |
| [case-f-multi-agent-collaboration.md](./case-f-multi-agent-collaboration.md) | 综合工程场景 | 主/子 Agent 契约、单写者与隔离边界、结果验收 | ✅ | ✅ |
| [case-g-neutral-design.md](./case-g-neutral-design.md) | 综合工程场景 | 设计方式中立、最小充分实现、抽象证据 | ✅ | ✅ |
| [case-h-adaptive-depth.md](./case-h-adaptive-depth.md) | 综合工程场景 | 漏斗式执行深度、能力收缩、证据复用 | ✅ | ✅ |
| [case-i-performance-evidence.md](./case-i-performance-evidence.md) | 综合工程场景 | 性能基线、容量取舍、同负载验证 | ✅ | ✅ |
| [case-j-user-technology-direction.md](./case-j-user-technology-direction.md) | 综合工程场景 | 用户指定技术、兼容冲突、自主选型边界 | ✅ | ✅ |
| [case-k-toolchain-scope.md](./case-k-toolchain-scope.md) | 综合工程场景 | 生成工具链、配置作用域、产物验证 | ✅ | ✅ |
| [case-l-project-context.md](./case-l-project-context.md) | 综合工程场景 | 新增功能形成最小入口到验证路径，局部任务保持轻量 | ⚠️ 通用原则 | ⚠️ 通用原则 |

## 维护约定

- 新增或修改规则能力时，同步新增或更新对应基准案例；行为基准与规则正文在同一提交中变更。
- 修改否决信号清单、门禁触发表或模块触发表时，同步更新执行循环中对应的 `[决:]` 锚点；锚点词汇必须与完整判定规则保持映射，不得只在锚点中新增触发词。
- `AGENTS.md` 只保存一个裸路径指针；不得在其中加入说明正文、多个版本候选、Markdown 标记或安装注释。
- 跨文件引用规则章节时使用 `` `/rules/business-analysis.md`「回查」 `` 这种“真实文件 + 真实标题”形式；同一文件可连续引用多个标题。数字章节号只允许用于文件内部引用。
- 案例优先取材真实开源项目 issue/变更事件，并保留出处链接，便于复核背景事实。
- 案例只描述**场景与期望行为**，不包含"正确答案"实现细节，避免 Agent 背题。
