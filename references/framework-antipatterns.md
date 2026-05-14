# 框架级反模式目录

> AI 生成代码在框架使用上的高频反模式。这些不是语言层面的问题，而是对框架 API 语义的误解导致的生产 Bug。

## 使用方法

审查代码时，对照本文件中的反模式，检查是否存在同类问题。按框架分类，快速定位。

---

## SQLAlchemy / ORM 反模式

| 反模式 | 表现 | 根因 | 正确做法 | 风险等级 |
|-------|------|-----|---------|---------|
| **flush ≠ commit** | 数据写入了数据库但 `get_db` 的 yield 退出前异常导致 rollback，数据丢失 | 误以为 `flush()` 就是持久化；依赖 session 上下文管理器的隐式 commit | 每个 CUD 操作后显式 `await session.commit()` | P0 |
| **ORM 读-改-写竞态** | `obj.count += 1; session.commit()` 并发下计数丢失 | ORM 加载到内存 → 修改 → 写回，三步非原子 | 用 SQL 原子操作：`UPDATE table SET count = count + 1` | P0 |
| **事务与非原子操作混用** | 先检查配额（SELECT）再创建任务（INSERT），两步不在同一事务或锁保护 | 跨请求/跨 Depends 的操作没有原子性保证 | 合并为条件 UPDATE：`UPDATE SET used=used+1 WHERE used < monthly RETURNING *` | P0 |
| **get_db 自动 commit 依赖** | 所有写操作只 flush 不 commit，依赖 `get_db` yield 后的自动 commit | 不了解 `get_db` 的 commit/rollback 逻辑，异常时 flush 数据会回滚 | 显式 commit，不依赖上下文管理器的隐式行为 | P0 |
| **N+1 查询** | 循环中逐条查询关联对象 | ORM 默认 lazy loading | 使用 `selectinload()`、`joinedload()` 或批量查询 | P1 |
| **未使用 expire_on_commit=False** | commit 后访问已加载的属性报 `DetachedInstanceError` | SQLAlchemy 默认 commit 后 expire 所有对象 | `sessionmaker(expire_on_commit=False)` 或 commit 后 refresh | P1 |

## FastAPI 反模式

| 反模式 | 表现 | 根因 | 正确做法 | 风险等级 |
|-------|------|-----|---------|---------|
| **Depends 链事务边界不明** | 中间件 Depends 检查配额，路由 Depends 创建任务，两步不在同一事务 | 每个 Depends 可以拿到不同的 session 实例 | 使用 `Depends(get_db)` 确保同一 session，或在路由内合并逻辑 | P0 |
| **分页参数无上限** | `limit` 参数可被用户设为极大值导致 OOM | 缺少 `le` 约束 | `limit: int = Query(20, ge=1, le=100)` | P1 |
| **全局异常处理吞细节** | `except Exception` 返回统一格式，丢失错误堆栈 | 过度统一错误响应 | 区分已知异常和未知异常，未知异常记录完整堆栈 | P1 |
| **CORS 过宽** | `allow_origins=["*"]` 或包含 `localhost` | 复制粘贴默认配置 | 从环境变量读取，生产环境只配实际域名 | P1 |
| **缺少 request lifespan 管理** | 资源（连接池、引擎）在模块级别初始化 | 不了解 FastAPI 生命周期 | 使用 `@asynccontextmanager` + `lifespan` 参数 | P2 |

## Celery / 异步任务反模式

| 反模式 | 表现 | 根因 | 正确做法 | 风险等级 |
|-------|------|-----|---------|---------|
| **new_event_loop 手动管理** | `loop = asyncio.new_event_loop(); loop.run_until_complete(...)` | 兼容同步 Celery worker 调用异步代码 | 使用 `asyncio.run()`（3.7+）或集成 `celery-aioredis` | P1 |
| **阻塞等待子任务** | `result = task.get(timeout=3600)` 在 worker 内阻塞 | 同步等待占满 worker 进程槽 | 使用 `group`/`chord` 异步编排，或 `result.ready()` + 回调 | P1 |
| **任务内无超时保护** | 外部 API 调用无 timeout，任务永远不结束 | 缺少 `time_limit`/`soft_time_limit` | `@celery_app.task(time_limit=300, soft_time_limit=270)` | P0 |
| **任务无幂等性** | 重复执行产生副作用（重复扣配额、重复发邮件） | 未设计幂等键 | 使用任务 ID 或业务唯一标识做去重检查 | P0 |
| **全局单例在 worker 中不安全** | 模块级别的 `detection_service = DetectionService()` 多 worker 状态不同步 | Celery fork 后全局变量各自独立 | 在任务内部创建实例或使用连接池 | P1 |

## Python 语法反模式

| 反模式 | 表现 | 根因 | 正确做法 | 风险等级 |
|-------|------|-----|---------|---------|
| **行末逗号导致 tuple** | `retry_backoff=True,\nretry_backoff_max=600,\nretry_kwargs={...}` 三个值变成元组 | Python 行末逗号使多行语句成为 tuple 表达式 | 去掉行末逗号，每行独立赋值 | P0 |
| **生成器中 yield 在 try 内** | async 生成器的 `yield` 在 `try` 块中，`except pass` 吞掉异常 | Python 生成器特殊语义，yield 后迭代器可能不继续 | yield 放在 try 外，或在 except 中至少 `logger.warning()` | P1 |
| **datetime.utcnow() 已弃用** | 使用 `datetime.utcnow()` 而非 `datetime.now(timezone.utc)` | Python 3.12+ 弃用 naive UTC 时间 | 全局替换为 `datetime.now(timezone.utc)` | P2 |
| **可变默认参数** | `def func(items=[]):` 多次调用共享同一 list | Python 默认参数在函数定义时求值 | `def func(items=None): items = items or []` | P1 |
| **is 比较字符串** | `if user.role is "admin":` 在 CPython 小字符串上碰巧有效 | `is` 比较对象身份，不是值相等 | `==` 比较值，`is` 只用于 None/True/False | P1 |

## React / TypeScript 反模式

| 反模式 | 表现 | 根因 | 正确做法 | 风险等级 |
|-------|------|-----|---------|---------|
| **useEffect 无 cleanup** | 组件卸载后仍执行 setState 导致内存泄漏 | 未返回清理函数 | useEffect 返回 `() => { controller.abort(); }` | P1 |
| **fetch 无超时** | 请求无限等待，用户体验差 | 原生 fetch 不支持 timeout | 用 AbortController 或 axios 的 timeout | P1 |
| **localStorage 存储 token** | XSS 攻击可直接读取 token | token 存在 localStorage 中无隔离 | 生产环境使用 HttpOnly Cookie | P1 |
| **前端类型与后端不一致** | 后端 UUID → 前端 number，后端 `is_active` → 前端 `active` | 手动维护类型定义，未与后端 schema 同步 | 用 openapi-generator 自动生成前端类型 | P1 |
| **console.log 遗留** | 生产代码中包含 console.log/console.error | 开发调试遗留 | ESLint 规则 `no-console` 自动检查 | P2 |

## Spring Boot (Java) 反模式

| 反模式 | 表现 | 根因 | 正确做法 | 风险等级 |
|-------|------|-----|---------|---------|
| **@Transactional 失效** | 同类方法调用事务注解不生效 | Spring AOP 代理机制，自调用不走代理 | 注入自身 `@Lazy private Self self;` 或拆分到不同 Bean | P0 |
| **事务传播不当** | `REQUIRES_NEW` 在批量操作中频繁开新事务 | 不理解事务传播行为 | 默认 `REQUIRED`，嵌套用 `NESTED` | P1 |
| **ThreadLocal 泄漏** | 线程池复用线程时 ThreadLocal 未清理 | 请求结束未 remove | finally 中 `threadLocal.remove()` | P1 |

---

## 维护说明

- 每次代码审查发现新的框架级反模式时，更新对应章节
- 标注实际项目中遇到的案例，便于对照
- 按使用频率排序，高频反模式排在前面
