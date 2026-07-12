"""Stage 2 (Crossref) — Harvest publications for the researcher universe.

For each universe member, fetch all their population-genetics-relevant works
from Crossref (same relevance gate as discovery), attribute authors by
normalized key, dedupe by DOI, and write:
  data/works.jsonl  — one record per unique work (metadata, authorships, abstract)
  data/refs.jsonl   — {id, refs:[DOIs]} for the in-corpus citation graph

Resumable: Crossref responses are cached, and re-runs replay from disk.
"""
from __future__ import annotations
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src import crossref as cr

RESEARCHERS = os.path.join(config.DATA, "researchers.jsonl")
WORKS_OUT = os.path.join(config.DATA, "works.jsonl")
REFS_OUT = os.path.join(config.DATA, "refs.jsonl")
KW = [re.compile(k, re.IGNORECASE) for k in config.POPGEN_TITLE_KEYWORDS]
SPECIALIST = [j.lower() for j in config.POPGEN_JOURNALS]
MAX_WORKS = 1200


def popgen_relevance(item) -> int:
    score = 0
    venue = (cr.container(item) or "").lower()
    if any(j in venue for j in SPECIALIST):
        score += 2
    title = cr.title_of(item) or ""
    if title and any(k.search(title) for k in KW):
        score += 1
    return score


def compact_authorships(item):
    out = []
    for i, a in enumerate(item.get("author", []) or []):
        k = cr.norm_name(a.get("given"), a.get("family"))
        if not k:
            continue
        insts = []
        for aff in (a.get("affiliation") or []):
            if aff.get("name"):
                insts.append({"id": None, "name": aff["name"], "country": None})
        seq = a.get("sequence")
        pos = "first" if seq == "first" else "middle"
        out.append({"id": k, "name": " ".join(x for x in [a.get("given"), a.get("family")] if x),
                    "pos": pos, "insts": insts})
    if out:
        out[-1]["pos"] = "last" if len(out) > 1 else out[-1]["pos"]
    return out


def ref_dois(item):
    dois = []
    for r in (item.get("reference") or []):
        d = r.get("DOI")
        if d:
            dois.append(d.lower())
    return dois


def load_universe():
    rows = []
    with open(RESEARCHERS) as fh:
        for line in fh:
            rows.append(json.loads(line))
    return rows


def main():
    universe = load_universe()
    print(f"== Stage 2 (Crossref): harvest works for {len(universe)} researchers ==", flush=True)

    seen = set()
    n_authors = 0
    with open(WORKS_OUT, "w") as wf, open(REFS_OUT, "w") as rf:
        for r in universe:
            n_authors += 1
            key = r["id"]
            query = r["name"] if r.get("name") else key
            got = 0
            for item in cr.paginate_works(
                    {"query.author": query,
                     "filter": f"from-pub-date:{config.YEAR_MIN}-01-01,"
                               f"until-pub-date:{config.YEAR_MAX}-12-31,type:journal-article"},
                    max_items=MAX_WORKS):
                ak = {cr.norm_name(a.get("given"), a.get("family")) for a in item.get("author", []) or []}
                if key not in ak:
                    continue
                if popgen_relevance(item) < 1:
                    continue
                doi = (item.get("DOI") or "").lower()
                if not doi or doi in seen:
                    continue
                seen.add(doi)
                got += 1
                rec = {
                    "id": doi,
                    "doi": doi,
                    "title": cr.title_of(item),
                    "year": cr.work_year(item),
                    "date": None,
                    "type": item.get("type"),
                    "cited_by": item.get("is-referenced-by-count", 0) or 0,
                    "fwci": None,
                    "venue": cr.container(item),
                    "topic": None, "topic_name": None, "subfield": None, "field": None,
                    "topic_ids": [],
                    "authorships": compact_authorships(item),
                    "abstract": cr.clean_abstract(item.get("abstract")),
                }
                wf.write(json.dumps(rec) + "\n")
                refs = ref_dois(item)
                if refs:
                    rf.write(json.dumps({"id": doi, "refs": refs}) + "\n")
            if n_authors % 50 == 0:
                print(f"  [{n_authors}/{len(universe)}] {r['name']}: +{got} "
                      f"(total unique {len(seen)})", flush=True)

    print(f"\nHarvest done: {len(seen)} unique works -> {WORKS_OUT}", flush=True)


if __name__ == "__main__":
    main()
