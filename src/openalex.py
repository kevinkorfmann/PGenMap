"""Thin, cached OpenAlex client.

Design goals: resumable (every response cached to disk by URL hash), polite
(mailto + gentle rate limiting + backoff), and dependency-light (stdlib only,
so discovery/harvest run under any Python).
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402

API = "https://api.openalex.org"
UA = f"PGenMap/0.1 (mailto:{config.MAILTO})"
_LAST_CALL = [0.0]
MIN_INTERVAL = 0.11          # ~9 req/s, well under the 10/s polite ceiling


def _cache_path(url: str) -> str:
    h = hashlib.sha1(url.encode()).hexdigest()
    return os.path.join(config.CACHE, h[:2], h + ".json")


def _throttle() -> None:
    dt = time.time() - _LAST_CALL[0]
    if dt < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - dt)
    _LAST_CALL[0] = time.time()


def get_json(url: str, use_cache: bool = True, retries: int = 5) -> dict:
    """GET a URL as JSON, caching the body to disk. Cached hits skip the network."""
    cp = _cache_path(url)
    if use_cache and os.path.exists(cp):
        try:
            with open(cp) as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            pass  # corrupt cache -> refetch
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            _throttle()
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.load(resp)
            os.makedirs(os.path.dirname(cp), exist_ok=True)
            tmp = cp + ".tmp"
            with open(tmp, "w") as fh:
                json.dump(data, fh)
            os.replace(tmp, cp)
            return data
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(min(2 ** attempt, 30))
                continue
            if e.code == 404:
                return {}
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last_err = e
            time.sleep(min(2 ** attempt, 30))
    raise RuntimeError(f"GET failed after {retries} tries: {url} :: {last_err}")


def build_url(endpoint: str, params: dict) -> str:
    p = dict(params)
    p.setdefault("mailto", config.MAILTO)
    return f"{API}/{endpoint}?" + urllib.parse.urlencode(p, safe=":|,")


def get(endpoint: str, params: dict, use_cache: bool = True) -> dict:
    return get_json(build_url(endpoint, params), use_cache=use_cache)


def paginate(endpoint: str, params: dict, max_pages: int | None = None,
             per_page: int = 200, use_cache: bool = True):
    """Yield every result across cursor pages. `select` should be set by caller
    to keep payloads (and the cache) small."""
    p = dict(params)
    p["per-page"] = per_page
    cursor = "*"
    pages = 0
    while cursor:
        p["cursor"] = cursor
        data = get(endpoint, p, use_cache=use_cache)
        results = data.get("results", [])
        if not results:
            break
        for r in results:
            yield r
        cursor = data.get("meta", {}).get("next_cursor")
        pages += 1
        if max_pages is not None and pages >= max_pages:
            break


def reconstruct_abstract(inv_index: dict | None) -> str | None:
    """Rebuild abstract text from OpenAlex's abstract_inverted_index."""
    if not inv_index:
        return None
    positions: list[tuple[int, str]] = []
    for word, idxs in inv_index.items():
        for i in idxs:
            positions.append((i, word))
    if not positions:
        return None
    positions.sort()
    return " ".join(w for _, w in positions)


def short_id(oa_id: str | None) -> str | None:
    """'https://openalex.org/A5088476239' -> 'A5088476239'."""
    if not oa_id:
        return None
    return oa_id.rstrip("/").split("/")[-1]
