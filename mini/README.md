# 规则体系

> 三层规则体系：基础锚点 + 按需触发 + 专项方法。轻量、单系统、渐进展开。

## 设计原则

1. **基础锚点**：核心原则约 60 行，由平台在每轮请求中纳入上下文
2. **触发按需**：匹配条件时加载对应触发规则，不匹配不加载
3. **方法按需**：详细执行指导不在系统提示中，需要时读取
4. **决策点共址**：命中规则后，在受控动作旁用完整自然语言重述当前约束
5. **示例驱动**：每条方法附带正确/错误示例

## 证据边界

- 三层结构的收益来自渐进展开：减少无关规则进入当前上下文，但任何已加载文本仍会占用上下文、延迟和费用。
- 决策点共址是待评估的工程策略。
- 默认使用语义完整的自然语言约束句。自然语言通常更明确，但是否优于某种格式仍以行为评估为准。
- 最终裁决看规则遵循行为和错误率。

## 目录结构

```
mini/
├── README.md              # 本文件
├── anchors.md             # L1 基础锚点（每轮纳入上下文，约60行）
├── triggers.md            # L2 触发规则（按需加载，约90行）
├── check_references.py    # 交叉引用自检脚本
├── methods/               # L3 参考方法（按需查阅，13 个文件）
│   ├── destructive-analysis.md
│   ├── business-rules.md
│   ├── project-documents.md
│   ├── project-context.md
│   ├── data-entity-analysis.md
│   ├── bug-diagnosis.md
│   ├── decision-recall.md
│   ├── dependency-upgrade.md
│   ├── toolchain-scope.md
│   ├── multi-agent.md
│   ├── technology-selection.md
│   ├── performance-evidence.md
│   └── neutral-design.md
../eval/                   # 仓库级规则回归验证（含项目上下文案例）
└── case-l-project-context.md
```

## 可选项目文档

`documents/` 是位于**目标项目根目录**的可选项目记忆库，不是本规则集默认已经具备的外部依赖。Mini 可按任务选择以下文件：

| 文件 | 职责 | 缺失时的含义 |
|------|------|--------------|
| `documents/project-doc.md` | 项目目标、范围、主要功能与成功标准 | 需要时从用户说明、README 和可验证行为重建最小项目目标 |
| `documents/architecture.md` | 系统边界、模块职责、依赖方向和运行拓扑 | 需要时从代码、配置和部署证据追踪当前结构 |
| `documents/tech-stack.md` | 当前技术栈、版本来源和工具链约束 | 需要时从声明、锁文件、配置和构建结果识别 |
| `documents/data-flow.md` | 关键功能的输入、状态、变换、依赖和输出路径 | 需要时沿调用、Schema、消息和测试追踪 |
| `documents/business-rules.md` | 保存有可定位证据的业务规则 | 当前没有可用的持久化规则记录，不代表业务没有规则 |
| `documents/decision-log.md` | 保存需长期回查的技术决策及状态 | 当前无法完成历史档案回查，不代表历史上没有决策 |
| `documents/coding-standards.md` | 保存项目特有且可验证的编码/测试约定 | 需要时以工具配置、CI 和现有代码为准 |
| `documents/glossary.md` | 保存经验证的术语、代码实体和存储映射 | 仅失去同义词扩展能力，可直接从代码和当前上下文检索 |

读取前必须先检查文件是否存在、是否只是示例/占位、是否适用于当前项目。缺失文档不会自动阻塞任务，也不得被解释成“项目没有目标/架构/规则/决策”。新增功能、制定计划、跨模块修改或恢复上下文时，可用 `methods/project-context.md` 从用户目标、代码、配置、测试和运行结果形成最小任务上下文包；简单任务不要求完整建模。只有内容已验证、具有跨会话复用价值且写入位于用户授权范围时，才按需创建或更新最小文件。完整流程和空模板见 `methods/project-documents.md`。


## 使用方式

**入口文件**：`anchors.md`。Agent 从该文件开始，它在头部明确了完整加载链：

```
加载 anchors.md
  ↓
收到任务 → 读取 triggers.md 判断触发
  ↓ 命中且不跳过
加载 methods/ 对应方法
  ↓
执行 anchors.md 中的每步核对清单
```

部署时只需将 `anchors.md` 加入系统提示或平台自动加载路径。其余规则文件由 agent 按需自行读取；目标项目不要求预先存在 `documents/`。命中专项规则后，应在真正受控的决策或动作旁重述一条语义完整的自然语言约束；不要只放一个需要再次查表才能理解的符号索引。
