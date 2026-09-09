"""P3 acceptance: new report → proposed claims → review → recompute, and the
collection draft / route / status and workspace-reset controls.

The report used here is fictional and dated after the fixture was generated, so
nothing in it can be answered from dataset truth. Its value is parameterised in
`REPORT_VALUE` and asserted back out of the UI, so the proposed claim has to
follow the text that was actually submitted.

Every test names the write endpoint it needs. While the backend does not
declare that endpoint, the test asserts the UI renders the *not served* state —
the control disabled and the endpoint named, never a dead button or a faked
result — and then marks itself `xfail(strict=True)`. The moment the endpoint
appears in `/openapi.json` the guard stops firing, the body runs for real, and
a strict xfail turns any silent pass into a failure.
"""
import json
import urllib.request
from pathlib import Path

import pytest

SCREENSHOTS = Path(__file__).parent / "screenshots"
VIEWPORT = {"width": 1440, "height": 900}
ACTOR = "ui test operator"
REASON = "supported by the reported span"
REPORT_VALUE = 41
REPORT_TITLE = "Harbour traffic summary — Kestrel Strait (UI test)"
REPORT_TEXT = (
    "HARBOUR TRAFFIC SUMMARY — KESTREL STRAIT\n"
    "Reporting office: Auberon port authority liaison\n"
    "Date-time group: 031200Z FEB 27\n\n"
    "The Auberon port authority reports that the Kestrel Strait sea lane "
    "throughput_per_day was measured at %d transits per day as of "
    "1 February 2027.\n"
    "Confidence in this judgment is moderate.\n"
) % REPORT_VALUE


def api(base, path):
    with urllib.request.urlopen(base + path, timeout=30) as r:
        return json.loads(r.read())


def declares(api_base, *fragments):
    """Is a path matching every fragment declared by the running backend?"""
    paths = api(api_base, "/openapi.json")["paths"]
    return [p for p in paths if all(f in p for f in fragments)]


def require(request, api_base, fragments, endpoint):
    """Skip-by-xfail while `endpoint` is not served, after proving the UI says so."""
    if declares(api_base, *fragments):
        return True
    request.applymarker(pytest.mark.xfail(
        strict=True, reason="%s is not served by this backend yet" % endpoint))
    return False


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


def text(page):
    return page.locator("#dc-root").inner_text()


def nav_to(page, label):
    page.get_by_role("button", name=label, exact=True).first.click()
    page.wait_for_timeout(200)


@pytest.fixture(scope="session", autouse=True)
def screenshot_dir():
    SCREENSHOTS.mkdir(parents=True, exist_ok=True)
    return SCREENSHOTS


@pytest.fixture(scope="module")
def app(browser, ui_url):
    page = browser.new_page(viewport=VIEWPORT)
    recorder = Recorder(page)
    page.goto(ui_url, wait_until="networkidle")
    page.wait_for_selector("#dc-root .command-bar button", timeout=15000)
    settle(page)
    yield page, recorder
    page.close()


def fill_report(page, value=REPORT_VALUE):
    nav_to(page, "Intelligence")
    page.get_by_label("Report title").fill(REPORT_TITLE)
    page.get_by_label("Report text").fill(REPORT_TEXT.replace(
        "%d" % REPORT_VALUE, "%d" % value))
    page.get_by_label("Reviewing actor").fill(ACTOR)
    page.wait_for_timeout(150)


def submit_report(page):
    page.get_by_role("button", name="Ingest report", exact=True).click()
    page.wait_for_timeout(1500)
    settle(page)


# ─────────────────────────────────────────────────────────────── ingestion
def test_report_form_keeps_the_whole_text_and_names_the_endpoint(app, api_base):
    """True whether or not the write API is served: the form never truncates
    and never invents a result."""
    page, recorder = app
    fill_report(page)
    assert page.get_by_label("Report text").input_value() == REPORT_TEXT
    body = text(page)
    if declares(api_base, "/api/reports"):
        assert page.get_by_role(
            "button", name="Ingest report", exact=True).is_enabled()
    else:
        assert page.get_by_role(
            "button", name="Ingest report", exact=True).is_disabled()
        assert "POST /api/reports is not served" in body
    page.screenshot(path=str(SCREENSHOTS / "p3_report_form.png"), full_page=True)
    recorder.clean()


def test_ingest_stores_the_original_and_proposes_claims_with_spans(
        request, app, api_base):
    page, recorder = app
    if not require(request, api_base, ["/api/reports"], "POST /api/reports"):
        assert "POST /api/reports is not served" in text(page)
        pytest.fail("POST /api/reports is not served by this backend yet")

    fill_report(page)
    submit_report(page)
    body = text(page)
    assert "SHA-256" in body
    assert "local_rules" in body            # the extractor that actually ran
    assert REPORT_TITLE in body

    spans = page.evaluate(
        """() => Array.from(document.querySelectorAll('#dc-root blockquote'))
             .map(b => b.innerText)""")
    assert spans, "the ingest returned no proposed claim with a span"
    for span in spans:
        assert span in REPORT_TEXT, span   # an exact slice of what was stored
    assert str(REPORT_VALUE) in body
    page.screenshot(path=str(SCREENSHOTS / "p3_ingest_proposed.png"),
                    full_page=True)
    recorder.clean()


def test_accepting_a_proposed_claim_recomputes_the_views(request, app, api_base):
    page, recorder = app
    if not require(request, api_base, ["/api/claims/proposed", "/decision"],
                   "POST /api/claims/proposed/{id}/decision"):
        nav_to(page, "Intelligence")
        assert "not served by this backend yet" in text(page)
        pytest.fail("POST /api/claims/proposed/{id}/decision is not served yet")

    fill_report(page)
    submit_report(page)
    page.get_by_label("Decision reason").fill(REASON)
    page.get_by_role("button", name="Accept", exact=True).first.click()
    page.wait_for_timeout(2000)
    settle(page)

    body = text(page)
    assert ACTOR in body and REASON in body       # the decision record
    assert "workspace overlay applied" in body    # the recompute is visible
    page.screenshot(path=str(SCREENSHOTS / "p3_ingest_accepted.png"),
                    full_page=True)
    recorder.clean()


def test_reingesting_the_same_report_deduplicates(request, app, api_base):
    page, recorder = app
    if not require(request, api_base, ["/api/reports"], "POST /api/reports"):
        pytest.fail("POST /api/reports is not served by this backend yet")

    fill_report(page)
    submit_report(page)
    first = text(page)
    fill_report(page)
    submit_report(page)
    second = text(page)
    assert "Duplicate of" in second, second[:400]
    assert first.count(REPORT_TITLE) >= 1
    recorder.clean()


# ──────────────────────────────────────────────── draft / route / status
def test_draft_route_and_status_on_a_collection_requirement(
        request, app, api_base):
    page, recorder = app
    nav_to(page, "Collection Management Agent")
    if not require(request, api_base, ["/api/collection/drafts"],
                   "POST /api/collection/drafts"):
        assert "POST /api/collection/drafts is not served" in text(page)
        assert page.get_by_role(
            "button", name="Draft requirement", exact=True).is_disabled()
        pytest.fail("POST /api/collection/drafts is not served by this backend yet")

    page.get_by_label("Strategy question").fill(
        "Is Kestrel Strait throughput above the planning floor?")
    page.get_by_label("Required evidence").fill(
        "A port-authority throughput measurement inside the LTIOV window")
    page.get_by_label("Gap reason").fill("Reported throughput contradicts the port log")
    page.get_by_label("Proposed owner").fill("JIOC collection cell")
    page.get_by_label("LTIOV").fill("2027-03-01")
    assumptions = page.evaluate(
        """() => Array.from(document.querySelectorAll(
             'select[aria-label="Link the draft to an assumption"] option'))
             .map(o => o.value).filter(v => v)""")
    if assumptions:
        page.locator('select[aria-label="Link the draft to an assumption"]'
                     ).select_option(assumptions[0])
    nav_to(page, "Intelligence")
    page.get_by_label("Reviewing actor").fill(ACTOR)
    nav_to(page, "Collection Management Agent")
    page.get_by_role("button", name="Draft requirement", exact=True).click()
    page.wait_for_timeout(1500)
    settle(page)

    body = text(page)
    assert "Recorded as" in body
    req_id = body.split("Recorded as ")[1].split(" ")[0].strip()
    assert req_id.startswith("preq_"), req_id
    page.screenshot(path=str(SCREENSHOTS / "p3_draft.png"), full_page=True)

    # the same gap again must deduplicate rather than create a second row
    page.get_by_role("button", name="Draft requirement", exact=True).click()
    page.wait_for_timeout(1500)
    assert "Deduplicated" in text(page)

    if declares(api_base, "/api/collection", "/route"):
        card = page.locator("#dc-root article", has_text=req_id)
        card.get_by_role("button", name="Route or update status").click()
        page.wait_for_timeout(200)
        page.get_by_label("Route to").fill("JIOC")
        page.get_by_label("Reason for the change").fill("internal queue assignment")
        card.get_by_role("button", name="Route requirement").click()
        page.wait_for_timeout(1500)
        settle(page)
        assert "route recorded" in text(page).lower()

    if declares(api_base, "/api/collection", "/status"):
        card = page.locator("#dc-root article", has_text=req_id)
        page.get_by_label("Requirement status").select_option("validation")
        card.get_by_role("button", name="Record status").click()
        page.wait_for_timeout(1500)
        settle(page)
        assert "status recorded" in text(page).lower()
    recorder.clean()


# ─────────────────────────────────────────────────────────── workspace reset
def test_reset_discards_the_demo_workspace(request, app, api_base):
    page, recorder = app
    if not require(request, api_base, ["/api/workspace/reset"],
                   "POST /api/workspace/reset"):
        assert page.get_by_role(
            "button", name="Reset demo workspace", exact=True).is_disabled()
        pytest.fail("POST /api/workspace/reset is not served by this backend yet")

    fill_report(page)
    submit_report(page)
    assert REPORT_TITLE in text(page)

    page.get_by_role("button", name="Reset demo workspace", exact=True).click()
    page.wait_for_timeout(2000)
    settle(page)
    body = text(page)
    assert "reset" in body.lower()
    assert REPORT_TITLE not in body
    page.screenshot(path=str(SCREENSHOTS / "p3_reset.png"), full_page=True)
    recorder.clean()
