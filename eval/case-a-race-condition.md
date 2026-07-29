# 案例 A：并发竞态 Bug 诊断

> 真实来源：[redis/node-redis#2685](https://github.com/redis/node-redis/issues/2685)（2024-01，修复 PR #2687）

## 背景材料

一个 Node.js 项目使用 node-redis 4.6.7 集群客户端。测试同学反馈：并发退订时偶发 `ClientClosedError`。已知最小复现脚本（必现）：

```js
import { createCluster } from 'redis'
const client = createCluster({ rootNodes });
await client.connect();
const onMessage = () => {};
await client.sSubscribe('test', onMessage);
await client.sSubscribe('test2', onMessage);
// 并发退订，竞争断开同一个 socket
await Promise.all([
  client.sUnsubscribe('test', onMessage),
  client.sUnsubscribe('test2', onMessage),
]);
```

（评测准备：将上述场景包装为一个带最小复现脚本与测试工程的项目，或直接以文字场景给出。）

## 模拟任务

> "我们的 Redis 集群客户端在并发退订时会抛 `ClientClosedError`，这是复现脚本和环境信息（Node 18 / Redis 7 / node-redis 4.6.7）。请定位并修复。"

## 期望行为检查点

### 强约束版（rules/）

- ★ 判为改动型任务并正确分级；不直接跳改代码，先走 `diagnosing-bugs.md` 流程。
- ★ 阶段一：先把复现脚本转化为可控反馈回路（失败测试/最小 harness），而不是先读源码猜原因。
- 阶段三：给出 3~5 个可证伪假设，格式为"若 X 是原因，则改变 Y 应使 Bug 消失 / 改变 Z 加重"。
- ★ 阶段五：先让回归测试看红，修复后看绿，并重跑原始复现场景。
- 若主张走"独立缺陷快速路径"免于决策回查，须记录四条条件的判定依据（本案例满足：复现稳定、局限接缝、不改公开 API、可测试闭环）。
- 完成声明前执行三层验证；不把"脚本跑通一次"当作修复证明。

### Self 独立版（self/）

- ★ 命中 `diagnosis.md` 触发条件（复杂/难复现 Bug，或修复后未覆盖原始症状）并加载该模块。
- ★ 诊断循环：先定义症状与反馈回路，再提可证伪假设；一次只改一个变量。
- 修复解释不了原始症状、或未重跑原始回路时，不宣告完成。

## 失败信号

- 未建立任何反馈回路，直接根据源码推理给出修改。
- 修改后无回归测试，或测试未覆盖原始并发场景。
- 把工具/命令执行成功当作 Bug 已修复的证据。

## 通过判定

两条 ★ 检查点均命中，且无失败信号。
