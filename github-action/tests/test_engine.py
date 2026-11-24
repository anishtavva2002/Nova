import json
from nova.engine import DEFAULTS, analyze, scan_text, write_reports

def test_detects_eval_and_location():
    found=scan_text("app.py","value = eval(user_input)",DEFAULTS)
    assert len(found)==1 and found[0].rule_id=="NOVA003"
    assert found[0].line==1 and found[0].column>0

def test_disable_rule_and_ignore_fingerprint():
    cfg={**DEFAULTS,"rules":{**DEFAULTS["rules"],"NOVA003":False}}
    assert scan_text("app.py","eval(x)",cfg)==[]
    cfg={**DEFAULTS,"ignore_fingerprints":[]}
    fp=scan_text("app.py","eval(x)",cfg)[0].fingerprint
    assert scan_text("app.py","eval(x)",{**cfg,"ignore_fingerprints":[fp]})==[]

def test_excludes_node_modules(tmp_path):
    (tmp_path/"src").mkdir(); (tmp_path/"src"/"a.py").write_text("eval(x)")
    (tmp_path/"node_modules").mkdir(); (tmp_path/"node_modules"/"b.py").write_text("eval(x)")
    assert [x.path for x in analyze(tmp_path,DEFAULTS)]==["src/a.py"]

def test_json_and_sarif_reports(tmp_path):
    paths=write_reports([],tmp_path/"reports")
    assert json.loads(open(paths["json"]).read())["finding_count"]==0
    assert json.loads(open(paths["sarif"]).read())["version"]=="2.1.0"
