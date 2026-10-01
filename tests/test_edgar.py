"""The live SEC download path, with ``requests.get`` mocked so it runs offline."""

import gzip
import json

import pytest
import requests

from buffett import edgar

TICKERS = {"0": {"cik_str": 1234, "ticker": "ROL", "title": "Rollins"}}
FACTS = {"cik": 1234, "entityName": "ROLLINS", "facts": {}}


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


@pytest.fixture
def calls(monkeypatch, tmp_path):
    """Route SEC requests to canned JSON; record (url, headers) for each call."""
    log = []

    def fake_get(url, headers=None, timeout=None):
        log.append((url, headers))
        return FakeResponse(TICKERS if url == edgar.TICKERS_URL else FACTS)

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(edgar, "CACHE", tmp_path)
    monkeypatch.setattr(edgar, "_MIN_INTERVAL", 0.0)
    monkeypatch.setenv("SEC_USER_AGENT", "Test Person test@example.com")
    return log


def test_sends_user_agent_and_resolves_cik(calls):
    assert edgar.fetch_companyfacts("rol") == FACTS
    assert [u for u, _ in calls] == [edgar.TICKERS_URL, edgar.FACTS_URL.format(cik=1234)]
    assert all(h == {"User-Agent": "Test Person test@example.com"} for _, h in calls)


def test_missing_user_agent_raises_before_any_request(calls, monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT")
    with pytest.raises(RuntimeError, match="SEC_USER_AGENT"):
        edgar.fetch_companyfacts("ROL")
    assert calls == []


def test_second_call_same_day_uses_cache(calls, tmp_path):
    edgar.load("ROL", live=True)
    n = len(calls)
    assert edgar.load("ROL", live=True) == FACTS
    assert len(calls) == n  # no new request
    cached = sorted(p.name for p in tmp_path.iterdir())
    assert len(cached) == 2 and all(p.endswith(".json.gz") for p in cached)
    with gzip.open(tmp_path / cached[0], "rt", encoding="utf-8") as f:
        json.load(f)  # cache is valid gzipped JSON


def test_unknown_ticker_raises_keyerror(calls):
    with pytest.raises(KeyError, match="ZZZZ"):
        edgar.ticker_to_cik("ZZZZ")
