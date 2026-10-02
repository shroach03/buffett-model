"""The live SEC download path, with the HTTP session mocked so it runs offline."""

import gzip
import json
import threading
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

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

    class FakeSession:
        def get(self, url, headers=None, timeout=None):
            log.append((url, headers))
            return FakeResponse(TICKERS if url == edgar.TICKERS_URL else FACTS)

    monkeypatch.setattr(edgar, "_SESSION", FakeSession())
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


def test_cache_keeps_one_file_per_name(calls, tmp_path):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    for name in ("company_tickers", "companyfacts_0000001234"):
        with gzip.open(tmp_path / f"{name}.{yesterday}.json.gz", "wt", encoding="utf-8") as f:
            json.dump({"stale": True}, f)
    assert edgar.load("ROL", live=True) == FACTS  # stale files are not today's, so it refetches
    today = date.today().isoformat()
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        f"company_tickers.{today}.json.gz",
        f"companyfacts_0000001234.{today}.json.gz",
    ]


def test_retries_after_429(monkeypatch):
    """Real HTTP against a local server: first response 429, second 200."""
    hits = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            hits.append(self.path)
            status, body = (429, b"slow down") if len(hits) == 1 else (200, json.dumps(FACTS).encode())
            self.send_response(status)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setattr(edgar, "_SESSION", None)  # build the real retrying session
    monkeypatch.setattr(edgar, "_MIN_INTERVAL", 0.0)
    monkeypatch.setenv("SEC_USER_AGENT", "Test Person test@example.com")
    try:
        assert edgar._get_json(f"http://127.0.0.1:{server.server_port}/facts") == FACTS
    finally:
        server.shutdown()
        server.server_close()
    assert len(hits) == 2
