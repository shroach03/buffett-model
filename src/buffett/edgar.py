"""SEC EDGAR access: ticker -> CIK, companyfacts download with caching.

The SEC publishes every XBRL-tagged number from every filing as JSON at
https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json. There is no
scraping involved. The SEC's fair-access rules require a descriptive
User-Agent (name + email) and fewer than 10 requests per second.

Two loaders share one schema:
  * ``fetch_companyfacts`` hits the live API (cached to disk per day).
  * ``load_snapshot`` reads the gzipped snapshots in ``buffett/data/fixtures``, which
    are the same JSON filtered to 10-K facts, so tests run offline and the
    results in the README are reproducible.

Bundled data ships inside the package and is only read. Set ``BUFFETT_DATA``
to use a different data directory (fixtures/, judgment/, prices.json). The
live-API cache goes to ``BUFFETT_CACHE``, default ``~/.cache/buffett``, never
into the install.
"""

from __future__ import annotations

import gzip
import json
import os
import time
from datetime import date
from importlib.resources import files
from pathlib import Path

DATA = Path(os.environ.get("BUFFETT_DATA", str(files("buffett") / "data")))
FIXTURES = DATA / "fixtures"
CACHE = Path(os.environ.get("BUFFETT_CACHE", Path.home() / ".cache" / "buffett"))

TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"

_MIN_INTERVAL = 0.15  # seconds between requests (~6.7 req/s, under the SEC's 10/s cap)
_last_request = 0.0
_SESSION = None


def _user_agent() -> str:
    ua = os.environ.get("SEC_USER_AGENT")
    if not ua:
        raise RuntimeError("Set SEC_USER_AGENT to 'Your Name your@email.com' (required by SEC fair-access rules).")
    return ua


def _session():
    """One shared session that retries throttling (429) and transient 5xx errors
    with exponential backoff, honouring the SEC's Retry-After header."""
    global _SESSION
    if _SESSION is None:
        import requests  # imported lazily so offline use needs no network deps
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
        _SESSION = requests.Session()
        _SESSION.mount("https://", HTTPAdapter(max_retries=retry))
        _SESSION.mount("http://", HTTPAdapter(max_retries=retry))
    return _SESSION


def _get_json(url: str) -> dict:
    global _last_request
    wait = _MIN_INTERVAL - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    resp = _session().get(url, headers={"User-Agent": _user_agent()}, timeout=30)
    _last_request = time.monotonic()
    resp.raise_for_status()
    data: dict = resp.json()
    return data


def _cached(name: str, url: str) -> dict:
    """Fetch ``url`` at most once per day; cache the raw JSON on disk."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.{date.today().isoformat()}.json.gz"
    if path.exists():
        with gzip.open(path, "rt", encoding="utf-8") as f:
            cached: dict = json.load(f)
        return cached
    data = _get_json(url)
    for old in CACHE.glob(f"{name}.*.json.gz"):  # keep one file per name: drop earlier days
        if old != path:
            old.unlink(missing_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(data, f)
    return data


def ticker_to_cik(ticker: str) -> int:
    table = _cached("company_tickers", TICKERS_URL)
    for row in table.values():
        if row["ticker"].upper() == ticker.upper():
            return int(row["cik_str"])
    raise KeyError(f"Ticker {ticker!r} not found in SEC ticker table")


def fetch_companyfacts(ticker: str) -> dict:
    cik = ticker_to_cik(ticker)
    return _cached(f"companyfacts_{cik:010d}", FACTS_URL.format(cik=cik))


def load_snapshot(ticker: str) -> dict:
    path = FIXTURES / f"{ticker.upper()}.json.gz"
    if not path.exists():
        raise FileNotFoundError(f"No snapshot for {ticker} at {path}")
    with gzip.open(path, "rt", encoding="utf-8") as f:
        facts: dict = json.load(f)
    return facts


def load(ticker: str, live: bool = False) -> dict:
    return fetch_companyfacts(ticker) if live else load_snapshot(ticker)
