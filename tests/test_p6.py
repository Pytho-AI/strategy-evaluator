"""P6: scoring is perfect on truth and the measured surface baseline is lower."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'dataset'))


def test_scoring_truth_and_baseline(tmp_path):
    from gen.__main__ import generate
    from eval.score_extraction import score_extraction
    from eval.score_effects import score_effects
    from eval.baseline import run_surface_baseline
    out = tmp_path / 'dataset'
    out.mkdir()
    ctx = generate(20260908, out)
    perfect = score_extraction(ctx.tables['claims'], ctx.tables['claims'], ctx.tables['sources'], out)
    assert perfect['overall']['f1'] == 1.0
    assert all(perfect[k] == 1.0 for k in ('supersession_accuracy', 'stale_echo_accuracy',
        'icd_term_accuracy', 'confidence_level_accuracy', 'sourcing_bracket_presence'))
    manifest = json.loads((out / 'injects/batch_3/manifest.json').read_text())
    effects = manifest['expected_effects']
    exact = score_effects(effects, effects)
    assert exact['overall'] == 1.0
    assert exact['strategy_rank_spearman'] == 1.0
    baseline = run_surface_baseline(ctx.tables, out)
    assert baseline['extraction']['overall']['f1'] < .8
    assert baseline['style_compliance'] < .8
