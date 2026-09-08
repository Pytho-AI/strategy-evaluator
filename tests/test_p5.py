"""P5: three timed inject batches and effects computed from claim states."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dataset'))


def test_inject_manifests_and_demo_beats(tmp_path):
    from gen.__main__ import generate
    from gen.models import Manifest
    out = tmp_path / 'dataset'
    out.mkdir()
    ctx = generate(20260908, out)
    manifests = []
    for batch in (1, 2, 3):
        path = out / 'injects' / f'batch_{batch}' / 'manifest.json'
        manifest = Manifest.model_validate(json.loads(path.read_text())).model_dump(mode='json', by_alias=True)
        assert 6 <= len(manifest['docs']) <= 10
        manifests.append(manifest)
    one, two, three = manifests
    assert one['expected_effects']['ranking_before'] != one['expected_effects']['ranking_after']
    assert any(x['strategy_id'] == 'str_blue_1' and x['test'] == 'acceptable'
               and x['before'] and not x['after'] for x in one['expected_effects']['validity_changed'])
    assert 'req_01' in two['expected_effects']['requirements_closed']
    assert any(x['assumption_id'].endswith('_k2') and x['from'] == 'unknown' and x['to'] == 'holds'
               for x in two['expected_effects']['assumptions_changed'])
    assert any(x['he_id'] == 'he_05' and x['level_after'] == 'significant'
               for x in three['expected_effects']['risk_assessments_changed'])
    assert any(x['problem_set_id'] == 'ps_energy' for x in three['expected_effects']['problem_sets_moved'])
    contradiction = [c for c in ctx.tables['claims'] if c['status'] == 'proposed'
                     and c['subject_id'] == 'inf_kestrel_lane' and c['value'] == 60]
    assert len(contradiction) == 1
