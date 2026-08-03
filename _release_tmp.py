import subprocess, sys, json, re
from pathlib import Path
ADAP = "adapters/reference_python"

def run(cmd, check=True):
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        print("FALLO:", " ".join(cmd[:6]), "\n", r.stdout, r.stderr); sys.exit(1)
    return r.stdout

def escalera(resumen, obs, esp, diag, ev, kind, ksum, rollback):
    out = run([sys.executable,"-B",f"{ADAP}/run_change.py","observe","--workspace",".",
               "--author","session:taller","--confirmed-by","human:vikingo","--scope","GLOBAL",
               "--summary",resumen,"--observed",obs,"--expected",esp])
    cid = re.search(r"CHANGE_ID=(\S+)", out).group(1)
    run([sys.executable,"-B",f"{ADAP}/run_change.py","record","--workspace",".","--author","session:taller",
         "--confirmed-by","human:vikingo","--change-id",cid,"--kind","DIAGNOSIS","--summary",diag,"--evidence",ev])
    run([sys.executable,"-B",f"{ADAP}/run_change.py","record","--workspace",".","--author","session:taller",
         "--confirmed-by","human:vikingo","--change-id",cid,"--kind",kind,"--summary",ksum,
         "--target-where","local:workspace","--evidence",ev,"--rollback",rollback])
    run([sys.executable,"-B",f"{ADAP}/run_change.py","close","--workspace",".","--author","session:taller",
         "--confirmed-by","human:vikingo","--change-id",cid,"--status","FINAL",
         "--result",ksum,"--tests","PASS","--architecture","NOT_APPLICABLE","--collision","NONE"])
    return f".lifecycle/changes/{cid}/004-closure.env"

def publicar(skill, impact, closure):
    plan_path = f".lifecycle/local/plan-{skill}.json"
    out = run([sys.executable,"-B",f"{ADAP}/run_publicar_skill.py","plan","--catalog","skills",
               "--skill",skill,"--impact",impact,"--closure-receipt",closure,"--output",plan_path])
    ph = re.search(r"^PLAN_HASH=(\S+)", out, re.M).group(1)
    to = re.search(r"^TO_VERSION=(\S+)", out, re.M).group(1)
    out2 = run([sys.executable,"-B",f"{ADAP}/run_publicar_skill.py","apply","--plan",plan_path,
                "--confirm-plan-hash",ph,"--confirmed-by","human:vikingo",
                "--commit","--commit-confirmed-by","human:vikingo",
                "--tag","--tag-confirmed-by","human:vikingo"])
    print(f"  {skill}: -> {to} | {re.search(r'RELEASE=(\S+)', out2).group(1)} | {re.search(r'TAG=(\S+)', out2).group(1)}")
    return to
