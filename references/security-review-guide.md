# 安全审查指南

> 基于 OWASP Top 10 和业界最佳实践的安全代码审查清单。

---

## 严重度等级

| 等级 | 说明 | 动作 |
|------|------|------|
| **Critical** | 可被直接利用，有数据泄露风险 | 阻断合并，立即修复 |
| **High** | 重大漏洞，需要特定条件 | 阻断合并，发布前修复 |
| **Medium** | 中等风险，深度防御层面 | 应修复，可带 tracking 合并 |
| **Low** | 轻微问题，最佳实践违反 | 建议修复，不阻断 |
| **Info** | 改进建议 | 可选增强 |

---

## 1. 身份认证与授权

### 认证检查清单
- [ ] 密码使用强哈希算法（bcrypt、argon2）
- [ ] 强制密码复杂度要求
- [ ] 失败尝试后账户锁定
- [ ] 安全的密码重置流程
- [ ] 敏感操作启用多因素认证（MFA）
- [ ] Session tokens 使用密码学安全随机数生成
- [ ] 实现 session 超时机制

### 授权检查清单
- [ ] 每个请求都进行授权检查
- [ ] 遵循最小权限原则
- [ ] 正确实现基于角色的访问控制（RBAC）
- [ ] 无权限提升路径
- [ ] 直接对象引用检查（IDOR 防护）
- [ ] API 端点有适当的保护

### JWT 安全（TypeScript 示例）
```typescript
// ❌ 不安全的 JWT 配置
jwt.sign(payload, 'weak-secret');

// ✅ 安全的 JWT 配置
jwt.sign(payload, process.env.JWT_SECRET, {
  algorithm: 'RS256',
  expiresIn: '15m',
  issuer: 'your-app',
  audience: 'your-api'
});

// ❌ 未正确验证 JWT
const decoded = jwt.decode(token);  // 无签名验证！

// ✅ 验证签名和 claims
const decoded = jwt.verify(token, publicKey, {
  algorithms: ['RS256'],
  issuer: 'your-app',
  audience: 'your-api'
});
```

---

## 2. 输入验证

### SQL 注入防护（Python 示例）
```python
# ❌ 存在 SQL 注入风险
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ 使用参数化查询
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# ✅ 使用 ORM（正确转义）
User.objects.filter(id=user_id)
```

### XSS 防护（TypeScript/React 示例）
```typescript
// ❌ 存在 XSS 风险
element.innerHTML = userInput;

// ✅ 使用 textContent 处理纯文本
element.textContent = userInput;

// ✅ 使用 DOMPurify 处理 HTML
element.innerHTML = DOMPurify.sanitize(userInput);

// ✅ React 自动转义（注意 dangerouslySetInnerHTML）
return <div>{userInput}</div>;  // 安全
return <div dangerouslySetInnerHTML={{__html: userInput}} />;  // 危险！
```

### 命令注入防护（Python 示例）
```python
# ❌ 存在命令注入风险
os.system(f"convert {filename} output.png")

# ✅ 使用 subprocess 并传入列表参数
subprocess.run(['convert', filename, 'output.png'], check=True)

# ✅ 验证和清理输入
import shlex
safe_filename = shlex.quote(filename)
```

### 路径遍历防护（TypeScript 示例）
```typescript
// ❌ 存在路径遍历风险
const filePath = `./uploads/${req.params.filename}`;

// ✅ 验证和清理路径
const path = require('path');
const safeName = path.basename(req.params.filename);
const filePath = path.join('./uploads', safeName);

// 验证仍在 uploads 目录内
if (!filePath.startsWith(path.resolve('./uploads'))) {
  throw new Error('Invalid path');
}
```

---

## 3. 数据保护

### 敏感数据处理检查清单
- [ ] 源码中无密钥/密码
- [ ] 密钥存储在环境变量或密钥管理器中
- [ ] 敏感数据静态加密
- [ ] 敏感数据传输加密（HTTPS）
- [ ] 按法规处理 PII（GDPR 等）
- [ ] 敏感数据不记录到日志
- [ ] 需要时安全删除数据

### 配置安全（YAML 示例）
```yaml
# ❌ 配置文件中包含密钥
database:
  password: "super-secret-password"

# ✅ 引用环境变量
database:
  password: ${DATABASE_PASSWORD}
```

### 错误消息（TypeScript 示例）
```typescript
// ❌ 泄露敏感信息
catch (error) {
  return res.status(500).json({
    error: error.stack,  // 暴露内部细节
    query: sqlQuery      // 暴露数据库结构
  });
}

// ✅ 通用错误消息
catch (error) {
  logger.error('Database error', { error, userId });  // 内部记录
  return res.status(500).json({
    error: 'An unexpected error occurred'
  });
}
```

---

## 4. API 安全

### 速率限制检查清单
- [ ] 所有公共端点都有速率限制
- [ ] 认证端点有更严格的限制
- [ ] 按用户和按 IP 的限制
- [ ] 超限时优雅处理

### CORS 配置（TypeScript 示例）
```typescript
// ❌ 过于宽松的 CORS
app.use(cors({ origin: '*' }));

// ✅ 限制性 CORS
app.use(cors({
  origin: ['https://your-app.com'],
  methods: ['GET', 'POST'],
  credentials: true
}));
```

### HTTP 安全头（TypeScript 示例）
```typescript
// 应设置的安全头
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
    }
  },
  hsts: { maxAge: 31536000, includeSubDomains: true },
  noSniff: true,
  xssFilter: true,
  frameguard: { action: 'deny' }
}));
```

---

## 5. 密码学

### 安全实践检查清单
- [ ] 使用成熟的算法（AES-256、RSA-2048+）
- [ ] 不实现自定义密码学
- [ ] 使用密码学安全的随机数生成
- [ ] 正确的密钥管理和轮换
- [ ] 安全的密钥存储（HSM、KMS）

### 常见错误（TypeScript 示例）
```typescript
// ❌ 弱随机数生成
const token = Math.random().toString(36);

// ✅ 密码学安全的随机数
const crypto = require('crypto');
const token = crypto.randomBytes(32).toString('hex');

// ❌ 使用 MD5/SHA1 处理密码
const hash = crypto.createHash('md5').update(password).digest('hex');

// ✅ 使用 bcrypt 或 argon2
const bcrypt = require('bcrypt');
const hash = await bcrypt.hash(password, 12);
```

---

## 6. 依赖安全

### 检查清单
- [ ] 依赖来自受信任的来源
- [ ] 无已知漏洞（npm audit、cargo audit）
- [ ] 依赖保持最新
- [ ] 提交锁文件（package-lock.json、Cargo.lock）
- [ ] 最小化依赖使用
- [ ] 验证许可证合规性

### 审计命令
```bash
# Node.js
npm audit
npm audit fix

# Python
pip-audit
safety check

# Rust
cargo audit

# 通用
snyk test
```

---

## 7. 日志与监控

### 安全日志检查清单
- [ ] 日志中无敏感数据（密码、tokens、PII）
- [ ] 日志防篡改
- [ ] 适当的日志保留策略
- [ ] 记录安全事件（登录尝试、权限变更）
- [ ] 防止日志注入

### 日志示例（TypeScript）
```typescript
// ❌ 记录敏感数据
logger.info(`User login: ${email}, password: ${password}`);

// ✅ 安全日志
logger.info('User login attempt', { email, success: true });
```
