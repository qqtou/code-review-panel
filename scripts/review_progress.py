"""
code-review-panel 进度管理脚本

功能：
1. 创建/读取进度文件
2. 每批次完成后自动更新进度
3. 中断恢复时快速定位断点
4. 生成批次状态摘要

用法：
    python review_progress.py init "D:\work\code\ScanIt"
    python review_progress.py status
    python review_progress.py complete 2
    python review_progress.py fail "批次3失败了"
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


PROGRESS_FILE = ".code_review_progress.json"


def _load_progress() -> dict | None:
    """加载进度文件（不存在返回 None）"""
    if not Path(PROGRESS_FILE).exists():
        return None
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _save_progress(data: dict) -> None:
    """保存进度文件"""
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def cmd_init(project_path: str, project_type: str = "unknown", tech_stack: str = "") -> None:
    """初始化审查进度"""
    if _load_progress():
        print(f"⚠️  进度文件已存在（{PROGRESS_FILE}），请先清理或继续审查")
        return

    data = {
        "project": project_path,
        "project_type": project_type,
        "tech_stack": tech_stack,
        "started_at": _now(),
        "updated_at": _now(),
        "batches": [],
        "total_p0": 0,
        "total_p1": 0,
        "total_p2": 0,
        "report_path": "CODE_REVIEW_REPORT.md",
        "status": "in_progress",
        "notes": [],
    }
    _save_progress(data)
    print(f"✅ 进度文件已创建：{PROGRESS_FILE}")
    print(f"   项目：{project_path}")
    print(f"   类型：{project_type}")


def cmd_add_batch(batch_num: int, unit_name: str, files: list[str]) -> None:
    """添加批次计划"""
    data = _load_progress()
    if not data:
        print("❌ 未找到进度文件，请先运行 init")
        return

    # 检查是否已存在
    existing = next((b for b in data["batches"] if b["batch"] == batch_num), None)
    if existing:
        print(f"⚠️  批次 {batch_num} 已存在，跳过添加")
        return

    data["batches"].append({
        "batch": batch_num,
        "unit": unit_name,
        "files": files,
        "status": "pending",
        "p0_found": 0,
        "p1_found": 0,
        "p2_found": 0,
        "context_patterns": [],
    })
    _save_progress(data)
    print(f"✅ 批次 {batch_num} 已添加：{unit_name}（{len(files)} 个文件）")


def cmd_start(batch_num: int) -> None:
    """标记批次开始"""
    data = _load_progress()
    if not data:
        print("❌ 未找到进度文件")
        return

    batch = next((b for b in data["batches"] if b["batch"] == batch_num), None)
    if not batch:
        print(f"❌ 未找到批次 {batch_num}")
        return

    batch["status"] = "in_progress"
    _save_progress(data)
    print(f"🔄 批次 {batch_num} 已开始：{batch['unit']}")


def cmd_complete(batch_num: int, p0: int = 0, p1: int = 0, p2: int = 0,
                 patterns: list[str] = None) -> None:
    """标记批次完成"""
    data = _load_progress()
    if not data:
        print("❌ 未找到进度文件")
        return

    batch = next((b for b in data["batches"] if b["batch"] == batch_num), None)
    if not batch:
        print(f"❌ 未找到批次 {batch_num}")
        return

    batch["status"] = "completed"
    batch["p0_found"] = p0
    batch["p1_found"] = p1
    batch["p2_found"] = p2
    batch["context_patterns"] = patterns or []
    batch["completed_at"] = _now()
    batch.pop("files_read", None)
    batch.pop("files_remaining", None)

    # 更新总计
    data["total_p0"] += p0
    data["total_p1"] += p1
    data["total_p2"] += p2

    _save_progress(data)
    print(f"✅ 批次 {batch_num} 已完成：发现 P0={p0}, P1={p1}, P2={p2}")
    if patterns:
        print(f"   新增模式：{patterns}")


def cmd_fail(batch_num: int, reason: str = "") -> None:
    """标记批次失败/中断"""
    data = _load_progress()
    if not data:
        print("❌ 未找到进度文件")
        return

    batch = next((b for b in data["batches"] if b["batch"] == batch_num), None)
    if batch:
        batch["status"] = "failed"
        batch["fail_reason"] = reason
        batch["failed_at"] = _now()

    data["notes"].append({
        "time": _now(),
        "batch": batch_num,
        "type": "fail",
        "reason": reason,
    })
    _save_progress(data)
    print(f"⚠️  批次 {batch_num} 标记为失败：{reason}")


def cmd_note(message: str) -> None:
    """添加备注"""
    data = _load_progress()
    if not data:
        print("❌ 未找到进度文件")
        return

    data["notes"].append({"time": _now(), "type": "note", "message": message})
    _save_progress(data)
    print(f"📝 备注已添加：{message}")


def cmd_status() -> None:
    """显示进度状态"""
    data = _load_progress()
    if not data:
        print("❌ 未找到进度文件")
        return

    print(f"\n{'='*60}")
    print(f"  Code Review Progress: {data['project']}")
    print(f"{'='*60}")
    print(f"  状态：{data['status']}")
    print(f"  开始：{data['started_at']}")
    print(f"  更新：{data['updated_at']}")
    print(f"  类型：{data['project_type']}")
    print(f"  栈：{data['tech_stack']}")
    print(f"  问题汇总：P0={data['total_p0']}, P1={data['total_p1']}, P2={data['total_p2']}")
    print(f"\n  批次进度：")
    for b in data["batches"]:
        status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "failed": "❌"}.get(b["status"], "?")
        context = f" | 模式: {', '.join(b['context_patterns'][:2])}" if b.get("context_patterns") else ""
        print(f"    {status_icon} 批次{b['batch']} | {b['unit']:<15} | P0={b['p0_found']} P1={b['p1_found']} P2={b['p2_found']}{context}")

    if data.get("notes"):
        print(f"\n  备注（{len(data['notes'])}条）：")
        for n in data["notes"][-3:]:
            print(f"    - [{n['time']}] {n.get('message', n.get('reason', ''))}")

    print(f"\n{'='*60}")

    # 计算下一个待处理批次
    pending = [b for b in data["batches"] if b["status"] in ("pending", "in_progress")]
    if pending:
        next_batch = pending[0]["batch"]
        print(f"  ➡️  下一步：批次 {next_batch}（{pending[0]['unit']}）")
        if pending[0]["status"] == "in_progress":
            remaining = pending[0].get("files_remaining", [])
            if remaining:
                print(f"         剩余文件：{', '.join(remaining[:3])}...")
    else:
        print(f"  ✅ 所有批次已完成！")

    print()


def cmd_reset() -> None:
    """重置进度（删除进度文件）"""
    if Path(PROGRESS_FILE).exists():
        Path(PROGRESS_FILE).unlink()
        print(f"✅ 进度文件已重置")
    else:
        print(f"⚠️  进度文件不存在")


# ── CLI 入口 ──────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：")
        print("  python review_progress.py init <项目路径> [项目类型] [技术栈]")
        print("  python review_progress.py add <批次号> <单元名> <文件1,文件2,...>")
        print("  python review_progress.py start <批次号>")
        print("  python review_progress.py complete <批次号> [-p0 N] [-p1 N] [-p2 N] [-patterns x,y,z]")
        print("  python review_progress.py fail <批次号> [原因]")
        print("  python review_progress.py note <消息>")
        print("  python review_progress.py status")
        print("  python review_progress.py reset")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        path = sys.argv[2] if len(sys.argv) > 2 else "."
        ptype = sys.argv[3] if len(sys.argv) > 3 else "unknown"
        stack = sys.argv[4] if len(sys.argv) > 4 else ""
        cmd_init(path, ptype, stack)

    elif cmd == "add":
        batch = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        unit = sys.argv[3] if len(sys.argv) > 3 else ""
        files = sys.argv[4].split(",") if len(sys.argv) > 4 else []
        cmd_add_batch(batch, unit, files)

    elif cmd == "start":
        cmd_start(int(sys.argv[2]))

    elif cmd == "complete":
        batch = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        p0 = p1 = p2 = 0
        patterns = []
        for arg in sys.argv[3:]:
            if arg.startswith("-p0"):
                p0 = int(arg[4:])
            elif arg.startswith("-p1"):
                p1 = int(arg[4:])
            elif arg.startswith("-p2"):
                p2 = int(arg[4:])
            elif arg.startswith("-patterns"):
                patterns = arg[10:].split(",")
        cmd_complete(batch, p0, p1, p2, patterns)

    elif cmd == "fail":
        batch = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        reason = sys.argv[3] if len(sys.argv) > 3 else ""
        cmd_fail(batch, reason)

    elif cmd == "note":
        cmd_note(sys.argv[2] if len(sys.argv) > 2 else "")

    elif cmd == "status":
        cmd_status()

    elif cmd == "reset":
        cmd_reset()

    else:
        print(f"❌ 未知命令：{cmd}")
        sys.exit(1)