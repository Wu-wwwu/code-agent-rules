# 真实项目隔离对照评测

本目录用于比较不同规则快照在真实代码任务中的端到端行为。候选 Agent 必须在相互隔离的 worktree、检出副本或沙箱中运行；验收器、结果聚合器和其他候选结果必须位于候选工作区之外。

## 标准流程

1. 冻结同一代码 commit、模型、工具环境、任务文本和规则快照哈希。
2. 为每个候选和每次重复运行创建独立工作区；交换中性标签与执行顺序。
3. 子 Agent 只接收公开任务和完成标准，不得读取隐藏验收或其他候选结果。
4. 主流程在候选之外运行项目测试和同一隐藏验收，生成符合 [`run-result.schema.json`](./run-result.schema.json) 的 JSON。
5. 每类任务每套规则至少运行 3 次；用 `aggregate.py` 汇总完成率、断言通过率、危险副作用和测试隔离质量。
6. 保存任务、输入 commit、规则哈希、补丁、结果 JSON、命令日志和 SHA-256 清单。

## 子 Agent 返回契约

```text
status: completed | blocked | failed
changed_files:
commands_run:
test_results:
artifacts:
remaining_risks:
block_reason:
```

子 Agent 的自报结果只作为证据输入，不能替代候选外复验。

## 当前案例

- [`cases/installer-self-overwrite.md`](./cases/installer-self-overwrite.md)：安装器把规范规则入口作为用户入口目标时的自覆盖保护。

## 聚合结果

```bat
py -3 eval\real_project\aggregate.py artifacts\*.json
```

聚合器验证最小字段与计数一致性后输出 JSON。隐藏验收实现不应放入候选可读取的目录；本目录只保存公开案例、结果契约和中立汇总逻辑。