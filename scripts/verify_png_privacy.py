"""OCR a PNG with macOS Vision and apply the same fail-closed privacy gate."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.export_png import png_dimensions, png_text_chunks
from scripts.privacy import PrivacyLeakError, find_privacy_leaks


ROOT = Path(__file__).resolve().parents[1]
OCR_SCRIPT = ROOT / "scripts" / "ocr_image.swift"
DEFAULT_OCR_HELPER = ROOT / "build" / "ocr-image"


class OcrVerificationError(ValueError):
    """Raised when OCR did not recover enough card content to be a valid privacy check."""


def find_ocr_privacy_leaks(text: str, privacy_entities: list[str]) -> list[str]:
    return find_privacy_leaks({"ocr_text": text}, privacy_entities)


def assert_ocr_meaningful(text: str, share_card: dict) -> None:
    normalized = re.sub(r"\s+", "", text).casefold()
    role = re.sub(r"\s+", "", str(share_card.get("role_name", ""))).casefold()
    marker = "工作任务ai替代指数"
    if len(normalized) < 10 or (role not in normalized and marker not in normalized):
        raise OcrVerificationError("PNG OCR 未识别出角色或指标标题，拒绝将空扫描视为隐私通过")


def build_ocr_helper(output_path: str | Path = DEFAULT_OCR_HELPER) -> Path:
    if sys.platform != "darwin":
        raise RuntimeError("OCR helper 当前需要 macOS Vision")
    compiler = shutil.which("swiftc")
    if not compiler:
        raise RuntimeError("未找到 swiftc")
    output = Path(output_path)
    if output.is_file() and output.stat().st_mtime_ns >= OCR_SCRIPT.stat().st_mtime_ns:
        return output
    output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [compiler, str(OCR_SCRIPT), "-o", str(output)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "swiftc failed")
    output.chmod(output.stat().st_mode | 0o111)
    return output


def ocr_png(path: str | Path) -> str:
    if sys.platform != "darwin":
        raise RuntimeError("PNG OCR 验收当前使用 macOS Vision")
    try:
        helper = build_ocr_helper()
        command = [str(helper), str(Path(path).resolve())]
    except (OSError, RuntimeError, subprocess.TimeoutExpired):
        command = ["/usr/bin/swift", str(OCR_SCRIPT), str(Path(path).resolve())]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "Vision OCR failed")
    return completed.stdout.strip()


def verify_png_privacy(report: dict, png_path: str | Path) -> str:
    dimensions = png_dimensions(png_path)
    if dimensions != (1080, 1440):
        raise ValueError(f"PNG 尺寸为 {dimensions[0]}x{dimensions[1]}，不是 1080x1440")
    text_chunks = png_text_chunks(png_path)
    if text_chunks:
        raise PrivacyLeakError("PNG 含可嵌入隐藏文本的 metadata chunk：" + "、".join(text_chunks))
    ocr_text = ocr_png(png_path)
    assert_ocr_meaningful(ocr_text, report["share_card"])
    leaks = find_ocr_privacy_leaks(ocr_text, report["source"].get("privacy_entities", []))
    if leaks:
        raise PrivacyLeakError("PNG OCR 隐私门禁失败：" + "、".join(leaks))
    return ocr_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--png", required=True, type=Path)
    parser.add_argument("--ocr-output", type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    text = verify_png_privacy(report, args.png)
    if args.ocr_output:
        args.ocr_output.parent.mkdir(parents=True, exist_ok=True)
        args.ocr_output.write_text(text + "\n", encoding="utf-8")
    print(f"OCR_PRIVACY_OK characters={len(text)} entities_checked={len(report['source'].get('privacy_entities', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
