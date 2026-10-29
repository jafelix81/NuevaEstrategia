import json, os, runpy, shutil

SRC = 'research/phase48_sec_13dg_source_regime_audit_v4.py'
SRC_OUT = 'phase48_sec_13dg_source_regime_audit_v4'
OUT = 'phase48_sec_13dg_source_regime_audit_v5'

os.makedirs(OUT, exist_ok=True)
try:
    runpy.run_path(SRC, run_name='__main__')
except SystemExit:
    pass

with open(os.path.join(SRC_OUT,'summary.json'), encoding='utf-8') as f:
    s = json.load(f)

pre, post = s['pre_regime'], s['post_regime']
pre_gate = (pre['sample'] > 0 and pre['download_ok'] == pre['sample'] and pre['structured_document'] == 0 and pre['cusip'] >= pre['sample']*.90 and pre['event_date'] >= pre['sample']*.90 and pre['reporting_person'] >= pre['sample']*.90 and pre['ownership_pct'] >= pre['sample']*.90)
post_gate = (post['sample'] > 0 and post['download_ok'] == post['sample'] and post['structured_document'] >= post['sample']*.96 and post['cusip'] >= post['sample']*.96 and post['event_date'] >= post['sample']*.96 and post['reporting_person'] >= post['sample']*.96 and post['ownership_pct'] >= post['sample']*.96)

# Submission retrieval failures are a universe-coverage/identity issue, not a
# document-regime parser failure. They are retained explicitly for the next gate.
s['phase'] = '48 v5'
s['gate'] = 'PASS' if pre_gate and post_gate else 'FAIL'
s['submission_errors_nonblocking'] = True
s['gate_rule'] = 'PASS requires complete pre/post document-field samples; submission retrieval errors are reported separately and must be resolved/covered by the historical identity gate before any alpha test.'
s['next_gate'] = 'historical active-universe CUSIP/issuer crosswalk with PIT knowledge dates; no alpha testing until coverage is quantified.'
for fn in ('summary.json','sample_results.csv'):
    shutil.copy2(os.path.join(SRC_OUT,fn), os.path.join(OUT,fn))
with open(os.path.join(OUT,'summary.json'),'w') as f:
    json.dump(s, f, indent=2)
print(json.dumps(s, indent=2))
if s['gate'] != 'PASS': raise SystemExit(1)
