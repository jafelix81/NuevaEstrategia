import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'Nueva_Estrategia_Fase28D_SEC_13DG_PIT_Event_Audit.py'
spec = importlib.util.spec_from_file_location('phase35_parser', PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_event_date_parenthetical_mmddyyyy():
    text = 'DATE OF EVENT WHICH REQUIRES FILING (MM/DD/YYYY) 10/17/2025'
    assert mod.parse_event_date(text) == '2025-10-17'


def test_event_date_colon_variant():
    text = 'DATE OF EVENT WHICH REQUIRES FILING: 9/3/2024'
    assert mod.parse_event_date(text) == '2024-09-03'


def test_event_date_iso_variant():
    text = 'DATE OF EVENT WHICH REQUIRES FILING (YYYY-MM-DD) 2023-12-01'
    assert mod.parse_event_date(text) == '2023-12-01'


def test_event_date_reverse_date_then_label():
    text = '10/17/2025 (Date of Event Which Requires Filing of this Statement)'
    assert mod.parse_event_date(text) == '2025-10-17'


def test_event_date_reverse_with_parenthetical_format():
    text = '09/03/2024 (MM/DD/YYYY) Date of Event Which Requires Filing'
    assert mod.parse_event_date(text) == '2024-09-03'


def test_event_date_month_name():
    text = 'Date of Event Which Requires Filing: October 17, 2025'
    assert mod.parse_event_date(text) == '2025-10-17'


def test_event_date_missing_returns_none():
    assert mod.parse_event_date('DATE OF EVENT WHICH REQUIRES FILING') is None
