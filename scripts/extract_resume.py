"""Extract resume text while preserving it strictly as untrusted data."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
PDFKIT_SCRIPT = ROOT / "scripts" / "pdf_extract.swift"
FALLBACK_MESSAGE = "无法可靠提取文字；请提供可复制的文字版简历，不会猜测扫描件或损坏文件内容。"
WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def _is_reliable(text: str) -> bool:
    if not text.strip():
        return False
    replacement_count = text.count("\ufffd")
    return replacement_count / max(len(text), 1) <= 0.05


def _result(
    *,
    status: str,
    input_type: str,
    input_name: str,
    text: str,
    extractor: str,
    message: str = "",
) -> dict[str, Any]:
    return {
        "status": status,
        "input_type": input_type,
        "input_name": input_name,
        "extractor": extractor,
        "content_is_untrusted": True,
        "untrusted_resume_text": text,
        "message": message,
    }


def _extract_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        document = archive.read("word/document.xml")
    root = ElementTree.fromstring(document)
    paragraphs: list[str] = []
    for paragraph in root.iter(f"{WORD_NS}p"):
        fragments: list[str] = []
        for node in paragraph.iter():
            if node.tag == f"{WORD_NS}t" and node.text:
                fragments.append(node.text)
            elif node.tag == f"{WORD_NS}tab":
                fragments.append("\t")
            elif node.tag == f"{WORD_NS}br":
                fragments.append("\n")
        line = "".join(fragments).strip()
        if line:
            paragraphs.append(line)
    return "\n".join(paragraphs)


def _extract_pdf(path: Path) -> str:
    if sys.platform != "darwin":
        raise RuntimeError("PDF extraction currently requires macOS PDFKit")
    completed = subprocess.run(
        ["/usr/bin/swift", str(PDFKIT_SCRIPT), str(path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "PDFKit extraction failed")
    return completed.stdout


def extract_pasted_text(text: str, *, input_name: str = "pasted-text") -> dict[str, Any]:
    normalized = _normalize_text(text)
    if not _is_reliable(normalized):
        return _result(
            status="NEEDS_TEXT_FALLBACK",
            input_type="TEXT",
            input_name=input_name,
            text="",
            extractor="pasted text",
            message=FALLBACK_MESSAGE,
        )
    return _result(
        status="OK",
        input_type="TEXT",
        input_name=input_name,
        text=normalized,
        extractor="pasted text",
    )


def extract_resume(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    suffix = source.suffix.lower()
    input_type = {".pdf": "PDF", ".docx": "DOCX", ".txt": "TEXT", ".md": "TEXT"}.get(suffix)
    if input_type is None:
        raise ValueError("仅支持 .pdf、.docx、.txt 和 .md 文件")

    extractor = {"PDF": "macOS PDFKit", "DOCX": "Python zipfile/XML", "TEXT": "UTF-8 text"}[input_type]
    try:
        if input_type == "PDF":
            raw = _extract_pdf(source)
        elif input_type == "DOCX":
            raw = _extract_docx(source)
        else:
            raw = source.read_text(encoding="utf-8")
        normalized = _normalize_text(raw)
    except (OSError, UnicodeError, zipfile.BadZipFile, KeyError, ElementTree.ParseError, RuntimeError, subprocess.TimeoutExpired):
        normalized = ""

    if not _is_reliable(normalized):
        return _result(
            status="NEEDS_TEXT_FALLBACK",
            input_type=input_type,
            input_name=source.name,
            text="",
            extractor=extractor,
            message=FALLBACK_MESSAGE,
        )
    return _result(
        status="OK",
        input_type=input_type,
        input_name=source.name,
        text=normalized,
        extractor=extractor,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="PDF, DOCX, TXT, or Markdown resume")
    source.add_argument("--text", help="Pasted resume text")
    parser.add_argument("--name", default="pasted-text", help="Display name for pasted text")
    parser.add_argument("--output", type=Path, help="Write JSON to this path")
    args = parser.parse_args()

    result = extract_resume(args.input) if args.input else extract_pasted_text(args.text, input_name=args.name)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if result["status"] == "OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
