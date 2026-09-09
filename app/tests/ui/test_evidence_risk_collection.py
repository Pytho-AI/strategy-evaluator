"""P3 acceptance: the evidence, risk, collection and change-explanation views.

Every expectation is fetched from the running API inside the test — the same
endpoint the browser called — so a dataset or evaluator change moves the test
and the product together. No expected value is written as a literal here; the
only literals are dataset **ids** (`clm_0844`, `he_05`, `req_01`, `req_07`),
which are the demo beats the handoff names.

Covered here:

* the evidence filters (source, status, minimum confidence) return exactly what
  `GET /api/claims` returns for the same filter;
* clicking a claim shows the exact `span_text` the API serves, its source, both
  dates, and likelihood and confidence as two separate fields;
* the batch-3 proposed throughput claim reads Proposed with a contradiction,
  and the approved claim it contradicts still reads Approved;
* a superseded T0 claim reads Superseded even though its `status` is approved;
* `clm_0844`'s trace at batch 1 reaches `asm_blue_1_k0` and labels that edge
  `current_evidence`;
* the risk view shows `he_05`'s forced-choice rationale at batch 3 and the
  cascade `he_05 → he_04`;
* `req_01` shows manifest-replay closure at batch 2 and `req_07` is JIPCL rank
  1 at batch 3;
* the change-explanation panels equal `GET /api/injects/{batch}/diff`, and T0
  says "no changes; baseline";
* the new controls are keyboard reachable, the page has no console errors and
  no failed requests at 1440x900, and no horizontal overflow at 1280x800 or
  390x844.
"""
import json
import urllib.request
from pathlib import Path

import pytest

SCREENSHOTS = Path(__file__).parent / "screenshots"
VIEWPORT = {"width": 1440, "height": 900}
BATCHES = [0, 1, 2, 3]


# ───────────────────────────────────────────────────────────── API expectations
def api(base, path):
    with urllib.request.urlopen(base + path, timeout=30) as r:
        return json.loads(r.read())


def claims(base, batch, **filters):
    query = "".join("&%s=%s" % (k, v) for k, v in filters.items())
    return api(base, "/api/claims?batch=%d%s" % (batch, query))


def all_claims(base, batch):
    return claims(base, batch, limit=1000)["claims"]


# ─────────────────────────────────────────────────────────────── browser helpers
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

    def clean(self):
        assert self.console == [], self.console
        assert self.failed == [], self.failed


def settle(page):
    page.wait_for_function(
        "() => !document.body.innerText.includes('Loading ')", timeout=20000)


def open_app(browser, url, viewport=None):
    page = browser.new_page(viewport=viewport or VIEWPORT)
    recorder = Recorder(page)
    page.goto(url, wait_until="networkidle")
    page.wait_for_selector("#dc-root .command-bar button", timeout=15000)
    settle(page)
    return page, recorder


def text(page):
    return page.locator("#dc-root").inner_text()


def all_text(page):
    """Rendered text plus the raw DOM text: panel eyebrows are
    text-transform:uppercase, and inner_text() returns them transformed."""
    return text(page) + "\n" + page.locator("#dc-root").text_content()


def nav_to(page, label):
    page.get_by_role("button", name=label, exact=True).first.click()
    page.wait_for_timeout(200)


def select_batch(page, batch):
    page.get_by_role("button", name="Show %s" % (
        "T0 (no injects)" if batch == 0 else "Inject batch %d" % batch)).click()
    page.wait_for_timeout(100)
    settle(page)
    page.wait_for_timeout(250)


def claim_rows(page):
    """The claim id in each visible row of the evidence table, in order."""
    return page.evaluate(
        """() => Array.from(
             document.querySelectorAll('table[data-table="claims"] tbody tr'))
             .map(tr => tr.querySelector('td').innerText.trim().split('\\n').pop())""")


def set_filter(page, aria, value):
    page.locator('select[aria-label="%s"]' % aria).select_option(value)
    page.wait_for_timeout(600)


def clear_filters(page):
    page.get_by_role("button", name="Clear filters", exact=True).click()
    page.wait_for_timeout(600)


@pytest.fixture(scope="session", autouse=True)
def screenshot_dir():
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    return SCREENSHOTS


@pytest.fixture(scope="module")
def app(browser, ui_url):
    page, recorder = open_app(browser, ui_url)
    yield page, recorder
    page.close()


# ──────────────────────────────────────────────────────────── evidence filters
def test_source_filter_returns_what_the_api_returns(app, api_base):
    page, recorder = app
    select_batch(page, 0)
    nav_to(page, "Intelligence")
    source = all_claims(api_base, 0)[0]["source"]["source_id"]

    set_filter(page, "Filter claims by source document", source)
    expected = claims(api_base, 0, source=source, limit=25)
    assert claim_rows(page) == [c["claim_id"] for c in expected["claims"]]
    assert str(expected["total"]) in text(page)
    page.screenshot(path=str(SCREENSHOTS / "p3_evidence_source_filter.png"),
                    full_page=True)
    clear_filters(page)
    recorder.clean()


def test_status_filter_returns_what_the_api_returns(app, api_base):
    page, recorder = app
    select_batch(page, 3)
    nav_to(page, "Intelligence")

    set_filter(page, "Filter claims by status", "proposed")
    expected = claims(api_base, 3, status="proposed", limit=25)
    assert expected["total"] > 0, "the dataset serves no proposed claim at batch 3"
    assert claim_rows(page) == [c["claim_id"] for c in expected["claims"]]
    clear_filters(page)
    recorder.clean()


def test_minimum_confidence_filter_returns_what_the_api_returns(app, api_base):
    page, recorder = app
    select_batch(page, 1)
    nav_to(page, "Intelligence")

    page.get_by_label("Filter claims by minimum confidence").fill("0.95")
    page.wait_for_timeout(700)
    expected = claims(api_base, 1, min_confidence="0.95", limit=25)
    assert claim_rows(page) == [c["claim_id"] for c in expected["claims"]]
    assert str(expected["total"]) in text(page)
    clear_filters(page)
    recorder.clean()


def test_entity_filter_returns_what_the_api_returns(app, api_base):
    page, recorder = app
    select_batch(page, 0)
    nav_to(page, "Intelligence")
    entity = all_claims(api_base, 0)[0]["subject_id"]

    set_filter(page, "Filter claims by entity", entity)
    expected = claims(api_base, 0, entity=entity, limit=25)
    assert claim_rows(page) == [c["claim_id"] for c in expected["claims"]]
    clear_filters(page)
    recorder.clean()


def test_relationship_filter_returns_what_the_api_returns(app, api_base):
    """The kinds offered are the ones the API itself named in a response."""
    page, recorder = app
    select_batch(page, 0)
    nav_to(page, "Intelligence")
    options = page.evaluate(
        """() => Array.from(document.querySelectorAll(
             'select[aria-label="Filter claims by dependency relationship"] option'))
             .map(o => o.value).filter(v => v)""")
    assert options, "no relationship kind was offered"
    kind = options[0]

    set_filter(page, "Filter claims by dependency relationship", kind)
    expected = claims(api_base, 0, relationship=kind, limit=25)
    assert claim_rows(page) == [c["claim_id"] for c in expected["claims"]]
    clear_filters(page)
    recorder.clean()


# ─────────────────────────────────────────────────────────── one claim in full
def open_claim(page, claim_id):
    page.get_by_role("button", name="Open claim %s" % claim_id).first.click()
    page.wait_for_timeout(700)


def focus_claim(page, api_base, batch, claim_id):
    """Filter to the claim's own source, then open it."""
    served = api(api_base, "/api/claims/%s?batch=%d" % (claim_id, batch))["claim"]
    set_filter(page, "Filter claims by source document", served["source"]["source_id"])
    open_claim(page, claim_id)
    return served


def test_clicking_a_claim_shows_the_exact_span_and_both_dates(app, api_base):
    page, recorder = app
    select_batch(page, 0)
    nav_to(page, "Intelligence")
    claim_id = all_claims(api_base, 0)[0]["claim_id"]
    served = focus_claim(page, api_base, 0, claim_id)

    assert page.locator('[data-span="claim-span"]').inner_text() == served["span_text"]
    body = text(page)
    assert served["source"]["title"] in body
    assert served["source"]["path"] in body
    assert served["asserted_at"] in body
    if served["valid_from"]:
        assert served["valid_from"] in body
    # likelihood and confidence are two fields, never one probability
    assert "Likelihood" in body and "Confidence" in body
    page.screenshot(path=str(SCREENSHOTS / "p3_claim_detail.png"), full_page=True)
    clear_filters(page)
    recorder.clean()


def test_batch3_proposed_claim_contradicts_an_approved_claim_that_stays_approved(
        app, api_base):
    page, recorder = app
    select_batch(page, 3)
    nav_to(page, "Intelligence")

    proposed = [c for c in claims(api_base, 3, status="proposed", limit=50)["claims"]
                if c["flags"]["contradiction"]]
    assert proposed, "no proposed contradicting claim at batch 3"
    throughput = next(c for c in proposed if "throughput" in c["predicate"])
    contradicted_id = throughput["flags"]["contradicts_claim_ids"][0]
    contradicted = api(api_base, "/api/claims/%s?batch=3" % contradicted_id)["claim"]
    assert contradicted["status"] == "approved"

    set_filter(page, "Filter claims by status", "proposed")
    row = page.locator('table[data-table="claims"] tbody tr',
                       has_text=throughput["claim_id"])
    assert "Proposed" in row.inner_text()
    assert contradicted_id in row.inner_text()
    clear_filters(page)

    # the approved claim it contradicts is still approved on the same screen
    set_filter(page, "Filter claims by source document",
               contradicted["source"]["source_id"])
    approved_row = page.locator('table[data-table="claims"] tbody tr',
                                has_text=contradicted_id)
    assert "Approved" in approved_row.inner_text()
    assert throughput["claim_id"] in approved_row.inner_text()
    page.screenshot(path=str(SCREENSHOTS / "p3_contradiction_batch3.png"),
                    full_page=True)
    clear_filters(page)
    recorder.clean()


def test_superseded_t0_claim_is_labelled_superseded(app, api_base):
    page, recorder = app
    select_batch(page, 1)
    nav_to(page, "Intelligence")

    superseded = next(c for c in all_claims(api_base, 1) if c["flags"]["superseded"])
    # the row must read the flag, not the status column
    assert superseded["status"] == "approved"

    set_filter(page, "Filter claims by source document",
               superseded["source"]["source_id"])
    row = page.locator('table[data-table="claims"] tbody tr',
                       has_text=superseded["claim_id"])
    assert "Superseded" in row.inner_text()
    assert superseded["flags"]["superseded_by_claim_id"] in row.inner_text()
    clear_filters(page)
    recorder.clean()


def test_trace_reaches_the_assumption_with_a_current_evidence_basis(app, api_base):
    """clm_0844 at batch 1 grounds asm_blue_1_k0 as current evidence."""
    page, recorder = app
    select_batch(page, 1)
    nav_to(page, "Intelligence")

    trace = api(api_base, "/api/claims/clm_0844?batch=1")["trace"]
    edge = next(e for e in trace["edges"] if e["to_id"] == "asm_blue_1_k0")
    assert edge["basis"] == "current_evidence"
    path = next(p for p in trace["paths"]
                if any(n["id"] == "asm_blue_1_k0" for n in p["nodes"]))
    strategy = next(n for n in path["nodes"] if n["type"] == "strategy")

    focus_claim(page, api_base, 1, "clm_0844")
    body = text(page)
    assert "asm_blue_1_k0" in body
    assert edge["to_name"] in body
    assert "current_evidence" in body
    assert "dependency_edge" in body      # the other basis is labelled too
    assert strategy["id"] in body and strategy["name"] in body
    page.screenshot(path=str(SCREENSHOTS / "p3_trace_clm_0844.png"), full_page=True)

    # each node links to its own screen
    page.get_by_role("button", name="Open strategy %s" % strategy["name"]).first.click()
    page.wait_for_timeout(300)
    assert "Strategy Comparison" in text(page) or strategy["name"] in text(page)
    nav_to(page, "Intelligence")
    clear_filters(page)
    recorder.clean()


# ────────────────────────────────────────────────────────────────── risk view
def test_risk_view_shows_forced_choice_rationale_and_the_cascade(app, api_base):
    page, recorder = app
    select_batch(page, 3)
    nav_to(page, "Predictive Interconnected Risk Engine")

    risks = api(api_base, "/api/risks?batch=3")
    he = next(h for h in risks["harmful_events"] if h["he_id"] == "he_05")
    forced = [h for h in he["horizons"] if h["forced_choice_applied"]]
    assert forced, "he_05 has no forced-choice horizon at batch 3"
    downstream = he["cascade"]["downstream_edges"]
    assert any(e["to_he_id"] == "he_04" for e in downstream)

    body = text(page)
    for horizon in forced:
        assert horizon["posture_rationale"] in body
        assert horizon["p_level"].capitalize() in body
        assert horizon["c_level"].capitalize() in body
        assert horizon["risk_level"].capitalize() in body
    assert "he_05 → he_04" in body
    assert he["statement"] in body
    # names, not raw ids, for the problem sets
    for ps in risks["problem_sets"]:
        assert ps["name"] in body
    page.screenshot(path=str(SCREENSHOTS / "p3_risk_batch3.png"), full_page=True)
    recorder.clean()


def test_risk_driver_links_to_the_satisfying_claim(app, api_base):
    page, recorder = app
    select_batch(page, 3)
    nav_to(page, "Predictive Interconnected Risk Engine")

    risks = api(api_base, "/api/risks?batch=3")
    driver = next(
        d
        for he in risks["harmful_events"] for h in he["horizons"]
        for d in h["active_drivers"] if d["claims"])
    claim = driver["claims"][0]
    assert claim["claim_id"] in text(page)

    page.get_by_role("button", name="Open claim %s" % claim["claim_id"]).first.click()
    page.wait_for_timeout(800)
    served = api(api_base, "/api/claims/%s?batch=3" % claim["claim_id"])["claim"]
    assert page.locator('[data-span="claim-span"]').inner_text() == served["span_text"]
    recorder.clean()


# ──────────────────────────────────────────────────────────── collection view
def test_req_01_closure_is_visible_at_batch_2(app, api_base):
    page, recorder = app
    select_batch(page, 2)
    nav_to(page, "Collection Management Agent")

    served = next(r for r in api(api_base, "/api/collection?batch=2")["requirements"]
                  if r["req_id"] == "req_01")
    assert served["closure_basis"] == "manifest_replay"
    card = page.locator("#dc-root article", has_text="req_01")
    body = card.text_content()
    assert served["status"].capitalize() in body
    assert "manifest replay" in body
    assert served["answered_by_source"]["title"] in body
    assert served["pir_statement"] in body
    assert served["eei"] in body
    assert served["assumption"]["assumption_id"] in body
    page.screenshot(path=str(SCREENSHOTS / "p3_collection_batch2.png"),
                    full_page=True)
    recorder.clean()


def test_req_07_is_the_first_collection_priority_at_batch_3(app, api_base):
    page, recorder = app
    select_batch(page, 3)
    nav_to(page, "Collection Management Agent")

    requirements = api(api_base, "/api/collection?batch=3")["requirements"]
    first = requirements[0]
    assert first["req_id"] == "req_07" and first["jipcl_rank"] == 1

    # text_content(), not inner_text(): the id chip is text-transform:uppercase
    # and inner_text() would return the transformed text.
    cards = page.locator("#dc-root article")
    top = cards.first.text_content()
    assert "req_07" in top
    assert "JIPCL #1" in top
    assert first["gap_type"] in top
    assert first["eei"] in top
    assert first["ltiov"] in top
    assert first["routing_authority"]["name"] in top
    # the priority basis is named, not a bare number
    assert ("EVPI" if first["priority_basis"]["basis"] == "evpi" else "Fallback") in top
    page.screenshot(path=str(SCREENSHOTS / "p3_collection_batch3.png"),
                    full_page=True)
    recorder.clean()


def test_the_routing_queue_is_the_same_requirements(app, api_base):
    page, recorder = app
    select_batch(page, 3)
    nav_to(page, "RFI Management")
    served = api(api_base, "/api/collection?batch=3")["requirements"]
    rows = page.evaluate(
        """() => Array.from(
             document.querySelectorAll('table[data-table="routing"] tbody tr'))
             .map(tr => tr.querySelector('td').innerText.trim())""")
    assert rows == [r["req_id"] for r in served]
    recorder.clean()


# ───────────────────────────────────────────── inject timeline / change panels
PANEL_TITLES = [
    "New or changed evidence",
    "Assumption state changes",
    "Validity changes",
    "Ranking and value changes",
    "Risk changes and cascade paths",
    "Collection requirement changes",
]


def open_changes(page):
    """The sub-tab lives on the Strategy Option Evaluation stage."""
    if page.get_by_role("button", name="Inject changes", exact=True).count() == 0:
        nav_to(page, "Strategy Option Evaluation")
    page.get_by_role("button", name="Inject changes", exact=True).first.click()
    page.wait_for_timeout(400)


def test_t0_change_panel_says_baseline(app):
    page, recorder = app
    select_batch(page, 0)
    open_changes(page)
    assert "no changes; baseline" in text(page)
    recorder.clean()


@pytest.mark.parametrize("batch", [1, 2, 3])
def test_change_panels_equal_the_diff_endpoint(app, api_base, batch):
    page, recorder = app
    select_batch(page, batch)
    open_changes(page)
    diff = api(api_base, "/api/injects/%d/diff" % batch)
    body = all_text(page)

    for title in PANEL_TITLES:
        assert title in body, title
    for claim in diff["evidence"]["claims_added"]:
        assert claim["claim_id"] in body
        assert claim["label"] in body
    for a in diff["assumptions_changed"]:
        assert a["assumption_id"] in body
        assert "%s → %s" % (a["from"], a["to"]) in body
    for v in diff["validity_changed"]:
        assert v["name"] in body and v["test"].capitalize() in body
    for s in diff["strategies_restated"]:
        assert s["name"] in body
    for r in diff["risk_assessments_changed"]:
        assert r["he_id"] in body
    for r in diff["jipcl_changed"]:
        assert r["req_id"] in body
    for r in diff["requirements_closed"]:
        assert (r if isinstance(r, str) else r["req_id"]) in body
    page.screenshot(path=str(SCREENSHOTS / ("p3_changes_batch%d.png" % batch)),
                    full_page=True)
    recorder.clean()


# ───────────────────────────────────────────── planning objects and workspace
def test_tracked_planning_objects_show_provenance_or_say_it_is_absent(app, api_base):
    page, recorder = app
    select_batch(page, 1)
    nav_to(page, "Plans & Strategic Guidance")
    snap = api(api_base, "/api/snapshot?batch=1")
    options = api(api_base, "/api/strategies?batch=1")["strategies"]
    blue = {s["strategy_id"] for s in options}
    body = text(page)

    for a in snap["assumptions"]:
        if a["strategy_id"] in blue:
            assert a["assumption_id"] in body
            assert a["statement"] in body
    for o in options:
        for c in o["constraints"] + o["restraints"]:
            assert c in body
    # constraints carry no provenance in the dataset, and the screen says so
    assert "no source span, validity window, confidence or review state" in body

    # an assumption's grounding evidence is fetched from the API on demand
    page.get_by_role("button", name="Show grounding evidence").first.click()
    page.wait_for_timeout(700)
    recorder.clean()


def test_the_workspace_indicator_is_on_every_wired_screen(app):
    page, recorder = app
    select_batch(page, 0)
    for label in ("Intelligence", "Collection Management Agent",
                  "Plans & Strategic Guidance", "RFI Management",
                  "Predictive Interconnected Risk Engine"):
        nav_to(page, label)
        body = text(page)
        assert "Demo workspace" in body or "workspace" in body.lower(), label
        assert "Graph" in body or "graph_version" in body, label
    recorder.clean()


# ───────────────────────────────────────────────── accessibility and layout
def test_the_new_controls_are_keyboard_reachable(app, api_base):
    page, recorder = app
    select_batch(page, 0)
    nav_to(page, "Intelligence")

    for aria in ("Filter claims by entity", "Filter claims by source document",
                 "Filter claims by status",
                 "Filter claims by dependency relationship"):
        page.locator('select[aria-label="%s"]' % aria).focus()
        assert page.evaluate(
            "document.activeElement.getAttribute('aria-label')") == aria

    page.get_by_label("Filter claims by minimum confidence").focus()
    assert page.evaluate("document.activeElement.tagName") == "INPUT"

    claim_id = all_claims(api_base, 0)[0]["claim_id"]
    set_filter(page, "Filter claims by source document",
               api(api_base, "/api/claims/%s?batch=0" % claim_id)["claim"]["source"]["source_id"])
    button = page.get_by_role("button", name="Open claim %s" % claim_id).first
    button.focus()
    page.keyboard.press("Enter")
    page.wait_for_timeout(700)
    assert page.locator('[data-span="claim-span"]').count() == 1
    clear_filters(page)
    recorder.clean()


def test_no_console_errors_and_no_failed_requests(app):
    page, recorder = app
    for batch in BATCHES:
        select_batch(page, batch)
        for label in ("Intelligence", "Collection Management Agent",
                      "RFI Management", "Plans & Strategic Guidance",
                      "Predictive Interconnected Risk Engine", "Strategy Option Evaluation"):
            nav_to(page, label)
    recorder.clean()


@pytest.mark.parametrize("size", [
    {"width": 1280, "height": 800},
    {"width": 390, "height": 844},
])
def test_no_horizontal_overflow(browser, ui_url, size):
    page, recorder = open_app(browser, ui_url, viewport=size)
    try:
        for label in ("Intelligence", "Collection Management Agent",
                      "RFI Management", "Plans & Strategic Guidance",
                      "Predictive Interconnected Risk Engine"):
            nav_to(page, label)
            page.wait_for_timeout(200)
            overflow = page.evaluate(
                "() => document.documentElement.scrollWidth - window.innerWidth")
            assert overflow <= 1, (label, size, overflow)
            page.screenshot(
                path=str(SCREENSHOTS / ("p3_%dx%d_%s.png" % (
                    size["width"], size["height"],
                    label.split()[0].lower()))),
                full_page=True)
        recorder.clean()
    finally:
        page.close()
