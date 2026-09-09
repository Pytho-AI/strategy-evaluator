"""The build is deterministic and the checked-in truth/ is what it produces."""
from __future__ import annotations

from pathlib import Path


def _files(directory: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(directory.glob("*.jsonl"))}


def test_rebuild_is_byte_identical(build, tmp_path):
    first, second = tmp_path / "a", tmp_path / "b"
    counts_a = build.write(out_dir=first)
    counts_b = build.write(out_dir=second)
    assert counts_a == counts_b
    assert _files(first) == _files(second)


def test_checked_in_truth_matches_a_fresh_build(build, tmp_path):
    fresh = tmp_path / "fresh"
    build.write(out_dir=fresh)
    stale = [name for name, data in _files(fresh).items()
             if (build.TRUTH_DIR / name).read_bytes() != data]
    assert stale == [], (
        f"app/scenarios/amber_shield/truth is out of date for {stale}; "
        "run python -m app.scenarios.amber_shield.build"
    )


def test_truth_rows_round_trip_through_the_loader(build):
    from app.scenarios.amber_shield._dataset import eval_module

    on_disk = eval_module("tables").load_dir(build.TRUTH_DIR)
    computed = build.load()
    assert set(on_disk) == set(computed)
    for name, rows in computed.items():
        assert on_disk[name] == rows, name
