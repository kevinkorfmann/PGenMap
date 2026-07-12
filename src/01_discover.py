"""Stage 1 (Crossref) — Discover the researcher universe.

Crossref has no canonical author entities, so we build the universe by
co-authorship expansion from the seeds, keeping only population-genetics-
relevant works (specialist venue OR popgen title keyword). Author identity is a
normalized 'family-initial' key; ORCID is tracked as metadata.

  hop 0: fetch each seed's popgen works -> co-author frequencies + seed links
  hop 1: fetch the best-connected co-authors' popgen works -> expand the pool
  select: score every candidate on popgen output + connectivity -> top TARGET

Writes data/researchers.jsonl. Fully resumable (Crossref responses cached).
"""
from __future__ import annotations
import json
import math
import os
import re
import sys
from collections import defaultdict, Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src import crossref as cr

OUT_PATH = os.path.join(config.DATA, "researchers.jsonl")
KW = [re.compile(k, re.IGNORECASE) for k in config.POPGEN_TITLE_KEYWORDS]
HISTORICAL_KW = [re.compile(k, re.IGNORECASE) for k in config.HISTORICAL_TITLE_KEYWORDS]
SPECIALIST = [j.lower() for j in config.POPGEN_JOURNALS]

SEED_MAX_WORKS = 800
HOP1_MAX_WORKS = 400
HOP1_AUTHORS = 650          # how many co-authors to expand in hop 1
MIN_POPGEN_WORKS = 3
TARGET = config.TARGET_UNIVERSE


def popgen_relevance(item) -> int:
    """0 = not relevant; >=1 relevant (specialist venue or popgen title kw)."""
    score = 0
    venue = (cr.container(item) or "").lower()
    if any(j in venue for j in SPECIALIST):
        score += 2
    title = (cr.title_of(item) or "")
    patterns = KW + (HISTORICAL_KW if config.YEAR_MIN < config.MODERN_YEAR_MIN else [])
    if title and any(k.search(title) for k in patterns):
        score += 1
    return score


def author_keys(item):
    """Return list of (key, orcid, given, family, affil) for a work's authors."""
    out = []
    for a in item.get("author", []) or []:
        k = cr.norm_name(a.get("given"), a.get("family"))
        if not k:
            continue
        affil = ""
        aff = a.get("affiliation") or []
        if aff and isinstance(aff, list) and aff[0].get("name"):
            affil = aff[0]["name"]
        out.append((k, cr.orcid_of(a), a.get("given"), a.get("family"), affil))
    return out


class Universe:
    def __init__(self):
        self.popgen_works = Counter()      # key -> # popgen works seen (processed authors)
        self.coauthor_freq = Counter()     # key -> co-occurrences in popgen works
        self.seed_links = defaultdict(set) # key -> set of seed keys co-authored with
        self.orcids = defaultdict(Counter)
        self.names = defaultdict(Counter)
        self.affils = defaultdict(Counter)
        self.cites = Counter()             # provisional: sum is-referenced-by-count
        self.years = defaultdict(list)
        self.seeds = set()
        self.processed = set()

    def record_author(self, k, orcid, given, family, affil):
        if orcid:
            self.orcids[k][orcid] += 1
        nm = " ".join(x for x in [given, family] if x)
        if nm:
            self.names[k][nm] += 1
        if affil:
            self.affils[k][affil] += 1

    def process(self, query_name, target_key, is_seed):
        """Fetch target's popgen works via Crossref; update stats + expand co-authors."""
        if target_key in self.processed:
            return
        self.processed.add(target_key)
        maxw = SEED_MAX_WORKS if is_seed else HOP1_MAX_WORKS
        n = 0
        for item in cr.paginate_works(
                {"query.author": query_name,
                 "filter": f"from-pub-date:{config.YEAR_MIN}-01-01,until-pub-date:{config.YEAR_MAX}-12-31,type:journal-article"},
                max_items=maxw):
            ak = author_keys(item)
            keys = {k for k, *_ in ak}
            if target_key not in keys:
                continue                    # fuzzy query matched a non-author
            if popgen_relevance(item) < 1:
                continue                    # not popgen -> disambiguation gate
            n += 1
            self.popgen_works[target_key] += 1
            yr = cr.work_year(item)
            if yr:
                self.years[target_key].append(yr)
            for k, orcid, given, family, affil in ak:
                self.record_author(k, orcid, given, family, affil)
                self.cites[k] += item.get("is-referenced-by-count", 0) or 0
                if k == target_key:
                    continue
                self.coauthor_freq[k] += 1
                if is_seed:
                    self.seed_links[k].add(target_key)
        return n


def resolve_seed_query(name):
    """Config seed 'Given Family' -> (query string, normalized key)."""
    parts = name.replace(".", " ").split()
    given = parts[0] if parts else ""
    family = parts[-1] if len(parts) > 1 else parts[0]
    key = cr.norm_name(given, family)
    return name, key


def main():
    os.makedirs(config.DATA, exist_ok=True)
    U = Universe()
    print("== Stage 1 (Crossref): discovery ==", flush=True)

    # hop 0: seeds
    seed_keys = {}
    seeds = list(config.SEED_RESEARCHERS)
    if config.YEAR_MIN < config.MODERN_YEAR_MIN:
        seeds += list(config.HISTORICAL_SEED_RESEARCHERS)
    for disp, hint in seeds:
        q, key = resolve_seed_query(disp)
        seed_keys[key] = disp
    U.seeds = set(seed_keys)
    print(f"processing {len(seed_keys)} seeds (hop 0)...", flush=True)
    for i, (key, disp) in enumerate(seed_keys.items(), 1):
        got = U.process(disp, key, is_seed=True)
        U.record_author(key, None, disp.split()[0], disp.split()[-1], "")
        if i % 15 == 0 or (got or 0) == 0:
            print(f"  [{i}/{len(seed_keys)}] {disp}: {got} popgen works", flush=True)

    # hop 1: expand best-connected co-authors
    cand = [(k, len(U.seed_links[k]), U.coauthor_freq[k])
            for k in U.coauthor_freq if k not in U.seeds]
    cand.sort(key=lambda x: (x[1], x[2]), reverse=True)
    hop1 = [k for k, links, freq in cand if links >= 1][:HOP1_AUTHORS]
    print(f"expanding {len(hop1)} co-authors (hop 1)...", flush=True)
    for i, k in enumerate(hop1, 1):
        disp = U.names[k].most_common(1)[0][0] if U.names[k] else k
        U.process(disp, k, is_seed=False)
        if i % 50 == 0:
            print(f"  [{i}/{len(hop1)}] processed (pool now {len(U.coauthor_freq)})", flush=True)

    # select universe
    all_keys = set(U.popgen_works) | set(U.coauthor_freq) | U.seeds
    rows = []
    for k in all_keys:
        pw = U.popgen_works[k]
        links = len(U.seed_links[k])
        freq = U.coauthor_freq[k]
        is_seed = k in U.seeds
        keep = is_seed or pw >= MIN_POPGEN_WORKS or links >= 2 or freq >= 6
        if not keep:
            continue
        score = pw * 1.5 + links * 3 + math.log10(U.cites[k] + 1) * 2 + min(freq, 40) * 0.3
        yrs = U.years.get(k, [])
        rows.append({
            "id": k,
            "name": (U.names[k].most_common(1)[0][0] if U.names[k] else k),
            "orcid": (U.orcids[k].most_common(1)[0][0] if U.orcids[k] else None),
            "institutions": [a for a, _ in U.affils[k].most_common(3)],
            "country": None,
            "works_count": pw,               # provisional; build_db recomputes
            "cited_by_count": U.cites[k],     # provisional
            "h_index": None,
            "field": None,
            "popgen_works": pw,
            "popgen_core": pw,
            "popgen_share": None,
            "seed": is_seed,
            "seed_links": links,
            "recent_year": max(yrs) if yrs else None,
            "top_topics": [],
            "score": round(score, 2),
            "provenance": (["seed"] if is_seed else []) +
                          (["processed"] if k in U.processed else ["coauthor"]),
        })

    rows.sort(key=lambda r: r["score"], reverse=True)
    if len(rows) > TARGET:
        seeds = [r for r in rows if r["seed"]]
        rest = [r for r in rows if not r["seed"]][:TARGET - len(seeds)]
        rows = sorted(seeds + rest, key=lambda r: r["score"], reverse=True)

    with open(OUT_PATH, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    n_seed = sum(1 for r in rows if r["seed"])
    print(f"\nKEPT {len(rows)} researchers ({n_seed} seeds) -> {OUT_PATH}", flush=True)
    print("Top 15 by score:", flush=True)
    for r in rows[:15]:
        print(f"  {r['score']:7.1f}  {r['name']:28s}  popgen_works={r['popgen_works']:4d} "
              f"links={r['seed_links']}  {r['institutions'][:1]}", flush=True)


if __name__ == "__main__":
    main()
