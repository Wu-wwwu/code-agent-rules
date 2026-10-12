# Case Q: 多轮需求的归并式细化

**测试目标**：验证 Agent 在多轮对话中能否将用户的增量补充归并到已有理解，而非累加式生成代码和追加式记录文档。

---

## 场景设置

项目：电商后端 API（Python/Flask）  
已有基础：数据库连接、基础路由框架

---

## 第 1 轮：初始需求

**用户输入**：
```
实现用户注册功能
```

**预期 Agent 行为**：
1. 识别这是新增功能，属于"直接执行"或"分析后执行"
2. 生成基础注册实现：
   - User 模型（user_id, username, password_hash）
   - POST /register 路由
   - 基础验证（用户名非空、密码强度）
3. 记录到 documents/architecture.md：
   ```markdown
   ## 用户管理
   
   **当前状态**：支持用户注册，存储用户名和密码哈希。
   
   **实现**：User 模型 @ models/user.py, POST /register @ routes/auth.py
   
   **待明确**：邮箱验证、用户名唯一性、用户状态管理
   ```

**检查点 1**：
- ✅ 生成的代码结构清晰，不过度设计
- ✅ User 模型有显式字段
- ✅ 文档使用"当前状态 + 待明确"结构，而非"用户要求 X"

---

## 第 2 轮：补充约束

**用户输入**：
```
用户名不能重复
```

**反模式（累加式）**：
```python
# 新增独立函数
def check_username_duplicate(username):
    existing = db.query(User).filter_by(username=username).first()
    if existing:
        raise DuplicateUsername()

# 在 register 路由中调用
def register():
    check_username_duplicate(request.json['username'])  # 外层包装
    # ... 原有逻辑
```

**预期 Agent 行为（归并式）**：
1. **识别归并信号**："不能重复"是对已有"用户名"字段的约束细化，而非新功能
2. **归并到已有验证逻辑**：
   ```python
   class User(db.Model):
       username = db.Column(db.String(50), unique=True, nullable=False)  # 添加 unique 约束
   
   def register():
       username = request.json['username']
       password = request.json['password']
       
       # 归并到统一验证点
       if not username or len(username) < 3:
           return {'error': 'Invalid username'}, 400
       if User.query.filter_by(username=username).first():  # 归并：唯一性检查
           return {'error': 'Username already exists'}, 409
       # ... 创建用户
   ```
3. **更新文档（重写而非追加）**：
   ```markdown
   ## 用户管理
   
   **当前状态**：支持用户注册，用户名唯一，存储用户名和密码哈希。
   
   **约束**：
   - 用户名：非空，≥3 字符，系统内唯一
   - 密码：非空，≥8 字符，需包含字母和数字
   
   **实现**：User 模型 @ models/user.py, POST /register @ routes/auth.py
   
   **待明确**：邮箱验证、用户状态管理
   ```

**检查点 2**：
- ✅ 未新增 check_username_duplicate 独立函数
- ✅ 唯一性约束归并到 User 模型的 unique=True
- ✅ 唯一性检查归并到 register 函数的统一验证段
- ✅ 文档更新为"当前状态：用户名唯一"，而非追加"2026-10-12 补充：用户名不重复"

---

## 第 3 轮：补充流程分支

**用户输入**：
```
注册后需要邮箱验证才能激活账号
```

**反模式（累加式）**：
```python
# 新增独立函数
def send_verification_email(user_id):
    # ...

def verify_email(user_id, token):
    user = User.query.get(user_id)
    user.email_verified = True  # 新增字段
    db.session.commit()

# register 函数末尾追加
def register():
    # ... 原有逻辑
    user = User(...)
    db.session.add(user)
    db.session.commit()
    send_verification_email(user.id)  # 追加调用
```

**预期 Agent 行为（归并式）**：
1. **识别归并信号**："邮箱验证才能激活"是对用户生命周期的细化，应归并为状态机
2. **归并为状态管理**：
   ```python
   class User(db.Model):
       username = db.Column(db.String(50), unique=True, nullable=False)
       email = db.Column(db.String(120), unique=True, nullable=False)
       password_hash = db.Column(db.String(255), nullable=False)
       status = db.Column(db.Enum('pending_verification', 'active', 'suspended'), default='pending_verification')
       verification_token = db.Column(db.String(255))
   
   def register():
       # ... 验证
       user = User(
           username=username,
           email=email,
           password_hash=hash_password(password),
           status='pending_verification',  # 显式初始状态
           verification_token=generate_token()
       )
       db.session.add(user)
       db.session.commit()
       send_verification_email(user.email, user.verification_token)  # 归并到注册流程
       return {'message': 'Registration successful. Please verify your email.'}, 201
   
   def verify_email():
       token = request.args.get('token')
       user = User.query.filter_by(verification_token=token).first()
       if not user:
           return {'error': 'Invalid token'}, 404
       if user.status != 'pending_verification':
           return {'error': 'Already verified'}, 400
       
       user.status = 'active'  # 状态转换
       user.verification_token = None
       db.session.commit()
       return {'message': 'Email verified successfully'}, 200
   ```

3. **更新文档（重写状态管理章节）**：
   ```markdown
   ## 用户管理
   
   **当前状态**：支持用户注册，用户名和邮箱唯一，注册后需邮箱验证才能激活。
   
   **用户状态**：
   - pending_verification：注册完成但未验证邮箱
   - active：邮箱已验证，可正常使用
   - suspended：账号被停用（待实现）
   
   **状态转换**：
   - 注册时：初始状态为 pending_verification
   - 邮箱验证后：pending_verification → active
   
   **约束**：
   - 用户名：非空，≥3 字符，系统内唯一
   - 邮箱：非空，合法格式，系统内唯一
   - 密码：非空，≥8 字符，需包含字母和数字
   
   **操作接口**：
   - POST /register：注册用户，发送验证邮件
   - GET /verify?token=xxx：验证邮箱，激活账号
   
   **实现**：User 模型 @ models/user.py, routes @ routes/auth.py
   ```

**检查点 3**：
- ✅ User 模型新增 status 枚举字段，而非简单的 email_verified 布尔
- ✅ 状态转换显式化：pending_verification → active
- ✅ send_verification_email 归并到 register 流程，而非后置调用
- ✅ 文档重写为"当前状态：注册后需邮箱验证"，而非追加"第 3 轮：增加邮箱验证"
- ✅ 文档显式列出状态集合和允许转换

---

## 第 4 轮：补充约束

**用户输入**：
```
同一个邮箱不能注册多次
```

**反模式（累加式）**：
```python
# 在 register 中又增加一个独立检查
def register():
    username = request.json['username']
    email = request.json['email']
    
    if User.query.filter_by(username=username).first():
        return {'error': 'Username already exists'}, 409
    if User.query.filter_by(email=email).first():  # 又一个独立 if
        return {'error': 'Email already exists'}, 409
    # ...
```

**预期 Agent 行为（归并式）**：
1. **识别归并信号**："邮箱不能重复"与"用户名不能重复"属于同类约束，应归并
2. **归并到统一验证**：
   ```python
   class User(db.Model):
       username = db.Column(db.String(50), unique=True, nullable=False)
       email = db.Column(db.String(120), unique=True, nullable=False)  # 添加 unique 约束
   
   def validate_registration(username, email, password):
       errors = []
       if not username or len(username) < 3:
           errors.append('Username must be at least 3 characters')
       if User.query.filter_by(username=username).first():
           errors.append('Username already exists')
       
       if not email or '@' not in email:
           errors.append('Invalid email format')
       if User.query.filter_by(email=email).first():
           errors.append('Email already registered')
       
       if not password or len(password) < 8:
           errors.append('Password must be at least 8 characters')
       
       return errors
   
   def register():
       username = request.json['username']
       email = request.json['email']
       password = request.json['password']
       
       errors = validate_registration(username, email, password)  # 统一验证
       if errors:
           return {'errors': errors}, 400
       # ... 创建用户
   ```

3. **更新文档（在约束章节补充邮箱唯一性）**：
   ```markdown
   **约束**：
   - 用户名：非空，≥3 字符，系统内唯一
   - 邮箱：非空，合法格式，系统内唯一
   - 密码：非空，≥8 字符，需包含字母和数字
   ```

**检查点 4**：
- ✅ 邮箱唯一性检查归并到 validate_registration，而非又一个独立 if
- ✅ 提取了统一验证函数，消除了分散的 if 判断
- ✅ 文档在约束列表中补充"邮箱唯一"，而非新增章节

---

## 最终验证

**代码结构检查**：
```
models/user.py
  - User 模型：5 个字段（username, email, password_hash, status, verification_token）
  - 状态枚举：3 个状态
  
routes/auth.py
  - validate_registration()：统一验证函数
  - register()：注册 + 发送验证邮件
  - verify_email()：验证邮箱 + 状态转换
```

**禁止出现的反模式**：
- ❌ check_username_duplicate() 独立函数
- ❌ check_email_duplicate() 独立函数
- ❌ send_verification_email() 在 register 之外单独调用
- ❌ email_verified 布尔字段（应使用状态枚举）
- ❌ register_v1(), register_v2() 多个注册函数版本

**文档检查**：
```markdown
documents/architecture.md

## 用户管理

**当前状态**：支持用户注册，用户名和邮箱唯一，注册后需邮箱验证才能激活。

**用户状态**：pending_verification | active | suspended

**状态转换**：
- 注册 → pending_verification
- 邮箱验证 → active

**约束**：
- 用户名：≥3 字符，唯一
- 邮箱：合法格式，唯一
- 密码：≥8 字符

**操作接口**：
- POST /register
- GET /verify?token=xxx

**实现**：models/user.py, routes/auth.py
```

**禁止出现的反模式**：
- ❌ "2026-10-12 初始需求：用户注册"
- ❌ "2026-10-12 补充：用户名唯一"
- ❌ "2026-10-12 补充：邮箱验证"
- ❌ 多个版本的需求描述追加

---

## 评分标准

| 检查项 | 权重 | 判定标准 |
|--------|------|---------|
| 代码归并 | 30% | 无独立的 check_* 函数，验证逻辑归并到统一函数 |
| 状态显式化 | 20% | 使用状态枚举而非布尔标志，状态转换显式 |
| 文档收敛 | 20% | 文档只有当前状态章节，无"第 N 轮"追加 |
| 约束集中 | 15% | 约束列在统一位置，而非分散在多处 |
| 概念一致 | 15% | User 模型、代码、文档对字段和状态的描述一致 |

**通过标准**：≥ 85 分

---

## 契约测试钩子

```python
def test_case_q_validates_incremental_refinement():
    """验证 Agent 在多轮对话中归并需求而非累加实现"""
    
    # 模拟 4 轮对话
    turns = [
        "实现用户注册功能",
        "用户名不能重复",
        "注册后需要邮箱验证才能激活账号",
        "同一个邮箱不能注册多次"
    ]
    
    # 执行并收集结果
    result = simulate_multi_turn_task(turns)
    
    # 代码归并检查
    assert 'check_username_duplicate' not in result.code, \
        "Should merge username uniqueness check, not create separate function"
    assert 'check_email_duplicate' not in result.code, \
        "Should merge email uniqueness check, not create separate function"
    assert result.code.count('def validate_') == 1, \
        "Should have exactly one validation function"
    
    # 状态显式化检查
    assert 'status' in result.user_model_fields, \
        "Should use status enum, not boolean flags"
    assert 'email_verified' not in result.user_model_fields, \
        "Should not use email_verified boolean"
    assert result.states == {'pending_verification', 'active', 'suspended'}, \
        "Should define explicit state set"
    
    # 文档收敛检查
    user_mgmt_sections = [s for s in result.doc_sections if s.title == '用户管理']
    assert len(user_mgmt_sections) == 1, \
        "Should have exactly one '用户管理' section, not append multiple"
    assert '第 1 轮' not in result.doc_content, \
        "Should not record round numbers"
    assert '用户要求' not in result.doc_content, \
        "Should not record 'user requested X' narrative"
    
    # 约束集中检查
    constraint_locations = result.find_text_pattern(r'用户名.*唯一|邮箱.*唯一')
    assert len(set(constraint_locations)) == 1, \
        "Constraints should be in one location"
```

---

## 与现有 Case 的关系

- **Case A**: 识别占位文档 → Case Q 进一步要求收敛式更新
- **Case B**: 新增功能的当前事实采集 → Case Q 要求多轮采集时归并
- **Case N**: 状态门禁评估 → Case Q 要求状态机归并而非布尔累加
- **Case O**: 当前事实生命周期 → Case Q 要求多轮事实收敛而非追加
