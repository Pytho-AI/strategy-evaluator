"""P7: public loader, documentation, deterministic archive."""
import hashlib
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'dataset'))


def test_loader_and_package(tmp_path):
    from gen.__main__ import generate
    from dataset.loader import _load_from
    out = tmp_path / 'dataset'
    out.mkdir()
    generate(20260908, out)
    started = time.monotonic()
    data = _load_from(out, base=True, extensions=[], through_batch=2)
    assert time.monotonic() - started < 2.0
    assert 'claims' in data and 'strategies' in data
    req = data['collection_requirements'].set_index('req_id').loc['req_01']
    assert req['status'] == 'satisfaction'
    assert (out / 'DATA_CARD.md').read_text().startswith('# strategy-evaluation-dataset-pytho')
    archive = out / 'strategy-evaluation-dataset-pytho.zip'
    assert archive.exists() and archive.stat().st_size > 1000
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    generate(20260908, out)
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == digest
