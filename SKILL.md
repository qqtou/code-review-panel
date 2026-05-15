---
name: code-review-panel
description: |
  代码审查专家团 - 多专家协同审查代码质量、安全漏洞、性能问题、并发安全。
  
  触发场景：
  - 用户请求 code review / 代码审核 / 帮我检查代码
  - 用户问"有没有线程安全问题"、"有没有安全漏洞"
  - 用户提交 PR / Commit / 代码片段请求分析
  - 用户要求生成代码审查报告
  
  不触发：
  - 单纯的代码生成请求（用 coding-agent）
  - 代码格式化/重构请求（用 coding-agent）
metadata:
  openclaw:
    emoji: "👔"
---

## 快速开始

> 第一次使用本 skill？按这个顺序读：
> 1. **审查严重度体系**（下面这一节）→ 理解 P0/P1/P2 分级
> 2. **四阶段审查流程** → 理解审查的标准步骤
> 3. **审查流程（标准操作规程）** → 实际操作时的详细步骤
> 4. `assets/report_template.md` → 查看报告模板
>
> 需要专项检查时，按需加载 `references/*.md`（见「渐进式披露」章节）。

---

# Code Review Panel - 代码审查专家团

## 核心理念

AI 擅长生成 CRUD 和基础接口，但在**事务一致性、幂等设计、分布式锁、参数校验、SQL性能、并发安全、敏感数据脱敏、权限控制、异常兜底**等场景容易遗漏。

本 skill 采用**三层审查体系**，模拟多位资深专家协同审查，拒绝"凭感觉审核"，建立标准化、量化的代码质量准入机制。

---

## 触发场景

| 场景 | 示例 |
|-----|------|
| **代码审查** | "review这段代码"、"帮我审核一下" |
| **问题检查** | "有没有线程安全问题"、"查一下安全漏洞" |
| **PR分析** | "审查这个PR"、"检查这个commit" |
| **报告生成** | "生成代码审查报告" |

### 不触发本 Skill

| 场景 | 应使用 |
|-----|-------|
| 代码生成 | coding-agent |
| 代码重构 | coding-agent |
| 代码格式化 | coding-agent |
| 简单语法检查 | 直接回答 |

---

## 审查严重度体系

> 采用双轨严重度体系：6级情感符号体系（精细沟通）+ P0/P1/P2 行动体系（内部分级）。
> 输出给用户时统一转换为 P0/P1/P2。

### 6 级情感符号（用于专家内部标记）

| 符号 | 级别 | 对应 P 级 | 定义 | 动作 |
|------|------|------------|------|--------|
| 🔴 `blocking` | 阻断 | P0 | 必须修复后才能合并，有生产风险 | 阻断合并 |
| 🟠 `important` | 重要 | P1 | 应该修复，视上下文可能阻断 | 建议修复 |
| 🟡 `nit` | 轻微 | P2 | 风格或偏好问题 | 可选修复 |
| 🔵 `suggestion` | 建议 | P2 | 值得考虑的改进 | 可选优化 |
| 📚 `learning` | 教学 | — | 教育性提示，帮助作者学习 | 不强制 |
| 🌟 `praise` | 表扬 | — | 明确指出优秀的实现 | 不强制 |

### P0/P1/P2 行动体系（输出给用户）

| 级别 | 定义 | 处理要求 |
|-------|-----|---------|
| **P0 必须修复** | 安全漏洞、数据一致性、资金安全、生产稳定性 | 阻塞上线，立即修复 |
| **P1 强烈建议** | 并发问题、性能瓶颈、潜在 Bug | 建议本次修复，或标记为技术债 |
| **P2 可选优化** | 代码风格、重复代码、可读性 | 可后续迭代优化 |

> 💡 映射规则：📚 和 🌟 只出现在审查评论中，不计入 P0/P1/P2 统计。

---

## 四阶段审查流程

> 参考 awesome-skills/code-review-skill 的四阶段审查流程，确保审查的系统性和完整性。

### 阶段一：上下文收集（Context Gathering）

- 理解 PR/变更的**范围**和**意图**
- 读取 PR 描述、关联 issue、commit message
- 确认审查目标：全面审查 or 针对性检查？
- 确定涉及的语言/框架，加载对应的 `references/` 指南

### 阶段二：高层审查（High-Level Review）

- **架构影响**：变更是否符合整体架构方向？
- **性能影响**：是否有明显的性能退化风险？
- **测试策略**：是否有足够的测试覆盖？边界情况是否有测试？
- **设计一致性**：是否与其他模块的设计风格一致？

### 阶段三：逐行分析（Line-by-Line Analysis）

- 五位专家各自从自己的维度**独立审查**
- **业务逻辑**：逻辑正确性、边界条件、状态机完整性
- **并发与事务**：事务边界、锁、幂等性、数据一致性
- **安全审计**：SQL 注入、XSS、权限越权、敏感数据
- **性能优化**：N+1、索引、算法复杂度、Bundle 体积
- **代码质量**：命名、重复代码、异常处理、可维护性

### 阶段四：汇总与决策（Summary & Decision）

- 按严重度**汇总所有问题**（🔴 → 🟠 → 🟡 → 🔵 → 📚 → 🌟）
- 生成**结构化反馈**，含具体修复建议或代码示例
- 给出**批准状态**：✅ 通过 / ⚠️ 修复后合并 / ❌ 不通过
- 输出**行动项清单**，按优先级排序

---

## 第一层：代码链路深度拆解与核查

### 1.1 七类代码分解

审查时按以下七类逐一拆解：

| 代码类型 | 审查重点 |
|---------|---------|
| **接口层** | 参数校验、入参边界、返回值规范、异常码映射 |
| **业务层** | 业务逻辑正确性、状态机完整性、幂等性设计 |
| **数据层** | SQL 性能、索引使用、事务边界、数据一致性 |
| **工具类** | 线程安全、边界条件、异常处理、可复用性 |
| **异常处理** | 异常捕获完整性、兜底逻辑、日志记录、错误传递 |
| **安全校验** | 权限控制、敏感数据脱敏、SQL注入、XSS/CSRF |
| **性能优化** | 缓存策略、批量处理、懒加载、资源释放 |

### 1.2 AI 易漏检查清单

以下场景是 AI 生成代码的高频遗漏点，**必须逐一核对**：

| 检查项 | 检查内容 | 风险等级 | 优先级 |
|-------|---------|---------|-------|
| **事务一致性** | 跨表操作是否在同一事务？分布式场景是否用 Saga/TCC？ | 高 | P0 |
| **幂等设计** | 重复请求是否产生副作用？是否有唯一标识去重？ | 高 | P0 |
| **分布式锁** | 并发场景是否加锁？锁超时/死锁是否处理？ | 高 | P0 |
| **并发安全** | 共享变量是否线程安全？是否有竞态条件？ | 高 | P1 |
| **权限控制** | 是否校验用户权限？越权访问是否阻断？ | 高 | P0 |
| **敏感数据脱敏** | 日志/返回值是否泄露敏感信息？ | 高 | P0 |
| **SQL 性能** | 是否走索引？是否有 N+1？是否有慢查询风险？ | 高 | P1 |
| **参数校验** | 必填项、格式、长度、范围、枚举值是否校验？ | 中 | P2 |
| **异常兜底** | 异常分支是否有兜底逻辑？是否影响系统稳定性？ | 中 | P2 |
| **前后端接口契约** | 前端调用的 API 端点是否在后端都有定义？字段名/类型/枚举值是否一致？ | 高 | P0 |
| **ORM 写操作语义** | flush() vs commit() 是否混淆？写操作是否真正持久化？ | 高 | P0 |
| **模型属性引用校验** | 代码中引用的模型属性/方法是否在对应类中真实存在？ | 高 | P0 |
| **环境配置硬编码** | .env 中密钥/Token 是否可推测？调试模式是否开启？CORS 是否过宽？ | 高 | P0 |
| **模板/邮件注入** | 用户输入是否直接拼入 HTML 邮件/模板而未转义？ | 高 | P0 |

### 1.4 核心原则

- **不偏离需求**：每段代码必须能追溯到需求点
- **不违反架构规范**：分层是否清晰？依赖是否合理？
- **不编造业务规则**：仅基于需求文档和已知约束判断，不确定时标注

---

## 第二层：量化质量分析

### 2.1 核心指标

| 指标 | 定义 | 合格标准 |
|-----|------|---------|
| **需求覆盖率** | 已实现需求点 / 总需求点 | ≥ 95% |
| **业务逻辑匹配度** | 与需求文档一致的逻辑点 / 总逻辑点 | 100% |
| **异常分支覆盖率** | 已处理异常场景 / 已知异常场景 | ≥ 90% |
| **SQL 性能风险率** | 存在性能问题的 SQL / 总 SQL | 0%（高风险） |
| **重复冗余代码率** | 重复代码行 / 总代码行 | ≤ 5% |
| **漏洞风险率** | 安全漏洞数 / 千行代码 | 0（高危/中危） |
| **高危场景覆盖率** | 已覆盖高危场景 / 已识别高危场景 | 100% |

### 2.2 对照物

审查时必须对照以下资料：

| 对照物 | 用途 |
|-------|------|
| **需求文档** | 验证功能完整性、业务逻辑正确性 |
| **数据库设计** | 验证 SQL 正确性、索引合理性 |
| **历史线上 Bug** | 避免同类问题复发 |
| **安全规范** | 检查安全漏洞、权限控制 |

### 2.3 代码分类

审查后对代码进行分类：

| 分类 | 定义 | 后续动作 |
|-----|------|---------|
| **可用代码** | 满足所有检查项，无风险 | 可上线 |
| **待修改代码** | 存在问题但不影响核心功能 | 修复后上线 |
| **风险无效代码** | 存在严重问题或无效逻辑 | 必须重写/删除 |

---

## 第三层：落地优化与质量准入

### 3.1 质量准入标准

代码上线前必须通过以下检查：

#### P0 检查项（必须通过）
- [ ] 无高危/中危安全漏洞
- [ ] 事务边界正确
- [ ] 权限校验完整
- [ ] 敏感数据已脱敏

#### P1 检查项（强烈建议）
- [ ] SQL 走索引
- [ ] 无 N+1 查询
- [ ] 并发场景有保护
- [ ] 幂等性设计

#### P2 检查项（可选优化）
- [ ] 命名规范
- [ ] 注释完整
- [ ] 无重复代码

### 3.2 工具扫描

以下工具可用于批量代码质量检测：

| 工具类型 | 工具示例 | 用途 |
|---------|---------|------|
| **代码扫描** | SonarQube、ESLint、Pylint、golangci-lint | 代码规范、潜在 Bug 检测 |
| **SQL 检查** | SQLReview、EXPLAIN 分析、慢查询日志 | SQL 性能、索引优化 |
| **漏洞检测** | Snyk、OWASP Dependency-Check、Trivy | 依赖漏洞、安全漏洞 |
| **安全扫描** | Semgrep、Bandit、Brakeman | 安全编码规范、漏洞模式 |
| **代码重复** | PMD CPD、SonarQube Duplications | 重复代码检测 |

**使用建议**：
- 在 CI/CD 流水线中集成自动化扫描
- P0 问题阻断构建，P1 问题标记为警告
- 定期运行全量扫描，增量提交时运行增量扫描

### 3.3 高风险模块人工复核

以下模块**必须人工复核**，不能仅依赖 AI 审查：

| 模块类型 | 风险点 | 复核重点 |
|---------|-------|---------|
| **支付** | 金额计算、状态流转、对账 | 资金安全、精度问题 |
| **订单** | 状态机、幂等性、超时处理 | 状态流转、数据一致性 |
| **库存** | 并发扣减、超卖、回滚 | 并发安全、数据一致性 |
| **权限** | 越权访问、权限继承 | 权限模型、边界条件 |
| **分布式** | 数据一致性、分布式锁、消息可靠性 | CAP 权衡、幂等性 |

### 3.4 知识沉淀

将以下内容沉淀为 AI 提示词库：

| 沉淀类型 | 内容 | 存放位置 |
|---------|------|---------|
| **业务规则** | 特定业务的约束和规则 | references/business-rules.md |
| **历史坑点** | 线上出现过的问题及修复方案 | references/pitfalls.md |
| **架构约束** | 系统架构的硬性约束 | references/architecture-constraints.md |

### 3.5 标准流程

```
AI 生成初稿 → 人工审核修正 → 代码评审 → 上线
     ↓              ↓           ↓
  工具扫描       复核高风险模块   生成审查报告
```

---

## 前后端契约一致性审查

> 前后端分离项目中，**接口契约不一致**是高频且隐蔽的问题类型。单文件审查无法发现，必须专项检查。

### 检查维度

| 检查项 | 说明 | 常见表现 |
|-------|------|---------|
| **端点存在性** | 前端调用的每个 API 端点在后端都有定义 | 前端调 `/auth/refresh` 但后端未实现 |
| **HTTP 方法** | 前端使用的 HTTP 方法与后端路由一致 | 前端 PUT 后端 PATCH |
| **请求体字段** | 前端发送的字段与后端 schema 一致 | 前端传 `refresh_token` 后端期望 `token` |
| **响应体类型** | 前端 TypeScript 类型与后端响应结构一致 | 后端返回 UUID 字符串前端定义 number |
| **枚举值匹配** | 前后端的枚举值完全一致 | 前端 `active` 后端 `is_active` |
| **认证流程** | 登录/刷新/登出流程前后端一致 | 前端有 refresh 逻辑后端无 refresh 端点 |
| **分页参数** | 分页字段名和语义一致 | 前端 `page` 后端 `offset` |

### 检查方法

1. **提取前端 API 调用清单**：从前端 API 客户端文件（如 `api.ts`、`client.ts`）中提取所有端点
2. **提取后端路由清单**：从后端路由文件中提取所有注册的端点
3. **交叉比对**：
   - 前端有但后端没有 → P0（调用必然 404）
   - 字段名不一致 → P1（运行时数据丢失）
   - 类型不一致 → P2（边界条件下出问题）

---

## 环境与配置文件审查

> 配置文件是安全漏洞的温床。很多生产事故源于 .env 中的弱密钥或错误的调试开关。

### 检查清单

| 检查项 | 说明 | 风险等级 |
|-------|------|---------|
| **密钥强度** | 密钥长度 ≥ 32 字符，不含可推测模式（年份、项目名、"change-me"等） | P0 |
| **数据库 URL** | 是否指向开发环境？生产环境是否用强密码？ | P0 |
| **调试模式** | `DEBUG=true` / `debug=true` 是否在生产环境启用？ | P0 |
| **CORS 配置** | 是否包含 `localhost`？是否使用通配符 `*`？ | P1 |
| **Secret 硬编码** | 代码中是否硬编码了密钥/Token？不应出现在源码中 | P0 |
| **默认凭证** | 是否使用默认用户名/密码？ | P0 |
| **敏感信息泄露** | .env 是否被提交到版本控制？.gitignore 是否包含 .env？ | P0 |
| **端口暴露** | 服务端口、管理端口是否绑定到 0.0.0.0？ | P1 |

### 弱密钥检测规则

以下模式视为弱密钥，必须标记为 P0：

```python
WEAK_PATTERNS = [
    "change", "secret", "password", "default", "example",
    "123456", "test", "dev", "demo", "placeholder",
]
```

---

## 多语言审查差异

不同语言有不同的审查重点：

### Java

| 审查点 | 检查内容 |
|-------|---------|
| **Spring 事务** | 事务传播行为、只读事务、事务失效场景 |
| **并发** | synchronized vs ReentrantLock、volatile、ThreadLocal 泄漏 |
| **JVM** | 内存泄漏、GC 调优、对象池化 |
| **常见问题** | 空指针、序列化问题、equals/hashCode |

### Go

| 审查点 | 检查内容 |
|-------|---------|
| **Goroutine** | 泄漏检测、goroutine 数量控制 |
| **Channel** | 死锁检测、关闭时机、select 超时 |
| **Defer** | 执行顺序、性能影响、资源释放 |
| **常见问题** | nil pointer、error 处理、interface 类型断言 |

### Python

| 审查点 | 检查内容 |
|-------|---------|
| **GIL** | CPU 密集型任务是否用多进程 |
| **协程** | async/await 正确使用、事件循环 |
| **装饰器** | 副作用、执行时机、参数传递 |
| **常见问题** | 可变默认参数、浅拷贝、异常吞噬 |

### Node.js / TypeScript

| 审查点 | 检查内容 |
|-------|---------|
| **事件循环** | 阻塞事件循环、setTimeout vs setImmediate |
| **异步** | Promise 错误处理、async/await 异常捕获 |
| **内存** | 内存泄漏、流处理、Buffer 管理 |
| **常见问题** | 回调地狱、undefined/null、类型断言 |

---

## 专家团成员及职责

审查时模拟以下专家视角，每位专家独立审查后汇总结论：

### 专家 1：业务逻辑专家
- **职责**：验证业务逻辑正确性、需求覆盖率
- **关注点**：状态机完整性、边界条件、业务规则
- **输出**：业务逻辑问题列表 + P0/P1/P2 分级

### 专家 2：并发与事务专家
- **职责**：检查并发安全、事务一致性
- **关注点**：分布式锁、幂等性、数据一致性
- **输出**：并发/事务问题列表 + P0/P1/P2 分级

### 专家 3：安全审计专家
- **职责**：检查安全漏洞、权限控制
- **关注点**：SQL注入、XSS、敏感数据、越权访问
- **输出**：安全问题列表（必须 P0）

### 专家 4：性能优化专家
- **职责**：检查性能问题、SQL 优化
- **关注点**：索引、N+1、缓存、批量处理
- **输出**：性能问题列表 + P1/P2 分级

### 专家 5：代码质量专家
- **职责**：检查代码规范、可维护性
- **关注点**：命名、注释、重复代码、异常处理
- **输出**：代码质量问题列表（通常 P2）

---

## 输出格式

> 输出时统一使用 P0/P1/P2 行动体系；内部标记可使用 6 级情感符号。

### 报告严重度标注规则

| 输出展示 | 内部标记 | 说明 |
|---------|---------|------|
| **P0 问题（必须修复）** | 🔴 blocking | 阻断合并，立即修复 |
| **P1 问题（强烈建议）** | 🟠 important | 建议修复，可跟踪处理 |
| **P2 问题（可选优化）** | 🟡 nit / 🔵 suggestion | 不阻断，可选优化 |
| **教学提示** | 📚 learning | 仅出现在评论中，帮助学习 |
| **优秀实现** | 🏆 praise | 仅出现在评论中，肯定优点 |

### 审查报告模板

```markdown
# 代码审查报告

## 项目结构概览
- **项目名**：[项目名]
- **项目类型**：[前端/后端/全栈]
- **技术栈**：[框架+语言]
- **文件总数**：[排除忽略目录后的文件数]
- **核心模块**：[列出核心模块名]
- **入口文件**：[main.py / index.ts 等]

## 审查计划

| 批次 | 审查单元 | 文件列表 | 状态 |
|-----|---------|---------|------|
| 1 | [模块名] | [文件列表] | ✅ 已完成 / ⏳ 进行中 / ⬜ 待审查 |
| 2 | ... | ... | ... |

## 概要
- **审查时间**：[时间]
- **语言**：[Java/Go/Python/Node.js]
- **代码分类**：[可用/待修改/风险无效]

## P0 问题（必须修复）
| 问题 | 位置 | 专家 | 修复建议 |
|-----|------|-----|----------|
| [问题描述] | [文件:行号/方法] | [专家名] | [具体修复方案或代码示例] |

## P1 问题（强烈建议）
| 问题 | 位置 | 专家 | 修复建议 |
|-----|------|-----|----------|
| [问题描述] | [文件:行号/方法] | [专家名] | [具体修复方案或代码示例] |

## P2 问题（可选优化）
| 问题 | 位置 | 专家 | 修复建议 |
|-----|------|-----|----------|
| [问题描述] | [文件:行号/方法] | [专家名] | [具体修复方案或代码示例] |

## 量化指标

| 指标 | 值 | 是否达标 |
|-----|-----|----------|
| 需求覆盖率 | X% | ✅/❌ |
| 异常分支覆盖率 | X% | ✅/❌ |
| SQL 性能风险率 | X% | ✅/❌ |
| P0 问题数 | X | ✅/❌ |

> 💡 **提示**：如需 CI/CD 集成，可生成 JSON 格式报告：`code-review-panel . --format json -o report.json`

## 高风险模块
- [模块名]：[风险描述] → [建议动作]

## 最终结论
- [ ] 通过，可上线
- [ ] 待修复 P0/P1 后上线
- [ ] 不通过，需重写

## 修复建议汇总

> 按优先级排序，每个建议必须包含具体操作步骤或代码示例

### P0 修复
1. **[问题标题]**
   - 文件：`[路径]`
   - 当前代码：
     ```[语言]
     [问题代码]
     ```
   - 修复方案：
     ```[语言]
     [修复后代码]
     ```

### P1 修复
1. **[问题标题]**
   - 同上格式
```

---

## JSON 报告格式

> 支持机器解析的标准化输出，适用于 CI/CD 集成、自动化流水线、质量门禁。

### JSON Schema

```json
{
  "version": "1.0",
  "metadata": {
    "project": "<项目名>",
    "language": "<语言>",
    "reviewDate": "<ISO 8601 日期>",
    "reviewer": "code-review-panel",
    "totalFiles": <文件总数>,
    "totalLines": <总行数>
  },
  "summary": {
    "p0Count": <P0 问题数>,
    "p1Count": <P1 问题数>,
    "p2Count": <P2 问题数>,
    "可用代码": <可用代码比例>,
    "待修改代码": <待修改代码比例>,
    "风险无效代码": <风险无效代码比例>,
    "status": "PASS | CONDITIONAL_PASS | FAIL"
  },
  "issues": [
    {
      "id": "P0-1",
      "severity": "P0",
      "category": "<安全/并发/逻辑/性能/规范>",
      "title": "<问题标题>",
      "location": {
        "file": "<文件路径>",
        "line": <行号>,
        "function": "<函数名>"
      },
      "description": "<问题描述>",
      "expert": "<专家名>",
      "fix": {
        "current": "<当前代码>",
        "suggested": "<建议代码>",
        "effort": "<LOW | MEDIUM | HIGH>",
        "estimatedMinutes": <预估分钟数>
      },
      "mustFix": true
    }
  ],
  "modules": [
    {
      "name": "<模块名>",
      "files": ["<文件列表>"],
      "status": "PASS | FAIL",
      "issues": ["P0-1", "P1-2"]
    }
  ],
  "checklist": {
    "p0Passed": <true | false>,
    "p1Passed": <true | false>,
    "p2Passed": <true | false>
  }
}
```

### 使用场景

| 场景 | 推荐格式 | 工具 |
|-----|---------|-----|
| 人工阅读 | Markdown | 直接查看 `CODE_REVIEW_REPORT.md` |
| CI 门禁 | JSON | `code-review-panel --format json -o report.json` |
| 自动化流水线 | JSON | 解析 `report.json` 的 `summary.status` |
| 质量仪表盘 | JSON | 提取 `summary.*` 字段绘制趋势图 |

### CI 集成示例

```yaml
# .github/workflows/code-review.yml
- name: Code Review
  run: |
    code-review-panel . --format json -o report.json
    
- name: Check Quality Gate
  run: |
    P0_COUNT=$(cat report.json | jq '.summary.p0Count')
    if [ "$P0_COUNT" -gt 0 ]; then
      echo "::error::Found $P0_COUNT P0 issues - blocking build"
      exit 1
    fi
```

---

## PR 评论格式生成

> 自动生成 GitHub PR / GitLab MR 评论，支持直接粘贴到评审界面。

### GitHub PR 评论格式

```markdown
## 📋 Code Review Report

### Summary
| Severity | Count | Status |
|----------|-------|--------|
| 🔴 P0 | {p0Count} | {'❌ FAIL' if p0Count > 0 else '✅ PASS'} |
| 🟠 P1 | {p1Count} | {'⚠️  Review Required' if p1Count > 0 else '✅ PASS'} |
| 🟡 P2 | {p2Count} | ℹ️  Optional |

### 🔴 P0 Issues (Must Fix)
{''.join([f"- **[P0-{i+1}]** {issue['title']}\n  - File: `{issue['location']['file']}`\n  - Expert: {issue['expert']}\n  - Fix: {issue['fix']['suggested'][:100]}..." for i, issue in enumerate(p0_issues)]) if p0_issues else '✅ No P0 issues found'}

### 🟠 P1 Issues (Recommended)
{''.join([f"- **[P1-{i+1}]** {issue['title']}" for i, issue in enumerate(p1_issues)]) if p1_issues else '✅ No P1 issues found'}

### ℹ️ Statistics
- Files reviewed: {totalFiles}
- Total lines: {totalLines}
- Review date: {reviewDate}

---
*Generated by code-review-panel*
```

### GitLab MR 评论格式

```markdown
## 📋 Code Review Report

### Summary
> P0: {p0Count} | P1: {p1Count} | P2: {p2Count}

### P0 Issues
{''.join([f"**{issue['title']}**\nFile: `{issue['location']['file']}`\n{issue['fix']['suggested'][:200]}" + '...' if len(issue['fix']['suggested']) > 200 else f"**{issue['title']}**\nFile: `{issue['location']['file']}`\n{issue['fix']['suggested']}" for i, issue in enumerate(p0_issues)]) if p0_issues else '✅ No P0 issues found'}
```

### 使用方法

1. **生成 Markdown 评论**：
   ```bash
   code-review-panel . --format pr-comment -o pr_comment.md
   ```

2. **复制到 PR/MR**：将 `pr_comment.md` 内容复制到 GitHub PR 或 GitLab MR 评论框

3. **自动化集成**：
   ```bash
   # GitHub PR 评论
   gh pr comment $PR_NUMBER -F pr_comment.md
   
   # GitLab MR 评论
   glab mr note $MR_NUMBER -F pr_comment.md
   ```

---

## 基线对比机制

> 记录每次审查结果，支持增量审查和趋势跟踪。

### 基线文件格式

```json
// .code-review-baseline.json
{
  "version": "1.0",
  "project": "<项目名>",
  "baselineDate": "<ISO 8601 日期>",
  "summary": {
    "p0Count": <当前 P0 数>,
    "p1Count": <当前 P1 数>,
    "p2Count": <当前 P2 数>
  },
  "issues": [
    {
      "id": "P0-1",
      "severity": "P0",
      "title": "<问题标题>",
      "location": { "file": "<文件>", "line": <行号> },
      "status": "OPEN | FIXED | NEW"
    }
  ]
}
```

### 工作流程

#### 保存基线

```bash
# 首次审查后保存基线
code-review-panel . --save-baseline

# 指定基线文件名
code-review-panel . --save-baseline --baseline .code-review-baseline-v1.json
```

#### 增量审查

```bash
# 与基线对比，只报告新增/已修复问题
code-review-panel . --diff --baseline .code-review-baseline.json
```

#### 增量审查输出

```markdown
## 与基线对比

### 📉 已修复（3）
- [FIXED] P0-1：JWT 密钥硬编码
- [FIXED] P1-2：N+1 查询问题
- [FIXED] P2-3：命名不规范

### 📈 新增问题（1）
- [NEW] P0-3：新增 XSS 漏洞（auth.py:42）

### 📊 趋势变化
| 类型 | 基线 | 当前 | 变化 |
|-----|------|------|------|
| P0 | 3 | 1 | -2 |
| P1 | 5 | 4 | -1 |
| P2 | 8 | 9 | +1 |
```

### Git Diff 模式

> 只审查 git 变更的文件，适合 PR 审查场景。

```bash
# 审查 git diff 中的文件
code-review-panel . --git-diff

# 审查指定 commit
code-review-panel . --git-diff HEAD~1

# 审查指定分支差异
code-review-panel . --git-diff main...feature-branch
```

Git Diff 模式自动：
1. 提取变更文件列表
2. 只审查变更文件
3. 在报告中标注"仅审查变更"
4. 支持增量基线对比

### 审查历史

```
.code-review-history/
  ├── 2026-05-14-initial.json      # 首次审查
  ├── 2026-05-20-followup.json    # 第二次审查
  └── 2026-06-01-baseline.json    # 正式基线
```

---

## 修复成本估算

> 每个问题必须包含修复成本估算，帮助团队合理安排修复计划。

### 成本分级

| 级别 | 标识 | 预估时间 | 典型问题 |
|------|------|---------|---------|
| **低风险** | 🟢 LOW | < 5 分钟 | 语法错误、硬编码、明显拼写 |
| **中风险** | 🟡 MEDIUM | 5-30 分钟 | 逻辑错误、缺少校验、简单重命名 |
| **高风险** | 🔴 HIGH | 30 分钟 - 2 小时 | 并发问题、架构缺陷、数据迁移 |
| **重构** | 🟣 REFACTOR | > 2 小时 | 需要重构的设计问题 |

### 成本估算标准

| 问题类型 | 典型成本 | 估算依据 |
|---------|---------|---------|
| 环境配置硬编码 | 🟢 LOW | 直接修改 .env |
| 参数校验缺失 | 🟡 MEDIUM | 添加 validate 函数 |
| SQL 性能问题 | 🟡-🔴 MEDIUM-HIGH | 添加索引 + 改写查询 |
| 并发竞态条件 | 🔴 HIGH | 需要引入锁机制 |
| 事务边界错误 | 🔴 HIGH | 重构事务范围 |
| 权限控制缺陷 | 🔴 HIGH | 审查 + 重构鉴权逻辑 |
| 架构设计缺陷 | 🟣 REFACTOR | 需要设计评审 |

### 报告展示

```markdown
## 修复成本估算

### P0 问题修复成本
| 问题 | 成本 | 预估时间 | 修复优先级 |
|-----|------|---------|----------|
| P0-1：JWT 密钥硬编码 | 🟢 LOW | 3 分钟 | 立即 |
| P0-2：配额竞态条件 | 🔴 HIGH | 45 分钟 | 立即 |

### P1 问题修复成本
| 问题 | 成本 | 预估时间 | 建议修复时机 |
|-----|------|---------|------------|
| P1-1：N+1 查询 | 🟡 MEDIUM | 15 分钟 | 本次迭代 |
| P1-2：缺少索引 | 🟡 MEDIUM | 10 分钟 | 本次迭代 |

### 总修复成本
- P0 总计：约 1 小时
- P1 总计：约 30 分钟
- P2 总计：约 2 小时（可选）

> 💡 **建议**：P0 问题可在 2 小时内集中修复，P1 问题纳入本次迭代。
```

---

## 优先级矩阵

> 影响面 × 严重度矩阵，帮助团队决定修复顺序。

### 矩阵定义

| | **高影响** | **低影响** |
|---|----------|----------|
| **严重 Bug** | 🔴 **立即修复** | 🟠 **本周修复** |
| **设计缺陷** | 🟠 **下周修复** | 🔵 **排期修复** |
| **代码异味** | 🔵 **排期修复** | ⚪ **可选修复** |

### 影响维度

| 影响类型 | 高影响 | 低影响 |
|---------|-------|-------|
| **数据安全** | 泄露用户数据 | 非敏感日志 |
| **系统稳定** | 服务不可用 | 性能轻微下降 |
| **业务连续性** | 核心功能不可用 | 边缘功能受影响 |
| **合规性** | 违反法规 | 轻微合规问题 |
| **用户规模** | 影响所有用户 | 影响少数用户 |

### 严重度定义

| 级别 | 定义 | 示例 |
|------|-----|-----|
| **严重 Bug** | 导致数据丢失、安全问题、系统崩溃 | SQL 注入、内存泄漏、事务不一致 |
| **设计缺陷** | 架构/设计层面的问题 | 循环依赖、紧耦合、违反SOLID |
| **代码异味** | 可维护性问题 | 重复代码、命名不规范、过长函数 |

### 矩阵决策示例

```markdown
## 优先级决策

### 🔴 高影响 + 严重 Bug = 立即修复
- P0-1：JWT 密钥可预测 → 立即修复
- P0-2：配额检查竞态 → 立即修复

### 🟠 高影响 + 设计缺陷 = 下周修复
- P1-1：循环依赖 → 下周重构
- P1-2：事务边界不清晰 → 下周重构

### 🔵 低影响 + 设计缺陷 = 排期修复
- P2-1：命名不规范 → 排入迭代
- P2-2：重复代码 → 排入迭代
```

---

## 业务规则自动化

> 自动从代码中提取业务规则，生成 `references/business-rules.md` 初稿供人工修正。

### 提取规则

| 规则类型 | 提取来源 | 提取方式 |
|---------|---------|---------|
| **表名/字段名** | 数据库模型 | 从 SQLAlchemy/TypeORM 模型名推断 |
| **业务约束** | 代码注释、变量名 | 关键词匹配（must/should/check/validate） |
| **状态枚举** | 模型字段 | 从 choices/enum 推断 |
| **API 契约** | 路由定义 | 从 path parameters/query parameters 推断 |
| **权限规则** | 鉴权装饰器 | 从 @require_permission 等推断 |

### 自动提取示例

```bash
# 提取业务规则到 business-rules-draft.md
python scripts/extract_business_rules.py . -o business-rules-draft.md

# 查看生成的规则
cat business-rules-draft.md
```

### 生成模板格式

```markdown
# 业务规则 - [项目名]

> ⚠️ 本文件由 code-review-panel 自动生成，请人工审核并修正。

## 数据模型规则

### Task（任务）
- **状态**：pending / running / completed / failed
- **约束**：
  - `tenant_id` 必须有效
  - `created_by` 必须存在
  - 同一租户下任务名唯一

### DetectionResult（检测结果）
- **状态**：pending / reviewed / accepted / rejected
- **约束**：
  - `task_id` 必须引用已存在的任务
  - `result` 字段最大 10MB

## API 约束

### 创建任务
- **路径**：POST /api/tasks
- **必填字段**：name, type
- **可选字段**：config, priority
- **权限**：tenant:write

### 查询任务
- **路径**：GET /api/tasks
- **查询参数**：status, tenant_id, page, size
- **权限**：tenant:read

## 业务约束

### 配额限制
- 每个租户每日最多创建 100 个任务
- 超出后返回 429 Too Many Requests

### 数据隔离
- 所有查询必须包含 `tenant_id` 条件
- 禁止跨租户访问
```

### 使用流程

```
1. 运行提取脚本：python scripts/extract_business_rules.py . -o business-rules-draft.md
2. 人工审核：检查推断的规则是否正确
3. 修正规则：补充遗漏的规则、修正错误的推断
4. 保存正式版本：mv business-rules-draft.md references/business-rules.md
5. 下次审查时加载：references/business-rules.md 将被自动读取
```

### extract_business_rules.py 使用

```bash
# 基本用法
python scripts/extract_business_rules.py <项目路径>

# 指定输出文件
python scripts/extract_business_rules.py . -o business-rules-draft.md

# 指定模型文件目录
python scripts/extract_business_rules.py . --models-dir app/models -o business-rules-draft.md

# 支持的语言
python scripts/extract_business_rules.py . --language python  # Python/SQLAlchemy
python scripts/extract_business_rules.py . --language java       # Java/JPA
python scripts/extract_business_rules.py . --language typescript # TypeScript/TypeORM
```

### 已知限制

| 限制 | 说明 | 建议 |
|------|-----|-----|
| 隐式业务规则 | 未在代码中体现的规则无法提取 | 人工补充 |
| 复杂约束 | 多表关联约束提取困难 | 人工标注 |
| 第三方库规则 | 不从外部库提取 | 手动添加 |

---

## 审查历史与趋势分析

> 记录每次审查结果，生成趋势图，帮助团队了解代码质量变化。

### 历史目录结构

```
.code-review-history/
  ├── 2026-05-14-initial.json       # 首次审查
  ├── 2026-05-20-followup.json     # 第二次审查
  ├── 2026-06-01-pre-release.json  # 发布前审查
  ├── trend.json                    # 趋势数据汇总
  └── trend.png                     # 趋势图（可选）
```

### 历史记录格式

```json
// 2026-05-14-initial.json
{
  "version": "1.0",
  "date": "2026-05-14T10:30:00+08:00",
  "project": "ScanIt",
  "commit": "a1b2c3d",
  "branch": "main",
  "summary": {
    "p0Count": 7,
    "p1Count": 12,
    "p2Count": 10,
    "filesReviewed": 59,
    "totalLines": 15234
  },
  "issues": [
    { "id": "P0-1", "title": "JWT 密钥硬编码", "status": "OPEN" },
    { "id": "P1-1", "title": "N+1 查询", "status": "OPEN" }
  ]
}
```

### 趋势数据汇总

```json
// trend.json
{
  "project": "ScanIt",
  "generatedAt": "2026-06-01T15:00:00+08:00",
  "history": [
    { "date": "2026-05-14", "p0": 7, "p1": 12, "p2": 10 },
    { "date": "2026-05-20", "p0": 3, "p1": 8, "p2": 9 },
    { "date": "2026-06-01", "p0": 0, "p1": 2, "p2": 5 }
  ],
  "trend": {
    "p0Change": -7,
    "p1Change": -10,
    "p2Change": -5,
    "overallTrend": "IMPROVING"
  }
}
```

### 使用命令

```bash
# 保存当前审查到历史
code-review-panel . --save-history

# 查看趋势
code-review-panel . --show-trend

# 生成趋势图（需要 matplotlib）
code-review-panel . --generate-trend-chart -o trend.png

# 对比两次审查
code-review-panel . --compare 2026-05-14-initial.json 2026-05-20-followup.json
```

### 趋势报告示例

```markdown
## 代码质量趋势报告

### 问题数量变化
| 日期 | P0 | P1 | P2 | 总计 |
|------|----|----|----|----|
| 2026-05-14 | 7 | 12 | 10 | 29 |
| 2026-05-20 | 3 | 8 | 9 | 20 |
| 2026-06-01 | 0 | 2 | 5 | 7 |

### 趋势分析
- ✅ P0 问题：从 7 降至 0（全部修复）
- ✅ P1 问题：从 12 降至 2（修复 10 个）
- ✅ P2 问题：从 10 降至 5（修复 5 个）
- 📈 整体趋势：**持续改善**

### 建议
- 当前代码质量良好，可以上线
- 剩余 2 个 P1 问题建议下个迭代修复
```

---

## 深度模式：数据流追踪

> 开启 `--deep` 模式后，进行跨文件数据流分析，追踪敏感数据和权限链路。

### 追踪维度

| 追踪类型 | 说明 | 检测目标 |
|---------|------|---------|
| **敏感数据流** | 用户输入 → 存储 → 响应 | 数据泄露、未脱敏 |
| **权限链路** | 路由 → 依赖 → 数据查询 | 越权访问 |
| **错误处理链** | 异常抛出 → 捕获 → 响应 | 异常吞没、敏感信息泄露 |
| **事务边界** | 开始 → 操作 → 提交/回滚 | 事务不一致 |

### 敏感数据流追踪

```
用户输入
    ↓
API 端点
    ↓
参数校验 ← 校验通过？
    ↓
存储到数据库 ← 是否脱敏？
    ↓
返回响应 ← 是否包含敏感字段？
```

**追踪示例**：

```markdown
## 敏感数据流追踪：用户手机号

### 数据流路径
1. **输入**：`POST /api/users` → `phone: "13800138000"`
2. **存储**：`users.phone = phone`（未脱敏）
3. **查询**：`GET /api/users/{id}` → 返回完整手机号
4. **问题**：⚠️ 手机号未脱敏直接存储和返回

### 建议修复
- 存储：`users.phone = mask_phone(phone)` → `138****8000`
- 返回：`UserResponse.phone` 使用脱敏字段
```

### 权限链路追踪

```
路由定义
    ↓
依赖注入
    ↓
获取当前用户
    ↓
检查权限 ← 权限校验存在？
    ↓
数据查询 ← 是否有 tenant_id 过滤？
    ↓
返回结果 ← 是否越权？
```

**追踪示例**：

```markdown
## 权限链路追踪：DELETE /api/tasks/{id}

### 链路分析
1. **路由**：`@router.delete("/tasks/{id}")`
2. **依赖**：`current_user = Depends(get_current_user)`
3. **权限检查**：❌ 未检查 `current_user` 是否有删除权限
4. **数据查询**：`task = await db.get(Task, id)`
5. **租户隔离**：❌ 未检查 `task.tenant_id == current_user.tenant_id`
6. **风险**：⚠️ 任意用户可删除任意任务（越权）

### 建议修复
```python
# 添加租户隔离检查
task = await db.execute(
    select(Task).where(
        Task.id == id,
        Task.tenant_id == current_user.tenant_id
    )
)
if not task:
    raise HTTPException(404, "Task not found")
```
```

### 错误处理链追踪

```markdown
## 错误处理链追踪：支付流程

### 链路分析
1. **入口**：`POST /api/payments`
2. **异常抛出**：`PaymentGatewayError("连接超时")`
3. **捕获**：`except Exception as e: logger.error(e)`
4. **响应**：`{"detail": "内部错误"}`
5. **问题**：⚠️ 异常被吞没，未返回具体错误信息给调用方

### 建议修复
```python
try:
    result = await payment_gateway.process(payment)
except PaymentGatewayError as e:
    logger.error(f"Payment failed: {e}")
    raise HTTPException(502, f"支付网关错误: {e}")
```
```

### 使用方法

```bash
# 开启深度模式
code-review-panel . --deep

# 只追踪敏感数据流
code-review-panel . --deep --track sensitive-data

# 只追踪权限链路
code-review-panel . --deep --track permission

# 只追踪错误处理
code-review-panel . --deep --track error-handling

# 只追踪事务边界
code-review-panel . --deep --track transaction
```

### 深度模式输出格式

```markdown
## 深度分析报告

### 敏感数据流追踪
| 数据类型 | 入口 | 存储是否脱敏 | 响应是否脱敏 | 风险等级 |
|---------|-----|------------|------------|---------|
| 手机号 | POST /users | ❌ | ❌ | 🔴 P0 |
| 邮箱 | POST /users | ❌ | ✅ | 🟡 P2 |
| 密码 | POST /auth/login | ✅ | ✅ | ✅ 安全 |

### 权限链路追踪
| 端点 | 鉴权 | 租户隔离 | 越权风险 |
|-----|-----|---------|---------|
| DELETE /tasks/{id} | ✅ | ❌ | 🔴 P0 |
| GET /results | ✅ | ✅ | ✅ 安全 |

### 错误处理链追踪
| 模块 | 异常捕获 | 错误传递 | 问题 |
|-----|---------|---------|-----|
| 支付 | ❌ 吞没 | ❌ | 🟠 P1 |
| 认证 | ✅ | ✅ | ✅ 正确 |
```

---

## 协作语气指南

> 审查评论的语气直接影响团队协作效率。参考 `references/code-review-best-practices.md`（完整沟通指南）。

### 核心原则

- 用**提问**代替命令："你觉得…怎么样？" 而不是 "你应该…"
- 用**建议**代替指责："我们可否考虑…" 而不是 "这是错的"
- **具体且可操作**：建议修改时附带代码示例
- **解释 "为什么"**：帮助作者理解建议背后的原因

### 严重度符号使用建议

| 符号 | 在评论中的措辞建议 |
|------|----------------|
| 🔴 blocking | "这个问题在生产前必须修复，因为…" |
| 🟠 important | "这个问题建议本次修复，原因是…" |
| 🟡 nit | "一个小建议，不考虑也没关系…" |
| 🔵 suggestion | "有一个改进思路，你可以考虑…" |
| 📚 learning | "补充一个知识点：…" |
| 🌟 praise | "这个实现很棒，特别是…" |

### 处理分歧

1. 先问澄清性问题，寻求理解
2. 承认有效观点
3. 提供数据支持（基准测试、文档、示例）
4. 必要时请高级开发者参与

---

## 渐进式披露

> 本 skill 采用渐进式披露设计：核心流程在 SKILL.md，详细检查清单按需加载自 `references/*.md`。

**按需加载规则：**

| 触发条件 | 加载文件 |
|-----------|---------|
| 安全相关问题 | `references/security-review-guide.md` |
| 通用代码质量检查 | `references/code-quality-universal.md` |
| 性能相关问题 | `references/performance-review-guide.md` |
| 审查沟通语气 | `references/code-review-best-practices.md` |
| Python 反模式 | `references/framework-antipatterns.md` |
| 前后端契约检查 | 运行 `scripts/extract_api_endpoints.py` |
| ORM 模型引用检查 | 运行 `scripts/check_model_attributes.py` |

**示例：运行脚本提取 API 端点**
```bash
# 在项目根目录执行
python scripts/extract_api_endpoints.py . -o api_endpoints.md

# 查看输出
cat api_endpoints.md
```

**示例：运行安全扫描**
```bash
python scripts/security_scan.py . -o security_report.md
```

**示例：运行模型属性检查**
```bash
python scripts/check_model_attributes.py . -o model_attrs.md
```

---

## 审查流程（标准操作规程）

> 当用户请求对整个项目/仓库进行代码审查时，**必须按以下流程执行**，不得跳过任何步骤。
> 本流程内置**进度持久化机制**，审查中断后可安全恢复，避免重复劳动。

### 第零步：代码范围评估与审查计划

> ⚠️ **强制要求**：每次代码审查前必须执行此步骤，不得跳过。评估结果必须**即时输出**给用户，不要等最后统一输出。

**目的**：明确审查范围，评估工作量，制定分步计划，让用户对审查进度有清晰预期。

1. **扫描项目目录结构**
   ```bash
   # 统计代码文件数量和大小
   find . -type f \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.go' -o -name '*.java' -o -name '*.vue' -o -name '*.rs' \) | wc -l
   
   # 统计总代码大小
   find . -type f \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' \) -exec du -ch {} + | tail -1
   
   # 按目录统计
   du -sh */ 
   ```

2. **输出范围评估报告**（立即输出，不等审查完成）
   ```markdown
   ## 代码范围评估
   
   | 指标 | 值 |
   |-----|-----|
   | 代码文件数 | X 个 |
   | 代码总大小 | X MB / X KB |
   | 最大文件 | [文件名] (X KB) |
   | 目录数 | X 个 |
   
   ### 模块分布
   | 目录 | 文件数 | 大小 | 说明 |
   |-----|-------|------|------|
   | backend/app/api | X | X KB | API 路由层 |
   | backend/app/models | X | X KB | 数据模型 |
   | ... | ... | ... | ... |
   
   ### 审查计划
   | 批次 | 范围 | 文件数 | 预估时间 |
   |-----|------|-------|----------|
   | 1 | 核心API + 认证 | X | X min |
   | 2 | 数据模型 + Schema | X | X min |
   | 3 | ... | ... | ... |
   
   **总预估时间**：X 分钟
   ```

3. **分步执行，持续输出**
   - 每完成一个批次，**立即输出**该批次的审查结果
   - 格式：`✅ 批次 N 完成 | 模块：XXX | P0: X | P1: X | P2: X | 耗时：X min`
   - 发现 P0 问题时**立即输出**，不攒到最后
   - 每个批次完成后更新进度文件

### 第零点五步：环境感知与进度恢复

**环境感知**：在恢复进度之前，先理解项目的技术栈和运行环境。

1. **读取项目配置文件**（预检查）
   - `package.json` / `requirements.txt` / `go.mod` / `pom.xml` → 确定技术栈版本
   - `.github/workflows/` / `.gitlab-ci.yml` → 了解 CI/CD 流程
   - `Dockerfile` / `docker-compose.yml` → 了解运行环境
   - `README.md` → 了解项目背景和业务目标
   - `pyproject.toml` / `.eslintrc` / `tsconfig.json` → 了解代码规范配置

2. **恢复审查进度**
   - 检查 `<项目根目录>/.code_review_progress.json` 是否存在
   - 如存在：读取已有批次状态和已发现问题，从最后一个未完成的批次继续
   - 如不存在：创建新的进度文件和空白报告

3. **环境感知输出**
   - 在报告开头增加「项目环境概览」章节：
     ```markdown
     ## 项目环境概览
     - **技术栈**：[从配置文件中提取]
     - **CI/CD**：[GitHub Actions / GitLab CI / Jenkins]
     - **运行环境**：[Docker / 直接运行 / K8s]
     - **代码规范**：[ESLint / Pylint / golangci-lint]
     ```

> ⚠️ **断点续审原则**：只要当前批次有任何实质输出（问题发现/文件读取），就把**批次状态更新写入进度文件**，再继续下一个批次。不等到整个审查完成才写入。

### 进度文件格式

```json
{
  "project": "D:\\work\\code\\ScanIt",
  "started_at": "2026-05-14T10:00:00",
  "updated_at": "2026-05-14T11:30:00",
  "batches": [
    {
      "batch": 1,
      "unit": "认证授权",
      "files": ["auth.py", "deps.py", "middleware.py"],
      "status": "completed",
      "p0_found": 2,
      "p1_found": 1,
      "p2_found": 0,
      "context_patterns": [
        "flush vs commit 不一致",
        "increment_quota_usage 无 commit"
      ],
      "completed_at": "2026-05-14T10:45:00"
    },
    {
      "batch": 2,
      "unit": "核心业务",
      "files": ["tasks.py", "results.py", "works.py"],
      "status": "completed",
      "p0_found": 3,
      "p1_found": 2,
      "p2_found": 0,
      "context_patterns": [
        "Task 模型无 title/keywords 字段",
        "Result 模型 reviewed_by/reviewed_at 字段缺失"
      ],
      "completed_at": "2026-05-14T11:20:00"
    },
    {
      "batch": 3,
      "unit": "LLM服务",
      "files": ["llm.py", "detector_llm.py", "llm_provider/"],
      "status": "in_progress",
      "p0_found": 0,
      "p1_found": 1,
      "p2_found": 0,
      "files_read": ["llm.py"],
      "files_remaining": ["detector_llm.py", "llm_provider/__init__.py"],
      "context_patterns": [
        "new_event_loop() 不安全"
      ]
    }
  ],
  "total_p0": 5,
  "total_p1": 4,
  "total_p2": 0,
  "report_path": "CODE_REVIEW_REPORT.md"
}
```

**关键字段说明**：

| 字段 | 说明 |
|-----|------|
| `status` | `pending` / `in_progress` / `completed` |
| `context_patterns` | 本批次发现的问题模式，传播到下一批次 |
| `files_read` | 当前批次已读取的文件（in_progress 时用） |
| `files_remaining` | 当前批次剩余待读文件 |
| `updated_at` | 每次批次完成时更新 |

### 第一步：项目结构探查

审查前**必须先了解项目全貌**，而不是直接读代码。

1. **查看项目根目录结构**
   ```
   ls -la <项目根目录>
   ```
   识别项目类型（前端/后端/全栈）、语言、框架、部署方式。

2. **读取 .gitignore**
   ```
   cat <项目根目录>/.gitignore
   ```
   记录需要忽略的目录和文件模式（如 node_modules、__pycache__、.env、dist、build、vendor 等）。

3. **递归列出项目文件树（排除忽略目录）**
   ```
   # Linux/Mac
   find <项目根目录> -type f \
     -not -path '*/node_modules/*' \
     -not -path '*/__pycache__/*' \
     -not -path '*/.git/*' \
     -not -path '*/dist/*' \
     -not -path '*/build/*' \
     -not -path '*/vendor/*' \
     -not -path '*/.venv/*' \
     | head -500
   
   # Windows PowerShell
   Get-ChildItem -Path <项目根目录> -Recurse -File `
     | Where-Object { $_.FullName -notmatch 'node_modules|__pycache__|\.git\\|dist|build|vendor|\.venv' } `
     | Select-Object -First 500 FullName
   ```

4. **统计项目规模**
   - 文件总数（排除忽略目录）
   - 各语言文件分布
   - 识别核心模块和入口文件

### 第二步：审查任务拆解

**大项目必须拆解**，不要试图一次读完所有代码。

1. **按模块/目录拆分审查单元**
   每个审查单元不超过 10 个文件，按功能聚合：

   | 审查单元 | 典型范围 | 优先级 |
   |---------|---------|-------|
   | 认证授权 | auth、login、JWT、middleware | 🔴 最高 |
   | 核心业务 | 订单、支付、库存等主流程 | 🔴 最高 |
   | 数据访问 | models、repository、DAO | 🟠 高 |
   | 接口层 | controllers、routes、API | 🟠 高 |
   | 异步任务 | celery、workers、jobs | 🟡 中 |
   | 工具/配置 | utils、config、helpers | 🟢 低 |
   | 前端页面 | pages、components | 🟢 低 |

2. **记录审查计划到报告**
   在审查报告开头增加 **审查计划** 章节：

   ```markdown
   ## 审查计划

   | 批次 | 审查单元 | 文件列表 | 状态 |
   |-----|---------|---------|------|
   | 1 | 认证授权 | auth.py, deps.py, middleware.py | ⏳ 进行中 |
   | 2 | 核心业务 | tasks.py, works.py, results.py | ⬜ 待审查 |
   | 3 | 数据访问 | models/*.py, base.py | ⬜ 待审查 |
   | 4 | 异步任务 | tasks/detection.py, alert.py | ⬜ 待审查 |
   | 5 | LLM服务 | llm.py, detector_llm.py | ⬜ 待审查 |
   | 6 | 前端 | api/client.ts | ⬜ 待审查 |
   ```

3. **按批次执行审查**
   - 每个批次内按优先级读取文件
   - 每个批次完成后更新审查计划状态
   - 发现的 P0 问题立即记录，不等到最后汇总

### 第三步：逐批执行审查（带上下文传播）

> **上下文传播**：每个批次审查前，回顾前序批次已发现的问题 pattern，形成**关注点清单**带入本批次。例如：
> - 前批次发现「flush 不 commit」→ 本批次重点检查所有写操作的持久化语义
> - 前批次发现「模型属性不存在」→ 本批次重点校验所有 ORM 属性引用
> - 前批次发现「Celery event loop 不安全」→ 本批次重点检查所有异步任务模式

每个审查单元执行以下流程：

1. **回顾上下文** — 查看前序批次的关注点清单，确定本批次的额外检查重点
2. **读取文件** — 按审查单元中的文件列表逐一读取
3. **专家团独立审查** — 五位专家各自从自己的维度检查
4. **问题记录** — 发现问题立即记录到报告对应章节
5. **交叉验证** — 同一问题如被多个专家同时发现，提升优先级
6. **提取 pattern** — 本批次发现的新问题模式，记录到关注点清单供后续批次使用
7. **更新计划状态** — 标记当前审查单元为 ✅ 已完成

### 第四步：跨文件关联性扫描

> 所有批次审查完成后，执行一次跨文件的关联性扫描，专门捕获**单文件审查中无法发现的问题**。

#### 4.1 前后端接口契约一致性

- 前端 API 客户端调用的每个端点，后端是否都有对应路由定义？
- 前端请求/响应的 TypeScript 类型与后端 Pydantic schema 字段名、类型是否一致？
- 前端枚举值（如 status、role）与后端 Enum 定义是否完全匹配？
- 前端调用的 HTTP 方法（GET/POST/PUT/PATCH/DELETE）与后端路由装饰器是否一致？

#### 4.2 模型属性引用校验

- 代码中通过点号访问的 ORM 模型属性（如 `user.webhook_url`），在对应模型类中是否存在？
- 代码中 import 的名称（如 `DBDetectionResult`），与实际导出的类名是否一致？
- 跨模块引用的函数/类，在被引用模块中是否已定义或正确导入？

#### 4.3 跨模块调用链路

- 中间件（middleware）与路由（router）的 Depends 链是否完整？
- 异步任务（Celery tasks）引用的模型和函数是否在 worker 可访问的模块中？
- 事件回调/钩子函数是否指向正确的事件名称？

#### 4.4 配置一致性

- 代码中使用的配置键（如 `settings.xxx`）在 config 类中是否有对应定义？
- .env 中配置的值是否满足代码中的校验条件？
- 多环境配置（dev/staging/prod）是否有一致性？

### 第五步：汇总与输出

1. **汇总所有批次的问题 + 跨文件扫描发现的问题**
2. **去重和优先级调整**（多专家命中或跨文件扫描命中的问题升级）
3. **计算量化指标**
4. **生成最终审查报告**，包含：
   - 项目结构概览
   - 审查计划及完成状态
   - P0/P1/P2 问题清单
   - 量化指标
   - 高风险模块
   - 最终结论
   - **修复建议**（每个问题必须附带具体修复方案或代码示例）
5. **写入报告文件**到项目根目录：`<项目根目录>/CODE_REVIEW_REPORT.md`

### 忽略规则（强制）

以下内容**不得纳入审查范围**：

| 类别 | 示例 | 原因 |
|-----|------|------|
| **依赖目录** | node_modules、vendor、.venv | 第三方代码，非项目代码 |
| **构建产物** | dist、build、out、target | 非源码 |
| **缓存/临时** | __pycache__、.cache、.tmp | 自动生成 |
| **版本控制** | .git | 非项目代码 |
| **IDE 配置** | .idea、.vscode | 个人配置 |
| **环境文件** | .env（仅内容，存在性需检查） | 敏感信息 |
| **生成代码** | protobuf 生成、ORM 迁移文件 | 非手写代码 |
| **锁文件** | package-lock.json、poetry.lock | 依赖锁定，非业务代码 |

### 特殊场景

| 场景 | 处理方式 |
|-----|---------|
| **项目极大（>200 文件）** | 只审查核心模块 + 高风险模块，其余标记为待审查 |
| **只审查某个模块** | 直接进入该模块的审查单元，跳过项目结构探查 |
| **只检查特定问题** | 只调用相关专家审查，其余专家跳过 |
| **审查 PR/Diff** | 先获取变更文件列表，再按变更范围执行审查 |

---

## 使用示例

### 示例 1：审查整个项目

**用户**：帮我审查 D:\work\code\ScanIt 项目

**Agent**：

1. **项目结构探查** — ls 根目录、读 .gitignore、列出文件树（排除 node_modules 等）
2. **任务拆解** — 按模块拆分审查单元，记录审查计划
3. **逐批审查** — 批次1(认证授权) → 批次2(核心业务) → 批次3(数据访问) → ...
4. **汇总输出** — 生成 CODE_REVIEW_REPORT.md，包含项目结构、审查计划、问题清单、修复建议

### 示例 2：审查单个接口

**用户**：帮我 review 这段订单创建接口代码

**Agent**：启动专家团审查...

1. 识别语言：Java（Spring Boot）
2. 业务逻辑专家检查订单状态机、金额计算
3. 并发与事务专家检查 @Transactional 边界、幂等性
4. 安全审计专家检查权限校验、敏感数据
5. 性能优化专家检查 SQL 索引、N+1
6. 代码质量专家检查异常处理、参数校验

输出审查报告（含 P0/P1/P2 分级 + 修复建议）。

### 示例 3：检查特定问题

**用户**：这段 Go 代码有没有 goroutine 泄漏？

**Agent**：由并发与事务专家专项检查...

1. 检查 goroutine 创建是否有对应退出机制
2. 检查 channel 是否正确关闭
3. 检查 select + context 超时处理
4. 输出问题列表 + 修复代码示例

---

### Python 异步框架反模式

> 参见 `references/framework-antipatterns.md` 获取完整目录

| 框架 | 反模式 | 正确做法 |
|-----|-------|--------|
| **SQLAlchemy** | `flush()` 后不 `commit()`，依赖 session yield 隐式提交 | 每个写操作显式 `commit()` |
| **SQLAlchemy** | ORM `obj.attr += 1` 读-改-写，并发下竞态 | 用 SQL 原子操作 `UPDATE SET attr=attr+1` |
| **FastAPI** | `Depends()` 链中多个写操作不在同一事务 | 合并为单条条件 UPDATE 或用 `with session.begin()` |
| **Celery** | `new_event_loop()` + `run_until_complete()` | 用 `asyncio.run()` 或集成 celery-redis |
| **Celery** | 任务中用 `ar.get(timeout=...)` 阻塞 worker | 用 Celery group/chord 异步编排 |
| **Python** | 类属性行末逗号导致 tuple 赋值 | 注意 `attr = val,` 等于 `attr = (val,)` |
| **Python** | 生成器中 `yield` 在 `try` 块内 `except pass` | 记录日志而非静默吞没 |
| **Python** | 使用已弃用的 `datetime.utcnow()` | 改用 `datetime.now(timezone.utc)` |

---

## 工具脚本

> `scripts/` 目录包含可自动执行专项扫描的 Python 脚本，审查时根据需要调用。

### extract_api_endpoints.py

**功能**：扫描后端代码，提取所有 API 端点（方法 + 路径 + 函数名）。

**支持框架**：FastAPI、Flask、Express、NestJS

**用法**：
```bash
python scripts/extract_api_endpoints.py <项目目录> -o endpoints.md
```

**输出**：Markdown 表格，可直接贴入审查报告的「前后端契约一致性」章节。

**在审查流程中使用**：第四步「跨文件关联性扫描 → 4.1 前后端接口契约一致性」

---

### security_scan.py

**功能**：扫描项目中的常见安全问题（弱密钥、硬编码密钥、调试模式、CORS 过宽、AWS Key、私钥泄露）。

**用法**：
```bash
python scripts/security_scan.py <项目目录> -o security_report.md
```

**输出**：Markdown 格式的问题清单，按 P0/P1/P2 分级。

**在审查流程中使用**：第一步「项目结构探查」阶段执行，或单独执行安全专项审查。

---

### check_model_attributes.py

**功能**：扫描 ORM 模型定义，提取所有模型和字段名，用于校验跨文件引用是否合法。

**支持 ORM**：SQLAlchemy、Django ORM、TypeORM、Prisma

**用法**：
```bash
python scripts/check_model_attributes.py <项目目录> -o model_attrs.md
```

**输出**：Markdown 表格，按模型名列出所有属性。

**在审查流程中使用**：第四步「跨文件关联性扫描 → 4.2 模型属性引用校验」

---

### review_progress.py

**功能**：管理审查进度，支持断点续审。可创建进度文件、标记批次状态、恢复中断的审查。

**用法**：
```bash
# 初始化进度文件（在项目根目录执行）
python scripts/review_progress.py init "D:\work\code\ScanIt" python+fastapi

# 添加审查批次计划
python scripts/review_progress.py add 1 "认证授权" "auth.py,deps.py,middleware.py"

# 查看当前进度
python scripts/review_progress.py status

# 标记批次开始
python scripts/review_progress.py start 1

# 标记批次完成（记录发现的问题数）
python scripts/review_progress.py complete 1 -p0 2 -p1 1 -p2 0 -patterns "flush不commit,模型属性缺失"

# 标记批次失败
python scripts/review_progress.py fail 2 "上下文超限，需要重新开始"

# 添加备注
python scripts/review_progress.py note "发现SQLAlchemy flush/commit混淆的通用问题"

# 重置进度（删除进度文件）
python scripts/review_progress.py reset
```

**进度文件**：`.code_review_progress.json`（自动创建在项目根目录）

**在审查流程中使用**：第零步「恢复进度」、每一步批次完成时更新状态。

---

## 报告模板

`assets/report_template.md` 提供了标准审查报告模板。

输出路径：`<项目根目录>/CODE_REVIEW_REPORT_YYYYMMDD.md`（例如 `CODE_REVIEW_REPORT_20260514.md`）

模板包含：项目概览、审查计划、P0/P1/P2 问题清单、量化指标、跨文件扫描结果、修复建议、附录（脚本使用记录）。

---

## 与其他 Skill 的协作

| 场景 | 协作方式 |
|-----|---------|
| **框架反模式** | 参见 `references/framework-antipatterns.md` |
| **代码文件编码问题** | 引用 openclaw-text-file 处理编码、换行符问题 |
| **定时审查任务** | 引用 openclaw-cron-skill 设置定期代码审查 |

---

## 注意事项

1. **不编造业务规则**：仅基于已知需求和约束判断，不确定时明确标注
2. **量化优于定性**：用指标说话，避免"感觉有问题"的主观判断
3. **高风险人工复核**：支付、订单、库存、权限等模块必须人工复核
4. **知识持续沉淀**：审查发现的问题应沉淀到 references/ 目录
5. **语言差异**：根据代码语言选择对应的审查重点
