# Phase 6 repository cleanup

The [pre-experiment inventory](../results/phase6/audit/cleanup_inventory.csv) classified tracked archives, local scratch, placeholders and ambiguous dataset checkpoints. The [actions ledger](../results/phase6/audit/cleanup_actions.csv) records measured byte lengths, decisions and after-checks. There were no Git submodules or LFS attributes in scope.

| Disposable folder | Files removed | Bytes removed |
| --- | ---: | ---: |
| `results/phase5_repeat/` | 571 | 40,991,342 |
| `results/phase6_rebuild/` | 769 | 13,418,439 |
| `results/phase6_proofs/` | 5 | 233,036 |
| `results/phase6_tex/` | 4 | 19,307 |
| `results/phase6_con_check/` | 96 | 762,190 |
| **Total** | **1,445** | **55,424,314** |

These are 52.86 MiB of temporary working copies produced or recreated during Phase 6. A previously approved local cleanup also removed archived-output repeats and local generated caches. Its seven empty marker deletions were already visible when Phase 6 began. The markers are absent from frozen manifests. Four other markers remain because separate frozen inventories reference them. The root README and narrow ignore rules now identify the supported scientific workflows.

The five listed scratch directories were checked against an explicit resolved-path allowlist and their tracked-file and reparse-point checks passed. Hash-bound figure review, compiler transcripts, original raw experiments, derived tables, and both exact rebuild reports remain committed. The independent rebuilds verified 123 Phase 5 and 57 Phase 6 derived files. The `phase6_pytest/verified` directory was empty and removed. Windows denied enumeration of three directories from interrupted tests, so their ignored parent `results/phase6_pytest/` remains locally. No destructive escalation was used on those directories. Nine ignored checkpoint files under dataset variants A and B contain unique bytes and were preserved.

The [post-clean audit](../results/phase6/audit/cleanup.json) reverified 4,476 protected tracked inputs, the original tag, and the 96-member Phase 3 archive. The dataset, scientific outputs, original and frozen implementations, manuscript archive and reproducibility inputs are preserved. The Phase 6 supplement includes all validated raw/plan identities in its audit, and ignore checks confirm the required raw output paths remain visible.

Windows reserves the directory name `con`. The archived Phase 3 replay can restore its CON records into a scratch output using the following PowerShell command. A clean test of this command's extended-path extraction restored every member with its archived bytes.

```powershell
$phase3AuditScratch = (Resolve-Path -LiteralPath 'results/phase3_reproduction').ProviderPath
python -m zipfile -e results/phase3/con_bundles.zip ("\\?\" + $phase3AuditScratch)
```

The historical replay directory must also contain the corresponding Phase 3 manifests, reports and raw/plan bundles. Phase 4, Phase 5 and Phase 6 readers open the ZIP directly. Keep the archive tracked and restored `raw/con` copies local.
