"""Static-server and browser fixtures for the UI equivalence tests.

Two `http.server` instances run on free ports: one over `app/ui/` (the recovered
tree) and one over a scratch copy of the supplied artifact. The artifact itself
is never written to — it is copied out and its SHA-256 is asserted.
"""
import functools
import hashlib
import http.server
import shutil
import socketserver
import threading
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
UI_DIR = REPO / "app" / "ui"

# The supplied artifact. The precheck copy is preferred because it is what the
# baseline screenshots were taken against; both are the same bytes.
ORIGINAL_SHA256 = "0d8e9e477aaac8213d0987f52c82468fa2753fa2b377c6aa743e5dd51c1aebed"
ORIGINAL_CANDIDATES = [
    Path("/tmp/precheck/ui/original.html"),
    Path.home() / "Downloads" / "Stratistics Wargaming System.html",
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


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # keep pytest output readable
        pass


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def serve(directory: Path) -> str:
    handler = functools.partial(_QuietHandler, directory=str(directory))
    httpd = _Server(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, "http://127.0.0.1:%d" % httpd.server_address[1]


@pytest.fixture(scope="session")
def ui_url():
    httpd, url = serve(UI_DIR)
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
