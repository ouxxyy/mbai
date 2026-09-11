"""Capture and measure real Chrome viewports through a tiny stdlib CDP client."""

from __future__ import annotations

import argparse
import base64
import http.client
import json
import os
import re
import socket
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.export_png import _stop_owned_browser, find_chrome, png_dimensions


def _browser_path(chrome_path: str | Path | None) -> Path:
    browser = Path(chrome_path) if chrome_path else find_chrome()
    if browser is None or not browser.is_file():
        raise RuntimeError("未找到 Chrome/Chromium")
    return browser


class _WebSocket:
    def __init__(self, url: str, timeout: float = 30):
        parsed = urlparse(url)
        self.socket = socket.create_connection((parsed.hostname, parsed.port or 80), timeout=timeout)
        self.socket.settimeout(timeout)
        self.buffer = bytearray()
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {parsed.path or '/'}{('?' + parsed.query) if parsed.query else ''} HTTP/1.1\r\n"
            f"Host: {parsed.hostname}:{parsed.port or 80}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "Origin: http://localhost\r\n\r\n"
        )
        self.socket.sendall(request.encode("ascii"))
        response = self._read_headers()
        if not response.startswith(b"HTTP/1.1 101"):
            raise RuntimeError(f"Chrome WebSocket 握手失败：{response[:200]!r}")
        self.next_id = 1

    def _read_headers(self) -> bytes:
        data = bytearray()
        while b"\r\n\r\n" not in data:
            chunk = self.socket.recv(4096)
            if not chunk:
                raise RuntimeError("WebSocket 握手期间连接关闭")
            data.extend(chunk)
        head, remainder = bytes(data).split(b"\r\n\r\n", 1)
        self.buffer.extend(remainder)
        return head + b"\r\n\r\n"

    def _read_exact(self, size: int) -> bytes:
        while len(self.buffer) < size:
            chunk = self.socket.recv(max(4096, size - len(self.buffer)))
            if not chunk:
                raise RuntimeError("WebSocket 连接意外关闭")
            self.buffer.extend(chunk)
        data = bytes(self.buffer[:size])
        del self.buffer[:size]
        return data

    def _send_frame(self, payload: bytes, opcode: int = 1) -> None:
        mask = os.urandom(4)
        length = len(payload)
        if length < 126:
            header = bytes([0x80 | opcode, 0x80 | length])
        elif length <= 0xFFFF:
            header = bytes([0x80 | opcode, 0x80 | 126]) + struct.pack(">H", length)
        else:
            header = bytes([0x80 | opcode, 0x80 | 127]) + struct.pack(">Q", length)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.socket.sendall(header + mask + masked)

    def _read_message(self) -> str:
        fragments = bytearray()
        started = False
        while True:
            first, second = self._read_exact(2)
            fin = bool(first & 0x80)
            opcode = first & 0x0F
            masked = bool(second & 0x80)
            length = second & 0x7F
            if length == 126:
                length = struct.unpack(">H", self._read_exact(2))[0]
            elif length == 127:
                length = struct.unpack(">Q", self._read_exact(8))[0]
            mask = self._read_exact(4) if masked else b""
            payload = self._read_exact(length)
            if masked:
                payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
            if opcode == 9:
                self._send_frame(payload, opcode=10)
                continue
            if opcode == 8:
                raise RuntimeError("Chrome WebSocket 已关闭")
            if opcode == 1:
                fragments = bytearray(payload)
                started = True
            elif opcode == 0 and started:
                fragments.extend(payload)
            else:
                continue
            if fin:
                return fragments.decode("utf-8")

    def call(self, method: str, params: dict | None = None) -> dict:
        request_id = self.next_id
        self.next_id += 1
        message = {"id": request_id, "method": method, "params": params or {}}
        self._send_frame(json.dumps(message, separators=(",", ":")).encode("utf-8"))
        while True:
            response = json.loads(self._read_message())
            if response.get("id") != request_id:
                continue
            if "error" in response:
                raise RuntimeError(f"CDP {method} 失败：{response['error']}")
            return response.get("result", {})

    def close(self) -> None:
        try:
            self._send_frame(b"", opcode=8)
        except OSError:
            pass
        self.socket.close()


def _wait_for_debugger(log_path: Path, timeout: float = 15) -> int:
    deadline = time.monotonic() + timeout
    pattern = re.compile(r"DevTools listening on ws://127\.0\.0\.1:(\d+)/")
    while time.monotonic() < deadline:
        text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
        match = pattern.search(text)
        if match:
            return int(match.group(1))
        time.sleep(0.05)
    raise TimeoutError("等待 Chrome DevTools 端口超时")


def _wait_for_page_target(port: int, timeout: float = 10) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
            connection.request("GET", "/json/list")
            response = connection.getresponse()
            targets = json.loads(response.read())
            connection.close()
            page = next((item for item in targets if item.get("type") == "page"), None)
            if page and page.get("webSocketDebuggerUrl"):
                return page["webSocketDebuggerUrl"]
        except (OSError, http.client.HTTPException, json.JSONDecodeError):
            pass
        time.sleep(0.05)
    raise TimeoutError("等待 Chrome 页面 target 超时")


def _run_cdp(
    html_path: str | Path,
    *,
    width: int,
    height: int,
    chrome_path: str | Path | None,
    capture: bool,
) -> tuple[dict[str, int | bool], bytes | None]:
    source = Path(html_path).resolve()
    browser = _browser_path(chrome_path)
    with tempfile.TemporaryDirectory(prefix="ai-exposure-cdp-") as directory:
        working = Path(directory)
        log_path = working / "chrome.log"
        with log_path.open("w", encoding="utf-8") as log:
            command = [
                str(browser),
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--disable-background-networking",
                "--disable-component-update",
                "--disable-default-apps",
                "--disable-sync",
                "--no-first-run",
                "--no-default-browser-check",
                "--remote-allow-origins=*",
                "--remote-debugging-address=127.0.0.1",
                "--remote-debugging-port=0",
                f"--user-data-dir={working / 'profile'}",
                "about:blank",
            ]
            process = subprocess.Popen(command, stdout=log, stderr=log, text=True)
        client = None
        try:
            port = _wait_for_debugger(log_path)
            client = _WebSocket(_wait_for_page_target(port))
            client.call(
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": width,
                    "height": height,
                    "deviceScaleFactor": 1,
                    "mobile": width <= 680,
                    "screenWidth": width,
                    "screenHeight": height,
                },
            )
            client.call("Page.enable")
            client.call("Page.navigate", {"url": source.as_uri()})

            deadline = time.monotonic() + 20
            value = None
            while time.monotonic() < deadline:
                result = client.call(
                    "Runtime.evaluate",
                    {
                        "expression": "({ready:document.readyState,cardReady:window.__CARD_READY__===true,viewportWidth:window.innerWidth,scrollWidth:document.documentElement.scrollWidth,horizontalOverflow:document.documentElement.scrollWidth>window.innerWidth,externalRequests:performance.getEntriesByType('resource').map(e=>e.name).filter(u=>!u.startsWith('data:')&&!u.startsWith('blob:')&&!u.startsWith('file:'))})",
                        "returnByValue": True,
                    },
                )
                value = result.get("result", {}).get("value")
                if value and value.get("ready") == "complete" and value.get("cardReady"):
                    break
                time.sleep(0.05)
            else:
                raise TimeoutError("等待报告页面和 Canvas 就绪超时")

            metrics = {
                "horizontal_overflow": bool(value["horizontalOverflow"]),
                "viewport_width": int(value["viewportWidth"]),
                "scroll_width": int(value["scrollWidth"]),
                "external_resource_requests": list(value.get("externalRequests") or []),
            }
            image = None
            if capture:
                screenshot = client.call(
                    "Page.captureScreenshot",
                    {"format": "png", "fromSurface": True, "captureBeyondViewport": False},
                )
                image = base64.b64decode(screenshot["data"])
            return metrics, image
        finally:
            if client is not None:
                client.close()
            _stop_owned_browser(process)


def probe_layout(
    html_path: str | Path,
    *,
    width: int,
    height: int,
    chrome_path: str | Path | None = None,
) -> dict[str, int | bool]:
    metrics, _ = _run_cdp(html_path, width=width, height=height, chrome_path=chrome_path, capture=False)
    return metrics


def capture_viewport(
    html_path: str | Path,
    output_path: str | Path,
    *,
    width: int,
    height: int,
    chrome_path: str | Path | None = None,
) -> Path:
    _, image = _run_cdp(html_path, width=width, height=height, chrome_path=chrome_path, capture=True)
    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image or b"")
    actual = png_dimensions(output)
    if actual != (width, height):
        raise RuntimeError(f"浏览器截图尺寸为 {actual}，期望 {(width, height)}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--width", required=True, type=int)
    parser.add_argument("--height", required=True, type=int)
    parser.add_argument("--screenshot", type=Path)
    args = parser.parse_args()
    metrics = probe_layout(args.html, width=args.width, height=args.height)
    if args.screenshot:
        capture_viewport(args.html, args.screenshot, width=args.width, height=args.height)
    print(
        f"BROWSER_LAYOUT_OK viewport={metrics['viewport_width']} scroll={metrics['scroll_width']} overflow={str(metrics['horizontal_overflow']).lower()}"
    )
    return 1 if metrics["horizontal_overflow"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
