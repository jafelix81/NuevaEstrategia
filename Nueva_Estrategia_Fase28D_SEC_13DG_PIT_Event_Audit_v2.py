import runpy
import re
from datetime import datetime

# Wrapper around the repaired Phase 28D audit. The prior parser correctly
# throttles SEC access and resolves filings, but its event-date regex omitted
# the common phrase "OF THIS STATEMENT". Patch only that parser here and keep
# filing_date as the PIT knowledge date.
ns = runpy.run_path('/tmp/phase35_audit.py')


def parse_event_date_v2(text):
    patterns = [
        r'DATE\s+OF\s+EVENT\s+WHICH\s+REQUIRES\s+FILING(?:\s+OF\s+THIS\s+STATEMENT)?\s*(?:\([^)]*\))?\s*[:\-]?\s*([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4}|\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})',
        r'DATE\s+OF\s+EVENT\s+WHICH\s+REQUIRES\s+FILING(?:\s+OF\s+THIS\s+STATEMENT)?\s*(?:\([^)]*\))?\s*[:\-]?\s*([^<\n]{0,80}?\d{4})',
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if not m:
            continue
        raw = re.sub(r'\s+', ' ', m.group(1)).strip(' :;')
        for fmt in ('%m/%d/%Y', '%Y-%m-%d', '%B %d, %Y', '%b %d, %Y'):
            try:
                return datetime.strptime(raw, fmt).date().isoformat()
            except ValueError:
                pass
    return None

ns['parse_event_date'] = parse_event_date_v2
ns['main']()
