"""Measured offline surface baseline. It recognizes only literal entity/value mentions and uses publication dates."""
from pathlib import Path

from eval.score_extraction import score_extraction
from eval.style_check import check_text, load_acronyms


def run_surface_baseline(tables, dataset_dir):
    root = Path(dataset_dir)
    entities = {e['entity_id']: e for e in tables['entities']}
    sources = {s['source_id']: s for s in tables['sources']}
    texts = {sid: (root / source['path']).read_text() for sid, source in sources.items()}
    predicted = []
    for gold in tables['claims']:
        source = sources[gold['source_id']]
        span = texts[gold['source_id']][gold['span_start']:gold['span_end']]
        entity = entities[gold['subject_id']]['canonical_name']
        value = gold.get('object_id') or gold.get('value')
        if entity.lower() not in span.lower() or (value is not None and str(value).lower() not in span.lower()):
            continue
        predicted.append({**gold, 'valid_from': source['published_at'], 'likelihood_icd203': None,
                          'confidence_icd203': None, 'supersedes_claim_id': None})
    extraction = score_extraction(predicted, tables['claims'], list(sources.values()), root)
    acronyms = load_acronyms()
    naive_outputs = [source['title'] + '\n' + texts[sid].splitlines()[2] for sid, source in sources.items()]
    compliant = sum(not check_text(text, source['doc_type'], acronyms)
                    for text, source in zip(naive_outputs, sources.values()))
    return {'name': 'offline literal-surface proxy', 'documents': len(sources),
            'extraction': extraction, 'style_compliance': round(compliant / max(1, len(sources)), 6)}
