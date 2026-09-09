"""Product-owned state: ingestion, review, collection workflow, tracked planning objects.

Nothing in this package reads ``dataset/truth/claims.jsonl``, ``dataset/truth/facts.jsonl``
or ``dataset/injects/*/manifest.json``. The extractor reads no file at all; the store writes
only under the workspace directory.
"""
