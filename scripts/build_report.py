"""Build final JSON, offline HTML, PNG, and OCR evidence from a draft analysis."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.export_png import export_png
from scripts.finalize_report import finalize_report
from scripts.privacy import assert_share_card_private
from scripts.render_report import render_report
from scripts.validate_report import assert_valid_report
from scripts.verify_png_privacy import verify_png_privacy


def build_report(
    draft_path: str | Path,
    output_dir: str | Path,
    *,
    export_card: bool = True,
    run_ocr: bool = True,
) -> dict[str, Path]:
    source = Path(draft_path)
    target = Path(output_dir)
    draft = json.loads(source.read_text(encoding="utf-8"))
    report = finalize_report(draft)
    assert_valid_report(report)
    assert_share_card_private(report["share_card"], report["source"]["privacy_entities"])

    target.mkdir(parents=True, exist_ok=True)
    json_path = target / "report.json"
    html_path = target / "report.html"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_report(report), encoding="utf-8")
    artifacts = {"report_json": json_path, "report_html": html_path}

    if export_card:
        png_path = export_png(html_path, target / "share-card.png")
        artifacts["share_png"] = png_path
        if run_ocr:
            ocr_text = verify_png_privacy(report, png_path)
            ocr_path = target / "share-card.ocr.txt"
            ocr_path.write_text(ocr_text + "\n", encoding="utf-8")
            artifacts["ocr_text"] = ocr_path
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--no-png", action="store_true", help="Build only JSON and HTML")
    parser.add_argument("--no-ocr", action="store_true", help="Skip macOS Vision OCR after PNG export")
    args = parser.parse_args()
    artifacts = build_report(
        args.draft,
        args.output_dir,
        export_card=not args.no_png,
        run_ocr=not args.no_ocr,
    )
    for name, path in artifacts.items():
        print(f"{name}={path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
