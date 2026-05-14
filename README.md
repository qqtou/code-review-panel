# Code Review Panel 👔

多专家协同代码审查技能，基于三层审查体系 + 四阶段流程，提供标准化、量化的代码质量准入机制。

## 核心特性

- **双轨严重度体系**：6 级情感符号（🔴🟠🟡🔵📚🌟）+ P0/P1/P2 行动体系
- **四阶段审查流程**：上下文收集 → 高层审查 → 逐行分析 → 汇总决策
- **五位专家团**：业务逻辑 / 并发事务 / 安全审计 / 性能优化 / 代码质量
- **全项目 SOP**：项目结构探查 → 任务拆解 → 逐批审查 → 跨文件扫描 → 汇总输出
- **自动化脚本**：API 端点提取、安全扫描、ORM 模型校验
- **渐进式披露**：核心流程在 SKILL.md，详细检查清单按需加载

## 目录结构

```
code-review-panel/
├── SKILL.md                          # 主入口，核心流程和规则
├── README.md                         # 本文件
│
├── scripts/                          # 自动化扫描脚本
│   ├── extract_api_endpoints.py      # 提取后端 API 端点
│   ├── security_scan.py              # 安全问题扫描
│   └── check_model_attributes.py     # ORM 模型属性提取
│
├── references/                       # 详细检查清单（按需加载）
│   ├── framework-antipatterns.md     # 框架级反模式（FastAPI/Flask/Celery/Spring...）
│   ├── pitfalls.md                   # 历史坑点（实战积累）
│   ├── security-checklist.md         # 安全检查清单
│   ├── security-review-guide.md      # 安全审查完整指南
│   ├── code-quality-universal.md     # 通用代码质量检查
│   ├── code-review-best-practices.md # 审查沟通最佳实践
│   ├── performance-review-guide.md   # 性能审查指南
│   ├── business-rules.md             # 业务规则模板
│   └── architecture-constraints.md   # 架构约束模板
│
└── assets/                           # 输出模板
    ├── report_template.md            # 全项目审查报告模板
    ├── pr-review-template.md         # PR 审查评论模板
    └── review-checklist.md           # 审查检查清单
```

## 使用方式

### 对话触发

直接告诉 AI 你需要代码审查：

```
帮我审查 D:\work\code\MyProject 项目
review 这段代码有没有安全问题
检查这个 PR 的并发问题
生成代码审查报告
```

### 脚本独立运行

三个脚本可以脱离 AI 独立使用：

```bash
# 提取 API 端点（自动检测框架）
python scripts/extract_api_endpoints.py ./my-project -o endpoints.md

# 安全扫描
python scripts/security_scan.py ./my-project -o security_report.md

# ORM 模型提取
python scripts/check_model_attributes.py ./my-project -o models.md

# 指定框架
python scripts/extract_api_endpoints.py ./my-project --framework express
python scripts/check_model_attributes.py ./my-project --orm django
```

## 脚本详解

### extract_api_endpoints.py

从后端代码中提取所有 API 端点，输出 Markdown 表格。

| 支持框架 | 检测方式 |
|---------|---------|
| FastAPI | `@router.get("/path")` 装饰器 |
| Flask | `@app.route("/path", methods=[...])` |
| Express | `router.get("/path", handler)` |
| NestJS | `@Get("/path")` 装饰器 |

输出包含：
- 按 HTTP 方法分组的端点清单（路径、函数名、文件、行号）
- ⚠️ 重复路径检测
- 前端契约检查清单模板

### security_scan.py

六大类安全扫描：

| 扫描项 | 检测内容 | 默认级别 |
|-------|---------|---------|
| 弱密钥 | 密钥包含可推测模式 | P0 |
| 硬编码密钥 | 源码中的密码/Token/数据库URL/AWS Key/私钥 | P0/P1 |
| 调试模式 | DEBUG=True、LOG_LEVEL=DEBUG | P0 |
| CORS 配置 | allow_origins=*、包含 localhost | P1 |
| .gitignore | .env 未忽略、敏感文件已跟踪 | P0 |
| 敏感日志 | 日志/print 中输出密码/Token | P1 |

自动去重，支持 `--severity P0` 只输出指定级别。

### check_model_attributes.py

从 ORM 模型定义中提取所有模型和字段。

| 支持 ORM | 检测方式 |
|---------|---------|
| SQLAlchemy | `class User(Base)` + `Column()` / `mapped_column()` |
| Django | `class User(models.Model)` + `models.CharField()` |
| TypeORM | `@Entity()` + `@Column()` |
| Prisma | `model User { }` in schema.prisma |

输出包含：
- 按模型分组的字段清单（名称、类型、可空、唯一、主键）
- 跨文件引用校验清单模板

## 审查流程

### PR / Commit 增量审查（四阶段）

```
阶段一：上下文收集 → 理解变更范围和意图
阶段二：高层审查   → 架构/性能/测试/设计一致性
阶段三：逐行分析   → 五位专家独立审查
阶段四：汇总决策   → 结构化反馈 + 批准状态
```

### 全项目审查（SOP 五步）

```
第一步：项目结构探查  → ls 根目录、读 .gitignore、文件树
第二步：审查任务拆解  → 按模块分批次
第三步：逐批执行审查  → 带上下文传播
第四步：跨文件扫描    → 端点契约 + 模型引用 + 调用链路 + 配置一致性
第五步：汇总与输出    → CODE_REVIEW_REPORT.md
```

## 严重度体系

| 输出展示 | 内部标记 | 动作 |
|---------|---------|------|
| **P0** | 🔴 blocking | 必须修复，阻断合并 |
| **P1** | 🟠 important | 建议修复 |
| **P2** | 🟡 nit / 🔵 suggestion | 可选优化 |
| 教学提示 | 📚 learning | 不强制 |
| 优秀实现 | 🌟 praise | 肯定优点 |

## 依赖

- Python 3.8+
- 无第三方依赖（纯标准库实现）

## 更新日志

- **v1.0** — 三层审查体系 + 五位专家团 + SOP 流程
- **v1.1** — 新增跨文件关联性扫描、环境配置审查、前后端契约检查
- **v2.0** — 双轨严重度体系、四阶段流程、协作语气指南、渐进式披露
- **v2.1** — 自动化脚本（端点提取/安全扫描/模型校验）、报告模板
