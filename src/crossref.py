"""Thin, cached Crossref client (stdlib only).

Crossref is free and open (no credits, no key) with a generous polite pool.
Unlike OpenAlex it has no canonical author entities, so identity here is
ORCID-when-present else a normalized name key, and disambiguation is done
downstream via venue + method relevance + collaborator overlap.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

API = "https://api.crossref.org"
UA = f"PGenMap/0.1 (https://github.com/kevinkorfmann/PGenMap; mailto:{config.MAILTO})"
CACHE = os.path.join(config.DATA, "cache_cr")
_LAST = [0.0]
MIN_INTERVAL = 0.12          # ~8 req/s; Crossref polite pool tolerates far more


def _cache_path(url: str) -> str:
    h = hashlib.sha1(url.encode()).hexdigest()
    return os.path.join(CACHE, h[:2], h + ".json")


def _throttle() -> None:
    dt = time.time() - _LAST[0]
    if dt < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - dt)
    _LAST[0] = time.time()


def get_json(url: str, use_cache: bool = True, retries: int = 6) -> dict:
    cp = _cache_path(url)
    if use_cache and os.path.exists(cp):
        try:
            with open(cp) as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            pass
    last = None
    for attempt in range(retries):
        try:
            _throttle()
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.load(resp)
            os.makedirs(os.path.dirname(cp), exist_ok=True)
            tmp = cp + ".tmp"
            with open(tmp, "w") as fh:
                json.dump(data, fh)
            os.replace(tmp, cp)
            return data
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503, 504):
                ra = e.headers.get("Retry-After") if e.headers else None
                try:
                    wait = float(ra) if ra else min(2 ** attempt, 20)
                except ValueError:
                    wait = min(2 ** attempt, 20)
                time.sleep(wait)
                continue
            if e.code == 404:
                return {}
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
            time.sleep(min(2 ** attempt, 20))
    raise RuntimeError(f"Crossref GET failed: {url} :: {last}")


WORKS_SELECT = ",".join([
    "DOI", "title", "author", "issued", "published", "container-title", "type",
    "is-referenced-by-count", "reference", "abstract", "subject", "short-container-title",
])


def build_url(endpoint: str, params: dict) -> str:
    p = dict(params)
    p.setdefault("mailto", config.MAILTO)
    return f"{API}/{endpoint}?" + urllib.parse.urlencode(p, safe=":,+-")


def paginate_works(params: dict, max_items: int = 2000, rows: int = 100):
    """Cursor-paginate /works. `params` should include query/filter; select is added."""
    p = dict(params)
    p["rows"] = rows
    p.setdefault("select", WORKS_SELECT)
    cursor = "*"
    fetched = 0
    while cursor and fetched < max_items:
        p["cursor"] = cursor
        data = get_json(build_url("works", p))
        msg = data.get("message", {})
        items = msg.get("items", [])
        if not items:
            break
        for it in items:
            yield it
            fetched += 1
            if fetched >= max_items:
                break
        cursor = msg.get("next-cursor")
        if len(items) < rows:
            break


# --- helpers ----------------------------------------------------------------

def norm_name(given: str | None, family: str | None) -> str | None:
    """Normalized identity key: 'family-x' where x is the given-name initial."""
    if not family:
        return None
    fam = _strip(family).lower().strip()
    fam = re.sub(r"[^a-z\s\-]", "", fam).replace(" ", "-")
    gi = ""
    if given:
        g = _strip(given).lower().strip()
        gi = g[0] if g else ""
    return f"{fam}-{gi}" if fam else None


def _strip(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def orcid_of(author: dict) -> str | None:
    o = author.get("ORCID")
    if not o:
        return None
    m = re.search(r"(\d{4}-\d{4}-\d{4}-[\dxX]{4})", o)
    return m.group(1).upper() if m else None


def clean_abstract(a: str | None) -> str | None:
    if not a:
        return None
    a = re.sub(r"<[^>]+>", " ", a)          # strip JATS tags
    a = re.sub(r"\s+", " ", a).strip()
    a = re.sub(r"^abstract\s*", "", a, flags=re.IGNORECASE)
    return a or None


def work_year(item: dict) -> int | None:
    for key in ("issued", "published", "published-online", "published-print"):
        dp = (item.get(key) or {}).get("date-parts")
        if dp and dp[0] and dp[0][0]:
            return int(dp[0][0])
    return None


def container(item: dict) -> str | None:
    ct = item.get("container-title") or item.get("short-container-title")
    if isinstance(ct, list) and ct:
        return ct[0]
    return ct or None


def title_of(item: dict) -> str | None:
    t = item.get("title")
    if isinstance(t, list) and t:
        return t[0]
    return t or None
