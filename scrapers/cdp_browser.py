#!/usr/bin/env python3
"""
CDPBrowser v3.0 - Singleton Chrome DevTools Protocol Manager

- Chrome'u CDP uzerinden yonetir (websocket-client)
- Harici Chrome'a baglanir (kullanici CMD'den baslattiginda)
- TAB-level WebSocket (page target) — JS evaluate duzgun calisir
- CDP event/response ayirimi (message ID matching)
- WebSocket retry (3x) + auto-reconnect
- Cookie injection (x_session.json / ig_session.json)
- JS evaluate with dynamic timeout for large payloads
- Chrome crash detection + auto-restart
"""

import json
import os
import subprocess
import time
import threading
import platform
import shutil
import logging
import urllib.request
import urllib.error
from typing import Any, Optional, Dict, List

try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

logger = logging.getLogger("CDPBrowser")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class CDPBrowser:
    """
    Singleton CDP Browser Manager.

    Chrome'u tek process olarak baslatir veya harici Chrome'a baglanir.
    Page-level WebSocket uzerinden CDP komutlari gonderir.
    """

    _instance: Optional["CDPBrowser"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(
        self,
        chrome_port: int = 9222,
        headless: bool = False,
        user_data_dir: Optional[str] = None,
    ):
        if self._initialized:
            return
        self._initialized = True

        self.chrome_port = chrome_port
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.chrome_process: Optional[subprocess.Popen] = None
        self.ws: Optional[websocket.WebSocket] = None
        self.ws_url: Optional[str] = None  # Page-level WS URL
        self._msg_id = 0
        self._ws_lock = threading.Lock()
        self._external_chrome = False  # True if Chrome was started externally

        # Pending events buffer (events received while waiting for response)
        self._event_buffer: List[Dict] = []

        # Find Chrome binary
        self.chrome_binary = self._find_chrome_binary()
        if not self.chrome_binary:
            logger.warning("Chrome/Chromium binary not found — will try connecting to external Chrome")

    # ------------------------------------------------------------------
    # Chrome Binary Detection
    # ------------------------------------------------------------------

    @staticmethod
    def _find_chrome_binary() -> Optional[str]:
        """Auto-detect Chrome/Chromium/Brave binary path"""
        system = platform.system()

        if system == "Windows":
            candidates = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            ]
        elif system == "Darwin":
            candidates = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
            ]
        else:  # Linux
            candidates = [
                "/home/openclaw-bot-pc/.local/chrome-install/opt/google/chrome/chrome",
                "google-chrome",
                "google-chrome-stable",
                "chromium",
                "chromium-browser",
                "/usr/bin/google-chrome",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/snap/bin/chromium",
            ]

        for path in candidates:
            if os.path.isfile(path):
                return path
            if system == "Linux" and shutil.which(path):
                return shutil.which(path)

        return None

    # ------------------------------------------------------------------
    # CDP HTTP Endpoint Check
    # ------------------------------------------------------------------

    def _cdp_base_url(self) -> str:
        """Get the working CDP base URL (IPv4 or IPv6)"""
        if hasattr(self, "_cached_base_url") and self._cached_base_url:
            return self._cached_base_url
        # Detect: Brave/Chrome may listen on IPv6 only
        for host in [f"http://127.0.0.1:{self.chrome_port}",
                     f"http://[::1]:{self.chrome_port}"]:
            try:
                with urllib.request.urlopen(f"{host}/json/version", timeout=2):
                    self._cached_base_url = host
                    return host
            except Exception:
                continue
        return f"http://127.0.0.1:{self.chrome_port}"

    def _cdp_http_check(self, timeout: float = 2) -> bool:
        """Check if CDP HTTP endpoint is responding (external or internal Chrome)"""
        for host in [f"http://127.0.0.1:{self.chrome_port}",
                     f"http://[::1]:{self.chrome_port}"]:
            try:
                with urllib.request.urlopen(f"{host}/json/version", timeout=timeout) as resp:
                    data = json.loads(resp.read().decode())
                    if "webSocketDebuggerUrl" in data:
                        self._cached_base_url = host
                        return True
            except Exception:
                continue
        return False

    def _get_page_ws_url(self) -> Optional[str]:
        """
        Get WebSocket URL for the first page tab (not browser-level).
        Page-level WS is required for Runtime.evaluate, DOM access, etc.
        """
        url = f"{self._cdp_base_url()}/json"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                targets = json.loads(resp.read().decode())

            # Find first "page" type target
            for target in targets:
                if target.get("type") == "page":
                    ws_url = target.get("webSocketDebuggerUrl")
                    if ws_url:
                        logger.info(f"Page target: {target.get('title', '?')} → {ws_url}")
                        return ws_url

            # Fallback: any target with WS URL
            for target in targets:
                ws_url = target.get("webSocketDebuggerUrl")
                if ws_url:
                    logger.warning(f"No 'page' target found, using: {target.get('type', '?')}")
                    return ws_url

            logger.error("No targets with WebSocket URL found")
            return None

        except Exception as e:
            logger.error(f"Failed to get page targets: {e}")
            return None

    def _get_browser_ws_url(self) -> Optional[str]:
        """Get browser-level WebSocket URL (for Network.setCookie etc.)"""
        url = f"{self._cdp_base_url()}/json/version"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                return data.get("webSocketDebuggerUrl")
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Chrome Process Management
    # ------------------------------------------------------------------

    def _is_chrome_running(self) -> bool:
        """Check if Chrome is available (internal process OR external)"""
        # Check internal process first
        if self.chrome_process is not None and self.chrome_process.poll() is None:
            return True

        # Check external Chrome via CDP HTTP
        if self._cdp_http_check():
            self._external_chrome = True
            return True

        return False

    def _start_chrome(self) -> None:
        """Start Chrome with CDP enabled"""
        if not self.chrome_binary:
            raise RuntimeError(
                "Chrome binary not found. Either:\n"
                "  1. Install Chrome/Chromium/Brave, or\n"
                "  2. Start Chrome manually with --remote-debugging-port=9222"
            )

        args = [
            self.chrome_binary,
            f"--remote-debugging-port={self.chrome_port}",
            "--remote-allow-origins=*",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
            "--disable-sync",
            "--disable-translate",
            "--metrics-recording-only",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--window-size=1920,1080",
        ]

        if self.headless:
            args.append("--headless=new")

        if self.user_data_dir:
            args.append(f"--user-data-dir={self.user_data_dir}")
        else:
            # Default: C:/tmp/chrome-mis2 (reuse profile with login state)
            if platform.system() == "Windows":
                default_dir = "C:/tmp/chrome-mis2"
            else:
                default_dir = "/tmp/chrome-mis2"
            args.append(f"--user-data-dir={default_dir}")

        self.chrome_process = subprocess.Popen(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._external_chrome = False

        logger.info(f"Chrome started (PID: {self.chrome_process.pid}, port: {self.chrome_port})")
        self._wait_for_cdp(timeout=15)

    def _wait_for_cdp(self, timeout: int = 15) -> None:
        """Wait until CDP endpoint responds and get page WS URL"""
        deadline = time.time() + timeout

        while time.time() < deadline:
            if self._cdp_http_check():
                ws_url = self._get_page_ws_url()
                if ws_url:
                    self.ws_url = ws_url
                    logger.info("CDP ready")
                    return
            time.sleep(0.5)

        raise TimeoutError(f"CDP did not become available within {timeout}s")

    def _stop_chrome(self) -> None:
        """Stop Chrome process (only if we started it)"""
        if self._external_chrome:
            logger.debug("External Chrome — not stopping")
            return

        if self.chrome_process:
            try:
                self.chrome_process.terminate()
                self.chrome_process.wait(timeout=5)
            except Exception:
                try:
                    self.chrome_process.kill()
                except Exception:
                    pass
            self.chrome_process = None
            logger.info("Chrome stopped")

    def ensure_running(self) -> None:
        """
        Ensure Chrome is running and WS is connected.
        Detects external Chrome (started by user via CMD).
        """
        if not self._is_chrome_running():
            logger.info("Chrome not running, starting...")
            self._start_chrome()
        else:
            # Chrome is running — make sure we have a page WS URL
            if not self.ws_url:
                self._wait_for_cdp(timeout=10)
                if self._external_chrome:
                    logger.info(f"Connected to external Chrome on port {self.chrome_port}")

        if self.ws is None or not self._ws_connected():
            self._connect_ws()

    def _restart_chrome(self) -> None:
        """Full restart: kill Chrome + reconnect"""
        logger.warning("Restarting Chrome...")
        self._disconnect_ws()

        if self._external_chrome:
            # Can't restart external Chrome — just reconnect
            logger.warning("External Chrome — attempting reconnect only")
            time.sleep(2)
            self._wait_for_cdp(timeout=10)
        else:
            self._stop_chrome()
            time.sleep(1)
            self._start_chrome()

        self._connect_ws()
        logger.info("Chrome reconnected successfully")

    # ------------------------------------------------------------------
    # WebSocket Connection (PAGE-level)
    # ------------------------------------------------------------------

    def _ws_connected(self) -> bool:
        """Check if WebSocket is still connected"""
        if self.ws is None:
            return False
        try:
            self.ws.ping()
            return True
        except Exception:
            return False

    def _connect_ws(self) -> None:
        """Connect to page-level CDP WebSocket"""
        if not WEBSOCKET_AVAILABLE:
            raise ImportError("websocket-client not installed. Run: pip install websocket-client")

        # Refresh page WS URL (tab may have changed)
        fresh_url = self._get_page_ws_url()
        if fresh_url:
            self.ws_url = fresh_url

        if not self.ws_url:
            raise ConnectionError("No page WebSocket URL available")

        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass

        self.ws = websocket.create_connection(
            self.ws_url,
            timeout=30,
            enable_multithread=True,
        )
        self._msg_id = 0
        self._event_buffer.clear()
        logger.info(f"WebSocket connected → {self.ws_url}")

    def _disconnect_ws(self) -> None:
        """Disconnect WebSocket"""
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None

    # ------------------------------------------------------------------
    # CDP Command Sending (with ID matching + 3x retry)
    # ------------------------------------------------------------------

    def _recv_response(self, msg_id: int, timeout: float = 30) -> Dict:
        """
        Receive CDP response matching msg_id.
        Events (messages without 'id') are buffered, not discarded.
        """
        deadline = time.time() + timeout

        while time.time() < deadline:
            remaining = deadline - time.time()
            if remaining <= 0:
                break

            self.ws.settimeout(min(remaining, 5))
            try:
                raw = self.ws.recv()
                msg = json.loads(raw)

                # Response: has 'id' field
                if "id" in msg:
                    if msg["id"] == msg_id:
                        return msg
                    # Response for a different ID — skip (stale)
                    continue

                # Event: no 'id' field — buffer it
                self._event_buffer.append(msg)

            except websocket.WebSocketTimeoutException:
                continue
            except Exception as e:
                raise ConnectionError(f"WebSocket recv error: {e}")

        raise TimeoutError(f"No response for message ID {msg_id} within {timeout}s")

    def _send(self, method: str, params: Optional[Dict] = None, timeout: float = 30) -> Dict:
        """
        Send CDP command with 3x retry on failure.
        Uses ID matching to correctly pair request/response.
        """
        max_retries = 3
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                with self._ws_lock:
                    self._msg_id += 1
                    current_id = self._msg_id
                    msg = {"id": current_id, "method": method}
                    if params:
                        msg["params"] = params

                    self.ws.send(json.dumps(msg))
                    result = self._recv_response(current_id, timeout=timeout)

                    if "error" in result:
                        error_msg = result["error"].get("message", "Unknown CDP error")
                        raise RuntimeError(f"CDP error: {error_msg}")

                    return result.get("result", {})

            except Exception as e:
                last_error = e
                logger.warning(f"CDP send failed (attempt {attempt}/{max_retries}): {e}")

                if attempt < max_retries:
                    time.sleep(attempt * 0.5)
                    try:
                        if not self._is_chrome_running():
                            self._restart_chrome()
                        else:
                            self._connect_ws()
                    except Exception as reconnect_err:
                        logger.error(f"Reconnect failed: {reconnect_err}")

        raise ConnectionError(f"CDP command failed after {max_retries} retries: {last_error}")

    # ------------------------------------------------------------------
    # Wait for CDP Event
    # ------------------------------------------------------------------

    def _wait_for_event(self, event_name: str, timeout: float = 30) -> Optional[Dict]:
        """
        Wait for a specific CDP event. Checks buffer first, then reads from WS.
        """
        # Check buffer first
        for i, evt in enumerate(self._event_buffer):
            if evt.get("method") == event_name:
                self._event_buffer.pop(i)
                return evt

        # Read from WS
        deadline = time.time() + timeout
        while time.time() < deadline:
            remaining = deadline - time.time()
            if remaining <= 0:
                break

            self.ws.settimeout(min(remaining, 5))
            try:
                raw = self.ws.recv()
                msg = json.loads(raw)

                if msg.get("method") == event_name:
                    return msg

                # Buffer other events/responses
                if "method" in msg:
                    self._event_buffer.append(msg)

            except websocket.WebSocketTimeoutException:
                continue
            except Exception:
                break

        return None

    # ------------------------------------------------------------------
    # Page Navigation
    # ------------------------------------------------------------------

    def navigate(self, url: str, timeout: float = 30) -> None:
        """Navigate to URL and wait for page load"""
        self.ensure_running()

        # Enable Page events
        self._send("Page.enable")

        # Navigate
        self._send("Page.navigate", {"url": url})

        # Wait for load event
        evt = self._wait_for_event("Page.loadEventFired", timeout=timeout)
        if evt is None:
            logger.warning(f"Navigation timeout ({timeout}s) for {url}")

    def get_current_url(self) -> str:
        """Get current page URL"""
        result = self._send("Runtime.evaluate", {
            "expression": "window.location.href",
            "returnByValue": True,
        })
        return result.get("result", {}).get("value", "")

    # ------------------------------------------------------------------
    # JavaScript Evaluation (dynamic timeout)
    # ------------------------------------------------------------------

    def evaluate(self, expression: str, timeout: float = None) -> Any:
        """
        Execute JS and return result.

        timeout: None = auto (10s base + 1s per 1KB of expression).
        """
        self.ensure_running()

        if timeout is None:
            payload_kb = len(expression) / 1024
            timeout = max(10, 10 + payload_kb)

        result = self._send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True,
            "timeout": int(timeout * 1000),
        }, timeout=timeout + 5)  # WS timeout slightly longer than CDP timeout

        remote_obj = result.get("result", {})

        # Check for exceptions
        if result.get("exceptionDetails"):
            exc_text = result["exceptionDetails"].get("text", "JS exception")
            logger.warning(f"JS exception: {exc_text}")
            return None

        if remote_obj.get("type") == "undefined":
            return None

        return remote_obj.get("value")

    def evaluate_chunked(self, items_js: str, chunk_size: int = 100) -> List[Any]:
        """
        Evaluate JS that returns an array, processing in chunks.
        Useful for large datasets (500+ tweets) to avoid timeout.
        """
        self.ensure_running()

        total = self.evaluate(f"({items_js}).length")
        if not total or total == 0:
            return []

        results = []
        for offset in range(0, total, chunk_size):
            chunk_expr = f"({items_js}).slice({offset}, {offset + chunk_size})"
            chunk = self.evaluate(chunk_expr, timeout=30)
            if chunk:
                results.extend(chunk)
            logger.debug(f"Chunk {offset}-{offset + chunk_size}: {len(chunk or [])} items")

        return results

    # ------------------------------------------------------------------
    # Cookie Injection
    # ------------------------------------------------------------------

    def inject_cookies(self, session_file: str, domain: str) -> int:
        """
        Inject cookies from session JSON file.
        Returns number of cookies injected.
        """
        self.ensure_running()

        if not os.path.isfile(session_file):
            logger.warning(f"Session file not found: {session_file}")
            return 0

        with open(session_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        if not isinstance(cookies, list):
            logger.error(f"Invalid session file format (expected list): {session_file}")
            return 0

        # Enable Network domain for cookie operations
        try:
            self._send("Network.enable")
        except Exception:
            pass  # May already be enabled

        count = 0
        for cookie in cookies:
            try:
                cdp_cookie = {
                    "name": cookie.get("name", ""),
                    "value": cookie.get("value", ""),
                    "domain": cookie.get("domain", domain),
                    "path": cookie.get("path", "/"),
                    "httpOnly": cookie.get("httpOnly", False),
                    "secure": cookie.get("secure", True),
                }

                if "expires" in cookie and cookie["expires"]:
                    try:
                        cdp_cookie["expires"] = float(cookie["expires"])
                    except (ValueError, TypeError):
                        pass
                if "expirationDate" in cookie and cookie["expirationDate"]:
                    try:
                        cdp_cookie["expires"] = float(cookie["expirationDate"])
                    except (ValueError, TypeError):
                        pass
                if "sameSite" in cookie and cookie["sameSite"]:
                    ss = str(cookie["sameSite"]).capitalize()
                    if ss in ("Strict", "Lax", "None"):
                        cdp_cookie["sameSite"] = ss

                self._send("Network.setCookie", cdp_cookie)
                count += 1
            except Exception as e:
                logger.debug(f"Cookie inject failed ({cookie.get('name', '?')}): {e}")

        logger.info(f"Injected {count}/{len(cookies)} cookies from {os.path.basename(session_file)}")
        return count

    def get_all_cookies(self, domain_filter: str = None) -> List[Dict]:
        """Get all cookies from browser, optionally filtered by domain"""
        self.ensure_running()

        try:
            self._send("Network.enable")
        except Exception:
            pass

        result = self._send("Network.getAllCookies")
        cookies = result.get("cookies", [])

        if domain_filter:
            cookies = [c for c in cookies if domain_filter in c.get("domain", "")]

        return cookies

    def clear_cookies(self) -> None:
        """Clear all browser cookies"""
        try:
            self._send("Network.enable")
        except Exception:
            pass
        self._send("Network.clearBrowserCookies")
        logger.info("All cookies cleared")

    # ------------------------------------------------------------------
    # Scrolling
    # ------------------------------------------------------------------

    def scroll_and_wait(
        self,
        scroll_px: int = 800,
        wait_ms_min: int = 1500,
        wait_ms_max: int = 3000,
    ) -> int:
        """
        Scroll down and wait random interval.
        Returns new scroll height.
        """
        import random

        self.evaluate(f"window.scrollBy(0, {scroll_px})")

        delay = random.uniform(wait_ms_min / 1000, wait_ms_max / 1000)
        time.sleep(delay)

        height = self.evaluate("document.body.scrollHeight")
        return height or 0

    def scroll_to_top(self) -> None:
        """Scroll to top of page"""
        self.evaluate("window.scrollTo(0, 0)")

    def get_scroll_height(self) -> int:
        """Get current scroll height"""
        return self.evaluate("document.body.scrollHeight") or 0

    # ------------------------------------------------------------------
    # DOM Helpers
    # ------------------------------------------------------------------

    def query_selector_all(self, selector: str) -> int:
        """Return count of elements matching selector"""
        return self.evaluate(f"document.querySelectorAll('{selector}').length") or 0

    def get_page_html(self) -> str:
        """Get full page HTML"""
        return self.evaluate("document.documentElement.outerHTML") or ""

    def screenshot(self, path: str) -> None:
        """Take a screenshot and save to file"""
        import base64

        result = self._send("Page.captureScreenshot", {"format": "png"})
        data = result.get("data", "")
        if data:
            with open(path, "wb") as f:
                f.write(base64.b64decode(data))
            logger.info(f"Screenshot saved: {path}")

    # ------------------------------------------------------------------
    # Tab Management
    # ------------------------------------------------------------------

    def new_tab(self, url: str = "about:blank") -> Optional[str]:
        """Open new tab and return target ID"""
        result = self._send("Target.createTarget", {"url": url})
        target_id = result.get("targetId")
        if target_id:
            logger.info(f"New tab: {target_id}")
        return target_id

    def list_tabs(self) -> List[Dict]:
        """List all open tabs"""
        url = f"{self._cdp_base_url()}/json"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Disconnect WS and optionally stop Chrome"""
        self._disconnect_ws()
        self._stop_chrome()
        CDPBrowser._instance = None
        self._initialized = False
        logger.info("CDPBrowser closed")

    def __enter__(self):
        self.ensure_running()
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
