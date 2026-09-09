"""P0 equivalence tests: the recovered tree under app/ui must render and behave
like the supplied artifact.

What is asserted:

* the artifact is unmodified (checked in conftest, before and after serving it);
* app/ui/index.html loads with zero page-origin console errors and zero failed
  or 4xx/5xx requests — including the JIPOE map iframe, which 404'd on
  `{{ mapSrc }}` in the original;
* all 9 nav entries render the same headings and the same screen text as the
  original. The comparison is over `#dc-root`, the app root; the
  `UNCLASSIFIED — SYNTHETIC` marking added during recovery sits outside it and
  is asserted separately;
* `runSim`, the collection `cycle` control and manual `ingest` still work.

Screenshots go to app/tests/ui/screenshots/ at 1440x900.
"""
import re
from pathlib import Path

import pytest

SCREENSHOTS = Path(__file__).parent / "screenshots"
VIEWPORT = {"width": 1440, "height": 900}

# Left-nav labels, in document order. Three of them route to the `coa` view at
# different steps, which is why there are 9 entries over 7 view values.
NAV = [
    "Strategy Option Evaluation",
    "Collection Management Agent",
    "Predictive Risk Engine",
    "Option Recommendation",
    "Intelligence",
    "Plans & Strategic Guidance",
    "Force Posture & GFM",
    "RFI Management",
    "Doctrine",
]

MARKING = "UNCLASSIFIED — SYNTHETIC"


def slug(label):
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


class Recorder:
    """Collects page-origin console errors and every failed / 4xx response."""

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


@pytest.fixture(scope="session", autouse=True)
def screenshot_dir():
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    return SCREENSHOTS


def open_app(browser, url):
    page = browser.new_page(viewport=VIEWPORT)
    recorder = Recorder(page)
    page.goto(url, wait_until="networkidle")
    page.wait_for_selector("#dc-root aside button", timeout=15000)
    return page, recorder


def nav_to(page, label):
    page.get_by_role("button", name=label, exact=True).first.click()
    page.wait_for_timeout(250)


def screen_text(page):
    return page.locator("#dc-root").inner_text()


def headings(page):
    return page.locator("#dc-root h1, #dc-root h2, #dc-root h3").all_inner_texts()


@pytest.fixture(scope="module")
def app(browser, ui_url):
    page, recorder = open_app(browser, ui_url)
    yield page, recorder
    page.close()


@pytest.fixture(scope="module")
def original(browser, original_url):
    page, _ = open_app(browser, original_url)
    yield page
    page.close()


def test_index_loads_clean(app):
    page, recorder = app
    assert page.title() == "Stratistics — Strategy Adjudicator"
    assert page.locator("#dc-root h1").first.inner_text() == "Strategy Adjudicator"
    assert page.locator("#classification-marking").inner_text() == MARKING
    assert page.locator("#classification-marking").is_visible()
    assert recorder.console == []
    assert recorder.failed == []


def test_branding_comes_from_the_branding_object(app):
    page, _ = app
    branding = page.evaluate("window.BRANDING")
    assert branding["productName"] == "Stratistics"
    assert branding["teamName"] == "Pytho"
    assert branding["title"] == "Strategy Adjudicator"
    # The nav mark and the header title are rendered from it, not hard-coded:
    # the recovered template interpolates, it does not carry the strings.
    assert branding["teamMark"] in screen_text(page)
    template = page.evaluate(
        "fetch('./src/app.dc.html').then(r => r.text())")
    assert "{{ brandMark }}" in template
    assert "{{ brandTitle }}" in template
    assert branding["teamMark"] not in template
    assert branding["title"] not in template


@pytest.mark.parametrize("label", NAV)
def test_screen_matches_original(app, original, label):
    page, recorder = app
    nav_to(page, label)
    nav_to(original, label)

    expected = screen_text(original)
    assert len(expected) > 500, "%s: original rendered nothing to compare" % label
    assert len(headings(original)) >= 1, label
    assert headings(page) == headings(original), label
    assert screen_text(page) == expected, label
    # The added marking lives outside the compared subtree and stays visible.
    assert page.locator("#classification-marking").is_visible()
    assert MARKING not in screen_text(page)

    page.screenshot(path=str(SCREENSHOTS / ("nav_%s.png" % slug(label))),
                    full_page=True)
    assert recorder.failed == []


def test_jipoe_map_iframe_loads(app):
    """The original fired GET /{{ mapSrc }} -> 404. The recovered page must not."""
    page, recorder = app
    nav_to(page, "Intelligence")
    frame = page.frame_locator('iframe[title="JIPOE map"]')
    frame.locator("#threat").wait_for(timeout=10000)
    # inner_text() would come back upper-cased by the map's text-transform.
    assert frame.locator("#threat").text_content() == "Olvana"
    # d3 drew the basemap from the vendored TopoJSON.
    assert page.frame_locator('iframe[title="JIPOE map"]').locator(
        "#map path").first.is_visible()
    assert recorder.failed == []
    assert not any("mapSrc" in f or "%7B%7B" in f for f in recorder.failed)


def test_run_sim(app):
    page, recorder = app
    nav_to(page, "Predictive Risk Engine")
    page.get_by_role("button", name="Run Wargame", exact=True).click()
    page.get_by_role("button", name="Re-run Wargame", exact=True).wait_for(
        timeout=20000)
    text = screen_text(page)
    assert "P(SUCCESS)" in text.upper()
    page.screenshot(path=str(SCREENSHOTS / "run_sim.png"), full_page=True)
    assert recorder.console == []
    assert recorder.failed == []


def test_collection_cycle(app):
    page, recorder = app
    nav_to(page, "Collection Management Agent")
    before = screen_text(page)
    button = page.get_by_role("button", name="Collection returned",
                              exact=True).first
    button.click()
    page.wait_for_timeout(250)
    assert screen_text(page) != before
    page.screenshot(path=str(SCREENSHOTS / "collection_cycle.png"),
                    full_page=True)
    assert recorder.console == []
    assert recorder.failed == []


def test_manual_ingest(app):
    page, recorder = app
    nav_to(page, "Intelligence")
    title = "UI RECOVERY TEST REPORT"
    page.get_by_placeholder("Title").fill(title)
    page.get_by_placeholder("Paste report text or drop a file…").fill(
        "body text, discarded by the placeholder handler")
    page.get_by_role("button", name="Ingest & Tag to PIR", exact=True).click()
    page.wait_for_timeout(250)
    assert title in screen_text(page)
    page.screenshot(path=str(SCREENSHOTS / "manual_ingest.png"), full_page=True)
    assert recorder.console == []
    assert recorder.failed == []
