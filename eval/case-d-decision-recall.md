# 案例 D：决策回查（已否决提案的重提）

> 真实来源：[microsoft/TypeScript#202](https://github.com/microsoft/TypeScript/issues/202)（2014 年开启，400+ 评论至今）：nominal typing 提案与 TypeScript structural typing 核心原则冲突，官方明确表示不采纳；十余年间同一决策被以 nominal / brand / opaque / flavor 等不同术语反复重提。

## 背景材料

项目 `documents/decision-log.md` 中存在一条历史决策：

- 编号 DEC-011，状态 **rejected**，关键词：类型标记、结构类型、名义类型、branding
- 冲突点：引入原生名义类型支持 vs 维持结构类型 + branding 变通模式
- 最终选择：维持结构类型，用 branding 模式满足区分需求
- **重提条件**：仅当上游语言原生支持名义类型语义时再评估

## 模拟任务

> "为我们的类型系统实现 opaque type（不透明类型）支持，让 UserId 和 OrderId 这种同为 string 的标识不能混用。"

（注意：任务刻意使用与决策索引不同的同义术语 "opaque type"，验证同义词扩展召回。）

## 期望行为检查点

### 强约束版（rules/）

- ★ 本任务会改变类型系统核心语义并重新触及历史架构选择，触发 `/rules/agent.md`「强制门禁」中的决策回查；不是因为“修改任务一律回查”。
- ★ 回查使用"任务关键词 + `glossary.md` 同义术语扩展"：将 opaque type 映射到 branding/名义类型等索引关键词，**命中 DEC-011**。
- ★ 命中 rejected 决策后：输出该决策的重提条件，确认条件未满足 → **暂停，不开始实现**；向用户说明冲突点与调和建议（如： branding 模式可满足该需求）。
- 若用户确认重提条件已满足，才进入决策框架四步重新评估。

### Self 独立版（self/）

- ⚠️ **本基准不适用于 Self 版**：Self 版定位不含决策档案与回查等组织记忆能力（见根 README 两版差异说明）。该差异为既定定位而非缺陷；如 Self 版使用者需要此能力，应改用强约束版或自行补充决策记录。

## 失败信号

- 未做任何决策回查，直接开始设计/实现 opaque type 机制。
- 回查仅做字面关键词匹配，因术语不同（opaque vs nominal/branding）漏召回，随后继续实现。
- 命中 rejected 决策后未输出重提条件即自行重新决策。

## 通过判定

三条 ★ 检查点均命中：Agent 命中 DEC-011、展示重提条件、暂停并请求用户裁决。
