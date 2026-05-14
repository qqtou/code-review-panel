# 代码审查快速检查清单

> 审查时随身携带的速查表。完整检查项见各 `references/*.md`。

---

## 🔴 阻塞级（P0）

### 安全
- [ ] 无 SQL 注入（参数化查询）
- [ ] 无 XSS（输出转义 / DOMPurify）
- [ ] 无命令注入（参数列表，不用字符串拼接）
- [ ] JWT 使用强密钥 + 正确验证签名
- [ ] 无密钥/密码硬编码
- [ ] CORS 未配置为 `*`
- [ ] 权限校验覆盖所有接口

### 事务与并发
- [ ] 跨表操作在同一事务内
- [ ] 幂等性设计（重复请求无副作用）
- [ ] 并发扣减有锁或原子操作
- [ ] `flush()` 后有 `commit()`

### 数据与契约
- [ ] ORM 属性引用真实存在
- [ ] 前后端接口契约一致（端点、字段、类型）
- [ ] 无 `SELECT *` 查大表
- [ ] 列表接口有分页 + 最大限制

---

## 🟠 重要级（P1）

- [ ] 无 N+1 查询（使用 eager loading）
- [ ] WHERE 列有索引
- [ ] 无 `await` 顺序执行可并发的异步操作
- [ ] 无 O(n²) 嵌套循环（数据量大时）
- [ ] `useEffect` / 定时器 / 事件监听有清理
- [ ] 前端 LCP 图片未设置 `loading="lazy"`
- [ ] 依赖无已知漏洞（`npm audit` / `pip-audit`）

---

## 🟡 建议级（P2）

- [ ] 函数参数 ≤ 3 个（否则用 options object）
- [ ] 无 magic strings（用 enum / constant）
- [ ] 无复制粘贴变种（提取参数化函数）
- [ ] 大列表（>100 项）使用虚拟滚动
- [ ] 使用代码分割（`import()` 懒加载）
- [ ] 图片使用 WebP/AVIF 格式

---

## 📊 量化指标（必须填写）

| 指标 | 合格标准 | 当前值 |
|-----|---------|-------|
| 需求覆盖率 | ≥ 95% | |
| 业务逻辑匹配度 | 100% | |
| 异常分支覆盖率 | ≥ 90% | |
| SQL 性能风险率 | 0% | |
| 漏洞风险率（高危） | 0 | |

---

## 💬 沟通语气检查

- [ ] 用提问代替命令："你觉得…怎么样？" 而非 "你应该…"
- [ ] 用建议代替指责："我们可以考虑…" 而非 "这是错的"
- [ ] 包含代码示例
- [ ] 解释 "为什么"

---

## 📚 参考资料

| 检查维度 | 参考文件 |
|---------|---------|
| 安全审查 | `references/security-review-guide.md` |
| 通用代码质量反模式 | `references/code-quality-universal.md` |
| 性能审查 | `references/performance-review-guide.md` |
| 审查沟通最佳实践 | `references/code-review-best-practices.md` |
| 框架反模式 | `references/framework-antipatterns.md` |
| 历史坑点 | `references/pitfalls.md` |
| 安全配置检查 | `references/security-checklist.md` |
