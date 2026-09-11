"""Generate fictional resumes, draft JSON, and optionally complete report artifacts."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_report import build_report
from scripts.export_png import _stop_owned_browser, find_chrome
from scripts.finalize_report import finalize_report
from scripts.sample_cases import case_definitions, draft_for_case


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def relative_artifact_paths(root: str | Path, artifacts: dict[str, Path]) -> dict[str, str]:
    base = Path(root).resolve()
    return {name: str(Path(path).resolve().relative_to(base)) for name, path in artifacts.items()}


def _write_docx(path: Path, text: str) -> None:
    paragraphs = []
    for line in text.splitlines():
        escaped = html.escape(line, quote=False)
        paragraphs.append(f'<w:p><w:r><w:t xml:space="preserve">{escaped}</w:t></w:r></w:p>')
    document = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(paragraphs)}<w:sectPr/></w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
        "</Types>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    )
    core = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>虚构测试简历</dc:title><dc:creator>AI Task Exposure Skill</dc:creator></cp:coreProperties>'
    )
    app = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
        '<Application>AI Task Exposure Skill</Application></Properties>'
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("word/document.xml", document)
        archive.writestr("word/_rels/document.xml.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>')
        archive.writestr("docProps/core.xml", core)
        archive.writestr("docProps/app.xml", app)


def _wait_for_stable_pdf(path: Path, process: subprocess.Popen, timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    last_size = -1
    stable = 0
    while time.monotonic() < deadline:
        if path.is_file():
            try:
                signature = path.read_bytes()[:5]
                size = path.stat().st_size
            except OSError:
                signature, size = b"", -1
            if signature == b"%PDF-" and size > 0:
                if size == last_size:
                    stable += 1
                    if stable >= 3:
                        return
                else:
                    last_size, stable = size, 0
        if process.poll() is not None:
            if path.is_file() and path.read_bytes()[:5] == b"%PDF-":
                return
            raise RuntimeError(f"Chrome 在生成 PDF 前退出（exit={process.returncode}）")
        time.sleep(0.05)
    raise TimeoutError(f"等待 Chrome 写出稳定 PDF 超时：{path}")


def _write_pdf(path: Path, text: str) -> None:
    chrome = find_chrome()
    if chrome is None:
        raise RuntimeError("生成 PDF 测试样例需要 Chrome/Chromium")
    path.parent.mkdir(parents=True, exist_ok=True)
    paragraphs = "".join(f"<p>{html.escape(line)}</p>" for line in text.splitlines())
    with tempfile.TemporaryDirectory(prefix="ai-exposure-pdf-") as directory:
        working = Path(directory)
        source = working / "resume.html"
        source.write_text(
            '<!doctype html><meta charset="utf-8"><style>@page{size:A4;margin:22mm}body{font-family:-apple-system,"PingFang SC",sans-serif;font-size:14px;line-height:1.8;color:#111}p{margin:0 0 10px}</style>' + paragraphs,
            encoding="utf-8",
        )
        command = [
            str(chrome),
            "--headless=new",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-sync",
            "--no-first-run",
            "--no-pdf-header-footer",
            f"--user-data-dir={working / 'profile'}",
            f"--print-to-pdf={path.resolve()}",
            source.as_uri(),
        ]
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as log:
            process = subprocess.Popen(command, stdout=log, stderr=log, text=True)
            try:
                _wait_for_stable_pdf(path, process)
            except (RuntimeError, TimeoutError) as exc:
                _stop_owned_browser(process)
                log.seek(0)
                raise RuntimeError(f"PDF 样例生成失败：{exc}；{log.read().strip()}") from exc
            finally:
                _stop_owned_browser(process)


def generate_examples(root: str | Path, *, build_outputs: bool = False, run_ocr: bool = False) -> Path:
    target = Path(root).resolve()
    resumes = target / "resumes"
    source_texts = target / "source-texts"
    drafts = target / "drafts"
    outputs = target / "output"
    for directory in (resumes, source_texts, drafts):
        directory.mkdir(parents=True, exist_ok=True)

    manifest_cases = []
    for case in case_definitions():
        slug = case["slug"]
        source_text = source_texts / f"{slug}.txt"
        source_text.write_text(case["resume_text"] + "\n", encoding="utf-8")

        extension = {"TEXT": "txt", "DOCX": "docx", "PDF": "pdf"}[case["input_type"]]
        resume = resumes / f"{slug}.{extension}"
        if case["input_type"] == "DOCX":
            _write_docx(resume, case["resume_text"])
        elif case["input_type"] == "PDF":
            _write_pdf(resume, case["resume_text"])
        else:
            resume.write_text(case["resume_text"] + "\n", encoding="utf-8")

        draft = draft_for_case(case)
        draft_path = drafts / f"{slug}.json"
        draft_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        final = finalize_report(draft)
        entry = {
            "slug": slug,
            "scenario": case["job_title"],
            "input_type": case["input_type"],
            "resume_path": str(resume.relative_to(target)),
            "resume_sha256": _sha256(resume),
            "source_text_path": str(source_text.relative_to(target)),
            "draft_path": str(draft_path.relative_to(target)),
            "expected_index": final["metrics"]["exposure_index"],
            "expected_level": final["metrics"]["exposure_level"],
            "is_sufficient_info": final["report_metadata"]["is_sufficient_info"],
        }
        if build_outputs:
            artifacts = build_report(draft_path, outputs / slug, export_card=True, run_ocr=run_ocr)
            entry["artifacts"] = relative_artifact_paths(target, artifacts)
        manifest_cases.append(entry)

    manifest = {
        "generated_at": "2026-09-11T20:00:00+08:00",
        "rule_version": "1.0.0",
        "fictional_data_only": True,
        "cases": manifest_cases,
    }
    manifest_path = target / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("examples"))
    parser.add_argument("--build-outputs", action="store_true")
    parser.add_argument("--ocr", action="store_true")
    args = parser.parse_args()
    manifest = generate_examples(args.root, build_outputs=args.build_outputs, run_ocr=args.ocr)
    print(f"EXAMPLES_OK manifest={manifest.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
