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
├── triggers.md            # L2 触发规则（按需加载，约80行）
├── check_references.py    # 交叉引用自检脚本
├── methods/               # L3 参考方法（按需查阅，10 个文件）
│   ├── destructive-analysis.md
│   ├── business-rules.md
│   ├── bug-diagnosis.md
│   ├── decision-recall.md
│   ├── dependency-upgrade.md
│   ├── toolchain-scope.md
│   ├── multi-agent.md
│   ├── technology-selection.md
│   ├── performance-evidence.md
│   └── neutral-design.md
```

> **外部依赖**：部分方法（decision-recall、business-rules）引用同级 `../documents/` 目录中的 `decision-log.md`、`glossary.md`、`business-rules.md`。使用 `install.py` 安装 mini 版时会同时补充缺失的 `documents/` 模板，已有项目文档不会被覆盖。


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

部署时只需将 `anchors.md` 加入系统提示或平台自动加载路径。其余文件由 agent 按需自行读取。命中专项规则后，应在真正受控的决策或动作旁重述一条语义完整的自然语言约束；不要只放一个需要再次查表才能理解的符号索引。
