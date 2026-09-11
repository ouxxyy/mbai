"""Run a real Safari WebDriver layout probe without third-party Python packages."""

from __future__ import annotations

import argparse
import base64
import http.client
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.export_png import _stop_owned_browser


def _free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _request(port: int, method: str, path: str, payload: dict | None = None) -> dict | list | str | None:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=20)
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json; charset=utf-8"} if body is not None else {}
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    raw = response.read()
    connection.close()
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"SafariDriver 返回非 JSON（HTTP {response.status}）：{raw[:300]!r}") from exc
    value = data.get("value", data) if isinstance(data, dict) else data
    if response.status >= 400 or (isinstance(value, dict) and value.get("error")):
        raise RuntimeError(f"SafariDriver {method} {path} 失败（HTTP {response.status}）：{value}")
    return value


def _wait_ready(port: int, timeout: float = 15) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            _request(port, "GET", "/status")
            return
        except (OSError, http.client.HTTPException, RuntimeError):
            time.sleep(0.1)
    raise TimeoutError("等待 safaridriver 就绪超时")


def _execute(port: int, session_id: str, script: str):
    return _request(
        port,
        "POST",
        f"/session/{session_id}/execute/sync",
        {"script": script, "args": []},
    )


def inspect_safari(
    html_path: str | Path,
    *,
    css_width: int,
    css_height: int,
    screenshot_path: str | Path | None = None,
) -> dict[str, int | bool | str]:
    driver = shutil.which("safaridriver")
    if not driver:
        raise RuntimeError("未找到 safaridriver")
    source = Path(html_path).resolve()
    port = _free_port()
    session_id = None

    with tempfile.TemporaryDirectory(prefix="ai-exposure-safari-") as directory:
        log_path = Path(directory) / "safaridriver.log"
        with log_path.open("w", encoding="utf-8") as log:
            process = subprocess.Popen([driver, "-p", str(port)], stdout=log, stderr=log, text=True)
        try:
            _wait_ready(port)
            value = _request(
                port,
                "POST",
                "/session",
                {"capabilities": {"alwaysMatch": {"browserName": "safari"}}},
            )
            if not isinstance(value, dict) or not value.get("sessionId"):
                raise RuntimeError(f"SafariDriver 未返回 sessionId：{value}")
            session_id = value["sessionId"]
            _request(port, "POST", f"/session/{session_id}/url", {"url": source.as_uri()})

            # WebDriver sets the outer window. Measure browser chrome and converge on the requested CSS viewport.
            _request(
                port,
                "POST",
                f"/session/{session_id}/window/rect",
                {"x": 40, "y": 40, "width": css_width + 120, "height": css_height + 160},
            )
            for _ in range(3):
                dimensions = _execute(
                    port,
                    session_id,
                    "return {innerWidth:window.innerWidth,innerHeight:window.innerHeight,outerWidth:window.outerWidth,outerHeight:window.outerHeight};",
                )
                target_outer_width = max(300, css_width + int(dimensions["outerWidth"]) - int(dimensions["innerWidth"]))
                target_outer_height = max(300, css_height + int(dimensions["outerHeight"]) - int(dimensions["innerHeight"]))
                _request(
                    port,
                    "POST",
                    f"/session/{session_id}/window/rect",
                    {"x": 40, "y": 40, "width": target_outer_width, "height": target_outer_height},
                )

            deadline = time.monotonic() + 15
            metrics = None
            while time.monotonic() < deadline:
                metrics = _execute(
                    port,
                    session_id,
                    "return {ready:document.readyState,cardReady:window.__CARD_READY__===true,viewportWidth:window.innerWidth,scrollWidth:document.documentElement.scrollWidth,horizontalOverflow:document.documentElement.scrollWidth>window.innerWidth,userAgent:navigator.userAgent};",
                )
                if metrics.get("ready") == "complete" and metrics.get("cardReady"):
                    break
                time.sleep(0.1)
            else:
                raise TimeoutError("等待 Safari 报告页面就绪超时")

            if screenshot_path is not None:
                encoded = _request(port, "GET", f"/session/{session_id}/screenshot")
                output = Path(screenshot_path)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(base64.b64decode(str(encoded)))

            return {
                "browser": "Safari",
                "viewport_width": int(metrics["viewportWidth"]),
                "scroll_width": int(metrics["scrollWidth"]),
                "horizontal_overflow": bool(metrics["horizontalOverflow"]),
                "user_agent": str(metrics["userAgent"]),
            }
        except Exception as exc:
            detail = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
            if detail and detail not in str(exc):
                exc.add_note("safaridriver log: " + detail[-2000:])
            raise
        finally:
            if session_id is not None:
                try:
                    _request(port, "DELETE", f"/session/{session_id}")
                except Exception:
                    pass
            _stop_owned_browser(process)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--width", required=True, type=int)
    parser.add_argument("--height", required=True, type=int)
    parser.add_argument("--screenshot", type=Path)
    args = parser.parse_args()
    result = inspect_safari(
        args.html,
        css_width=args.width,
        css_height=args.height,
        screenshot_path=args.screenshot,
    )
    print(
        f"SAFARI_LAYOUT_OK viewport={result['viewport_width']} scroll={result['scroll_width']} overflow={str(result['horizontal_overflow']).lower()}"
    )
    return 1 if result["horizontal_overflow"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
