# 最小实现决策

> 本规则定义实现选择的优先级梯子，用于对抗过度设计和累加式生成。借鉴 ponytail 的 YAGNI 操作化方法，与 `./incremental-refinement.md` 的多轮归并细化互补。

## 触发时机

- 用户提出新功能、新模块或新依赖
- Agent 准备生成 > 20 行新代码
- 发现可能的重复实现
- 需要在多个实现方案间选择

## 实现选择梯（按顺序检查，第一个满足的停止）

### 1. 需要存在吗？

**检查**：
- 用户要求中是否明确提及该功能
- 成功标准中是否包含该功能
- 业务规则中是否依赖该功能

**不满足条件**：
- 用户说"实现 X"但未提及功能 Y → 跳过 Y
- 成功标准是"查询订单"但准备实现"导出 Excel" → 跳过导出
- "改进性能"不自动包含"缓存层" → 需明确确认

**输出**：在结果中列出"跳过：X（用户未要求）"或"跳过：Y（不在成功标准）"

### 2. 已有实现？

**检查**：
- `grep -r "function_name" .` 查找已有函数
- `find . -name "*helper*" -o -name "*util*"` 查找工具模块
- 已有 component/service/pattern 是否可复用

**满足条件**：
- 已有 `validateEmail()` → 复用，不新增 `checkEmail()`
- 已有 `Button` 组件 → 复用，不新增 `ClickableButton`
- 已有状态机实现模式 → 延续该模式

**注意**：复用时保持调用方式一致，不引入新的包装层

### 3. 标准库/平台特性？

**检查**：
- 语言标准库文档（如 Python `datetime`, JavaScript `Array.prototype.map`）
- 平台 API（如浏览器 `<input type="date">`, Node.js `fs.promises`）
- 运行时内置功能（如 JVM `java.util.concurrent`, .NET `System.Linq`）

**满足条件**：
- 需要日期选择器 + 浏览器 `<input type="date">` 可用 → 使用原生控件
- 需要数组去重 + 有 `Set` → 使用 `[...new Set(arr)]`
- 需要异步队列 + 有 `Promise.all` → 使用内置并发

**例外**：项目已有自己的实现（如 house component）优先于平台特性

### 4. 已安装依赖？

**检查**：
- `package.json` / `requirements.txt` / `go.mod` / `Cargo.toml`
- `node_modules` / `venv` / `vendor` 目录

**满足条件**：
- 已安装 `lodash` 且需要深拷贝 → 使用 `_.cloneDeep()`
- 已安装 `axios` 且需要 HTTP 请求 → 使用 axios
- 已安装 `dayjs` 且需要日期格式化 → 使用 dayjs

**禁止**：为使用 1-2 个函数新增依赖

### 5. 能一行解决？

**检查**：
- 实现 ≤ 1 行
- 可读性不受影响（不是密码学级别的单行）

**满足条件**：
```python
# 需要获取唯一值
unique = list(set(items))  # 一行，清晰

# 需要过滤空值
valid = [x for x in items if x]  # 一行，清晰
```

**不满足**：
```python
# 虽然一行，但不可读
result = (lambda x: reduce(lambda a,b: a+b if b else a, map(lambda y: y*2 if y>0 else 0, x)))(data)
```

### 6. 最小新代码

**门槛**：
- 新增代码 < 50 行 → 直接实现
- 新增代码 ≥ 50 行 → 复核是否可拆分或复用

**检查**：
- 是否可以拆分为多个小函数？
- 是否隐藏了可复用的部分？
- 是否包含了未要求的功能？

---

## 依赖新增门槛

### 禁止新增依赖的情况

以下情况**不得**新增依赖：

1. **替代实现 ≤ 50 行**
   ```python
   # 禁止：为此新增 underscore
   def flatten(lst):
       result = []
       for item in lst:
           if isinstance(item, list):
               result.extend(flatten(item))
           else:
               result.append(item)
       return result  # 8 行，不值得新依赖
   ```

2. **只使用依赖的 1-2 个函数**
   ```javascript
   // 禁止：为 debounce 引入整个 lodash
   function debounce(func, wait) {
       let timeout;
       return function(...args) {
           clearTimeout(timeout);
           timeout = setTimeout(() => func.apply(this, args), wait);
       };
   }  // 6 行，不值得新依赖
   ```

3. **依赖未被广泛采用**
   - GitHub stars < 1000
   - 最近 6 个月无更新
   - 无主要组织背书（如 TC39, Python Software Foundation）

### 允许新增依赖的情况

以下情况**可以**新增依赖：

1. **替代实现 > 50 行且有技术壁垒**
   - 密码学（bcrypt, argon2）
   - 日期时间处理（moment, dayjs, date-fns）
   - 国际化（i18next, react-intl）
   - 复杂数据结构（immutable.js）

2. **安全关键功能**
   - JWT 验证（jsonwebtoken）
   - SQL 防注入（parameterized queries 库）
   - XSS 防护（DOMPurify）

3. **标准事实接口**
   - HTTP 客户端（axios, fetch）
   - 日志框架（winston, log4j）
   - 测试框架（jest, pytest）

### 新增依赖检查清单

新增依赖前必须回答：

- [ ] 替代实现是否 > 50 行？
- [ ] 是否涉及安全或技术壁垒？
- [ ] 依赖是否被广泛采用（stars > 1000, 活跃维护）？
- [ ] 项目是否已有类似依赖可复用？
- [ ] 依赖的许可证是否兼容？
- [ ] 依赖的大小是否合理（< 100KB for frontend）？

全部通过才新增依赖。

---

## 删除优先原则

### 核心规则

**"删除优于添加"**：新实现替代旧实现时，删除旧代码优先于保留兼容。

### 默认删除的情况

1. **功能被完全替代**
   ```python
   # 旧实现
   def calculate_total_old(items):
       total = 0
       for item in items:
           total += item.price
       return total
   
   # 新实现（更高效）
   def calculate_total(items):
       return sum(item.price for item in items)
   
   # 删除 calculate_total_old，不保留
   ```

2. **调用方全部迁移完成**
   ```javascript
   // 旧 API
   function getUser(id, callback) { /* ... */ }
   
   // 新 API（Promise 化）
   async function getUser(id) { /* ... */ }
   
   // grep 确认无调用方后，删除旧 API
   ```

3. **临时代码、调试代码、无消费者代码**
   ```python
   # 删除
   # def debug_print(x):
   #     print(f"DEBUG: {x}")
   
   # 删除
   def unused_helper():
       pass  # 无调用方
   ```

### 保留旧代码的充分条件（全部必须满足）

1. **明确的兼容/迁移/回退要求**
   - 用户要求："保留旧 API 3 个月"
   - 外部消费者迁移计划："v2 API 在 2026-12-31 前并存"
   - 灰度发布："新旧实现通过 feature flag 切换"

2. **记录保留依据**
   ```python
   # DEPRECATED: 2026-10-12, remove after 2027-01-01
   # Kept for backward compatibility with mobile app v1.x
   # Migration guide: /docs/api-v2-migration.md
   def get_user_old(id):
       return get_user(id).__dict__  # delegate to new API
   ```

3. **可观察的移除条件**
   - "外部调用量 < 1% 时移除"
   - "所有消费者升级到 v2 后移除"
   - "2027-01-01 到期自动移除"

4. **责任边界明确**
   - 谁负责监控移除条件？
   - 谁负责执行移除？
   - 移除失败的回退方案？

### 禁止的保留理由

- ❌ "可能以后用得上"
- ❌ "删了万一有人用怎么办"
- ❌ "保留一下比较保险"
- ❌ "只是注释掉，不占空间"

**原则**：没有证据证明需要保留 = 删除。

---

## shortcut 注释约定

### 格式

已知限制的简化实现使用以下格式：

```
# shortcut: <当前限制>, <升级时机>
```

### 示例

```python
# shortcut: max 100 items, upgrade when >1000 records or user reports slow
def get_all_users():
    return db.query("SELECT * FROM users LIMIT 100")
```

```javascript
// shortcut: no pagination, add when API returns >50 results
function fetchOrders() {
    return api.get('/orders');
}
```

```java
// shortcut: single-threaded, parallelize when processing time >5s
public void processFiles(List<File> files) {
    for (File file : files) {
        process(file);
    }
}
```

### 与 TODO 的区别

| TODO | shortcut |
|------|----------|
| "未完成" | "当前足够" |
| "应该做" | "满足条件时做" |
| 无升级条件 | 有可观察的升级条件 |
| 积累成技术债 | 可聚合、可监控 |

### 聚合为技术债清单

所有 `shortcut:` 注释可通过以下命令聚合：

```bash
grep -rn "shortcut:" . --include="*.py" --include="*.js" --include="*.java" > technical-debt.txt
```

定期检查升级条件是否满足：
- 性能监控：处理时间、记录数量
- 错误日志：用户报告、异常率
- 业务指标：订单量、并发数

---

## 集成到现有规则

### 在 agent.md 能力路由表中新增

```markdown
| 如何选择最简实现？避免过度设计？ | `./minimal-implementation.md` | 已有代码、标准库、依赖清单 |
```

### 在 coding-principles.md 基本准则中新增

```markdown
| **删除优于添加** | 新实现替代旧实现时，删除旧代码优先于保留兼容；只有明确的兼容/迁移/回退要求时才保留旧代码；记录保留依据、可观察的移除条件和责任边界 |
| **依赖门槛** | 新增依赖需证明：替代实现 > 50 行或有技术壁垒，且依赖被广泛采用（stars > 1000, 活跃维护）；禁止为 1-2 个函数新增依赖 |
```

### 在 incremental-refinement.md 中引用

多轮对话归并时，单次实现也要遵循最小实现梯：

```markdown
归并后的代码仍需通过最小实现检查：
1. 归并后的统一验证函数是否可用标准库实现？
2. 状态机是否可用已有模式？
3. 是否引入了不必要的新依赖？
```

---

## 反模式检测

### 过度抽象

```python
# 反模式：为 2 个调用方建抽象
class UserFetcher:
    def __init__(self, db):
        self.db = db
    
    def fetch(self, id):
        return self.db.get(id)

# 正确：直接调用
user = db.get(user_id)
```

### 过度配置

```javascript
// 反模式：无人用的配置项
const config = {
    maxRetries: 3,        // 无人修改
    timeout: 5000,        // 无人修改
    cacheEnabled: true,   // 无人修改
    logLevel: 'info',     // 无人修改
};

// 正确：硬编码，需要时再配置化
const MAX_RETRIES = 3;
```

### 过度包装

```python
# 反模式：为标准库加包装
def my_json_parse(text):
    return json.loads(text)

# 正确：直接用标准库
data = json.loads(text)
```

---

## 验证清单

实现完成后自检：

- [ ] 是否引入了用户未要求的功能？
- [ ] 是否可用已有实现/标准库/已安装依赖？
- [ ] 新增依赖是否满足门槛（> 50 行替代 或 技术壁垒）？
- [ ] 是否保留了可删除的旧代码？
- [ ] 已知限制是否标记了 `shortcut:` 注释？
- [ ] 能否减少新增概念/文件/依赖而不损害成功标准？

---

## 与 ponytail 的差异

| 维度 | ponytail | 本规则 |
|------|----------|--------|
| 触发 | 单次任务 | 单次任务 + 多轮归并 |
| 梯子 | 6 级（隐式"需要吗"） | 6 级（显式"需要吗"） |
| 依赖 | "Never add for a few lines" | 50 行门槛 + 技术壁垒例外 |
| 删除 | "Deletion beats addition" | 删除优先 + 保留充分条件 |
| 技术债 | `shortcut:` 注释 | `shortcut:` 注释 + 聚合工具 |
| 测试 | 非平凡逻辑留小测试 | 集成到验证步骤的 4 类测试 |
| 多轮 | 无 | 与 incremental-refinement.md 互补 |

---

## 评测案例

参见 `eval/case-r-minimal-implementation.md`（待补充）：
- 场景：用户要求"实现缓存系统"
- 预期：推回 → "哪些数据？多大规模？" → 最终用 20 行 LRU dict
- 反模式：直接生成 Redis 集成 + 缓存策略配置类 + 失效通知机制
