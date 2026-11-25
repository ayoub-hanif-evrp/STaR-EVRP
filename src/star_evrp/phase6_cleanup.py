"""Classify disposable workspace artifacts and verify research evidence."""

from collections import Counter
import subprocess
from zipfile import ZipFile

from star_evrp.phase4_results import file_sha, git, require
from star_evrp.phase6_archive import MARKERS, verify, write_csv, write_json

REPEATS = ("results/phase4_repeat","results/phase5_repeat")
PROOFS = ("results/phase4_proofs","results/phase5_proofs")
LOCAL = (".pytest_cache",".mypy_cache",".ruff_cache","src/star_evrp.egg-info","src/star_evrp/__pycache__",
         "tests/__pycache__","dataset/EVRPTW_ChargingStations_Dataset/code/__pycache__")
SCRATCH = ("results/phase6_rebuild","results/phase6_proofs","results/phase6_tex","results/phase6_con_check","results/phase6_pytest")
CON = "results/phase3/raw/con"
CANDIDATES = (*REPEATS,*PROOFS,*LOCAL,CON,*SCRATCH,*MARKERS)


def is_link(path):
    return path.is_symlink() or getattr(path,"is_junction",lambda:False)()


def inventory(root,out,*,final=False):
    lines = git(root,"status","--short","--untracked-files=all").decode().splitlines()
    known = Counter(line[:2] for line in lines)
    tracked = git(root,"ls-files","-z").decode().strip("\0").split("\0")
    ignored = git(root,"ls-files","--others","--ignored","--exclude-standard","-z").decode().strip("\0").split("\0")
    checkpoint_paths = [name for name in ignored if "/.ipynb_checkpoints/" in name]
    output = []
    groups = Counter()
    for name in tracked:
        path = root/name
        if path.is_file() and not is_link(path):
            groups[name.split("/")[0]] += path.stat().st_size
    for name,bytes_total in sorted(groups.items()):
        output.append(dict(path=name,category="tracked scientific or repository support",status="tracked",bytes=bytes_total,
                           reason="Protect corpus and research evidence or update only explicit navigation files",action="preserve"))
    for relative in CANDIDATES:
        path = root/relative
        old = relative in MARKERS
        candidate = path.exists() and not is_link(path)
        amount = None
        if candidate:
            if path.is_file():
                amount=path.stat().st_size
            else:
                files = [p for p in path.rglob("*") if p.is_file() and not is_link(p) and p.resolve().is_relative_to(root)]
                amount=sum(f.stat().st_size for f in files)
        reason = ("Empty placeholder in nonempty directory, absent from frozen manifests" if old
                  else "ZIP exact historical bundles, extract for original Phase 3 CLI" if relative==CON
                  else "Recompute with documented commands; reviewed published evidence remains" if relative.startswith("results/")
                  else "Local interpreter, build or test cache")
        output.append(dict(path=relative,category="disposable",status="tracked empty marker" if old else "local",
                           bytes=0 if old else amount,reason=reason,
                           action="consider after verification" if candidate else "already absent"))
    if checkpoint_paths:
        output.append(dict(path="dataset/.../.ipynb_checkpoints/",category="ambiguous user data",status="ignored",
                           bytes=sum((root/k).stat().st_size for k in checkpoint_paths),
                           reason=f"{len(checkpoint_paths)} local checkpoint files have no byte-identical dataset copy",action="preserve"))
    output.append(dict(path="prompts/PROMPT_06_MATHEMATICAL_STRENGTHENING_AND_REPOSITORY_CLEANUP.md",
                       category="user specification",status="pre-existing untracked",bytes=(root/"prompts/PROMPT_06_MATHEMATICAL_STRENGTHENING_AND_REPOSITORY_CLEANUP.md").stat().st_size,
                       reason="Authoritative specification",action="include in scientific commit"))
    tag = "final" if final else "pre_experiment"
    write_json(out/"audit"/f"cleanup_{tag}_git.json",dict(
        statuses=dict(known),tracked_paths=len(tracked),ignored_paths=len([n for n in ignored if n]),checkpoint_paths=len(checkpoint_paths),
        submodule_count=sum(b.startswith(b"160000 ") for b in git(root,"ls-tree","-r","HEAD").splitlines()),
        lfs_pointer_rule="filter=lfs" in (root/".gitattributes").read_text(),
        task_paths=[line for line in lines if line[3:].startswith(("results/phase6/","docs/PHASE6","configs/phase6",
                    "scripts/run_phase6","src/star_evrp/phase6","tests/test_phase6","prompts/PROMPT_06"))
                    or line[3:] in {"README.md",".gitignore",".gitattributes",*MARKERS}]))
    if not final:
        write_csv(out/"audit/cleanup_inventory.csv",output)
    return output


def verified_cleanup(root,out,actions):
    protocol = verify(root,out,all_inputs=True)
    base = protocol["configuration"]["base_commit"]
    names = git(root,"diff","--name-only",base).decode().splitlines()
    require(all(name in {*MARKERS,"README.md",".gitignore",".gitattributes"} or name.startswith((
        "docs/PHASE6_","results/phase6/","scripts/run_phase6.py","src/star_evrp/phase6_",
        "configs/phase6.yaml","tests/test_phase6_","prompts/PROMPT_06")) for name in names),"Unexpected change")
    with ZipFile(root/"results/phase3/con_bundles.zip") as archive:
        require(len(archive.namelist())==96 and archive.testzip() is None,"CON ZIP failed integrity check")
    require(not (root/CON).is_dir(),"A permanent reserved-path extraction was unexpectedly materialized")
    tracked_output = [p.relative_to(root).as_posix() for p in (out/"raw").rglob("*.json.gz")]
    require(bool(tracked_output),"Missing raw results after cleanup")
    ignore = subprocess.run(["git","-C",str(root),"check-ignore","--no-index","--stdin"],
                            input="\n".join(tracked_output)+"\n",text=True,capture_output=True)
    require(ignore.returncode==1 and not ignore.stdout,"Ignore rules hide Phase 6 raw results")
    inventory(root,out,final=True)
    total = sum(int(row["bytes"]) for row in actions if row["action"]=="removed")
    data = dict(status="pass",protected_hashes=len(protocol["protected_sha256"]),
                removed_bytes=total,actions=len(actions),frozen_commit=protocol["frozen_commit"],
                phase3_con_members=96,permission_limited=[row["path"] for row in actions
                                                        if row["after_verification"]=="UnauthorizedAccessException"])
    write_csv(out/"audit/cleanup_actions.csv",actions)
    write_json(out/"audit/cleanup.json",data)
    return data
