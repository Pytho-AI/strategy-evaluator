"""Server and browser fixtures for the UI tests.

The UI is static files that talk to `/api` on their own origin, and the backend
does not mount them. So the tests run two processes:

* uvicorn serving the **real** backend over the real dataset — no mocked JSON,
  no fixture bodies;
* an `http.server` over `app/ui/` that forwards `/api/...` and `/openapi.json`
  to that uvicorn. Same origin, so the page needs no CORS and no `API_BASE`.

The equivalence tests additionally serve a scratch copy of the supplied
artifact. The artifact itself is never written to — it is copied out and its
SHA-256 is asserted before and after.
"""
import functools
import hashlib
import http.server
import os
import shutil
import socket
import socketserver
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
UI_DIR = REPO / "app" / "ui"
PROXIED = ("/api/", "/openapi.json")

# The supplied artifact. The precheck copy is preferred because it is what the
# baseline screenshots were taken against; both are the same bytes.
ORIGINAL_SHA256 = "b949279befe8fbe7856601cd0f55a6cc1675a707272d81928459b6896c7fdf0c"
ORIGINAL_CANDIDATES = [
    Path.home() / "Downloads" / "UI_V2.html",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_original() -> Path:
    for candidate in ORIGINAL_CANDIDATES:
        if candidate.is_file() and sha256(candidate) == ORIGINAL_SHA256:
            return candidate
    pytest.skip(
        "supplied artifact (sha256 %s) not found at %s"
        % (ORIGINAL_SHA256[:16], " or ".join(str(c) for c in ORIGINAL_CANDIDATES))
    )


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep pytest output readable
        pass


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def serve(directory: Path, api_base: str | None = None):
    """Serve `directory`; when `api_base` is given, forward the API paths to it."""

    class Handler(_QuietHandler):
        def do_GET(self):
            if api_base and self.path.startswith(PROXIED):
                self.proxy()
            else:
                super().do_GET()

        def do_POST(self):
            if api_base and self.path.startswith(PROXIED):
                self.proxy()
            else:
                self.send_error(404)

        def proxy(self):
            body = None
            if self.command == "POST":
                length = int(self.headers.get("content-length", "0"))
                body = self.rfile.read(length)
            request = urllib.request.Request(
                api_base + self.path,
                data=body,
                method=self.command,
                headers={
                    "accept": self.headers.get("accept", "application/json"),
                    "content-type": self.headers.get(
                        "content-type", "application/json"
                    ),
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=30) as up:
                    status, body, ctype = up.status, up.read(), up.headers.get(
                        "content-type", "application/json")
            except urllib.error.HTTPError as e:  # relay the error envelope as-is
                status, body, ctype = e.code, e.read(), e.headers.get(
                    "content-type", "application/json")
            except Exception as e:  # the API is down: say so in the body
                status, body, ctype = 502, str(e).encode(), "text/plain"
            self.send_response(status)
            self.send_header("content-type", ctype)
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    handler = functools.partial(Handler, directory=str(directory))
    httpd = _Server(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, "http://127.0.0.1:%d" % httpd.server_address[1]


@pytest.fixture(scope="session")
def api_base(tmp_path_factory):
    """The real backend, over the real dataset, on its own port."""
    port = free_port()
    env = dict(
        os.environ,
        PYTHONUNBUFFERED="1",
        STRATEGY_WORKSPACE_DIR=str(tmp_path_factory.mktemp("ui-workspaces")),
    )
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.backend.main:app",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
        cwd=str(REPO), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    base = "http://127.0.0.1:%d" % port
    deadline = time.time() + 60
    while time.time() < deadline:
        if proc.poll() is not None:
            out = proc.stdout.read().decode(errors="replace")
            pytest.fail("uvicorn exited before serving:\n%s" % out)
        try:
            with urllib.request.urlopen(base + "/api/health", timeout=2) as r:
                if r.status == 200:
                    break
        except Exception:
            time.sleep(0.25)
    else:
        proc.terminate()
        pytest.fail("backend did not become healthy within 60s")
    yield base
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="session")
def ui_url(api_base):
    httpd, url = serve(UI_DIR, api_base=api_base)
    yield url + "/index.html"
    httpd.shutdown()


@pytest.fixture(scope="session")
def original_url(tmp_path_factory):
    src = find_original()
    root = tmp_path_factory.mktemp("original")
    shutil.copyfile(src, root / "original.html")
    httpd, url = serve(root)
    yield url + "/original.html"
    httpd.shutdown()
    # The artifact must be byte-identical after the run.
    assert sha256(src) == ORIGINAL_SHA256


@pytest.fixture(scope="session")
def browser():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()
