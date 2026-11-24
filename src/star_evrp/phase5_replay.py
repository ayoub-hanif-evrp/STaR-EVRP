"""Replay every saved plan without entering the optimization path."""

from concurrent.futures import ProcessPoolExecutor
from time import perf_counter

from star_evrp.phase4_results import canonical, read_json, require, sha, write_json
from star_evrp.phase5_experiments import case_worker, clock, get_protocol, settings


def replay_stage(root,out,stage):
    protocol=get_protocol(root,out)
    cfg=settings(root)[1]["config"]
    execution=read_json(out/"audit"/f"{stage}_execution.json")
    token=sha(canonical(protocol))
    require(execution["protocol"]==token and not execution["errors"],"Execution not complete")
    roster={(row["parent_key"],row["variant"]):row for row in
            read_json(root/"results/manifests/dataset_inventory.json")["instances"]}
    start,elapsed=clock(),perf_counter()
    records=[]
    with ProcessPoolExecutor(max_workers=protocol["workers"]) as pool:
        jobs=[pool.submit(case_worker,root,out,roster[row["parent"],row["variant"]],stage,protocol,True)
              for row in execution["cases"]]
        for index,job in enumerate(jobs,1):
            result=job.result()
            records.append(result)
            if "error" in result:
                print(result,flush=True)
            if index%12==0 or index==len(jobs):
                print(f"{stage} replay: {index}/{len(jobs)} instances",flush=True)
    errors=[row for row in records if "error" in row]
    path=out/"audit"/f"{stage}_replay.json"
    if path.exists():
        previous=read_json(path)
        if not previous["errors"]:
            require(previous["cases"]==records and not errors,"Saved replay no longer matches")
            return previous
        write_json(out/"logs"/f"{stage}_replay_{sha(canonical(previous))[:12]}.json",previous)
    result={"start_utc":start,"end_utc":clock(),"elapsed_seconds":perf_counter()-elapsed,"stage":stage,"protocol":token,
            "cases":records,"records":sum(row.get("records",0) for row in records),"errors":errors,
            "scalar_per_plan":cfg["validation_scalar_checks"]}
    write_json(path,result)
    require(not errors and records==execution["cases"],"Selected plan replay is incomplete")
    return result
