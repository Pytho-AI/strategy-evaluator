"""CLI.  python -m gen --seed 20260908           regenerate truth/, corpus/, injects/
        python -m gen schema                    export schema/*.json
        python -m gen check --seed 20260908     run every gate and print gate -> PASS/FAIL
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

DATASET_DIR = Path(__file__).resolve().parents[1]
ROOT = DATASET_DIR.parent
for p in (str(DATASET_DIR), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

DEFAULT_SEED = 20260908


def stages():
    """Ordered generation stages; each is `fn(ctx)` and idempotent."""
    from gen import rps
    out = [("rps", rps.build)]
    try:
        from gen import scaffold, facts, strategies, risk, plan_docs, render, injects  # noqa: F401
        out = [("scaffold", scaffold.build), ("facts", facts.build), ("strategies", strategies.build), ("risk", risk.build),
               ("plan_docs", plan_docs.build), ("render", render.build), ("rps", rps.build), ("injects", injects.build)]
    except ImportError:
        pass
    return out


def generate(seed: int, dataset_dir: Path, only: list[str] | None = None):
    from gen.context import Ctx
    from eval.engine import recompute

    ctx = Ctx(seed=seed, dataset_dir=dataset_dir)
    for name, fn in stages():
        if only and name not in only:
            continue
        fn(ctx)
    # compute every derived column for world version 0 (T0)
    if not getattr(ctx, "computed", False):
        ctx.tables = recompute(ctx.tables, ctx.t0, ctx.world_version)
    ctx.write()
    return ctx


def cmd_schema(_args):
    from gen.export_schema import export
    from gen.schema_md import main as schema_md
    for p in export():
        print(p.relative_to(DATASET_DIR))
    schema_md()


def cmd_generate(args):
    ctx = generate(args.seed, DATASET_DIR, args.stages)
    for name, rows in ctx.tables.items():
        if rows:
            print(f"{name:26s} {len(rows):5d}")
    print(f"docs {len(ctx.docs)}")


def cmd_check(args) -> int:
    from eval.tables import load_dir
    from gen import validate
    from gen.context import T0

    results = []
    tables = load_dir(DATASET_DIR / "truth")
    results.append(validate.schema_load(tables))
    results += validate.run_all(tables, DATASET_DIR, T0, 0)
    # reproducibility: regenerate into a temp dir and compare truth byte-for-byte
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "dataset"
        shutil.copytree(DATASET_DIR, tmp, ignore=shutil.ignore_patterns("truth", "corpus", "injects", "__pycache__", "cache"))
        (tmp / "truth").mkdir()
        generate(args.seed, tmp)
        diffs = []
        for f in sorted((DATASET_DIR / "truth").glob("*.jsonl")):
            g = tmp / "truth" / f.name
            if not g.exists() or not filecmp.cmp(f, g, shallow=False):
                diffs.append(f.name)
        for f in sorted((DATASET_DIR / "corpus").rglob("*")):
            if f.is_file():
                g = tmp / "corpus" / f.relative_to(DATASET_DIR / "corpus")
                if not g.exists() or not filecmp.cmp(f, g, shallow=False):
                    diffs.append(str(f.relative_to(DATASET_DIR)))
        results.append(validate.Result("repro", not diffs, f"regeneration with seed {args.seed} is byte-identical" if not diffs else f"differs: {diffs[:5]}"))
    # extension gates / eval truth-vs-truth are appended by later phases when present
    try:
        from gen import gates_extra
        results += gates_extra.run(DATASET_DIR, tables)
    except ImportError:
        pass
    width = max(len(r.id) for r in results)
    ok = True
    for r in results:
        ok &= r.passed
        print(f"{r.id:<{width}}  {'PASS' if r.passed else 'FAIL'}  {r.detail}")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="gen")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--stages", nargs="*", default=None)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("schema")
    c = sub.add_parser("check")
    c.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = ap.parse_args(argv)
    if args.cmd == "schema":
        cmd_schema(args)
        return 0
    if args.cmd == "check":
        return cmd_check(args)
    cmd_generate(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
