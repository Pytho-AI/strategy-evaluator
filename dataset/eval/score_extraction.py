"""Score extracted claims against the corpus claim gold set."""
from datetime import date
import json
from pathlib import Path


def _day(value):
    return value if isinstance(value, date) else date.fromisoformat(value)


def _same_value(a, b):
    if a.get('object_id') is not None or b.get('object_id') is not None:
        return a.get('object_id') == b.get('object_id')
    x, y = a.get('value'), b.get('value')
    if isinstance(x, (int, float)) and not isinstance(x, bool) and isinstance(y, (int, float)) and not isinstance(y, bool):
        return abs(float(x) - float(y)) <= max(1e-6, .01 * abs(float(y)))
    return x == y


def _matches(predicted, gold):
    try:
        dated = abs((_day(predicted['valid_from']) - _day(gold['valid_from'])).days) <= 3
    except (KeyError, TypeError, ValueError):
        dated = False
    return (predicted.get('subject_id') == gold.get('subject_id') and
            predicted.get('predicate') == gold.get('predicate') and _same_value(predicted, gold) and dated)


def _ratio(n, d):
    return 1.0 if d == 0 else n / d


def _prf(tp, predicted, gold):
    precision = _ratio(tp, predicted)
    recall = _ratio(tp, gold)
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return {'precision': round(precision, 6), 'recall': round(recall, 6), 'f1': round(f1, 6),
            'true_positive': tp, 'predicted': predicted, 'gold': gold}


def score_extraction(predicted, gold, sources=None, dataset_dir=None):
    """Greedy one-to-one match on subject, predicate, value and valid_from within three days."""
    available = set(range(len(gold)))
    pairs = []
    unmatched = []
    for pi, claim in enumerate(predicted):
        candidates = [gi for gi in available if _matches(claim, gold[gi])]
        hit = min(candidates, key=lambda gi: (gold[gi].get('source_id') != claim.get('source_id'), gi)) if candidates else None
        if hit is None:
            unmatched.append(pi)
        else:
            available.remove(hit)
            pairs.append((pi, hit))
    predicates = sorted({c.get('predicate') for c in predicted + gold if c.get('predicate')})
    per_predicate = {}
    for predicate in predicates:
        pp = sum(c.get('predicate') == predicate for c in predicted)
        gg = sum(c.get('predicate') == predicate for c in gold)
        tp = sum(predicted[pi].get('predicate') == predicate for pi, _ in pairs)
        per_predicate[predicate] = _prf(tp, pp, gg)

    def accuracy(select, compare):
        relevant = [(predicted[pi], gold[gi]) for pi, gi in pairs if select(gold[gi])]
        return round(_ratio(sum(compare(p, g) for p, g in relevant), len([g for g in gold if select(g)])), 6)

    supersession = accuracy(lambda g: bool(g.get('supersedes_claim_id')) or g.get('status') == 'superseded',
        lambda p, g: bool(p.get('supersedes_claim_id')) == bool(g.get('supersedes_claim_id')) and p.get('status') == g.get('status'))
    src = {s['source_id']: s for s in sources or []}
    stale_ids = {s['source_id'] for s in sources or [] if 'stale_echo' in s.get('perturbations', [])}
    stale = accuracy(lambda g: g.get('source_id') in stale_ids and g.get('status') == 'superseded',
        lambda p, g: p.get('valid_from') == g.get('valid_from') and p.get('valid_to') == g.get('valid_to'))
    icd = accuracy(lambda g: g.get('estimative'), lambda p, g: p.get('likelihood_icd203') == g.get('likelihood_icd203'))
    confidence = accuracy(lambda g: True, lambda p, g: p.get('confidence_icd203') == g.get('confidence_icd203'))
    sourcing_values = []
    if dataset_dir is not None and sources:
        root = Path(dataset_dir)
        texts = {}
        for pi, gi in pairs:
            g = gold[gi]
            s = src.get(g.get('source_id'))
            if not s or s['doc_type'] not in ('assessment', 'reference_entry'):
                continue
            text = texts.setdefault(s['path'], (root / s['path']).read_text())
            start = predicted[pi].get('span_start', 0)
            end = predicted[pi].get('span_end', 0)
            line_end = text.find('\n', end)
            sourcing_values.append(f"[src: {s['source_id']}]" in text[start:line_end if line_end >= 0 else len(text)])
    distractor_ids = {s['source_id'] for s in sources or [] if 'distractor' in s.get('perturbations', [])}
    distractor_predictions = [predicted[i] for i in unmatched if predicted[i].get('source_id') in distractor_ids]
    return {
        'overall': _prf(len(pairs), len(predicted), len(gold)), 'per_predicate': per_predicate,
        'supersession_accuracy': supersession, 'stale_echo_accuracy': stale,
        'icd_term_accuracy': icd, 'confidence_level_accuracy': confidence,
        'sourcing_bracket_presence': round(_ratio(sum(sourcing_values), len(sourcing_values)), 6),
        'distractor_false_positive_rate': round(_ratio(len(distractor_predictions), max(1, len(predicted))), 6),
    }


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('predicted')
    parser.add_argument('--dataset', default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args(argv)
    root = Path(args.dataset)
    read = lambda p: [json.loads(line) for line in Path(p).read_text().splitlines() if line.strip()]
    result = score_extraction(read(args.predicted), read(root / 'truth/claims.jsonl'), read(root / 'truth/sources.jsonl'), root)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
