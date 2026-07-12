"""Stage 1 — Discover the researcher universe.

Builds the population-genetics researcher set by (1) resolving seeds to
canonical OpenAlex author IDs, (2) topic-crawling popgen topics for prolific
authors, (3) expanding through seed co-authorship, then (4) scoring every
candidate on popgen relevance + connectivity and keeping the top ~TARGET.

Writes data/researchers.jsonl (one JSON record per kept researcher).
Resumable: every API call is disk-cached, so re-runs are near-instant.
"""
from __future__ import annotations
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src import openalex as oa

POPGEN_TOPICS = set(config.POPGEN_TOPIC_IDS)
CORE_TOPICS = set(config.CORE_POPGEN_TOPICS)
TOPIC_W = config.TOPIC_WEIGHTS
POPGEN_CONCEPTS = set(config.POPGEN_CONCEPT_IDS)
OUT_PATH = os.path.join(config.DATA, "researchers.jsonl")

# Relevance / filtering knobs (all in terms of CORE popgen-topic works) -------
MIN_POPGEN_WORKS = 3        # core popgen works to qualify with a share test
MIN_POPGEN_SHARE = 0.05     # ...and at least this fraction of the author's output
STRONG_POPGEN_WORKS = 6     # unconditional keep threshold
SEED_COAUTHOR_HOPS = 1      # network expansion depth from seeds
AUTHOR_BATCH = 50


def author_short(a: dict) -> str | None:
    return oa.short_id(a.get("id"))


def popgen_work_count(author: dict) -> float:
    """Weighted sum of the author's work counts in popgen topics (broad set)."""
    n = 0.0
    for t in author.get("topics", []) or []:
        tid = oa.short_id(t.get("id"))
        if tid in POPGEN_TOPICS:
            n += int(t.get("count", 0)) * TOPIC_W.get(tid, 1.0)
    for c in author.get("x_concepts", []) or []:
        if oa.short_id(c.get("id")) in POPGEN_CONCEPTS and c.get("score", 0) >= 40:
            n += 2
    return n


def popgen_core_count(author: dict) -> int:
    """Work count in the two CORE popgen topics only — the strict signal that
    separates real population geneticists from clinical/forensic namesakes."""
    n = 0
    for t in author.get("topics", []) or []:
        if oa.short_id(t.get("id")) in CORE_TOPICS:
            n += int(t.get("count", 0))
    return n


def institution_names(author: dict) -> list[str]:
    out = []
    for inst in author.get("last_known_institutions", []) or []:
        if inst.get("display_name"):
            out.append(inst["display_name"])
    for aff in author.get("affiliations", []) or []:
        nm = (aff.get("institution") or {}).get("display_name")
        if nm:
            out.append(nm)
    return out


def primary_field(author: dict) -> str | None:
    topics = author.get("topics", []) or []
    if topics:
        return (topics[0].get("field") or {}).get("display_name")
    return None


# --- 1. seed resolution ------------------------------------------------------

def resolve_seed(name: str, hint: str | None) -> tuple[dict | None, float]:
    data = oa.get("authors", {"filter": f"display_name.search:{name}", "per-page": 50})
    best, best_score, best_hit = None, -1.0, 0.0
    for cand in data.get("results", []):
        core = popgen_core_count(cand)
        wc = max(cand.get("works_count", 0), 1)
        core_share = core / wc
        insts = " ; ".join(institution_names(cand)).lower()
        hit = 1.0 if (hint and hint.lower() in insts) else 0.0
        cites = cand.get("cited_by_count", 0)
        # Rank on core popgen output, its *concentration*, and institution match.
        # Citations count only when core popgen output is well-concentrated, so a
        # high-citation clinical namesake with a few incidental popgen papers
        # cannot win on citations alone.
        cite_credit = math.log10(cites + 1) * 2.0 if (core >= 3 and core_share >= 0.02) else 0.0
        score = core * 3.0 + core_share * 100.0 + hit * 150.0 + cite_credit
        if score > best_score:
            best, best_score, best_hit = cand, score, hit
    if best is None:
        return None, 0.0
    core = popgen_core_count(best)
    core_share = core / max(best.get("works_count", 0), 1)
    # Keep only with real corroboration: an institution-hint match, or genuine
    # *concentrated* core popgen output. A tiny popgen share on a huge clinical
    # output (e.g. 4 popgen papers among 3000) is a wrong same-name author.
    if best_hit == 0.0 and not (core >= 3 and core_share >= 0.02):
        return None, 0.0
    conf = (0.5 if best_hit else 0.0) + (0.5 if (core >= 3 and core_share >= 0.02) else 0.0)
    return best, conf


# --- 2. topic crawl ----------------------------------------------------------

def discover_topic_ids() -> list[str]:
    ids = list(config.CORE_POPGEN_TOPICS)
    for phrase in config.TOPIC_SEARCH_PHRASES:
        data = oa.get("topics", {"search": phrase, "per-page": 6})
        for t in data.get("results", []):
            field = (t.get("field") or {}).get("display_name", "")
            if field in ("Biochemistry, Genetics and Molecular Biology",
                         "Agricultural and Biological Sciences",
                         "Immunology and Microbiology"):
                tid = oa.short_id(t.get("id"))
                if tid and tid not in ids and t.get("works_count", 0) > 3000:
                    ids.append(tid)
    return ids


def topic_authors(topic_id: str, top: int = 200) -> dict[str, int]:
    """Top authors in a topic via group_by; returns {author_id: work_count}."""
    data = oa.get("works", {
        "filter": f"primary_topic.id:{topic_id},from_publication_date:{config.YEAR_MIN}-01-01",
        "group_by": "authorships.author.id",
        "per-page": top,
    })
    out = {}
    for g in data.get("group_by", []):
        aid = oa.short_id(g.get("key"))
        if aid and aid.startswith("A"):
            out[aid] = int(g.get("count", 0))
    return out


# --- 3. network expansion ----------------------------------------------------

def seed_coauthors(author_id: str, max_works: int = 400) -> dict[str, int]:
    counts: dict[str, int] = {}
    n = 0
    for w in oa.paginate("works",
                         {"filter": f"author.id:{author_id}",
                          "select": "id,authorships"},
                         per_page=200, max_pages=max(1, max_works // 200)):
        for a in w.get("authorships", []) or []:
            cid = oa.short_id((a.get("author") or {}).get("id"))
            if cid and cid != author_id:
                counts[cid] = counts.get(cid, 0) + 1
        n += 1
        if n >= max_works:
            break
    return counts


# --- 4. batch author records + scoring --------------------------------------

def fetch_authors(ids: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i in range(0, len(ids), AUTHOR_BATCH):
        chunk = ids[i:i + AUTHOR_BATCH]
        data = oa.get("authors", {
            "filter": "ids.openalex:" + "|".join(chunk),
            "per-page": AUTHOR_BATCH,
        })
        for a in data.get("results", []):
            sid = author_short(a)
            if sid:
                out[sid] = a
    return out


def main() -> None:
    os.makedirs(config.DATA, exist_ok=True)
    print("== Stage 1: discovery ==", flush=True)

    # 1. seeds
    seeds: dict[str, dict] = {}
    seed_conf: dict[str, float] = {}
    print(f"resolving {len(config.SEED_RESEARCHERS)} seeds...", flush=True)
    for name, hint in config.SEED_RESEARCHERS:
        a, conf = resolve_seed(name, hint)
        if a:
            sid = author_short(a)
            seeds[sid] = a
            seed_conf[sid] = conf
            flag = "" if conf >= 0.5 else "  <-- low confidence"
            print(f"  {name:32s} -> {sid} {a.get('display_name')} "
                  f"({institution_names(a)[:1]}) cites={a.get('cited_by_count')}{flag}", flush=True)
    print(f"resolved {len(seeds)} unique seed authors", flush=True)

    # 2. topic crawl
    topic_ids = discover_topic_ids()
    print(f"crawling {len(topic_ids)} popgen topics: {topic_ids}", flush=True)
    topic_hits: dict[str, int] = {}
    for tid in topic_ids:
        ta = topic_authors(tid)
        for aid, cnt in ta.items():
            topic_hits[aid] = topic_hits.get(aid, 0) + cnt
        print(f"  {tid}: +{len(ta)} authors", flush=True)
    print(f"topic crawl surfaced {len(topic_hits)} candidate authors", flush=True)

    # 3. network expansion from seeds
    coauthor_hits: dict[str, int] = {}
    coauthor_seedlinks: dict[str, set] = {}
    print(f"expanding co-author network (hop {SEED_COAUTHOR_HOPS}) from seeds...", flush=True)
    for sid in seeds:
        cos = seed_coauthors(sid)
        for cid, cnt in cos.items():
            coauthor_hits[cid] = coauthor_hits.get(cid, 0) + cnt
            coauthor_seedlinks.setdefault(cid, set()).add(sid)
    print(f"co-author expansion surfaced {len(coauthor_hits)} candidates", flush=True)

    # union candidate pool
    candidate_ids = set(seeds) | set(topic_hits) | set(coauthor_hits)
    print(f"total candidate pool: {len(candidate_ids)}", flush=True)

    # 4. fetch full records for candidates not already loaded
    need = [c for c in candidate_ids if c not in seeds]
    print(f"fetching {len(need)} candidate author records...", flush=True)
    records = dict(seeds)
    records.update(fetch_authors(need))
    print(f"have {len(records)} author records", flush=True)

    # 5. score + filter (centered on CORE popgen output to keep the corpus clean)
    kept = []
    for aid, a in records.items():
        pg = popgen_work_count(a)          # weighted broad signal (for scoring)
        core = popgen_core_count(a)        # strict core-topic signal (for keep gate)
        wc = max(a.get("works_count", 0), 1)
        share = pg / wc
        share_core = core / wc
        seedlinks = len(coauthor_seedlinks.get(aid, set()))
        is_seed = aid in seeds
        field = primary_field(a)
        life_sci = field in ("Biochemistry, Genetics and Molecular Biology",
                             "Agricultural and Biological Sciences",
                             "Immunology and Microbiology",
                             "Medicine", None)
        keep = (
            is_seed
            or core >= STRONG_POPGEN_WORKS
            or (core >= MIN_POPGEN_WORKS and share_core >= MIN_POPGEN_SHARE)
            or (seedlinks >= 2 and core >= 1)
        )
        if not keep or not life_sci:
            continue
        cites = a.get("cited_by_count", 0)
        stats = a.get("summary_stats", {}) or {}
        score = core * (0.5 + share_core) + math.log10(cites + 1) * 2 + seedlinks
        counts_by_year = a.get("counts_by_year", []) or []
        years = [c["year"] for c in counts_by_year if c.get("works_count", 0) > 0]
        kept.append({
            "id": aid,
            "name": a.get("display_name"),
            "orcid": a.get("orcid"),
            "institutions": institution_names(a)[:3],
            "country": next((i.get("country_code") for i in
                             (a.get("last_known_institutions") or []) if i.get("country_code")), None),
            "works_count": a.get("works_count", 0),
            "cited_by_count": cites,
            "h_index": stats.get("h_index"),
            "field": field,
            "popgen_works": round(pg, 1),
            "popgen_core": core,
            "popgen_share": round(share, 3),
            "seed": is_seed,
            "seed_conf": round(seed_conf.get(aid, 0.0), 2) if is_seed else None,
            "seed_links": seedlinks,
            "recent_year": max(years) if years else None,
            "top_topics": [t.get("display_name") for t in (a.get("topics") or [])[:5]],
            "score": round(score, 2),
            "provenance": (["seed"] if is_seed else [])
                          + (["topic"] if aid in topic_hits else [])
                          + (["network"] if aid in coauthor_hits else []),
        })

    kept.sort(key=lambda r: r["score"], reverse=True)
    if len(kept) > config.TARGET_UNIVERSE:
        # always keep seeds even if beyond the cap
        seed_rows = [r for r in kept if r["seed"]]
        rest = [r for r in kept if not r["seed"]][: config.TARGET_UNIVERSE - len(seed_rows)]
        kept = seed_rows + rest
        kept.sort(key=lambda r: r["score"], reverse=True)

    with open(OUT_PATH, "w") as fh:
        for r in kept:
            fh.write(json.dumps(r) + "\n")

    n_seed = sum(1 for r in kept if r["seed"])
    print(f"\nKEPT {len(kept)} researchers ({n_seed} seeds) -> {OUT_PATH}", flush=True)
    print("Top 15 by score:", flush=True)
    for r in kept[:15]:
        print(f"  {r['score']:7.1f}  {r['name']:28s}  pg={r['popgen_works']:4d} "
              f"cites={r['cited_by_count']:>8d}  {r['institutions'][:1]}", flush=True)


if __name__ == "__main__":
    main()
