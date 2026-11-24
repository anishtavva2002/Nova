import argparse
import fnmatch
import hashlib
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    title: str
    message: str
    path: str
    line: int
    column: int
    fingerprint: str

PATTERNS = [
 ("NOVA001","critical","Hard-coded credential",re.compile(r"""(?i)\b(?:password|passwd|api[_-]?key|secret|token)\b\s*[:=]\s*["'][^"'$\s]{8,}["']""")),
 ("NOVA002","high","Potential command injection",re.compile(r"""(?i)\b(?:os\.system|subprocess\.(?:run|Popen|call))\s*\([^)]*(?:shell\s*=\s*True|f["']|\.format\()""")),
 ("NOVA003","high","Dynamic code execution",re.compile(r"\b(?:eval|exec)\s*\(")),
 ("NOVA004","high","TLS verification disabled",re.compile(r"(?i)\bverify\s*=\s*False\b")),
 ("NOVA005","medium","Unsafe deserialization",re.compile(r"\bpickle\.loads?\s*\(")),
 ("NOVA006","medium","Potential SQL injection",re.compile(r"""(?i)\b(?:execute|executemany)\s*\(\s*(?:f["']|["'][^"']*%s|["'][^"']*\+)""")),
 ("NOVA007","low","Debug mode enabled",re.compile(r"(?i)\b(?:debug\s*=\s*True|app\.run\([^)]*debug\s*=\s*True)")),
]
DEFAULTS={"version":1,"exclude":[".git/**",".venv/**","venv/**","__pycache__/**",".nova-reports/**","node_modules/**","dist/**","build/**",".pytest_cache/**"],"include_extensions":[".py",".js",".jsx",".ts",".tsx",".java",".go",".rb",".php",".sh",".yml",".yaml",".json",".toml",".env",".properties",".xml",".md"],"max_file_bytes":1048576,"rules":{f"NOVA{i:03d}":True for i in range(1,8)},"ignore_fingerprints":[]}

def load_config(path):
    cfg=dict(DEFAULTS); p=Path(path)
    if p.exists():
        try: data=json.loads(p.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError) as exc: raise ValueError(f"Cannot read config {p}: {exc}") from exc
        if not isinstance(data,dict): raise ValueError("Config root must be an object")
        cfg.update(data)
    if cfg.get("version")!=1: raise ValueError("Unsupported config version")
    for key,kind in (("rules",dict),("exclude",list),("include_extensions",list),("ignore_fingerprints",list)):
        if not isinstance(cfg.get(key),kind): raise ValueError(f"Invalid config type: {key}")
    try: cfg["max_file_bytes"]=int(cfg["max_file_bytes"])
    except (KeyError,TypeError,ValueError) as exc: raise ValueError("max_file_bytes must be positive") from exc
    if cfg["max_file_bytes"]<1: raise ValueError("max_file_bytes must be positive")
    return cfg

def scan_text(path,content,cfg):
    found=[]; ignored=set(cfg.get("ignore_fingerprints",[]))
    for number,line in enumerate(content.splitlines(),1):
        for rid,sev,title,pattern in PATTERNS:
            if not cfg["rules"].get(rid,True): continue
            match=pattern.search(line)
            if match is None: continue
            normalized=" ".join(line.strip().split())
            fp=hashlib.sha256(f"{rid}:{path}:{normalized}".encode()).hexdigest()[:20]
            if fp not in ignored:
                found.append(Finding(rid,sev,title,f"{title}. Review this line; Nova uses a static heuristic.",path,number,match.start()+1,fp))
    return found

def analyze(root,cfg):
    base=Path(root).resolve()
    if not base.is_dir(): raise ValueError(f"Not a directory: {base}")
    found=[]; exts={str(x).lower() for x in cfg["include_extensions"]}
    for file in sorted(base.rglob("*")):
        if not file.is_file(): continue
        rel=file.relative_to(base).as_posix()
        if any(fnmatch.fnmatch(rel,p) or fnmatch.fnmatch("/"+rel,p) for p in cfg["exclude"]): continue
        if file.suffix.lower() not in exts and file.name not in {".env","Dockerfile"}: continue
        try:
            if file.stat().st_size>cfg["max_file_bytes"]: continue
            content=file.read_text(encoding="utf-8",errors="replace")
        except OSError: continue
        found.extend(scan_text(rel,content,cfg))
    return sorted(found,key=lambda x:(x.path,x.line,x.rule_id))

def write_reports(found,outdir):
    out=Path(outdir); out.mkdir(parents=True,exist_ok=True)
    jp=out/"nova.json"
    jp.write_text(json.dumps({"tool":"Nova Repository Guardian","version":1,"finding_count":len(found),"findings":[asdict(x) for x in found]},indent=2),encoding="utf-8")
    rules={}; results=[]
    for x in found:
        rules.setdefault(x.rule_id,{"id":x.rule_id,"name":x.title,"shortDescription":{"text":x.title}})
        results.append({"ruleId":x.rule_id,"level":{"critical":"error","high":"error","medium":"warning","low":"note"}[x.severity],"message":{"text":x.message},"locations":[{"physicalLocation":{"artifactLocation":{"uri":x.path},"region":{"startLine":x.line,"startColumn":x.column}}}],"partialFingerprints":{"nova/v1":x.fingerprint}})
    sp=out/"nova.sarif"
    sp.write_text(json.dumps({"$schema":"https://json.schemastore.org/sarif-2.1.0.json","version":"2.1.0","runs":[{"tool":{"driver":{"name":"Nova","version":"1.0.0","rules":list(rules.values())}},"results":results}]},indent=2),encoding="utf-8")
    mp=out/"nova.md"; rows=["# Nova Repository Guardian","",f"Findings: {len(found)}","","| Severity | Rule | Location | Finding |","|---|---|---|---|"]
    rows.extend(f"| {x.severity} | {x.rule_id} | {x.path}:{x.line} | {x.title} |" for x in found)
    if not found: rows.append("| — | — | — | No findings detected |")
    mp.write_text("\n".join(rows)+"\n",encoding="utf-8")
    return {"json":str(jp),"sarif":str(sp),"markdown":str(mp)}

def main(argv=None):
    p=argparse.ArgumentParser(description="Deterministic LLM-free repository guardian")
    p.add_argument("--path",default="."); p.add_argument("--config",default=".nova.json"); p.add_argument("--output",default=".nova-reports")
    p.add_argument("--fail-on",choices=["critical","high","medium","low","never"],default="high"); p.add_argument("--summary",choices=["true","false"],default="false")
    a=p.parse_args(argv)
    try:
        cp=Path(a.config)
        if not cp.is_absolute() and not cp.exists(): cp=Path(a.path)/cp
        cfg=load_config(cp); found=analyze(a.path,cfg); paths=write_reports(found,a.output)
    except (ValueError,OSError) as exc:
        print(f"Nova error: {exc}",file=sys.stderr); return 2
    print(f"Nova scanned {a.path}: {len(found)} finding(s)")
    for x in found: print(f"{x.severity.upper()} {x.rule_id} {x.path}:{x.line} {x.title}")
    print(f"JSON: {paths['json']}\nSARIF: {paths['sarif']}\nMarkdown: {paths['markdown']}")
    if os.getenv("GITHUB_ACTIONS")=="true":
        for x in found:
            level="error" if x.severity in {"critical","high"} else "warning"
            msg=x.message.replace("%","%25").replace("\r","%0D").replace("\n","%0A")
            print(f"::{level} file={x.path},line={x.line},col={x.column},title={x.rule_id}::{msg}")
        output=os.getenv("GITHUB_OUTPUT")
        if output:
            with open(output,"a",encoding="utf-8") as f: f.write(f"findings={len(found)}\nreport={paths['json']}\n")
        summary=os.getenv("GITHUB_STEP_SUMMARY")
        if a.summary=="true" and summary:
            with open(summary,"a",encoding="utf-8") as f: f.write(f"## Nova Repository Guardian\n\n{len(found)} finding(s)\n")
    order={"critical":0,"high":1,"medium":2,"low":3,"never":99}
    return 1 if any(order[x.severity]<=order[a.fail_on] for x in found) else 0

if __name__=="__main__": raise SystemExit(main())
