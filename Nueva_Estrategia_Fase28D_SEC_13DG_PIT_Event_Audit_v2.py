import runpy

# Materialize the base audit without executing its __main__ block, then use
# its robust parser directly. Keep filing_date as the PIT knowledge date.
ns = runpy.run_path('/tmp/phase35_audit.py', run_name='phase35_audit')
ns['main']()
