# Phase 3 reproduction and audit

Run from a checkout containing the frozen tag and complete benchmark files. Install the project and use the versions in `results/phase3/manifests/freeze.json`. This run uses Python 3.12.10. Set `OPENBLAS_NUM_THREADS=1` and `OMP_NUM_THREADS=1` in the process environment. Windows PowerShell:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:PYTHONDONTWRITEBYTECODE='1'
python -B -m pytest -p no:cacheprovider -q
python -B scripts/phase3.py preflight --output results/phase3_reproduction
python -B scripts/phase3.py freeze --output results/phase3_reproduction
python -B scripts/phase3.py smoke --output results/phase3_reproduction
python -B scripts/phase3.py run --output results/phase3_reproduction
python -B scripts/phase3.py replay --output results/phase3_reproduction
python -B scripts/phase3.py analyze --output results/phase3_reproduction
python -B scripts/phase3.py audit --output results/phase3_reproduction
```

The first two Phase 3 commands assume HEAD is the tagged clean executable commit (not a later results commit). For existing outcomes, use the original immutable manifest bundle with equivalent committed executable files and dependency versions; `replay`, `analyze` and `audit` do not rerun optimization. Use `report` to regenerate the Markdown report/manuscript in the repository's `docs/` directory. Avoid writing reports from a separate replication over the original report files.

`raw/con` contains generated deposited-CON routes. For each profile `raw/<profile>` and `plans/<profile>` contain gzip-compressed JSON batches with up to 24 original routes across all designated methods. Every batch binds to the freeze, source hashes, exact route/method work keys and baseline digest; rows are SHA-256 protected and linked to each ordered plan. Writes are atomic. Restart `run` at the existing output path to resume missing batches without overwriting completed outcome records. Use one driver per output directory. Never manually repair outcome payloads. If replacing a corrupted batch is needed, archive it and disclose the deviation.

The replay command rebuilds routes from the exact serialized stops, checks customer order/ID and physical validity, confirms customer and fleet coverage on CON, checks the B0/B4 topology restriction, repeats all independent validation and stress draws, and verifies selected scenarios against the scalar simulator. Analysis consumes only complete executed/replayed sets; it generates the report source JSON, 400-DPI PNGs and CSV/TeX/Markdown tables together. The audit verifies run coverage, the frozen revision and raw/derived file hashes. TeX tables exceeding 30 rows use `longtable`.

Elapsed seconds depend on scheduling and are not expected to repeat bit-for-bit. The wall guard is cooperative, and route selection can depend on it if it binds. Re-running a frozen optimization is a reproduction, not a new untouched confirmatory experiment.
