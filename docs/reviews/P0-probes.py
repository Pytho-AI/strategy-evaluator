"""Read-only review probes; run from repository root with PYTHONDONTWRITEBYTECODE=1."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from app.backend.adapter import DatasetAdapter
from app.backend.main import create_app
from app.backend.errors import SchemaIncompatible

client = TestClient(create_app(DatasetAdapter()))
for batch in range(4):
    response = client.get('/api/snapshot', params={'batch': batch})
    body = response.json()
    print(json.dumps({
        'batch': batch, 'status': response.status_code, 'load_ms': body.get('load_ms'),
        'blue_ranking': next((r['strategy_ids'] for r in body.get('rankings', [])
                              if r['actor_id'] == 'ent_blue'), None),
    }))
for url in ['/api/claims', '/api/strategies/str_blue_1',
            '/api/strategies/str_does_not_exist']:
    print('GET', url, client.get(url).status_code)

original = Path.read_text
for field in ['value', 'status']:
    def changed(path, *args, **kwargs):
        text = original(path, *args, **kwargs)
        if path.name == 'strategies.json' and path.parent.name == 'schema':
            schema = json.loads(text)
            schema['properties'][field] = {'type': 'object'}
            return json.dumps(schema)
        return text

    with patch.object(Path, 'read_text', changed):
        try:
            DatasetAdapter().check()
            print('SCHEMA TYPE MUTATION', field, 'object: ACCEPTED')
        except SchemaIncompatible as exc:
            print('SCHEMA TYPE MUTATION', field, 'object: REJECTED', exc)
