"""Render inject claims and compute all manifest effects from before/after world states."""
from copy import deepcopy
from datetime import date
import json

from eval.engine import recompute, ranking
from gen import scenario_data as S
from gen.models import Manifest
from gen.render_common import product_header, product_footer, fmt_date, fmt_dtg, locate_span

ICD = {
    'almost_no_chance': 'almost no chance', 'very_unlikely': 'very unlikely',
    'unlikely': 'unlikely', 'roughly_even_chance': 'roughly even chance',
    'likely': 'likely', 'very_likely': 'very likely', 'almost_certain': 'almost certain',
}


def _value(ctx, fact):
    if fact.get('object_id'):
        return ctx.get('entities', entity_id=fact['object_id'])['canonical_name']
    if isinstance(fact['value'], bool):
        return 'true' if fact['value'] else 'false'
    return str(fact['value'])


def _render_fact(ctx, fact, source_id, published):
    subject = ctx.get('entities', entity_id=fact['subject_id'])['canonical_name']
    label = fact['predicate'].replace('_', ' ')
    value = _value(ctx, fact)
    if fact['estimative']:
        sentence = f"We assess it is {ICD[fact['likelihood_icd203']]} that {subject}'s {label} is {value}. [src: {source_id}]"
        lines = [f"Assessment Update: {subject}",
                 f"1. Purpose. Record the assessment issued {fmt_date(published)}.",
                 f"2. Judgment. {sentence}",
                 f"3. Confidence. Confidence is {fact['confidence_icd203'].title()}.",
                 f"4. Sources. {source_id}: reliability B, credibility 2."]
        return 'assessment', sentence, product_header() + '\n'.join(lines) + '\n' + product_footer([])
    sentence = f"{subject}'s reported {label} is {value}, valid from {fmt_date(date.fromisoformat(fact['valid_from']))}."
    lines = [f"Date-time group: {fmt_dtg(published, '1200')}", 'From: reporting element',
             'To: the supported combatant command', f"Subject: {subject} update", f"1. {sentence}"]
    return 'message_traffic', sentence, product_header() + '\n'.join(lines) + '\n' + product_footer([])


def _add_fact_doc(ctx, fact, batch):
    source_id = ctx.next_id('src')
    published = ctx.day(S.BATCH_DAYS[batch])
    doc_type, sentence, text = _render_fact(ctx, fact, source_id, published)
    rel = f'injects/batch_{batch}/{doc_type}_{source_id[4:]}.md'
    sha = ctx.add_doc(rel, text)
    reliability = 'B' if batch < 3 or fact['subject_id'] == 'ent_varenia' else 'C'
    ctx.add('sources', dict(source_id=source_id, doc_type=doc_type,
        title=f"Inject update: {fact['subject_id']} {fact['predicate']}", published_at=published,
        author_org='the supported combatant command J-2', reliability=reliability,
        credibility='2' if reliability == 'B' else '3', real_world=False, path=rel, batch=batch,
        text_sha256=sha, perturbations=['paraphrase', 'alias']))
    previous = None
    if fact.get('supersedes_fact_id'):
        old = ctx.get('facts', fact_id=fact['supersedes_fact_id'])
        old_claims = [c for c in ctx.tables['claims'] if c.get('truth_claim_id') == old['fact_id']]
        for claim in old_claims:
            claim['valid_to'] = old['valid_to']
        previous = old_claims[0]['claim_id'] if old_claims else None
    start, end = locate_span(text, sentence)
    copied = {k: fact.get(k) for k in ('subject_id', 'predicate', 'object_id', 'value', 'value_type', 'unit',
              'valid_from', 'valid_to', 'estimative', 'likelihood_icd203', 'confidence_icd203', 'confidence')}
    ctx.add('claims', dict(claim_id=ctx.next_id('clm'), source_id=source_id, span_start=start,
        span_end=end, asserted_at=published, likelihood_surface_term=ICD.get(fact.get('likelihood_icd203')),
        status='approved', supersedes_claim_id=previous, truth_claim_id=fact['fact_id'], **copied))
    return source_id


def _add_contradiction(ctx):
    spec = S.CONTRADICTION
    source_id = ctx.next_id('src')
    published = ctx.day(spec['asserted_day'])
    subject = ctx.get('entities', entity_id=spec['subject'])['canonical_name']
    sentence = f"{subject} has a reported throughput per day of {spec['false_value']}."
    lines = ['Shipping report questions strait capacity', f"Lisenne, {fmt_date(published)} — Meridian Wire Service.", sentence]
    text = product_header() + '\n'.join(lines) + '\n' + product_footer([])
    rel = f'injects/batch_3/news_{source_id[4:]}.md'
    sha = ctx.add_doc(rel, text)
    ctx.add('sources', dict(source_id=source_id, doc_type='news', title=lines[0], published_at=published,
        author_org='Meridian Wire Service', reliability='D', credibility='4', real_world=False,
        path=rel, batch=3, text_sha256=sha, perturbations=['contradiction', 'paraphrase']))
    start, end = locate_span(text, sentence)
    ctx.add('claims', dict(claim_id=ctx.next_id('clm'), subject_id=spec['subject'], predicate=spec['predicate'],
        value=spec['false_value'], value_type='number', unit='transits/day', source_id=source_id,
        span_start=start, span_end=end, asserted_at=published, valid_from=published, estimative=False,
        confidence_icd203='low', confidence=.8055, status='proposed'))
    return source_id


def _state(ctx, as_of, version, basing_source):
    tables = deepcopy(ctx.tables)
    if as_of >= ctx.day(S.BATCH_DAYS[2]):
        req = next(r for r in tables['collection_requirements'] if r['req_id'] == 'req_01')
        req['status'] = 'satisfaction'
        req['answered_by_source_id'] = basing_source
    return recompute(tables, as_of, version)


def _effects(before, after):
    amap = lambda t: {a['assumption_id']: a for a in t['assumptions']}
    smap = lambda t: {s['strategy_id']: s for s in t['strategies']}
    rmap = lambda t: {(r['he_id'], r['jsps_horizon']): r for r in t['risk_assessments']}
    pmap = lambda t: {(r['problem_set_id'], r['jsps_horizon']): r for r in t['problem_set_assessments']}
    qmap = lambda t: {r['req_id']: r for r in t['collection_requirements']}
    aa, ab = amap(before), amap(after)
    sa, sb = smap(before), smap(after)
    ra, rb = rmap(before), rmap(after)
    pa, pb = pmap(before), pmap(after)
    qa, qb = qmap(before), qmap(after)
    assumptions = [dict(assumption_id=k, **{'from': aa[k]['status'], 'to': ab[k]['status']})
                   for k in aa.keys() & ab.keys() if aa[k]['status'] != ab[k]['status']]
    restated = [dict(strategy_id=k, value_before=sa[k]['value'], value_after=sb[k]['value'],
                     status_before=sa[k]['status'], status_after=sb[k]['status'])
                for k in sa.keys() & sb.keys() if (sa[k]['value'], sa[k]['status']) != (sb[k]['value'], sb[k]['status'])]
    risks = [dict(he_id=k[0], horizon=k[1], level_before=ra[k]['risk_level'], level_after=rb[k]['risk_level'],
                  trend_after=rb[k]['trend'], p_before=ra[k]['p_raw'], p_after=rb[k]['p_raw'])
             for k in ra.keys() & rb.keys() if (ra[k]['risk_level'], ra[k]['trend'], ra[k]['p_raw']) !=
             (rb[k]['risk_level'], rb[k]['trend'], rb[k]['p_raw'])]
    problems = [dict(problem_set_id=k[0], jsps_horizon=k[1], level_before=pa[k]['max_risk_level'],
                     level_after=pb[k]['max_risk_level']) for k in pa.keys() & pb.keys()
                if pa[k]['max_risk_level'] != pb[k]['max_risk_level']]
    validity = [dict(strategy_id=k, test=test, before=sa[k]['validity'][test]['pass'],
                     after=sb[k]['validity'][test]['pass']) for k in sa.keys() & sb.keys()
                for test in sa[k]['validity'] if sa[k]['validity'][test]['pass'] != sb[k]['validity'][test]['pass']]
    jipcl = [dict(req_id=k, rank_before=qa[k]['jipcl_rank'], rank_after=qb[k]['jipcl_rank'],
                  status_before=qa[k]['status'], status_after=qb[k]['status'])
             for k in qa.keys() & qb.keys() if (qa[k]['jipcl_rank'], qa[k]['status']) !=
             (qb[k]['jipcl_rank'], qb[k]['status'])]
    return dict(assumptions_changed=assumptions, strategies_restated=restated,
        ranking_before=ranking(before, 'meridian', 'ent_blue'), ranking_after=ranking(after, 'meridian', 'ent_blue'),
        requirements_closed=[k for k in qa.keys() & qb.keys() if qa[k]['status'] not in ('satisfaction', 'closed') and qb[k]['status'] in ('satisfaction', 'closed')],
        problem_sets_moved=problems, risk_assessments_changed=risks, validity_changed=validity, jipcl_changed=jipcl)


def build(ctx):
    docs = {1: [], 2: [], 3: []}
    basing_source = None
    for batch in (1, 2, 3):
        for fact in [f for f in ctx.tables['facts'] if f['first_asserted_batch'] == batch]:
            source = _add_fact_doc(ctx, fact, batch)
            docs[batch].append(source)
            if (fact['subject_id'], fact['predicate']) == ('ent_corvane', 'basing_access'):
                basing_source = source
    docs[3].append(_add_contradiction(ctx))
    ctx.add('collection_requirements', dict(req_id='req_07', pir_id='pir_01',
        eei='What is the current throughput of the Kestrel Strait sea lane?',
        indicators=['Port logs disagree with news reporting'], sir='Resolve the conflicting throughput reports.',
        gap_type='contradiction', subject_id='inf_kestrel_lane', predicate='throughput_per_day',
        rfi_disposition='gap_confirmed', routing='JIOC', ltiov=ctx.day(80), created_at=ctx.day(68), status='validation'))
    dates = [ctx.t0] + [ctx.day(S.BATCH_DAYS[b]) for b in (1, 2, 3)]
    states = [_state(ctx, d, i, basing_source) for i, d in enumerate(dates)]
    facts = {f['fact_id']: f for f in ctx.tables['facts']}
    for batch in (1, 2, 3):
        changes = []
        for f in [x for x in ctx.tables['facts'] if x['first_asserted_batch'] == batch]:
            old = facts.get(f.get('supersedes_fact_id'))
            changes.append(dict(fact_id_old=old['fact_id'] if old else None, fact_id_new=f['fact_id'],
                subject_id=f['subject_id'], predicate=f['predicate'],
                old_value=(old.get('object_id') or old.get('value')) if old else None,
                new_value=f.get('object_id') or f.get('value')))
        data = dict(batch=batch, as_of=dates[batch], docs=docs[batch], change_events=changes,
                    expected_effects=_effects(states[batch - 1], states[batch]))
        manifest = Manifest.model_validate(data).model_dump(mode='json', by_alias=True)
        ctx.add_doc(f'injects/batch_{batch}/manifest.json', json.dumps(manifest, sort_keys=True, indent=2) + '\n')
