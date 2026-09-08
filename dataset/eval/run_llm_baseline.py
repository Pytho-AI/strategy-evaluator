"""Optional live baseline: one independent, schema-blind model call per document."""
import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--dataset', default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args()
    if not os.environ.get('ANTHROPIC_API_KEY'):
        raise SystemExit('ANTHROPIC_API_KEY is required for the live baseline')
    import anthropic
    root = Path(args.dataset)
    sources = [json.loads(line) for line in (root / 'truth/sources.jsonl').read_text().splitlines()]
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
    output = []
    for source in sources:
        document = (root / source['path']).read_text()
        response = client.messages.create(model=args.model, max_tokens=1200, messages=[{'role': 'user', 'content':
            'Extract the factual statements in this document. Return only a JSON array. Each item needs subject, predicate, value, and quoted evidence. Do not infer dates or use outside context.\n\n' + document}])
        output.append({'source_id': source['source_id'], 'response': response.content[0].text})
    path = root / 'eval/live_baseline_output.json'
    path.write_text(json.dumps(output, indent=2) + '\n')
    print(path)


if __name__ == '__main__':
    main()
