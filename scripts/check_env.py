"""聚合环境就绪检查：一条命令确认本机能否跑完整流水线。

检查项与 INSTALL.md 的三条手工命令一致，并给出各环节的降级路径：
- Python ≥ 3.11（硬性要求，缺失时退出码为 1）；
- 系统 Swift/PDFKit（文字型 PDF 解析；缺失时 extract_resume.py 返回 NEEDS_TEXT_FALLBACK）；
- Chrome（命令行导出 PNG；缺失时用 build_report.py --no-png，HTML 内仍可手动导出分享卡）。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.export_png import find_chrome

MIN_PYTHON = (3, 11)
SWIFT_BINARY = "/usr/bin/swift"


def check_python() -> tuple[bool, str]:
    version = sys.version_info
    detail = f"Python {version.major}.{version.minor}.{version.micro}（要求 ≥ {MIN_PYTHON[0]}.{MIN_PYTHON[1]}）"
    if version >= MIN_PYTHON:
        return True, detail
    return False, detail + "；请升级到 Python 3.11+ 后再运行流水线"


def check_swift() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [SWIFT_BINARY, "--version"], capture_output=True, text=True, timeout=60
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, "swift 不可用；文字型 PDF 解析降级：extract_resume.py 返回 NEEDS_TEXT_FALLBACK，请让用户提供可复制文字版"
    output = (result.stdout or result.stderr).strip()
    first_line = output.splitlines()[0] if output else "swift（无版本输出）"
    if result.returncode == 0:
        return True, first_line
    return False, first_line + "；文字型 PDF 解析降级：extract_resume.py 返回 NEEDS_TEXT_FALLBACK"


def check_chrome() -> tuple[bool, str]:
    chrome = find_chrome()
    if chrome is None:
        return False, "未找到 Chrome；命令行不生成 PNG：请用 build_report.py --no-png 生成 HTML，并让用户在页面内手动导出分享卡"
    return True, f"{chrome.name} 就绪（可用环境变量 AI_EXPOSURE_CHROME_PATH 覆盖探测路径）"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    args = parser.parse_args()

    checks = [
        ("python", check_python),
        ("swift-pdfkit", check_swift),
        ("chrome", check_chrome),
    ]
    results = {name: check() for name, check in checks}
    python_ok = results["python"][0]

    if args.json:
        import json

        print(
            json.dumps(
                {
                    "status": "ok" if python_ok else "blocked",
                    "checks": {
                        name: {"ok": ok, "detail": detail} for name, (ok, detail) in results.items()
                    },
                },
                ensure_ascii=False,
            )
        )
    else:
        print("环境就绪检查：")
        for name, (ok, detail) in results.items():
            print(f"- [{'通过' if ok else '降级'}] {name}: {detail}")
        if not python_ok:
            print("结论：Python 未达标，流水线不可运行。")
        else:
            degraded = [name for name, (ok, _) in results.items() if not ok]
            if degraded:
                print(f"结论：可运行；{'、'.join(degraded)} 环节按上述提示降级。")
            else:
                print("结论：全部就绪。")

    return 0 if python_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
