"""Build and package the Prompt-09 four-method conference exhibits from publication inputs."""

import argparse
import os
import sys
import zipfile
from pathlib import Path

for variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from star_evrp.conference_data import inputs_dir
from star_evrp.conference_exhibits import TABLE_STEMS, build
from star_evrp.conference_figures import STEMS
from star_evrp.phase4_results import file_sha, require
from star_evrp.phase6_archive import write_json


def package(root: Path, out: Path, scratch: Path) -> dict:
    require(not scratch.exists(), "Use an empty ZIP proof directory")
    scratch.mkdir(parents=True)
    zip_path = out / "STaR_EVRP_CONFERENCE_EXHIBITS.zip"
    if zip_path.exists():
        zip_path.unlink()
    include = []
    for folder in ("figures", "tables", "data", "audit"):
        base = out / folder
        if base.exists():
            include.extend([p for p in base.rglob("*") if p.is_file()])
    for name in (
        "FIGURE_CAPTIONS.md", "TABLE_NOTES.md", "METHOD_GLOSSARY.md", "CLAIMS_AND_LIMITATIONS.md",
        "ARCHIVAL_EVIDENCE.md", "SOURCE_TRACEABILITY.md", "EXHIBIT_INDEX.csv", "MANIFEST.json",
        "README_RESULTS_PACKAGE.md", "FONT_LICENSE.txt",
    ):
        path = out / name
        if path.is_file():
            include.append(path)
    # Exclude prior ZIP members and proof junk.
    include = [p for p in include if p.resolve() != zip_path.resolve() and "conference_p" not in p.as_posix()]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(include, key=lambda p: p.relative_to(out).as_posix()):
            archive.write(path, path.relative_to(out).as_posix())
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(scratch)
        names = set(archive.namelist())
    require("figures/Fig01_spatial_charging_repair.png" in names, "ZIP missing Fig01")
    require(not any("Fig05" in n or "Sup0" in n or "star_framework" in n for n in names), "ZIP has obsolete exhibits")
    require(sum(1 for n in names if n.startswith("figures/Fig") and n.endswith(".png")) == 4, "ZIP figure count")
    require(sum(1 for n in names if n.startswith("tables/Tab") and n.endswith(".csv")) == 3, "ZIP table count")
    meta = dict(zip_sha256=file_sha(zip_path), members=len(names), path=zip_path.as_posix())
    write_json(out / "audit" / "zip_envelope.json", meta)
    return meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "package", "check-inputs"))
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("results/conference"))
    parser.add_argument("--width-mm", type=float, default=178)
    parser.add_argument("--scratch", type=Path, help="ZIP extraction proof directory")
    args = parser.parse_args()
    root = args.project_root.resolve()
    out = (root / args.output).resolve()
    require(out != root and not out.is_relative_to(root / "dataset") and not out.is_relative_to(root / "src"),
            "Unsafe output")
    if args.command == "check-inputs":
        path = inputs_dir(root)
        print(f"Publication inputs OK: {path}")
        return
    if args.command == "build":
        inputs_dir(root)
        build(root, out, args.width_mm)
        print(f"Built four main figures and three tables in {out}")
        print("Stems:", ", ".join(STEMS))
        print("Tables:", ", ".join(TABLE_STEMS))
        return
    scratch = (root / (args.scratch or Path("results/conference_p9_work/zip_check"))).resolve()
    require(not scratch.exists() and not scratch.is_relative_to(out), "Use an empty ZIP proof directory outside the release")
    print(package(root, out, scratch))


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as exc:
        sys.exit(f"Conference build or package failed: {exc}")
