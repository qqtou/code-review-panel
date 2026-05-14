# 历史坑点模板

> 记录项目中实际出现过的线上问题，供审查时对照避免复发。

## 使用方法

审查代码时，对照本文件中的历史坑点，检查同类问题是否再次出现。

---

## 并发类

| 坑点 | 表现 | 根因 | 修复方案 | 关联模块 |
|-----|------|-----|---------|---------|
| 配额超卖 | 高并发下配额使用量超过月度上限 | `quota_used += 1` ORM 读-改-写非原子 | 改用 SQL 原子操作 `UPDATE SET quota_used = quota_used + 1` | 配额/计数器 |
| 配额检查与扣减非原子 | 请求通过配额检查但实际超额创建任务 | 检查（SELECT）和扣减（INSERT）分两步，无锁保护 | 合并为条件更新 `UPDATE SET used=used+1 WHERE used < monthly RETURNING *` | 任何资源配额 |
| 注册唯一性竞态 | 并发注册相同邮箱，一个 500（IntegrityError） | 先查后插，中间无锁 | 捕获 IntegrityError 返回友好错误，或用数据库唯一约束兜底 | 用户注册 |

## 事务类

| 坑点 | 表现 | 根因 | 修复方案 | 关联模块 |
|-----|------|-----|---------|---------|
| flush 不等于 commit | 数据看起来写入了但异常时丢失 | 误以为 `flush()` 已持久化，依赖 session yield 的隐式 commit | 每个 CUD 操作后显式 `await session.commit()` | 所有 ORM 写操作 |
| 部分写入未回滚 | 多步写操作中某步失败，前序写入未回滚 | 未正确使用事务边界或 `try/except/rollback` | 用 `async with session.begin():` 包裹完整事务 | 跨表操作 |

## 数据类

| 坑点 | 表现 | 根因 | 修复方案 | 关联模块 |
|-----|------|-----|---------|---------|
| 模型属性不存在 | 运行时 AttributeError | 代码中引用了模型中未定义的属性（如 `user.webhook_url`） | 审查时对照模型定义逐字段校验 | ORM 模型引用 |
| import 名称不一致 | NameError | 文件 import 了 `DetectionResult` 但代码中用 `DBDetectionResult` | 统一命名或使用 `as` 别名 | 跨模块引用 |
| 前后端类型不匹配 | 前端 number 类型对应后端 UUID 字符串，边缘场景数据异常 | 手动维护前后端类型定义，未自动同步 | 用 openapi-generator 从后端 schema 自动生成前端类型 | 前后端接口 |

## 安全类

| 坑点 | 表现 | 根因 | 修复方案 | 关联模块 |
|-----|------|-----|---------|---------|
| JWT 弱密钥 | 密钥可被暴力推测（包含项目名、年份、"change-me"） | .env 中使用有含义的字符串作为密钥 | 用 `openssl rand -hex 32` 生成随机密钥 + 启动时弱模式检测 | 认证 |
| 邮件 XSS | 用户输入的内容在邮件客户端中执行恶意脚本 | f-string 直接拼用户输入到 HTML 邮件正文 | 拼入前 `html.escape()` | 邮件/模板 |
| 越权删除 | system_admin 可删除任意租户数据，tenant_id=None 时校验失效 | `normalize_uuid(None)` 返回 None，`!= None` 恒为 True | system_admin 单独处理，非 admin 严格校验 tenant_id | 多租户 |
| 删除操作无隔离 | 通过 URL 遍历 ID 可删除他人数据 | DELETE 接口只校验 user_id 未校验 tenant_id | 多租户接口必须同时校验 user_id + tenant_id | 多租户 |

## 性能类

| 坑点 | 表现 | 根因 | 修复方案 | 关联模块 |
|-----|------|-----|---------|---------|
| Celery worker 阻塞 | 批量任务执行时 worker 全部被占满 | `task.get(timeout=3600)` 同步等待子任务完成 | 改用 Celery group/chord 异步编排 | 异步任务 |
| Dashboard 统计全返回 0 | 仪表盘数据全是 0，实际有数据 | 统计查询只查了 Work/Task 表，Result 表数据硬编码为 0 | 补全 Result 表的统计查询 | 数据展示 |

## Python 语法类

| 坑点 | 表现 | 根因 | 修复方案 | 关联模块 |
|-----|------|-----|---------|---------|
| 行末逗号变 tuple | Celery 任务重试配置全部失效 | `attr=val,\nattr2=val2,` Python 解析为 `(val, val2, ...)` 赋给 attr | 去掉行末逗号 | 类属性定义 |
| 生成器异常吞没 | 搜索/比对出错但无任何日志 | async 生成器中 `yield` 在 `try` 块，`except pass` 吞异常 | except 中至少 `logger.warning()` | 异步生成器 |
| datetime.utcnow() 弃用 | Python 3.12+ 运行时 DeprecationWarning | 未跟进 Python 版本更新 | 全局替换 `datetime.now(timezone.utc)` | 时间处理 |

---

## 填写规范

1. **坑点**：简短描述问题
2. **表现**：线上实际现象
3. **根因**：代码层面的根本原因
4. **修复方案**：最终采取的修复方法
5. **关联模块**：可能复现的模块类型
