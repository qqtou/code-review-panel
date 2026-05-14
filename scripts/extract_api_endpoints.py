#!/usr/bin/env python3
"""
extract_api_endpoints.py — 扫描后端代码，提取所有 API 端点。

支持框架：FastAPI、Flask、Express、NestJS
输出：Markdown 表格

用法：
    python extract_api_endpoints.py <项目目录> [-o output.md] [--framework auto|fastapi|flask|express|nestjs]
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Endpoint:
    method: str
    path: str
    function_name: str
    file: str
    line: int
    decorators: list = field(default_factory=list)
    tags: list = field(default_factory=list)


def detect_framework(project_dir: str) -> str:
    """根据项目文件自动检测框架"""
    # Check for Python frameworks
    if (Path(project_dir) / "requirements.txt").exists():
        with open(Path(project_dir) / "requirements.txt", "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().lower()
            if "fastapi" in content:
                return "fastapi"
            if "flask" in content:
                return "flask"

    # Check for pyproject.toml
    pyproject = Path(project_dir) / "pyproject.toml"
    if pyproject.exists():
        with open(pyproject, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().lower()
            if "fastapi" in content:
                return "fastapi"
            if "flask" in content:
                return "flask"

    # Check for Node.js frameworks
    package_json = Path(project_dir) / "package.json"
    if package_json.exists():
        with open(package_json, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().lower()
            if "@nestjs" in content or "nestjs" in content:
                return "nestjs"
            if "express" in content:
                return "express"

    # Check for common file patterns
    for root, dirs, files in os.walk(project_dir):
        # Skip common non-source dirs
        dirs[:] = [d for d in dirs if d not in {
            "node_modules", "__pycache__", ".git", "dist", "build",
            "vendor", ".venv", "venv", ".idea", ".vscode",
        }]
        for fname in files:
            if fname.endswith(".py"):
                return "fastapi"  # Default for Python
            if fname.endswith(".ts") or fname.endswith(".js"):
                return "express"  # Default for JS/TS

    return "unknown"


def extract_fastapi(project_dir: str) -> list:
    """从 FastAPI 项目中提取端点"""
    endpoints = []

    # FastAPI patterns
    # Pattern 1: @router.get/post/put/delete/patch("/path")
    http_methods = ["get", "post", "put", "delete", "patch", "options", "head"]
    decorator_pattern = re.compile(
        r'@(?:(?:router|app|api_router)\.)?('
        + '|'.join(http_methods)
        + r')\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*[^)]*)?\)'
    )

    # Also match: @app.route("/path", methods=["GET"])
    route_pattern = re.compile(
        r'@(?:(?:router|app|api_router)\.)?route\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*methods\s*=\s*\[([^\]]*)\])?'
    )

    py_files = []
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in {
            "node_modules", "__pycache__", ".git", "dist", "build",
            "vendor", ".venv", "venv", ".idea", ".vscode", "migrations",
            "alembic", "tests", "test",
        }]
        for fname in files:
            if fname.endswith(".py"):
                py_files.append(os.path.join(root, fname))

    for filepath in py_files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            continue

        for line_no, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # Check decorator pattern
            match = decorator_pattern.search(line_stripped)
            if match:
                method = match.group(1).upper()
                path = match.group(2)
                # Find the function name on the next non-empty, non-decorator line
                func_name = _find_next_function(lines, line_no)
                rel_path = os.path.relpath(filepath, project_dir)
                endpoints.append(Endpoint(
                    method=method,
                    path=path,
                    function_name=func_name,
                    file=rel_path,
                    line=line_no,
                ))
                continue

            # Check route pattern
            match = route_pattern.search(line_stripped)
            if match:
                path = match.group(1)
                methods_str = match.group(2)
                if methods_str:
                    methods = re.findall(r'["\'](\w+)["\']', methods_str)
                else:
                    methods = ["GET"]
                rel_path = os.path.relpath(filepath, project_dir)
                func_name = _find_next_function(lines, line_no)
                for m in methods:
                    endpoints.append(Endpoint(
                        method=m.upper(),
                        path=path,
                        function_name=func_name,
                        file=rel_path,
                        line=line_no,
                    ))

    return endpoints


def _find_next_function(lines: list, from_line: int) -> str:
    """在装饰器之后找到下一个函数定义"""
    for i in range(from_line, min(from_line + 10, len(lines))):
        line = lines[i].strip()
        match = re.match(r'(?:async\s+)?def\s+(\w+)\s*\(', line)
        if match:
            return match.group(1)
    return "(unknown)"


def extract_flask(project_dir: str) -> list:
    """从 Flask 项目中提取端点 — 复用 FastAPI 逻辑（语法兼容）"""
    return extract_fastapi(project_dir)


def extract_express(project_dir: str) -> list:
    """从 Express 项目中提取端点"""
    endpoints = []

    http_methods = ["get", "post", "put", "delete", "patch", "options", "all"]
    # Pattern: router.get("/path", ...) or app.get("/path", ...)
    pattern = re.compile(
        r'(?:router|app|api)\.'
        + '(' + '|'.join(http_methods) + ')'
        + r'\s*\(\s*["\']([^"\']+)["\']\s*(?:,\s*(.*?))?(?:\)|,)\s*$'
    )

    js_ts_files = []
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in {
            "node_modules", "__pycache__", ".git", "dist", "build",
            "vendor", ".venv", "venv", ".idea", ".vscode",
        }]
        for fname in files:
            if fname.endswith((".ts", ".js")) and not fname.endswith(".d.ts"):
                js_ts_files.append(os.path.join(root, fname))

    for filepath in js_ts_files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            continue

        for line_no, line in enumerate(lines, 1):
            match = pattern.search(line.strip())
            if match:
                method = match.group(1).upper()
                path = match.group(2)
                handler = match.group(3).strip().split(",")[0].strip() if match.group(3) else "(anonymous)"
                # Clean up handler name
                handler = re.sub(r'.*\.', '', handler)  # Remove module prefix
                handler = re.sub(r'[;)\s].*$', '', handler)  # Remove trailing chars
                rel_path = os.path.relpath(filepath, project_dir)
                endpoints.append(Endpoint(
                    method=method,
                    path=path,
                    function_name=handler or "(anonymous)",
                    file=rel_path,
                    line=line_no,
                ))

    return endpoints


def extract_nestjs(project_dir: str) -> list:
    """从 NestJS 项目中提取端点"""
    endpoints = []

    # NestJS decorators: @Get("/path"), @Post("/path"), etc.
    http_methods = ["Get", "Post", "Put", "Delete", "Patch", "Options"]
    pattern = re.compile(
        r'@(' + '|'.join(http_methods) + r')\s*\(\s*["\']([^"\']+)["\']\s*\)'
    )

    ts_files = []
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in {
            "node_modules", "__pycache__", ".git", "dist", "build",
            "vendor", ".venv", "venv", ".idea", ".vscode",
        }]
        for fname in files:
            if fname.endswith(".ts") and not fname.endswith(".d.ts"):
                ts_files.append(os.path.join(root, fname))

    for filepath in ts_files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            continue

        for line_no, line in enumerate(lines, 1):
            match = pattern.search(line.strip())
            if match:
                method = match.group(1).upper()
                path = match.group(2)
                # Find controller class method
                func_name = _find_next_ts_method(lines, line_no)
                rel_path = os.path.relpath(filepath, project_dir)
                endpoints.append(Endpoint(
                    method=method,
                    path=path,
                    function_name=func_name,
                    file=rel_path,
                    line=line_no,
                ))

    return endpoints


def _find_next_ts_method(lines: list, from_line: int) -> str:
    """在 TypeScript 装饰器之后找到下一个方法定义"""
    for i in range(from_line, min(from_line + 10, len(lines))):
        line = lines[i].strip()
        match = re.match(r'(?:async\s+)?(\w+)\s*\(', line)
        if match:
            return match.group(1)
    return "(unknown)"


def format_output(endpoints: list, framework: str, project_dir: str) -> str:
    """格式化输出为 Markdown"""
    lines = []
    lines.append(f"# API 端点扫描报告")
    lines.append(f"")
    lines.append(f"- **项目**：`{project_dir}`")
    lines.append(f"- **检测框架**：{framework}")
    lines.append(f"- **端点总数**：{len(endpoints)}")
    lines.append(f"")

    if not endpoints:
        lines.append("> 未检测到任何 API 端点。")
        return "\n".join(lines)

    # Group by method
    method_order = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "ALL", "OTHER"]
    grouped = {}
    for ep in endpoints:
        m = ep.method if ep.method in method_order else "OTHER"
        grouped.setdefault(m, []).append(ep)

    for method in method_order:
        eps = grouped.get(method, [])
        if not eps:
            continue
        lines.append(f"## {method}")
        lines.append("")
        lines.append(f"| 路径 | 函数 | 文件 | 行号 |")
        lines.append(f"|------|------|------|------|")
        for ep in sorted(eps, key=lambda x: x.path):
            lines.append(f"| `{ep.path}` | `{ep.function_name}` | `{ep.file}` | {ep.line} |")
        lines.append("")

    # Dedup summary
    paths = [ep.path for ep in endpoints]
    duplicates = [p for p in set(paths) if paths.count(p) > 1]
    if duplicates:
        lines.append("## ⚠️ 重复路径")
        lines.append("")
        for p in sorted(duplicates):
            matching = [ep for ep in endpoints if ep.path == p]
            lines.append(f"- `{p}` 出现 {len(matching)} 次：")
            for ep in matching:
                lines.append(f"  - [{ep.method}] `{ep.file}:{ep.line}` `{ep.function_name}`")
            lines.append("")

    # Quick reference for frontend contract check
    lines.append("## 前端契约检查清单")
    lines.append("")
    lines.append("| 前端调用路径 | 后端是否存在 | 备注 |")
    lines.append("|------------|-------------|------|")
    lines.append("| (待填入前端端点) | — | — |")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="扫描后端代码，提取所有 API 端点",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
    python extract_api_endpoints.py ./my-project -o endpoints.md
    python extract_api_endpoints.py ./my-project --framework fastapi
        """,
    )
    parser.add_argument("project_dir", help="项目根目录")
    parser.add_argument("-o", "--output", help="输出文件路径（默认 stdout）")
    parser.add_argument(
        "--framework",
        choices=["auto", "fastapi", "flask", "express", "nestjs"],
        default="auto",
        help="指定框架（默认自动检测）",
    )
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        print(f"错误：目录不存在 — {project_dir}", file=sys.stderr)
        sys.exit(1)

    # Detect or use specified framework
    framework = args.framework
    if framework == "auto":
        framework = detect_framework(project_dir)
        if framework == "unknown":
            print("警告：无法自动检测框架，默认使用 fastapi 模式扫描", file=sys.stderr)
            framework = "fastapi"

    print(f"检测框架：{framework}", file=sys.stderr)

    # Extract endpoints
    extractors = {
        "fastapi": extract_fastapi,
        "flask": extract_flask,
        "express": extract_express,
        "nestjs": extract_nestjs,
    }
    extractor = extractors.get(framework, extract_fastapi)
    endpoints = extractor(project_dir)

    print(f"发现 {len(endpoints)} 个端点", file=sys.stderr)

    # Format and output
    output = format_output(endpoints, framework, project_dir)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"报告已写入：{args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
