# Code Agent Rules — Claude Code 入口（CLAUDE.md）

本仓库是一套可被 AI Coding Agent 加载的行为规则。规则正文与具体工具无关；本文件只负责告诉 Agent「去读哪些文件」，不把全部内容塞进上下文（遵循规则自身的「按需取证」原则）。Claude Code 会自动读取仓库根目录的 `CLAUDE.md`（也兼容 `AGENTS.md`）。

## 选择版本
取消注释你需要的那一行（两版独立，选其一即可，不要同时启用）：

- 强约束版（完整门禁，需配套 `documents/`）：读取并遵循 `rules/agent.md`，并按其中“能力路由与知识加载”章节按需加载 `rules/` 下专项规则与 `documents/`。
- Self 独立版（轻量，按需加载模块）：读取并遵循 `self/core.md`；复杂场景按 `self/README.md` 的触发表加载对应模块（context / diagnosis / change / security / technology / collaboration）。

## 文件地图
- `rules/agent.md`        强约束版总入口（多维任务画像、执行深度、门禁、执行循环）
- `rules/*.md`            专项规则：业务分析、数据流、数据建模、破坏性分析、排错、文档、编码、技术选型与多 Agent 协作
- `self/core.md`          Self 版精简入口
- `self/README.md`        Self 版模块索引（含技术选型与多 Agent 协作）
- `documents/`            8 类项目事实与决策记录示例（强约束版配套，接入后须替换为真实内容）
- `eval/`                 规则回归验证基准（维护者使用）

## 给 Agent 的执行要求
1. 先按所选版本校准目标、成功标准、任务画像、状态与风险。
2. 先复用仍适用的直接证据；每轮只补会改变下一动作的最小知识，不全文通读无关文件。
3. 工具执行成功 ≠ 任务成功；每轮对照预期与实际验证。
4. 不编造事实 / API / 版本 / 业务规则；高风险或未知项先暂停确认。
5. 用户未指定技术时不预设语言或技术栈；从需求、文档、代码、配置和环境证据中识别或选择。用户明确指定时先验证兼容性，可行则遵循。作为主 Agent 或子 Agent 时均保持原授权、风险和验证边界。

> 更多说明见仓库 `README.md`。通用入口见 `AGENTS.md`。
