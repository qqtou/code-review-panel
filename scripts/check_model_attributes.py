#!/usr/bin/env python3
"""
check_model_attributes.py — 扫描 ORM 模型定义，提取所有模型和字段名。

支持 ORM：SQLAlchemy、Django ORM、TypeORM、Prisma
输出：Markdown 表格，供跨文件引用校验使用

用法：
    python check_model_attributes.py <项目目录> [-o model_attrs.md] [--orm auto|sqlalchemy|django|typeorm|prisma]
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ModelField:
    name: str
    field_type: str
    nullable: bool = False
    unique: bool = False
    primary_key: bool = False
    default: str = ""
    comment: str = ""


@dataclass
class Model:
    name: str
    file: str
    line: int
    base_classes: list = field(default_factory=list)
    fields: list = field(default_factory=list)
    is_abstract: bool = False


SKIP_DIRS = {
    "node_modules", "__pycache__", ".git", "dist", "build",
    "vendor", ".venv", "venv", ".idea", ".vscode",
    ".next", ".nuxt", "coverage", ".mypy_cache",
    "migrations", "alembic", ".tox", ".pytest_cache",
}


def detect_orm(project_dir: str) -> str:
    """根据项目文件自动检测 ORM"""
    # Check for Python
    pyproject = Path(project_dir) / "pyproject.toml"
    requirements = Path(project_dir) / "requirements.txt"

    for f in [pyproject, requirements]:
        if f.exists():
            content = f.read_text(encoding="utf-8", errors="ignore").lower()
            if "sqlalchemy" in content:
                return "sqlalchemy"
            if "django" in content:
                return "django"

    # Check for Node.js
    package_json = Path(project_dir) / "package.json"
    if package_json.exists():
        content = package_json.read_text(encoding="utf-8", errors="ignore").lower()
        if "prisma" in content:
            return "prisma"
        if "typeorm" in content or "type-orm" in content:
            return "typeorm"

    # Check for schema.prisma
    if (Path(project_dir) / "prisma" / "schema.prisma").exists():
        return "prisma"

    # Check for models.py
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if fname.endswith(".py") and "model" in fname.lower():
                return "sqlalchemy"
            if fname.endswith(".ts") and "model" in fname.lower():
                return "typeorm"
            if fname.endswith(".ts") and "entity" in fname.lower():
                return "typeorm"

    return "unknown"


def extract_sqlalchemy(project_dir: str) -> list:
    """从 SQLAlchemy 项目中提取模型"""
    models = []

    py_files = []
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if fname.endswith(".py"):
                py_files.append(os.path.join(root, fname))

    for filepath in py_files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")
        except Exception:
            continue

        # Find class definitions that inherit from a SQLAlchemy base
        # Pattern: class ClassName(Base) or class ClassName(DeclarativeBase)
        class_pattern = re.compile(
            r'^class\s+(\w+)\s*\(([^)]+)\)\s*:',
            re.MULTILINE,
        )

        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            bases = match.group(2)
            line_no = content[:match.start()].count("\n") + 1

            # Check if it's a SQLAlchemy model (has Column or mapped_column)
            class_body_start = match.end()
            # Find the end of the class (next class at same or lower indentation, or EOF)
            class_body = _extract_class_body(content, class_body_start, lines, line_no)

            # Check for SQLAlchemy indicators
            if not re.search(r'(?:Column|mapped_column|__tablename__|relationship)', class_body):
                continue

            # Extract base classes
            base_list = [b.strip() for b in bases.split(",")]
            is_abstract = any("abstract" in b.lower() for b in base_list)

            # Extract __tablename__
            table_match = re.search(r'__tablename__\s*=\s*["\'](\w+)["\']', class_body)

            # Extract fields
            model_fields = _extract_sqlalchemy_fields(class_body)

            rel_path = os.path.relpath(filepath, project_dir)
            models.append(Model(
                name=class_name,
                file=rel_path,
                line=line_no,
                base_classes=base_list,
                fields=model_fields,
                is_abstract=is_abstract,
            ))

    return models


def _extract_class_body(content: str, start: int, lines: list, class_line: int) -> str:
    """提取类体内容"""
    class_indent = len(lines[class_line - 1]) - len(lines[class_line - 1].lstrip())

    body_lines = []
    for i in range(class_line, len(lines)):
        line = lines[i]
        if not line.strip():
            body_lines.append(line)
            continue
        current_indent = len(line) - len(line.lstrip())
        if current_indent <= class_indent and line.strip() and not line.strip().startswith(("#", '"""', "'''")):
            break
        body_lines.append(line)

    return "\n".join(body_lines)


def _extract_sqlalchemy_fields(class_body: str) -> list:
    """从 SQLAlchemy 模型类体中提取字段"""
    fields = []

    # Pattern 1: Column(Type, ...)  — SQLAlchemy 1.x style
    # Pattern 2: field_name: Mapped[Type] = mapped_column(...)  — SQLAlchemy 2.x style
    # Pattern 3: field_name: str = Column(String, ...)

    # Extract Column definitions
    column_pattern = re.compile(
        r'(?:(\w+)\s*(?::\s*[^\n=]+)?\s*=\s*)?Column\s*\(([^)]+)\)',
        re.DOTALL,
    )
    for match in column_pattern.finditer(class_body):
        field_name = match.group(1) or ""
        column_args = match.group(2)

        # Parse column arguments
        field_type = _parse_column_type(column_args)
        nullable = "nullable=True" in column_args or "nullable = True" in column_args
        if "nullable=False" not in column_args and "nullable = False" not in column_args:
            nullable = True  # Default
        unique = "unique=True" in column_args or "unique = True" in column_args
        primary_key = "primary_key=True" in column_args or "primary_key = True" in column_args

        fields.append(ModelField(
            name=field_name,
            field_type=field_type,
            nullable=nullable,
            unique=unique,
            primary_key=primary_key,
        ))

    # Extract mapped_column definitions (SQLAlchemy 2.x)
    mapped_pattern = re.compile(
        r'(\w+)\s*:\s*Mapped\s*\[([^\]]+)\]\s*=\s*mapped_column\s*\(([^)]*)\)',
    )
    for match in mapped_pattern.finditer(class_body):
        field_name = match.group(1)
        mapped_type = match.group(2).strip()
        column_args = match.group(3)

        nullable = "nullable=False" not in column_args and "nullable = False" not in column_args
        unique = "unique=True" in column_args or "unique = True" in column_args
        primary_key = "primary_key=True" in column_args or "primary_key = True" in column_args

        fields.append(ModelField(
            name=field_name,
            field_type=mapped_type,
            nullable=nullable,
            unique=unique,
            primary_key=primary_key,
        ))

    # Extract relationship definitions
    rel_pattern = re.compile(
        r'(\w+)\s*(?::\s*[^\n=]+)?\s*=\s*relationship\s*\(([^)]+)\)',
    )
    for match in rel_pattern.finditer(class_body):
        field_name = match.group(1)
        rel_args = match.group(2)

        # Extract related model name
        rel_model = ""
        rel_match = re.search(r'["\'](\w+)["\']', rel_args)
        if rel_match:
            rel_model = rel_match.group(1)

        fields.append(ModelField(
            name=field_name,
            field_type=f"relationship → {rel_model}",
            nullable=False,
        ))

    # Extract simple annotated fields without Column (for Mapped[Type] without mapped_column)
    simple_pattern = re.compile(
        r'(\w+)\s*:\s*Mapped\s*\[([^\]]+)\]\s*$',
        re.MULTILINE,
    )
    for match in simple_pattern.finditer(class_body):
        field_name = match.group(1)
        if any(f.name == field_name for f in fields):
            continue
        mapped_type = match.group(2).strip()
        fields.append(ModelField(
            name=field_name,
            field_type=mapped_type,
        ))

    return fields


def _parse_column_type(column_args: str) -> str:
    """从 Column 参数中解析类型"""
    type_match = re.search(r'(String|Integer|Float|Boolean|DateTime|Date|Text|BigInteger|Numeric|JSON|LargeBinary|UUID|Enum|ForeignKey)\s*(?:\([^)]*\))?', column_args)
    if type_match:
        return type_match.group(0)
    # Generic type
    type_match = re.search(r'(\w+)\s*\(', column_args)
    if type_match:
        return type_match.group(1)
    return "unknown"


def extract_django(project_dir: str) -> list:
    """从 Django 项目中提取模型"""
    models = []

    py_files = []
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if fname.endswith(".py") and "model" in Path(root).name.lower():
                py_files.append(os.path.join(root, fname))

    for filepath in py_files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")
        except Exception:
            continue

        class_pattern = re.compile(r'^class\s+(\w+)\s*\(([^)]+)\)\s*:', re.MULTILINE)

        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            bases = match.group(2)
            line_no = content[:match.start()].count("\n") + 1

            if "models.Model" not in bases and "Model" not in bases:
                continue

            class_body = _extract_class_body(content, match.end(), lines, line_no)

            # Extract fields
            model_fields = []
            field_pattern = re.compile(
                r'(\w+)\s*=\s*models\.(\w+(?:Field))\s*\(([^)]*)\)',
            )
            for fm in field_pattern.finditer(class_body):
                field_name = fm.group(1)
                django_type = fm.group(2)
                field_args = fm.group(3)

                nullable = "null=True" in field_args
                unique = "unique=True" in field_args
                primary_key = "primary_key=True" in field_args

                model_fields.append(ModelField(
                    name=field_name,
                    field_type=f"models.{django_type}",
                    nullable=nullable,
                    unique=unique,
                    primary_key=primary_key,
                ))

            rel_path = os.path.relpath(filepath, project_dir)
            models.append(Model(
                name=class_name,
                file=rel_path,
                line=line_no,
                base_classes=[b.strip() for b in bases.split(",")],
                fields=model_fields,
            ))

    return models


def extract_typeorm(project_dir: str) -> list:
    """从 TypeORM 项目中提取模型/实体"""
    models = []

    ts_files = []
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            if fname.endswith(".ts") and not fname.endswith(".d.ts"):
                ts_files.append(os.path.join(root, fname))

    for filepath in ts_files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\n")
        except Exception:
            continue

        # Check for @Entity() decorator
        if not re.search(r'@Entity\s*\(', content):
            continue

        class_pattern = re.compile(r'^export\s+(?:abstract\s+)?class\s+(\w+)', re.MULTILINE)

        for match in class_pattern.finditer(content):
            class_name = match.group(1)
            line_no = content[:match.start()].count("\n") + 1

            class_body = _extract_class_body(content, match.end(), lines, line_no)

            model_fields = []
            # Pattern: @Column() \n fieldName: type;
            col_pattern = re.compile(
                r'@Column\s*\(([^)]*)\)\s*\n\s*(?:(@\w+(?:\([^)]*\))?\s*\n\s*)*)*(?:private\s+|public\s+|readonly\s+)?(\w+)\s*(\?)?:\s*(\w+)',
            )
            for fm in col_pattern.finditer(class_body):
                col_args = fm.group(1)
                field_name = fm.group(3)
                field_type = fm.group(4)
                is_optional = fm.group(2) == "?"

                model_fields.append(ModelField(
                    name=field_name,
                    field_type=field_type,
                    nullable=is_optional,
                    primary_key="@PrimaryGeneratedColumn" in class_body and field_name == "id",
                ))

            rel_path = os.path.relpath(filepath, project_dir)
            models.append(Model(
                name=class_name,
                file=rel_path,
                line=line_no,
                fields=model_fields,
            ))

    return models


def extract_prisma(project_dir: str) -> list:
    """从 Prisma schema 中提取模型"""
    models = []

    schema_path = Path(project_dir) / "prisma" / "schema.prisma"
    if not schema_path.exists():
        # Also check root
        schema_path = Path(project_dir) / "schema.prisma"
    if not schema_path.exists():
        return models

    try:
        content = schema_path.read_text(encoding="utf-8")
    except Exception:
        return models

    # Pattern: model Name { ... }
    model_pattern = re.compile(r'^model\s+(\w+)\s*\{', re.MULTILINE)

    for match in model_pattern.finditer(content):
        model_name = match.group(1)
        model_start = match.end()
        model_end = content.find("}", model_start)
        if model_end == -1:
            continue
        model_body = content[model_start:model_end]
        line_no = content[:match.start()].count("\n") + 1

        model_fields = []
        for field_line in model_body.strip().split("\n"):
            field_line = field_line.strip()
            if not field_line or field_line.startswith("@@") or field_line.startswith("//"):
                continue

            # Pattern: fieldName  Type  @decorators
            field_match = re.match(r'(\w+)\s+(\w+(?:\(\d+(?:,\s*\d+)?\))?)\s*(.*)', field_line)
            if field_match:
                fname = field_match.group(1)
                ftype = field_match.group(2)
                decorators = field_match.group(3)

                is_optional = "?" in fname or "??" in ftype
                if "?" in fname:
                    fname = fname.replace("?", "")

                is_unique = "@unique" in (decorators or "")
                is_id = "@id" in (decorators or "")

                model_fields.append(ModelField(
                    name=fname,
                    field_type=ftype,
                    nullable=is_optional,
                    unique=is_unique,
                    primary_key=is_id,
                ))

        rel_path = os.path.relpath(str(schema_path), project_dir)
        models.append(Model(
            name=model_name,
            file=rel_path,
            line=line_no,
            fields=model_fields,
        ))

    return models


def format_output(models: list, orm: str, project_dir: str) -> str:
    """格式化输出为 Markdown"""
    lines = []
    lines.append("# ORM 模型属性扫描报告")
    lines.append("")
    lines.append(f"- **项目**：`{project_dir}`")
    lines.append(f"- **检测 ORM**：{orm}")
    lines.append(f"- **模型总数**：{len(models)}")
    lines.append(f"- **字段总数**：{sum(len(m.fields) for m in models)}")
    lines.append("")

    if not models:
        lines.append("> 未检测到任何 ORM 模型。")
        return "\n".join(lines)

    for model in models:
        abstract_tag = " *(abstract)*" if model.is_abstract else ""
        lines.append(f"## {model.name}{abstract_tag}")
        lines.append("")
        lines.append(f"- **文件**：`{model.file}:{model.line}`")
        lines.append(f"- **继承**：`{', '.join(model.base_classes)}`")
        lines.append("")

        if not model.fields:
            lines.append("> 无字段定义（可能是抽象基类或 mixin）。")
            lines.append("")
            continue

        lines.append("| 字段名 | 类型 | 可空 | 唯一 | 主键 |")
        lines.append("|--------|------|------|------|------|")
        for f in model.fields:
            pk = "✅" if f.primary_key else ""
            nn = "✅" if not f.nullable else "—"
            uq = "✅" if f.unique else ""
            lines.append(f"| `{f.name}` | `{f.field_type}` | {nn} | {uq} | {pk} |")
        lines.append("")

    # Cross-reference check section
    lines.append("---")
    lines.append("## 跨文件引用校验清单")
    lines.append("")
    lines.append("> 在代码中搜索以下模式的引用，确认属性是否存在：")
    lines.append("")
    lines.append("| 模型 | 属性 | 搜索模式 | 引用文件 | 是否存在 |")
    lines.append("|------|------|---------|---------|---------|")
    for model in models:
        for f in model.fields:
            if f.primary_key:
                continue  # Skip PK, usually always referenced
            search_pattern = f"{model.name}.{f.name}"
            lines.append(f"| `{model.name}` | `{f.name}` | `{search_pattern}` | (待填) | — |")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="扫描 ORM 模型定义，提取所有模型和字段名",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_dir", help="项目根目录")
    parser.add_argument("-o", "--output", help="输出文件路径（默认 stdout）")
    parser.add_argument(
        "--orm",
        choices=["auto", "sqlalchemy", "django", "typeorm", "prisma"],
        default="auto",
        help="指定 ORM（默认自动检测）",
    )
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        print(f"错误：目录不存在 — {project_dir}", file=sys.stderr)
        sys.exit(1)

    # Detect or use specified ORM
    orm = args.orm
    if orm == "auto":
        orm = detect_orm(project_dir)
        if orm == "unknown":
            print("警告：无法自动检测 ORM，默认使用 sqlalchemy 模式", file=sys.stderr)
            orm = "sqlalchemy"

    print(f"检测 ORM：{orm}", file=sys.stderr)

    # Extract models
    extractors = {
        "sqlalchemy": extract_sqlalchemy,
        "django": extract_django,
        "typeorm": extract_typeorm,
        "prisma": extract_prisma,
    }
    extractor = extractors.get(orm, extract_sqlalchemy)
    models = extractor(project_dir)

    print(f"发现 {len(models)} 个模型", file=sys.stderr)

    output = format_output(models, orm, project_dir)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"报告已写入：{args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
