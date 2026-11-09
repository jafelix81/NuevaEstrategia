import json, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path
from research.phase234_cftc_bpr_capture import capture_latest, list_futures_links, select_latest_futures_url
from research.phase234_cftc_bpr_equity_index_feasibility_audit import aggregate_contract, parse_bank_row

IDX = '''<a href="/MarketReports/BankParticipation/deanov26f">Futures</a>
<a href="/MarketReports/BankParticipation/deanov26o">Options</a>
<a href="/MarketReports/BankParticipation/deaoct26f">Futures</a>'''
IDX_REVERSED = '''<a href="/MarketReports/BankParticipation/deaoct26f">Futures</a>
<a href="/MarketReports/BankParticipation/deanov26f">Futures</a>'''
IDX_DEC = '''<a href="/MarketReports/BankParticipation/deadec26f">Futures</a>
<a href="/MarketReports/BankParticipation/deanov26f">Futures</a>
<a href="/MarketReports/BankParticipation/deaoct26f">Futures</a>'''
IDX_CATCHUP = '''<a href="/MarketReports/BankParticipation/deadec26f">Futures</a>
<a href="/MarketReports/BankParticipation/deasep26f">Futures</a>
<a href="/MarketReports/BankParticipation/deanov26f">Futures</a>
<a href="/MarketReports/BankParticipation/deaoct26f">Futures</a>'''
NOV = '<h1>November BPR</h1><div>REPORT DATE: 11/3/2026</div>'
DEC = '<h1>December BPR</h1><div>REPORT DATE: 12/1/2026</div>'
SEP = '<h1>September BPR</h1><div>REPORT DATE: 9/1/2026</div>'

def dt(y,m,d,h=20,mi=35):
    return datetime(y,m,d,h,mi,tzinfo=timezone.utc)

def fetcher(index, pages):
    def get(url):
        if url.endswith('index.htm'):
            return index.encode(), {}
        slug=url.rsplit('/',1)[-1]
        if slug not in pages:
            raise AssertionError(url)
        return pages[slug].encode(), {'Date':'Fri, 06 Nov 2026 20:35:00 GMT'}
    return get

class Phase235Tests(unittest.TestCase):
    def test_link_order_and_options(self):
        self.assertTrue(select_latest_futures_url(IDX_REVERSED).endswith('deanov26f'))
        self.assertEqual([x.rsplit('/',1)[-1] for x in list_futures_links(IDX)], ['deaoct26f','deanov26f'])
        self.assertNotIn('deanov26o',' '.join(list_futures_links(IDX)))

    def test_conflicting_month_link_fails(self):
        bad=IDX+'\\n<a href="https://cftc.gov/MarketReports/BankParticipation/deanov26f">Futures</a>'
        with self.assertRaises(ValueError):
            list_futures_links(bad)

    def test_first_scheduled_observation_is_state_only_and_append_only(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); f=fetcher(IDX,{'deanov26f':NOV})
            a=capture_latest(root=root,event_name='schedule',now=dt(2026,11,6),fetcher=f,env={})
            b=capture_latest(root=root,event_name='schedule',now=dt(2026,11,9),fetcher=f,env={})
            self.assertTrue(a['initial_baseline'])
            self.assertFalse(a['pit_eligible_from_pipeline_receipt'])
            self.assertTrue(a['prospective_state_usable_after_receipt'])
            self.assertFalse(b['new_snapshot'])
            self.assertTrue(b['prospective_state_usable_after_receipt'])
            self.assertEqual(len(list((root/'data/cftc_bpr/raw').glob('*.html'))),1)
            self.assertEqual(len(list((root/'data/cftc_bpr/index_snapshots/raw').glob('*.html'))),1)

    def test_new_report_after_baseline_is_event_pit_from_receipt(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            capture_latest(root=root,event_name='schedule',now=dt(2026,11,6),fetcher=fetcher(IDX,{'deanov26f':NOV}),env={})
            r=capture_latest(root=root,event_name='schedule',now=dt(2026,12,4),fetcher=fetcher(IDX_DEC,{'deadec26f':DEC}),env={})
            self.assertTrue(r['pit_eligible_from_pipeline_receipt'])
            self.assertEqual(r['report_date'],'2026-12-01')

    def test_manual_capture_does_not_advance_baseline(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            capture_latest(root=root,event_name='schedule',now=dt(2026,11,6),fetcher=fetcher(IDX,{'deanov26f':NOV}),env={})
            capture_latest(root=root,event_name='workflow_dispatch',now=dt(2026,12,4,18,0),fetcher=fetcher(IDX_DEC,{'deadec26f':DEC}),env={})
            r=capture_latest(root=root,event_name='schedule',now=dt(2026,12,4),fetcher=fetcher(IDX_DEC,{'deadec26f':DEC}),env={})
            self.assertTrue(r['pit_eligible_from_pipeline_receipt'])

    def test_multiple_catchup_urls_captured(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            capture_latest(root=root,event_name='schedule',now=dt(2026,11,6),fetcher=fetcher(IDX,{'deanov26f':NOV}),env={})
            r=capture_latest(root=root,event_name='schedule',now=dt(2026,12,9),fetcher=fetcher(IDX_CATCHUP,{'deadec26f':DEC,'deasep26f':SEP,'deanov26f':NOV}),env={})
            dates={x['report_date'] for x in r['captures'] if x.get('new_snapshot')}
            self.assertEqual(dates,{'2026-09-01','2026-12-01'})

    def test_latest_revision_appends_new_hash(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); n={'v':0}
            def get(url):
                if url.endswith('index.htm'):
                    return IDX.encode(),{}
                n['v']+=1
                page=NOV if n['v']==1 else NOV.replace('November BPR','November BPR corrected')
                return page.encode(),{}
            capture_latest(root=root,event_name='schedule',now=dt(2026,11,6),fetcher=get,env={})
            r=capture_latest(root=root,event_name='schedule',now=dt(2026,11,9),fetcher=get,env={})
            self.assertEqual(r['captures'][0]['status'],'NEW_REVISION')
            self.assertTrue(r['pit_eligible_from_pipeline_receipt'])
            self.assertEqual(len(list((root/'data/cftc_bpr/raw').glob('*.html'))),2)

    def test_report_date_must_match_link_month(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):
                capture_latest(root=Path(t),event_name='schedule',now=dt(2026,11,6),fetcher=fetcher(IDX,{'deanov26f':DEC}),env={})

    def test_blank_fields_unknown_explicit_zero_preserved(self):
        row=parse_bank_row('IFED TEST | U.S. |  | 0 | 0.0 | 20 | 0.2 | 10000','US')
        self.assertIsNone(row.bank_count)
        self.assertEqual(row.long_positions,0)
        self.assertEqual(row.long_pct_oi,0.0)
        blank=parse_bank_row('IFED TEST | U.S. | 4 |  |  | 20 | 0.2 | 10000','US')
        self.assertIsNone(blank.long_positions)
        self.assertIsNone(blank.long_pct_oi)

    def test_total_only_unknown_and_full_reconciliation(self):
        us=parse_bank_row('IFED TEST | U.S. | 4 |  |  | 20 | 0.2 | 10000','US')
        non=parse_bank_row('NON U.S. | 5 | 100 | 1.0 | 30 | 0.3 |','NON_US')
        r=aggregate_contract(us,non,{'bank_count':9,'long_positions':100,'short_positions':50})
        self.assertEqual(r['coverage_status'],'OBSERVED_TOTAL_ONLY')
        self.assertEqual(r['net_to_open_interest'],0.005)
        u2=parse_bank_row('IFED TEST | U.S. | 4 | 60 | 0.6 | 20 | 0.2 | 10000','US')
        n2=parse_bank_row('NON U.S. | 5 | 40 | 0.4 | 30 | 0.3 |','NON_US')
        r2=aggregate_contract(u2,n2,{'bank_count':9,'long_positions':100,'short_positions':50})
        self.assertTrue(r2['category_sum_reconciled'])
        with self.assertRaises(ValueError):
            aggregate_contract(u2,n2,{'bank_count':9,'long_positions':101,'short_positions':50})
        unknown=aggregate_contract(us,non,{'bank_count':9,'long_positions':'','short_positions':50})
        self.assertIsNone(unknown['net_long_minus_short'])
        self.assertEqual(unknown['coverage_status'],'UNKNOWN_TOTAL_POSITION')

if __name__=='__main__':
    unittest.main()
