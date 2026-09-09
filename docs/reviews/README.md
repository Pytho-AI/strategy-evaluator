# Independent review log

While the product was being built, a second agent ran continuously as an independent
reviewer with a write boundary limited to this directory. It re-ran every gate itself,
reproduced defects with its own probe scripts, and judged whether each acceptance test
actually proved its requirement.

Everything it found is kept here unedited, including the findings that were valid against
us. Four are worth reading as evidence of how the gates were tightened:

| File | What it found |
|---|---|
| [P0-review.md](P0-review.md) | Schema preflight accepted incompatible field types; an unknown-ID test passed only because the route did not exist; a cache test asserted identity rather than immutability. All four were fixed and re-verified (addendum at the top of the file). |
| [P0-validation-output.md](P0-validation-output.md) | Exact command output for every gate it executed, independent of the builder's own runs. |
| [P1-integration-notes.md](P1-integration-notes.md) + [P1-trace-probes.py](P1-trace-probes.py) | Inject claims had no trace path to the assumptions they drive, because the trace walked only frozen edges. The evaluator's own as-of selection now supplies current-evidence links. |
| [P2-integration-notes.md](P2-integration-notes.md) | Overlapping batch loads could leave a stale batch selected. Fixed with a request sequence guard and a delayed-response test. |
| [STEERING.md](STEERING.md) | The reviewer's own running log and priorities. |

The probe scripts are runnable: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python docs/reviews/P1-trace-probes.py`.
