"""Export the built-in share-card canvas to a physical 1080x1440 PNG."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
import subprocess
import tempfile
import time
from pathlib import Path


CHROME_CANDIDATES = (
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
    Path("/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"),
)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def find_chrome() -> Path | None:
    configured = os.environ.get("AI_EXPOSURE_CHROME_PATH")
    if configured and Path(configured).is_file():
        return Path(configured)
    return next((candidate for candidate in CHROME_CANDIDATES if candidate.is_file()), None)


def png_dimensions(path: str | Path) -> tuple[int, int]:
    data = Path(path).read_bytes()[:24]
    if len(data) != 24 or data[:8] != PNG_SIGNATURE or data[12:16] != b"IHDR":
        raise ValueError("文件不是有效 PNG")
    return struct.unpack(">II", data[16:24])


def png_text_chunks(path: str | Path) -> list[str]:
    data = Path(path).read_bytes()
    if len(data) < 8 or data[:8] != PNG_SIGNATURE:
        raise ValueError("文件不是有效 PNG")
    chunks: list[str] = []
    offset = 8
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("PNG chunk 截断")
        if chunk_type in {b"tEXt", b"zTXt", b"iTXt"}:
            chunks.append(chunk_type.decode("ascii"))
        offset = end
        if chunk_type == b"IEND":
            break
    return chunks


def _multica_daemon_pid() -> int | None:
    executable = shutil.which("multica")
    if not executable:
        return None
    try:
        completed = subprocess.run(
            [executable, "daemon", "status", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        payload = json.loads(completed.stdout) if completed.returncode == 0 else {}
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None
    for key in ("pid", "daemon_pid", "process_id"):
        if isinstance(payload.get(key), int):
            return payload[key]
    return None


def _stop_owned_browser(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    daemon_pid = _multica_daemon_pid()
    if daemon_pid is not None and process.pid == daemon_pid:
        raise RuntimeError("拒绝终止 Multica daemon；Chrome 子进程 PID 发生异常冲突")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def _wait_for_stable_png(path: Path, process: subprocess.Popen, timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    last_size = -1
    stable_observations = 0
    while time.monotonic() < deadline:
        if path.is_file():
            try:
                png_dimensions(path)
                size = path.stat().st_size
            except (OSError, ValueError):
                size = -1
            if size > 0 and size == last_size:
                stable_observations += 1
                if stable_observations >= 3:
                    return
            else:
                stable_observations = 0
                last_size = size
        if process.poll() is not None:
            if path.is_file():
                png_dimensions(path)
                return
            raise RuntimeError(f"Chrome 在生成 PNG 前退出（exit={process.returncode}）")
        time.sleep(0.05)
    raise TimeoutError(f"等待 Chrome 写出稳定 PNG 超时：{path}")


def export_png(
    html_path: str | Path,
    output_path: str | Path,
    *,
    chrome_path: str | Path | None = None,
) -> Path:
    source = Path(html_path).resolve()
    destination = Path(output_path).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    browser = Path(chrome_path) if chrome_path else find_chrome()
    if browser is None or not browser.is_file():
        raise RuntimeError("未找到 Chrome/Chromium；仍可在 HTML 内点击按钮离线导出 PNG")

    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ai-exposure-chrome-") as profile_dir:
        temporary_png = destination.with_name(f".{destination.name}.partial.png")
        command = [
            str(browser),
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-default-apps",
            "--disable-sync",
            "--metrics-recording-only",
            "--no-first-run",
            "--no-default-browser-check",
            "--force-device-scale-factor=1",
            "--window-size=1080,1440",
            "--run-all-compositor-stages-before-draw",
            f"--user-data-dir={profile_dir}",
            f"--screenshot={temporary_png}",
            source.as_uri() + "?share=1",
        ]
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as browser_log:
            process = subprocess.Popen(command, stdout=browser_log, stderr=browser_log, text=True)
            try:
                _wait_for_stable_png(temporary_png, process)
            except (RuntimeError, TimeoutError) as exc:
                _stop_owned_browser(process)
                browser_log.seek(0)
                detail = browser_log.read().strip()
                raise RuntimeError(f"Chrome PNG 导出失败：{exc}；{detail}") from exc
            finally:
                _stop_owned_browser(process)
        dimensions = png_dimensions(temporary_png)
        if dimensions != (1080, 1440):
            temporary_png.unlink(missing_ok=True)
            raise RuntimeError(f"PNG 尺寸错误：{dimensions[0]}x{dimensions[1]}，期望 1080x1440")
        temporary_png.replace(destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--chrome", type=Path)
    args = parser.parse_args()
    output = export_png(args.html, args.output, chrome_path=args.chrome)
    width, height = png_dimensions(output)
    print(f"PNG_OK path={output} width={width} height={height} bytes={output.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
