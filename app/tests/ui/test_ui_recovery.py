"""The API-backed product keeps the UI V2 shell and removes simulated behavior.

The V2 artifact is immutable and checked by SHA-256 in ``conftest.py``. These
tests cover the top command bar, the four-stage workflow, and direct access to
supporting screens. Other browser modules test the API-backed screen content.
"""
from pathlib import Path

import pytest

SCREENSHOTS = Path(__file__).parent / "screenshots"
VIEWPORT = {"width": 1440, "height": 900}
NAV = [
    "Strategy Option Evaluation",
    "Collection Management Agent",
    "Predictive Interconnected Risk Engine",
    "Option Recommendation",
    "Intelligence",
    "Plans & Strategic Guidance",
    "Force Posture & GFM",
    "RFI Management",
    "Doctrine",
]


class Recorder:
    def __init__(self, page):
        self.console = []
        self.failed = []
        page.on("console", self._console)
        page.on("pageerror", lambda e: self.console.append("pageerror: %s" % e))
        page.on("requestfailed", lambda r: self.failed.append(
            "%s %s" % (r.url, r.failure)))
        page.on("response", self._response)

    def _console(self, msg):
        if msg.type in ("error", "warning"):
            self.console.append("%s: %s" % (msg.type, msg.text))

    def _response(self, response):
        if response.status >= 400:
            self.failed.append("HTTP %d %s" % (response.status, response.url))


def open_app(browser, url):
    page = browser.new_page(viewport=VIEWPORT)
    recorder = Recorder(page)
    page.goto(url, wait_until="networkidle")
    page.wait_for_selector("#dc-root .command-bar button", timeout=15000)
    return page, recorder


def nav_to(page, label):
    target = page.get_by_role("button", name=label, exact=True)
    if target.count() == 0:
        page.get_by_role("button", name="Strategy evaluation home").click()
        page.wait_for_timeout(100)
        target = page.get_by_role("button", name=label, exact=True)
    target.first.click()
    page.wait_for_timeout(250)


def screen_text(page):
    return page.locator("#dc-root").inner_text()


@pytest.fixture(scope="session", autouse=True)
def screenshot_dir():
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    return SCREENSHOTS


@pytest.fixture(scope="module")
def app(browser, ui_url):
    page, recorder = open_app(browser, ui_url)
    yield page, recorder
    page.close()


@pytest.fixture(scope="module")
def original(browser, original_url):
    page = browser.new_page(viewport=VIEWPORT)
    page.goto(original_url, wait_until="networkidle")
    page.wait_for_selector("#dc-root main button", timeout=15000)
    yield page
    page.close()


def test_index_loads_clean(app):
    page, recorder = app
    assert page.locator("#dc-root h1").first.inner_text() == "Strategy Adjudicator"
    assert page.locator("#classification-marking").is_visible()
    assert recorder.console == []
    assert recorder.failed == []


def test_branding_comes_from_the_api_backed_branding_object(app):
    page, _ = app
    branding = page.evaluate("window.BRANDING")
    assert branding["teamName"] == "Pytho"
    assert branding["title"] == "Strategy Adjudicator"
    template = page.evaluate("fetch('./src/app.dc.html').then(r => r.text())")
    assert "{{ brandMark }}" in template
    assert "{{ brandTitle }}" in template
    assert branding["teamMark"] not in template
    assert branding["title"] not in template


def test_product_uses_the_v2_top_bar_instead_of_the_old_sidebar(app, original):
    page, _ = app
    assert original.locator("#dc-root aside").count() == 0
    assert page.locator("#dc-root aside").count() == 0
    assert page.locator("#dc-root .command-bar").is_visible()
    assert page.get_by_role("button", name="Strategy evaluation home").is_visible()
    assert page.get_by_role("button", name="Doctrine", exact=True).is_visible()


@pytest.mark.parametrize("label", NAV)
def test_every_product_area_is_reachable(app, label):
    page, recorder = app
    nav_to(page, label)
    assert len(screen_text(page)) > 500, label
    assert page.locator("#dc-root h1, #dc-root h2, #dc-root h3").count() >= 1
    assert recorder.failed == []


def test_the_fabricated_wargame_is_gone(app):
    page, recorder = app
    nav_to(page, "Predictive Interconnected Risk Engine")
    body = screen_text(page).lower()
    for gone in ("run wargame", "p(success)", "80% ci", "casualties p90",
                 "p(escalation)", "action – reaction – counteraction"):
        assert gone not in body, gone
    assert page.get_by_role(
        "button", name="Recompute from dataset", exact=True).is_visible()
    page.screenshot(path=str(SCREENSHOTS / "risk_engine.png"), full_page=True)
    assert recorder.console == []
    assert recorder.failed == []


def test_jipoe_map_iframe_loads_from_local_assets(app):
    page, recorder = app
    nav_to(page, "Intelligence")
    frame = page.frame_locator('iframe[title="JIPOE map"]')
    frame.locator("#threat").wait_for(timeout=10000)
    assert frame.locator("#threat").text_content() == "Olvana"
    assert frame.locator("#map path").first.is_visible()
    assert recorder.failed == []


def test_collection_uses_stable_api_requirements(app):
    page, recorder = app
    nav_to(page, "Collection Management Agent")
    for gone in ("Collection returned", "Task assets", "Add PIR"):
        assert page.get_by_role("button", name=gone, exact=True).count() == 0
    body = screen_text(page)
    assert "Draft requirement" in body
    assert "Closure basis" in body or "Open — no closure recorded" in body
    assert recorder.console == []
    assert recorder.failed == []


def test_report_form_keeps_text_for_the_real_ingestion_endpoint(app):
    page, recorder = app
    nav_to(page, "Intelligence")
    assert page.get_by_role(
        "button", name="Ingest & Tag to PIR", exact=True).count() == 0
    body_text = "body text the old placeholder handler used to discard"
    page.get_by_label("Report title").fill("UI V2 RECOVERY TEST REPORT")
    page.get_by_label("Report text").fill(body_text)
    assert page.get_by_label("Report text").input_value() == body_text
    assert page.get_by_role("button", name="Ingest report", exact=True).count() == 1
    assert recorder.console == []
    assert recorder.failed == []
