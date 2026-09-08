"""Stage 4: render documents from truth (template backend, deterministic) and write claims with
character spans. An optional LLM backend (`--llm`, ANTHROPIC_API_KEY) is cached under gen/cache/ and
must return the same evidence sentences; it is not used for the shipped corpus (see DATA_CARD.md).

Every rendered product obeys gen/styles/*.md: markings, CJCS paragraph scheme, DD Month YYYY dates
(date-time groups in message traffic and situation reports), ICD 203 vocabulary in intelligence
products with confidence in a separate sentence, [src: id] brackets, acronyms spelled out at first
use and listed in a closing glossary.
"""
from __future__ import annotations

import re
from datetime import date

import yaml

from gen import scenario_data as S
from gen.context import Ctx
from gen.plan_docs import DocPlan
from gen.render_common import CAVEAT, fmt_date, fmt_dtg, locate_span, product_footer, product_header

ACRONYMS = {k: v for k, v in yaml.safe_load((__import__("pathlib").Path(__file__).resolve().parent / "styles" / "acronyms.yml").read_text())["acronyms"].items()}
ACRO_TOKEN = re.compile(r"(?<![\w/])([A-Z][A-Za-z0-9&/\-\.\(\)]*[A-Z0-9\)])(?![\w/])")

ICD_TERM = {"almost_no_chance": "almost no chance", "very_unlikely": "very unlikely", "unlikely": "unlikely", "roughly_even_chance": "a roughly even chance",
            "likely": "likely", "very_likely": "very likely", "almost_certain": "almost certain"}
HEDGE = {"likely": "probable", "very_likely": "highly probable", "unlikely": "improbable", "very_unlikely": "highly improbable", "almost_certain": "nearly certain",
         "roughly_even_chance": "roughly even odds", "almost_no_chance": "remote"}
POSTURE_WORDS = {"hardened": "hardened", "postured_to_react": "postured to react", "mitigated": "covered by rehearsed mitigations",
                 "vulnerable": "highly vulnerable", "out_of_position": "out of position", "unmitigated": "without rehearsed mitigations"}
ALIGN_WORDS = {"blue_aligned": "aligned with Blue", "neutral": "neutral", "red_aligned": "aligned with Varenia"}
COUNT_NOUN = {"sys_dorne_asm": "launchers", "sys_serath_lrs": "missiles", "sys_talon_frigate": "hulls", "sys_sable_submarine": "hulls", "sys_kite_uav": "airframes",
              "sys_varen_strike_ac": "airframes", "sys_vigil_frigate": "hulls", "sys_halyard_sam": "fire units", "sys_skylark_strike": "airframes",
              "sys_meridian_standoff_munition": "rounds", "sys_gull_patrol_boat": "boats", "sys_lark_isr_uav": "airframes"}
THROUGHPUT_NOUN = {"inf_kestrel_lane": "transits", "inf_southern_passage": "transits", "inf_auberon_halden_airbridge": "sorties", "inf_ilmara_coastal_road": "vehicles"}
DISTRACTORS = [
    "The commanding officer briefed visiting reporters at the pier on the morning of the report.",
    "Sea state was three with visibility near eight kilometres for most of the period.",
    "The terminal operator scheduled a maintenance window for the last week of the month.",
    "A delegation from the Corvane assembly toured the field and met the airfield manager.",
    "Fuel prices in Lisenne rose four percent in August according to the finance ministry.",
    "The harbour master reported two fishing vessels overdue after the storm of the previous week.",
    "Local contractors completed resurfacing of the access road to the gate.",
    "A cultural festival in Lisenne drew crowds to the waterfront over the weekend.",
    "The chaplain's office announced a memorial service for the following Friday.",
    "The band of the coastal division played at the harbour ceremony.",
    "Rainfall for the month was twice the seasonal average across the western shore.",
    "The library at the base extended its opening hours for the deployment.",
]


class Namer:
    def __init__(self, ctx: Ctx):
        self.ent = {e["entity_id"]: e for e in ctx.tables["entities"]}

    def name(self, eid: str, alias: bool = False, rng=None) -> str:
        e = self.ent[eid]
        if alias and e.get("aliases"):
            return e["aliases"][rng.randrange(len(e["aliases"]))] if rng else e["aliases"][0]
        return e["canonical_name"]


def fmt_num(v) -> str:
    if isinstance(v, float) and not float(v).is_integer():
        return f"{v:g}"
    return f"{int(v):,}" if abs(float(v)) >= 1000 else f"{int(v)}"


def value_phrase(f: dict, drift: int, nm: Namer) -> str:
    p, v, s = f["predicate"], f["value"], f["subject_id"]
    if p == "range_km":
        if drift == 1:
            return f"{round(v / 1.852)} nautical miles"
        if drift == 2:
            return f"roughly {round(v / 1.609 / 5) * 5} miles"
        return f"{fmt_num(v)} km"
    if p == "count":
        return f"{fmt_num(v)} {COUNT_NOUN.get(s, 'items')}"
    if p == "readiness":
        return f"{round(v * 100)} percent"
    if p == "throughput_per_day":
        return f"{fmt_num(v)} {THROUGHPUT_NOUN.get(s, 'movements')} per day"
    if p == "capacity_mw":
        return f"{fmt_num(v)} megawatts"
    if p == "munitions_stock_days":
        return f"{fmt_num(v)} days of supply"
    if p == "mobilization_days":
        return f"{fmt_num(v)} days"
    if p == "displaced_persons":
        return f"{fmt_num(v)} displaced persons"
    if p == "outage_hours":
        return f"{fmt_num(v)} hours of outage"
    if p == "mobilized_brigades":
        return f"{fmt_num(v)} brigades"
    return str(v)


def clause(f: dict, nm: Namer, variant: int, alias: bool, drift: int, implicit: bool, rng, published: date, future: bool) -> str:
    """The propositional clause (no final period) for a fact; variant selects paraphrase."""
    S_ = nm.name(f["subject_id"], alias, rng)
    p, v = f["predicate"], f["value"]
    O = nm.name(f["object_id"], alias, rng) if f.get("object_id") else None
    V = value_phrase(f, drift, nm)
    if p == "range_km":
        forms = [f"{S_} has a maximum range of {V}", f"the stated reach of {S_} is {V}", f"{S_} can engage targets out to {V}"]
    elif p == "count":
        forms = [f"{S_} numbers {V}", f"holdings of {S_} stand at {V}", f"the inventory of {S_} is {V}"]
        if future:
            forms = [f"{S_} will number {V}", f"holdings of {S_} will reach {V}"]
    elif p == "readiness":
        forms = [f"{S_} reports readiness at {V}", f"readiness of {S_} stands at {V}", f"{S_} is at {V} readiness"]
    elif p == "status":
        forms = [f"{S_} is {v}", f"{S_} remains {v}", f"the status of {S_} is {v}"]
    elif p == "throughput_per_day":
        forms = [f"{S_} carried {V}", f"daily throughput of {S_} is {V}", f"{S_} handles {V}"]
    elif p == "alignment":
        forms = [f"{S_} is {ALIGN_WORDS[v]}", f"the alignment of {S_} is {ALIGN_WORDS[v]}"]
    elif p == "basing_access":
        forms = [f"{S_} grants Blue basing access" if v else f"{S_} does not grant Blue basing access"]
    elif p == "mobilization_days":
        forms = [f"{S_} would need {V} to mobilize two brigades", f"mobilizing two brigades would take {S_} {V}"]
    elif p == "mobilized_brigades":
        forms = [f"{S_} has {V} mobilized", f"the number of brigades {S_} has mobilized is {fmt_num(v)}"]
    elif p == "cyber_capacity":
        forms = [f"the cyber capacity of {S_} against Blue logistics networks is {v}", f"{S_} has {v} cyber capacity against Blue logistics networks"]
    elif p == "munitions_stock_days":
        forms = [f"{S_} holds {V} of precision munitions", f"precision munitions held by {S_} amount to {V}"]
    elif p == "posture_state":
        forms = [f"{S_} is {POSTURE_WORDS[v]}", f"the posture of {S_} is {POSTURE_WORDS[v]}"]
    elif p == "capacity_mw":
        forms = [f"{S_} has a generating capacity of {V}", f"the generating capacity of {S_} is {V}"]
    elif p == "displaced_persons":
        forms = [f"{S_} counts {V}", f"the number of displaced persons recorded by {S_} is {fmt_num(v)}"]
    elif p == "outage_hours":
        forms = [f"{S_} recorded {V} in the period", f"outage at {S_} totalled {V}"]
    elif p == "intent":
        forms = [f"the intent of {S_} toward Ilmara is {v}", f"{S_} shows {v} intent toward Ilmara"]
    elif p == "located_at":
        forms = [f"{S_} is located at {O}", f"{S_} is at {O}", f"{S_} operates from {O}"]
        if implicit:
            forms = [f"{S_} relocated to {O} alongside its escort", f"{S_} now operates from {O} with its supporting elements"]
    elif p == "operated_by":
        forms = [f"{S_} is operated by {O}", f"{O} operates {S_}"]
    elif p == "subordinate_to":
        forms = [f"{S_} is subordinate to {O}", f"{S_} reports to {O}"]
        if implicit:
            forms = [f"{S_} moved with the rest of {O}"]
    elif p == "supplies":
        forms = [f"{S_} supplies {O}", f"{O} is supplied by {S_}"]
    elif p == "controls":
        forms = [f"{S_} controls {O}", f"{S_} retains control of {O}"]
    elif p == "hosts":
        forms = [f"{S_} hosts {O}", f"{O} is hosted at {S_}"]
    else:
        forms = [f"{S_} {p} {v if v is not None else O}"]
    return forms[variant % len(forms)]


def date_cue(f: dict, published: date, future: bool, baseline: date | None = None) -> str:
    """Validity cue. Extraction convention: a claim's valid_from is the document's stated baseline
    date unless the sentence carries its own 'as of' cue; without either it is the publication date."""
    vf = date.fromisoformat(f["valid_from"])
    if future:
        return f" by {fmt_date(vf)}"
    if abs((published - vf).days) <= 3:
        return ""
    if baseline is not None and abs((baseline - vf).days) <= 3:
        return ""
    return f" as of {fmt_date(vf)}"


def cap(s: str) -> str:
    return s[0].upper() + s[1:]


def fact_sentence(f: dict, nm: Namer, plan: DocPlan, rng, published: date, variant: int, baseline: date | None = None) -> tuple[str, str | None, str | None]:
    """Returns (sentence, surface_likelihood_term, confidence_sentence)."""
    alias = "alias" in plan.perturbations and rng.random() < 0.5
    drift = rng.choice([1, 2]) if ("unit_drift" in plan.perturbations and f["predicate"] == "range_km" and rng.random() < 0.7) else 0
    implicit = "implicit" in plan.perturbations and f["predicate"] in ("located_at", "subordinate_to") and rng.random() < 0.5
    future = f["valid_from"] > published.isoformat()
    c = clause(f, nm, variant, alias, drift, implicit, rng, published, future)
    cue = date_cue(f, published, future, baseline)
    if f["estimative"]:
        term = ICD_TERM[f["likelihood_icd203"]]
        surface = None
        if "hedge_drift" in plan.perturbations and plan.doc_type in ("news", "sitrep", "message_traffic"):
            surface = HEDGE[f["likelihood_icd203"]]
            sent = f"It is {surface} that {c}{cue}."
        else:
            sent = f"It is {term} that {c}{cue}."
        conf = f"Confidence in this judgment is {f['confidence_icd203']}."
        return sent, surface, conf
    return cap(c) + cue + ".", None, None


def echo_sentence(f: dict, nm: Namer, rng, asserted: date) -> str:
    c = clause(f, nm, 0, False, 0, False, rng, asserted, False)
    tail = ""
    if f.get("valid_to"):
        tail = f", an estimate valid through {fmt_date(date.fromisoformat(f['valid_to']))}"
    if f["estimative"]:
        return f"A report dated {fmt_date(asserted)} judged it {ICD_TERM[f['likelihood_icd203']]} that {c}{tail}."
    return f"A report dated {fmt_date(asserted)} put it that {c}{tail}."


class Expander:
    """Stateful first-use acronym expansion: 'expansion (ACR)' the first time an acronym appears in
    the document, plain acronym afterwards. Sentences are expanded at emit time so recorded evidence
    spans equal the rendered text."""

    def __init__(self):
        self.seen: list[str] = []
        self.prior = ""

    def expand(self, text: str) -> str:
        def repl(m):
            tok = m.group(1)
            core = tok[:-1] if tok.endswith("s") and tok[:-1] in ACRONYMS else tok
            if core not in ACRONYMS:
                return tok
            if core in self.seen:
                return tok
            self.seen.append(core)
            exps = ACRONYMS[core].get("expansions") or [ACRONYMS[core]["expansion"]]
            if any(e.lower() in (self.prior + text[: m.start()]).lower() for e in exps):
                return tok
            return f"{exps[0]} ({tok})"
        out = ACRO_TOKEN.sub(repl, text)
        self.prior += out + "\n"
        return out


def apply_typos(text: str, rng, protected: list[str], rate: float = 0.003) -> str:
    """Character-level noise outside the protected evidence sentences."""
    n = max(1, round(len(text) * rate))
    spans = [(m.start(), m.end()) for p in protected for m in [re.search(re.escape(p), text)] if m]
    chars = list(text)
    tries = 0
    while n > 0 and tries < 200:
        tries += 1
        i = rng.randrange(len(chars))
        if not chars[i].isalpha() or any(a <= i < b for a, b in spans):
            continue
        j = i + 1
        if j < len(chars) and chars[j].isalpha() and not any(a <= j < b for a, b in spans):
            chars[i], chars[j] = chars[j], chars[i]
        else:
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if chars[i].isupper() else "abcdefghijklmnopqrstuvwxyz"
            chars[i] = alphabet[(alphabet.index(chars[i]) + 1) % len(alphabet)]
        n -= 1
    return "".join(chars)


# ---------------------------------------------------------------- document composers
def compose(plan: DocPlan, ctx: Ctx, nm: Namer, rng) -> tuple[str, list[dict]]:
    """Returns (text, evidence) where evidence rows are {fact_id, sentence, asserted, status, surface, echo}."""
    fact = {f["fact_id"]: f for f in ctx.tables["facts"]}
    published = ctx.day(plan.published_day)
    evidence: list[dict] = []
    sents: list[str] = []
    protected: list[str] = []
    variant_base = rng.randrange(3)
    facts = [fact[i] for i in plan.facts]
    ax = Expander()
    X = ax.expand if plan.doc_type != "tabular" else (lambda t: t)
    src_tag = f" [src: {plan.doc_id}]" if plan.doc_type in ("reference_entry", "assessment") else ""
    # document baseline date: the most common valid_from among the current facts (directive products state it)
    baseline = None
    if plan.doc_type in ("reference_entry", "assessment", "sitrep") and facts:
        from collections import Counter
        vf = Counter(f["valid_from"] for f in facts if f["valid_from"] <= published.isoformat())
        if vf:
            baseline = date.fromisoformat(vf.most_common(1)[0][0])

    def emit(f, i):
        s, surface, conf = fact_sentence(f, nm, plan, rng, published, variant_base + i if "paraphrase" in plan.perturbations else variant_base, baseline)
        s = X(s)
        evidence.append({"fact_id": f["fact_id"], "sentence": s, "asserted": published, "status": "approved", "surface": surface, "echo": False})
        protected.append(s)
        return s + src_tag + ((" " + conf) if conf else "")

    def emit_echo(f):
        asserted = date.fromisoformat(f["valid_from"]) + (date.fromisoformat(f["valid_to"]) - date.fromisoformat(f["valid_from"])) / 2 if f.get("valid_to") else published
        s = X(echo_sentence(f, nm, rng, asserted))
        evidence.append({"fact_id": f["fact_id"], "sentence": s, "asserted": asserted, "status": "superseded", "surface": None, "echo": True})
        protected.append(s)
        return s + src_tag

    def emit_proposed(pr):
        s = X(cap(pr["text"]) + ".")
        evidence.append({"fact_id": None, "sentence": s, "asserted": published, "status": "proposed", "surface": None, "echo": False, "proposed": pr})
        protected.append(s)
        return s

    distract = "distractor" in plan.perturbations
    d_pool = list(DISTRACTORS)
    rng.shuffle(d_pool)

    def maybe_distractor():
        if distract and d_pool and rng.random() < 0.15:
            return X(d_pool.pop())
        return None

    lines: list[str] = []
    dt = plan.doc_type
    if dt == "reference_entry":
        lines.append(X(f"{plan.title}."))
        lines.append(X(f"1. Identification. Published {fmt_date(published)} by {plan.author_org}. Aliases: {', '.join(nm.ent[plan.focus[0]]['aliases'])}. Unless a sentence states otherwise, facts below have been valid since {fmt_date(baseline or published)}."))
        lines.append("2. Attributes.")
        letters = "abcdefghijklmnopqrstuvwxyz"
        k = 0
        for i, f in enumerate(facts):
            if f["estimative"]:
                continue
            lines.append(f"{letters[k % 26]}. {emit(f, i)}")
            k += 1
            d = maybe_distractor()
            if d:
                lines.append(f"{letters[k % 26]}. {d}")
                k += 1
        est = [f for f in facts if f["estimative"]]
        n = 3
        if est:
            lines.append("3. Assessment.")
            for i, f in enumerate(est):
                lines.append(f"{letters[i % 26]}. {emit(f, i)}")
            n = 4
        for f in [fact[i] for i in plan.echo_facts]:
            lines.append(f"{n}. Prior reporting. {emit_echo(f)}")
            n += 1
        lines.append(X(f"{n}. Sources. {plan.doc_id}: reliability {plan.reliability}, credibility {plan.credibility}. Reported facts carry {'high' if plan.reliability in 'AB' else 'moderate'} confidence unless stated."))
    elif dt == "assessment":
        lines.append(X(f"{plan.title}."))
        lines.append(X(f"1. Purpose. This assessment by {plan.author_org}, dated {fmt_date(published)}, addresses {', '.join(nm.name(e) for e in plan.focus)}. Unless a sentence states otherwise, facts below have been valid since {fmt_date(baseline or published)}."))
        lines.append("2. Judgments.")
        letters = "abcdefghijklmnopqrstuvwxyz"
        k = 0
        for i, f in enumerate(facts):
            if not f["estimative"]:
                continue
            lines.append(f"{letters[k % 26]}. {emit(f, i)}")
            k += 1
        if k == 0:
            lines.append("a. No new analytic judgments; see reported facts.")
        lines.append("3. Reported facts.")
        k = 0
        for i, f in enumerate(facts):
            if f["estimative"]:
                continue
            lines.append(f"{letters[k % 26]}. {emit(f, i)}")
            k += 1
        n = 4
        for f in [fact[i] for i in plan.echo_facts]:
            lines.append(f"{n}. Prior reporting. {emit_echo(f)}")
            n += 1
        if "mixed_scale" in plan.perturbations:
            lines.append(f'{n}. Risk note. The analytic likelihood is roughly even chance. There is a "Likely" probability that the situation degrades in the near-term (0-3 years); the risk level is Moderate, trending up.')
            n += 1
        lines.append(X(f"{n}. Sources. {plan.doc_id}: reliability {plan.reliability}, credibility {plan.credibility}. Confidence levels are stated with each judgment."))
    elif dt == "sitrep":
        lines.append(X(f"Situation report, {plan.author_org}, as of {fmt_dtg(published, '0600')}. Unless stated, facts have been valid since {fmt_date(baseline or published)}."))
        lines.append("1. Own forces.")
        own = [f for f in facts if f["subject_id"].startswith("unit_") or f["subject_id"].startswith("sys_")]
        other = [f for f in facts if f not in own]
        for i, f in enumerate(own):
            lines.append(f"a. {emit(f, i)}" if i == 0 else f"{'abcdefghijklmnopqrstuvwxyz'[i % 26]}. {emit(f, i)}")
            d = maybe_distractor()
            if d:
                lines.append(f"{'abcdefghijklmnopqrstuvwxyz'[(i + 1) % 26]}. {d}")
        if other:
            lines.append("2. Situation.")
            for i, f in enumerate(other):
                lines.append(f"{'abcdefghijklmnopqrstuvwxyz'[i % 26]}. {emit(f, i)}")
        for f in [fact[i] for i in plan.echo_facts]:
            lines.append(f"3. Prior reporting. {emit_echo(f)}")
        lines.append("4. Assessment. Nothing further to report.")
    elif dt == "message_traffic":
        lines.append(X(f"Date-time group: {fmt_dtg(published, '1430')}"))
        lines.append(X(f"From: {plan.author_org}"))
        lines.append("To: the supported combatant command")
        lines.append(X(f"Subject: {plan.title}"))
        for i, f in enumerate(facts):
            lines.append(f"{i + 1}. {emit(f, i)}")
    elif dt == "news":
        lines.append(X(f"{plan.title}"))
        lines.append(X(f"Lisenne, {fmt_date(published)} — {plan.author_org}."))
        para: list[str] = []
        for i, f in enumerate(facts):
            para.append(emit(f, i))
            d = maybe_distractor()
            if d:
                para.append(d)
            if len(para) >= 3:
                lines.append(" ".join(para))
                para = []
        for pr in plan.proposed:
            para.append(emit_proposed(pr))
        for f in [fact[i] for i in plan.echo_facts]:
            para.append(emit_echo(f))
        if para:
            lines.append(" ".join(para))
    elif dt == "tabular":
        lines.append("entity,attribute,value,unit,as_of,notes")
        for i, f in enumerate(facts):
            val = nm.name(f["object_id"]) if f.get("object_id") else f["value"]
            note = "alias" if ("alias" in plan.perturbations and rng.random() < 0.2) else ""
            name = nm.name(f["subject_id"], alias=(note == "alias"), rng=rng)
            row = f"{name},{f['predicate']},{val},{f.get('unit') or ''},{f['valid_from']},{note}"
            evidence.append({"fact_id": f["fact_id"], "sentence": row, "asserted": published, "status": "approved", "surface": None, "echo": False})
            protected.append(row)
            lines.append(row)
    else:
        raise ValueError(dt)

    used = ax.seen
    body = "\n".join(lines) + "\n"
    if "typo" in plan.perturbations:
        protected.extend(m.group(0) for m in re.finditer(r"\b\d{6}Z [A-Z]{3} \d{2}\b", body))
        body = apply_typos(body, rng, protected)
    text = product_header() + (plan.title + "\n" if dt == "tabular" else "") + body + product_footer(used)
    return text, evidence


def render_plans(ctx: Ctx, plans: list[DocPlan]) -> None:
    nm = Namer(ctx)
    fact = {f["fact_id"]: f for f in ctx.tables["facts"]}
    for plan in plans:
        rng = __import__("random").Random(f"{ctx.seed}:{plan.doc_id}")
        text, evidence = compose(plan, ctx, nm, rng)
        ext = "csv" if plan.doc_type == "tabular" else "md"
        folder = "corpus" if plan.batch == 0 else f"injects/batch_{plan.batch}"
        rel = f"{folder}/{plan.doc_type}_{plan.doc_id[4:]}.{ext}"
        sha = ctx.add_doc(rel, text)
        ctx.add("sources", {"source_id": plan.doc_id, "doc_type": plan.doc_type, "title": plan.title, "published_at": ctx.day(plan.published_day),
                            "author_org": plan.author_org, "reliability": plan.reliability, "credibility": plan.credibility, "real_world": False,
                            "public_reference": None, "path": rel, "batch": plan.batch, "text_sha256": sha, "perturbations": plan.perturbations})
        for ev in evidence:
            s, e = locate_span(text, ev["sentence"])
            f = fact.get(ev["fact_id"]) if ev["fact_id"] else None
            if f is None:
                pr = ev["proposed"]
                vt = "bool" if isinstance(pr["value"], bool) else ("number" if isinstance(pr["value"], (int, float)) else "string")
                ctx.add("claims", {"claim_id": ctx.next_id("clm"), "subject_id": pr["subject_id"], "predicate": pr["predicate"], "object_id": None, "value": pr["value"],
                                   "value_type": vt, "unit": None, "source_id": plan.doc_id, "span_start": s, "span_end": e, "asserted_at": ev["asserted"],
                                   "valid_from": ev["asserted"], "valid_to": None, "estimative": False, "likelihood_icd203": None, "confidence_icd203": "low",
                                   "confidence": 0.8055, "likelihood_surface_term": None, "status": "proposed", "supersedes_claim_id": None, "truth_claim_id": None})
                continue
            ctx.add("claims", {
                "claim_id": ctx.next_id("clm"), "subject_id": f["subject_id"], "predicate": f["predicate"], "object_id": f.get("object_id"), "value": f.get("value"),
                "value_type": f["value_type"], "unit": f.get("unit"), "source_id": plan.doc_id, "span_start": s, "span_end": e, "asserted_at": ev["asserted"],
                "valid_from": f["valid_from"], "valid_to": f.get("valid_to"),
                "estimative": f["estimative"], "likelihood_icd203": f.get("likelihood_icd203"), "confidence_icd203": f["confidence_icd203"], "confidence": f["confidence"],
                "likelihood_surface_term": ev["surface"] or (ICD_TERM[f["likelihood_icd203"]] if f["estimative"] else None), "status": ev["status"],
                "supersedes_claim_id": None, "truth_claim_id": f["fact_id"],
            })
    # supersession links: a current claim supersedes the echo claims of the fact it replaced
    by_fact: dict[str, list[dict]] = {}
    for c in ctx.tables["claims"]:
        if c.get("truth_claim_id"):
            by_fact.setdefault(c["truth_claim_id"], []).append(c)
    for f in ctx.tables["facts"]:
        old = f.get("supersedes_fact_id")
        if old and old in by_fact and f["fact_id"] in by_fact:
            newest = by_fact[f["fact_id"]][0]
            newest["supersedes_claim_id"] = by_fact[old][0]["claim_id"]
def build(ctx: Ctx) -> None:
    """render_intel stage: T0 intelligence-bearing documents."""
    render_plans(ctx, [p for p in ctx.doc_plans if p.batch == 0 and p.doc_type in ("reference_entry", "sitrep", "news", "message_traffic", "tabular", "assessment")])
