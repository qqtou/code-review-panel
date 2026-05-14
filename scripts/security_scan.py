#!/usr/bin/env python3
"""
security_scan.py — 扫描项目中的常见安全问题。

检测项：
  - 弱密钥/弱密码模式
  - 硬编码密钥/Token
  - 调试模式开关
  - CORS 过宽配置
  - AWS Access Key 泄露
  - 私钥文件泄露
  - .env 文件版本控制
  - 敏感信息在日志中输出

用法：
    python security_scan.py <项目目录> [-o report.md] [--severity P0|P1|P2|all]
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Finding:
    severity: str
    category: str
    title: str
    description: str
    file: str
    line: int
    snippet: str
    remediation: str


# Weak key/password patterns
WEAK_PATTERNS = [
    "change-me", "change_me", "changeme",
    "default-secret", "default_password", "defaultpassword",
    "example-key", "example_key", "example_secret",
    "secret-key", "secret_key",
    "test-secret", "test_secret", "test_key",
    "dev-secret", "dev_secret",
    "demo-secret", "demo_secret",
    "password123", "admin123", "123456",
    "please-change", "please_change",
    "placeholder", "replace-me", "replace_me",
    "your-secret", "your_secret", "your-api-key",
]

# Patterns for hardcoded secrets
SECRET_PATTERNS = [
    (r'(?i)(?:password|passwd|pwd)\s*[:=]\s*["\']([^"\']{3,})["\']', "硬编码密码"),
    (r'(?i)(?:secret[_-]?key|api[_-]?key|access[_-]?key|private[_-]?key)\s*[:=]\s*["\']([^"\']{8,})["\']', "硬编码密钥/Key"),
    (r'(?i)(?:jwt[_-]?secret|token[_-]?secret)\s*[:=]\s*["\']([^"\']{8,})["\']', "硬编码 JWT 密钥"),
    (r'(?i)database[_-]?url\s*[:=]\s*["\']([^"\']+)["\']', "硬编码数据库 URL"),
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key 泄露"),
    (r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----', "私钥文件内容泄露"),
]

# Debug mode patterns
DEBUG_PATTERNS = [
    (r'(?i)DEBUG\s*[:=]\s*True', "调试模式启用 (DEBUG=True)"),
    (r'(?i)debug\s*[:=]\s*true', "调试模式启用 (debug=true)"),
    (r'(?i)app\.debug\s*=\s*True', "Flask 调试模式"),
    (r'(?i)DEBUG\s*=\s*[\'"]1[\'"]', "调试模式启用 (DEBUG='1')"),
    (r'(?i)(?:LOG_LEVEL|log[_-]?level)\s*[:=]\s*["\']DEBUG["\']', "日志级别设为 DEBUG"),
]

# CORS patterns
CORS_PATTERNS = [
    (r'(?i)allow_origins?\s*[:=]\s*\[?\s*["\']?\*["\']?\s*\]?', "CORS 允许所有来源 (*)"),
    (r'(?i)Access-Control-Allow-Origin.*\*', "CORS 响应头允许所有来源"),
    (r'(?i)cors[_-]?origins?\s*[:=]\s*\[.*localhost', "CORS 包含 localhost"),
]


SKIP_DIRS = {
    "node_modules", "__pycache__", ".git", "dist", "build",
    "vendor", ".venv", "venv", ".idea", ".vscode",
    ".next", ".nuxt", "coverage", ".mypy_cache",
    "migrations", "alembic", ".tox", ".pytest_cache",
}


def is_ignored_file(filepath: str) -> bool:
    """判断文件是否应跳过"""
    parts = Path(filepath).parts
    for part in parts:
        if part in SKIP_DIRS:
            return True
    # Skip binary files
    ext = Path(filepath).suffix.lower()
    binary_exts = {".pyc", ".pyo", ".so", ".dll", ".exe", ".bin", ".png", ".jpg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".eot"}
    if ext in binary_exts:
        return True
    # Skip lock files
    name = Path(filepath).name
    if name in {"package-lock.json", "poetry.lock", "yarn.lock", "Pipfile.lock"}:
        return True
    return False


def scan_weak_keys(project_dir: str) -> list:
    """扫描弱密钥模式"""
    findings = []
    text_extensions = {".py", ".js", ".ts", ".env", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".json", ".properties", ".xml"}

    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            filepath = os.path.join(root, fname)
            if is_ignored_file(filepath):
                continue
            if Path(filepath).suffix.lower() not in text_extensions and fname != ".env":
                continue
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
            except Exception:
                continue

            for line_no, line in enumerate(lines, 1):
                stripped = line.strip()
                # Skip comments
                if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
                    continue
                for pattern in WEAK_PATTERNS:
                    if pattern.lower() in stripped.lower():
                        # Check if it's in a string value (not just a variable name)
                        if re.search(r'["\'][^"\']*' + re.escape(pattern) + r'[^"\']*["\']', stripped, re.IGNORECASE):
                            findings.append(Finding(
                                severity="P0",
                                category="弱密钥",
                                title="弱密钥模式",
                                description=f"密钥/密码包含可推测模式「{pattern}」",
                                file=os.path.relpath(filepath, project_dir),
                                line=line_no,
                                snippet=stripped[:120],
                                remediation="使用 cryptographically secure 随机密钥替换（如 openssl rand -hex 32）",
                            ))
    return findings


def scan_hardcoded_secrets(project_dir: str) -> list:
    """扫描硬编码密钥"""
    findings = []

    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            filepath = os.path.join(root, fname)
            if is_ignored_file(filepath):
                continue
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
            except Exception:
                continue

            for line_no, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("//"):
                    continue
                for pattern, category in SECRET_PATTERNS:
                    match = re.search(pattern, stripped)
                    if match:
                        # Don't flag placeholder values
                        value = match.group(1) if match.lastindex else match.group(0)
                        if any(p in value.lower() for p in ["<", ">", "{", "}", "your-", "xxx", "..."]):
                            continue
                        # Don't flag .env.example or template files
                        if "example" in Path(filepath).name.lower() or "template" in Path(filepath).name.lower():
                            continue
                        severity = "P0" if category in ("AWS Access Key 泄露", "私钥文件内容泄露") else "P1"
                        # Mask sensitive values in snippet
                        masked = stripped
                        if len(value) > 8:
                            masked = masked[:masked.index(value)] + value[:4] + "***" + value[-4:] + masked[masked.index(value) + len(value):]
                        findings.append(Finding(
                            severity=severity,
                            category="硬编码密钥",
                            title=category,
                            description=f"检测到{category}",
                            file=os.path.relpath(filepath, project_dir),
                            line=line_no,
                            snippet=masked[:120],
                            remediation="移至环境变量或密钥管理服务（如 Vault、AWS Secrets Manager）",
                        ))
    return findings


def scan_debug_mode(project_dir: str) -> list:
    """扫描调试模式"""
    findings = []

    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            filepath = os.path.join(root, fname)
            if is_ignored_file(filepath):
                continue
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
            except Exception:
                continue

            for line_no, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("//"):
                    continue
                for pattern, description in DEBUG_PATTERNS:
                    if re.search(pattern, stripped):
                        # Check if this is .env.example or development config
                        parent = Path(filepath).parent.name.lower()
                        if "example" in parent or "template" in parent or "dev" in parent:
                            continue
                        findings.append(Finding(
                            severity="P0",
                            category="调试模式",
                            title=description,
                            description="调试模式在生产代码中启用，可能导致敏感信息泄露",
                            file=os.path.relpath(filepath, project_dir),
                            line=line_no,
                            snippet=stripped[:120],
                            remediation="使用环境变量控制，生产环境必须设为 False/关闭",
                        ))
    return findings


def scan_cors(project_dir: str) -> list:
    """扫描 CORS 配置"""
    findings = []

    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            filepath = os.path.join(root, fname)
            if is_ignored_file(filepath):
                continue
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
            except Exception:
                continue

            for line_no, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("//"):
                    continue
                for pattern, description in CORS_PATTERNS:
                    if re.search(pattern, stripped):
                        findings.append(Finding(
                            severity="P1",
                            category="CORS 配置",
                            title=description,
                            description="CORS 配置过宽，允许任意来源访问",
                            file=os.path.relpath(filepath, project_dir),
                            line=line_no,
                            snippet=stripped[:120],
                            remediation="配置具体的允许域名列表，生产环境移除 localhost 和通配符",
                        ))
    return findings


def check_gitignore(project_dir: str) -> list:
    """检查 .gitignore 是否正确忽略敏感文件"""
    findings = []

    gitignore_path = os.path.join(project_dir, ".gitignore")
    if not os.path.exists(gitignore_path):
        findings.append(Finding(
            severity="P0",
            category=".gitignore",
            title="缺少 .gitignore 文件",
            description="项目根目录没有 .gitignore 文件，敏感文件可能被提交",
            file="(project root)",
            line=0,
            snippet="",
            remediation="创建 .gitignore 并包含 .env、*.key、credentials 等条目",
        ))
        return findings

    with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
        gitignore_content = f.read().lower()

    # Check if .env is ignored
    if ".env" not in gitignore_content:
        findings.append(Finding(
            severity="P0",
            category=".gitignore",
            title=".env 未在 .gitignore 中",
            description="环境变量文件可能被提交到版本控制",
            file=".gitignore",
            line=0,
            snippet="",
            remediation="在 .gitignore 中添加 .env",
        ))

    # Check if .env is already tracked
    git_dir = os.path.join(project_dir, ".git")
    if os.path.isdir(git_dir):
        env_path = os.path.join(project_dir, ".env")
        if os.path.exists(env_path):
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "-C", project_dir, "ls-files", ".env"],
                    capture_output=True, text=True, timeout=5,
                )
                if result.stdout.strip():
                    findings.append(Finding(
                        severity="P0",
                        category="敏感信息泄露",
                        title=".env 文件已被 Git 跟踪",
                        description=".env 文件已提交到版本控制，密钥/密码已泄露",
                        file=".env",
                        line=0,
                        snippet="(已跟踪的文件)",
                        remediation="立即轮换所有密钥，并使用 git rm --cached .env 移除跟踪",
                    ))
            except Exception:
                pass

    # Check for key files
    sensitive_patterns = [".key", ".pem", ".p12", ".pfx", "credentials", "id_rsa", "id_dsa"]
    for pattern in sensitive_patterns:
        if pattern not in gitignore_content:
            # Only warn if such files exist
            for root, dirs, files in os.walk(project_dir):
                dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
                for fname in files:
                    if pattern in fname.lower():
                        findings.append(Finding(
                            severity="P0",
                            category=".gitignore",
                            title=f"敏感文件类型 *{pattern} 未在 .gitignore 中",
                            description=f"发现文件 {fname}，但 .gitignore 未排除 *{pattern} 类文件",
                            file=os.path.relpath(os.path.join(root, fname), project_dir),
                            line=0,
                            snippet="",
                            remediation=f"在 .gitignore 中添加 *{pattern}",
                        ))
                        break

    return findings


def scan_sensitive_logging(project_dir: str) -> list:
    """扫描日志中的敏感信息输出"""
    findings = []
    log_patterns = [
        (r'(?i)(?:logger|console|logging)\.\w+\s*\(\s*f?["\'].*(?:password|token|secret|api[_-]?key|credit[_-]?card|ssn)\s*[:=]\s*\{', "日志中可能输出敏感字段"),
        (r'(?i)print\s*\(\s*f?["\'].*(?:password|token|secret)\s*[:=]\s*\{', "print 语句中可能输出敏感字段"),
    ]

    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fname in files:
            filepath = os.path.join(root, fname)
            if not fname.endswith((".py", ".js", ".ts")):
                continue
            if is_ignored_file(filepath):
                continue
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
            except Exception:
                continue

            for line_no, line in enumerate(lines, 1):
                stripped = line.strip()
                for pattern, description in log_patterns:
                    if re.search(pattern, stripped):
                        findings.append(Finding(
                            severity="P1",
                            category="敏感信息泄露",
                            title=description,
                            description="日志/print 语句中直接输出敏感字段，可能泄露到日志系统",
                            file=os.path.relpath(filepath, project_dir),
                            line=line_no,
                            snippet=stripped[:120],
                            remediation="对敏感字段做脱敏处理（如掩码、hash）后再输出日志",
                        ))
    return findings


def format_output(findings: list, project_dir: str) -> str:
    """格式化输出为 Markdown"""
    lines = []
    lines.append("# 安全扫描报告")
    lines.append("")
    lines.append(f"- **项目**：`{project_dir}`")
    lines.append(f"- **问题总数**：{len(findings)}")
    lines.append(f"  - P0（必须修复）：{sum(1 for f in findings if f.severity == 'P0')}")
    lines.append(f"  - P1（强烈建议）：{sum(1 for f in findings if f.severity == 'P1')}")
    lines.append(f"  - P2（可选优化）：{sum(1 for f in findings if f.severity == 'P2')}")
    lines.append("")

    if not findings:
        lines.append("✅ 未检测到安全问题。")
        return "\n".join(lines)

    # Group by severity
    for severity in ["P0", "P1", "P2"]:
        items = [f for f in findings if f.severity == severity]
        if not items:
            continue

        label = {"P0": "P0 — 必须修复", "P1": "P1 — 强烈建议", "P2": "P2 — 可选优化"}[severity]
        lines.append(f"## {label}")
        lines.append("")

        # Group by category
        categories = {}
        for f in items:
            categories.setdefault(f.category, []).append(f)

        for category, cat_items in categories.items():
            lines.append(f"### {category}")
            lines.append("")
            for f in cat_items:
                lines.append(f"**{f.title}**")
                lines.append(f"- 文件：`{f.file}:{f.line}`")
                lines.append(f"- 描述：{f.description}")
                if f.snippet:
                    lines.append(f"- 代码：`{f.snippet}`")
                lines.append(f"- 修复：{f.remediation}")
                lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="扫描项目中的常见安全问题",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("project_dir", help="项目根目录")
    parser.add_argument("-o", "--output", help="输出文件路径（默认 stdout）")
    parser.add_argument(
        "--severity",
        choices=["P0", "P1", "P2", "all"],
        default="all",
        help="只输出指定级别及以上的问题（默认 all）",
    )
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        print(f"错误：目录不存在 — {project_dir}", file=sys.stderr)
        sys.exit(1)

    # Run all scans
    all_findings = []
    scanners = [
        ("弱密钥扫描", scan_weak_keys),
        ("硬编码密钥", scan_hardcoded_secrets),
        ("调试模式", scan_debug_mode),
        ("CORS 配置", scan_cors),
        (".gitignore 检查", check_gitignore),
        ("敏感日志", scan_sensitive_logging),
    ]

    for name, scanner in scanners:
        print(f"扫描：{name}...", file=sys.stderr)
        try:
            results = scanner(project_dir)
            all_findings.extend(results)
            print(f"  → 发现 {len(results)} 个问题", file=sys.stderr)
        except Exception as e:
            print(f"  → 扫描失败：{e}", file=sys.stderr)

    # Filter by severity
    severity_order = {"P0": 0, "P1": 1, "P2": 2}
    min_severity = severity_order.get(args.severity, 2)
    filtered = [f for f in all_findings if severity_order.get(f.severity, 2) <= min_severity]

    # Sort: P0 first, then P1, then P2
    filtered.sort(key=lambda f: (severity_order.get(f.severity, 9), f.file, f.line))

    # Deduplicate (same file + same line + same category)
    seen = set()
    deduped = []
    for f in filtered:
        key = (f.file, f.line, f.category, f.title)
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    print(f"\n共发现 {len(deduped)} 个安全问题（去重后）", file=sys.stderr)

    output = format_output(deduped, project_dir)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"报告已写入：{args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
