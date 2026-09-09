"""P2 acceptance: the wired workbench against the real backend.

Every expectation is read from the API during the test — `api(...)` fetches the
same endpoint the browser did — so a dataset or evaluator change moves the test
and the product together instead of silently passing.

Covered here:

* the decision overview names the head of `/api/snapshot` `rankings` for the
  Blue actor, at every batch;
* at batch 1 `str_blue_1` is invalid, stays on the comparison screen and names
  the gate that failed, and cannot be recorded as the recommendation;
* T0 -> 1 -> 2 -> 3 -> T0 updates the recommendation, the as-of date and the
  assumption statuses together, with no restart;
* an out-of-order batch response cannot pull the screen back to an old batch;
* the JP 5-0 App. F caution is on the comparison screen, the value range is
  labelled as an adversary-scenario range, and the words "confidence interval"
  appear nowhere;
* the batch controls are reachable by Tab and operable by Enter and Space;
* no console errors and no failed requests anywhere in the flow.

Screenshots (1440x900) land in app/tests/ui/screenshots/.
"""
import json
import time
import urllib.request
from pathlib import Path

import pytest

SCREENSHOTS = Path(__file__).parent / "screenshots"
VIEWPORT = {"width": 1440, "height": 900}
BLUE = ("meridian", "ent_blue")
BATCHES = [0, 1, 2, 3]


# ───────────────────────────────────────────────────────────── API expectations
def api(base, path):
    with urllib.request.urlopen(base + path, timeout=30) as r:
        return json.loads(r.read())


def snapshot(base, batch):
    return api(base, "/api/snapshot?batch=%d" % batch)


def blue_ranking(snap):
    for r in snap["rankings"]:
        if (r["game_id"], r["actor_id"]) == BLUE:
            return r["strategy_ids"]
    return []


def blue_strategies(snap):
    return [s for s in snap["strategies"]
            if (s["game_id"], s["actor_id"]) == BLUE]


def strategy(snap, sid):
    return next(s for s in snap["strategies"] if s["strategy_id"] == sid)


# ─────────────────────────────────────────────────────────────── browser helpers
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

    def clean(self):
        assert self.console == [], self.console
        assert self.failed == [], self.failed


def open_app(browser, url):
    page = browser.new_page(viewport=VIEWPORT)
    recorder = Recorder(page)
    page.goto(url, wait_until="networkidle")
    page.wait_for_selector("#dc-root .command-bar button", timeout=15000)
    settle(page)
    return page, recorder


def settle(page):
    """Wait until no batch load is in flight."""
    page.wait_for_function(
        "() => !document.body.innerText.includes('Loading ')", timeout=20000)


def text(page):
    return page.locator("#dc-root").inner_text()


def nav_to(page, label):
    page.get_by_role("button", name=label, exact=True).first.click()
    page.wait_for_timeout(150)


def subtab(page, label):
    """Click a Strategy Option Evaluation sub-tab, entering that stage first."""
    loc = page.get_by_role("button", name=label, exact=True)
    if loc.count() == 0:
        nav_to(page, "Strategy Option Evaluation")
        loc = page.get_by_role("button", name=label, exact=True)
    loc.first.click()
    page.wait_for_timeout(150)


def batch_button(page, batch):
    return page.get_by_role(
        "button", name="Show %s" % ("T0 (no injects)" if batch == 0
                                    else "Inject batch %d" % batch))


def select_batch(page, batch):
    batch_button(page, batch).click()
    page.wait_for_timeout(80)
    settle(page)


def selected_batch(page):
    for b in BATCHES:
        if batch_button(page, b).get_attribute("aria-pressed") == "true":
            return b
    return None


@pytest.fixture(scope="session", autouse=True)
def screenshot_dir():
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    return SCREENSHOTS


@pytest.fixture(scope="module")
def app(browser, ui_url):
    page, recorder = open_app(browser, ui_url)
    yield page, recorder
    page.close()


# ─────────────────────────────────────────────────────────────────────── tests
def test_boots_against_the_api(app, api_base):
    page, recorder = app
    meta = api(api_base, "/api/meta")
    assert page.title() == "%s — Strategy Adjudicator" % meta["product_name"]
    marking = page.locator("#classification-marking")
    assert marking.text_content() == meta["marking"]
    assert marking.is_visible()
    branding = page.evaluate("window.BRANDING")
    # branding.js holds no product identity of its own: both come from /api/meta.
    assert branding["productName"] == meta["product_name"]
    assert branding["marking"] == meta["marking"]
    assert branding["error"] is None
    assert meta["product_name"] in text(page)
    recorder.clean()


def test_decision_overview_names_the_ranked_first_strategy(app, api_base):
    page, recorder = app
    select_batch(page, 0)
    snap = snapshot(api_base, 0)
    top = strategy(snap, blue_ranking(snap)[0])
    body = text(page)
    assert "Decision Overview" in body
    assert top["name"] in body
    assert top["strategy_id"] in body
    assert snap["as_of"] in body
    # The demo beat this batch is supposed to show.
    assert top["strategy_id"] == "str_blue_1"
    page.screenshot(path=str(SCREENSHOTS / "p2_overview_batch0.png"), full_page=True)
    recorder.clean()


def test_batch_1_switches_the_recommendation_and_names_the_failed_gate(app, api_base):
    page, recorder = app
    select_batch(page, 1)
    snap = snapshot(api_base, 1)
    ranking = blue_ranking(snap)
    top = strategy(snap, ranking[0])
    assert top["strategy_id"] == "str_blue_2"

    body = text(page)
    assert top["name"] in body and snap["as_of"] in body

    invalid = [s for s in blue_strategies(snap) if s["strategy_id"] not in ranking]
    assert [s["strategy_id"] for s in invalid] == ["str_blue_1"]
    failed = [v["test"] for v in invalid[0]["validity"] if not v["passed"]]
    assert failed == ["acceptable"]

    subtab(page, "Strategy Comparison")
    comparison = text(page)
    # The invalid option stays visible, is labelled invalid in words, and names
    # the gate.
    assert invalid[0]["name"] in comparison
    assert "✕ Invalid" in comparison
    assert "Cannot be recommended — Acceptable gate failed." in comparison
    for v in invalid[0]["validity"]:
        assert v["evidence"] in comparison
    page.screenshot(path=str(SCREENSHOTS / "p2_comparison_batch1.png"), full_page=True)
    recorder.clean()


def test_invalid_strategy_cannot_be_recorded_as_the_recommendation(app, api_base):
    page, recorder = app
    select_batch(page, 1)
    snap = snapshot(api_base, 1)
    ranking = blue_ranking(snap)
    invalid_id = next(s["strategy_id"] for s in blue_strategies(snap)
                      if s["strategy_id"] not in ranking)

    nav_to(page, "Option Recommendation")
    card = page.locator("#dc-root article", has_text=invalid_id)
    button = card.get_by_role("button")
    assert button.is_disabled()
    button.click(force=True)  # a disabled control must also do nothing on force
    page.wait_for_timeout(150)

    page.get_by_role("button", name="Approve", exact=True).click()
    page.wait_for_timeout(200)
    record = text(page)
    assert "Approved" in record
    # The recorded decision is the ranked-first valid option, never the invalid one.
    assert "%s — %s" % (strategy(snap, ranking[0])["name"], ranking[0]) in record
    assert "%s — %s" % (strategy(snap, invalid_id)["name"], invalid_id) not in record
    recorder.clean()


def test_timeline_round_trip_updates_every_panel(app, api_base):
    page, recorder = app
    for batch in [0, 1, 2, 3, 0]:
        select_batch(page, batch)
        snap = snapshot(api_base, batch)
        top = strategy(snap, blue_ranking(snap)[0])

        assert selected_batch(page) == batch
        overview = text(page)
        assert snap["as_of"] in overview, batch
        assert top["name"] in overview, batch
        assert top["strategy_id"] in overview, batch
        page.screenshot(path=str(SCREENSHOTS / ("p2_overview_batch%d.png" % batch)),
                        full_page=True)

        subtab(page, "Strategy Comparison")
        comparison = text(page)
        for s in blue_strategies(snap):
            assert s["name"] in comparison
            assert ("%.3f" % s["value"]) in comparison
        page.screenshot(path=str(SCREENSHOTS / ("p2_comparison_batch%d.png" % batch)),
                        full_page=True)

        # Assumption statuses move with the batch, as words not colours.
        subtab(page, "Assumptions & Requirements")
        rows = page.locator("#dc-root tbody tr")
        seen = {}
        for i in range(rows.count()):
            cells = rows.nth(i).locator("td")
            seen[cells.nth(0).inner_text()] = cells.nth(3).inner_text()
        expected = {a["assumption_id"]: a["status"] for a in snap["assumptions"]
                    if a["strategy_id"] in {s["strategy_id"]
                                            for s in blue_strategies(snap)}}
        assert set(seen) == set(expected), batch
        for aid, status in expected.items():
            assert status.capitalize() in seen[aid], (batch, aid, seen[aid])

        subtab(page, "Decision Overview")
    recorder.clean()


def test_out_of_order_batch_response_does_not_win(browser, ui_url, api_base):
    """Batch 1 responds after batch 3; the screen must stay on batch 3."""
    page, recorder = open_app(browser, ui_url)
    try:
        # Delay the batch-1 response in the page, so the real request still goes
        # to the real API and only its completion order changes.
        page.evaluate("""() => {
          const orig = window.fetch;
          window.fetch = (u, o) => String(u).includes('snapshot?batch=1')
            ? new Promise(r => setTimeout(() => r(orig(u, o)), 2000))
            : orig(u, o);
        }""")
        batch_button(page, 1).click()
        batch_button(page, 3).click()
        settle(page)

        snap3 = snapshot(api_base, 3)
        top3 = strategy(snap3, blue_ranking(snap3)[0])
        assert selected_batch(page) == 3
        assert snap3["as_of"] in text(page)
        assert top3["name"] in text(page)

        # Let the whole stale batch-1 chain land. Nothing may change.
        page.wait_for_timeout(6000)
        assert selected_batch(page) == 3
        body = text(page)
        assert snap3["as_of"] in body
        assert top3["name"] in body
        assert snapshot(api_base, 1)["as_of"] not in body
        recorder.clean()
    finally:
        page.close()


def test_batch_controls_are_keyboard_operable(app, api_base):
    page, recorder = app
    select_batch(page, 0)
    batch_button(page, 1).focus()
    assert page.evaluate(
        "document.activeElement.getAttribute('aria-label')") == "Show Inject batch 1"
    page.keyboard.press("Enter")
    settle(page)
    assert selected_batch(page) == 1

    # Tab moves to the next control in the group and Space activates it.
    page.keyboard.press("Tab")
    assert page.evaluate(
        "document.activeElement.getAttribute('aria-label')") == "Show Inject batch 2"
    page.keyboard.press("Space")
    settle(page)
    assert selected_batch(page) == 2
    assert snapshot(api_base, 2)["as_of"] in text(page)

    page.get_by_role("button", name="Reset to T0", exact=True).click()
    settle(page)
    assert selected_batch(page) == 0
    recorder.clean()


def test_caution_and_range_labels(app, api_base):
    page, recorder = app
    select_batch(page, 0)
    subtab(page, "Strategy Comparison")
    body = text(page)
    snap = snapshot(api_base, 0)
    served = (snap.get("decision_overview") or {}).get("caution")
    assert "JP 5-0 APPENDIX F CAUTION" in body   # the panel is on the screen
    if served:
        assert served in body                    # verbatim from the API
    else:
        assert "Appendix F" in body and "comparison by criterion" in body
    assert "Adversary-scenario range" in body
    assert "confidence interval" not in body.lower().replace(
        "not a statistical confidence interval", "")
    for label in ("P(SUCCESS)", "CASUALTIES", "P(ESCALATION)", "80% CI"):
        assert label.lower() not in body.lower(), label
    recorder.clean()
