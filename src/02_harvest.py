"""Stage 2 — Harvest publications for the researcher universe.

Reads data/researchers.jsonl, pulls every work for each author (cursor
paginated, disk-cached), dedupes by work id, and writes:
  data/works.jsonl  — one record per unique work (metadata, authorships, abstract)
  data/refs.jsonl   — one record per work: {id, refs:[work ids]} for the citation graph

Resumable: OpenAlex responses are cached, so re-runs replay from disk quickly.
"""
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src import openalex as oa

RESEARCHERS = os.path.join(config.DATA, "researchers.jsonl")
WORKS_OUT = os.path.join(config.DATA, "works.jsonl")
REFS_OUT = os.path.join(config.DATA, "refs.jsonl")

SELECT = ",".join([
    "id", "doi", "title", "publication_year", "publication_date", "type",
    "cited_by_count", "fwci", "primary_topic", "topics", "authorships",
    "referenced_works", "abstract_inverted_index", "primary_location",
])


def load_universe() -> list[dict]:
    rows = []
    with open(RESEARCHERS) as fh:
        for line in fh:
            rows.append(json.loads(line))
    return rows


def compact_authorships(w: dict) -> list[dict]:
    out = []
    for a in w.get("authorships", []) or []:
        aid = oa.short_id((a.get("author") or {}).get("id"))
        if not aid:
            continue
        insts = []
        for inst in a.get("institutions", []) or []:
            if inst.get("display_name"):
                insts.append({"id": oa.short_id(inst.get("id")),
                              "name": inst.get("display_name"),
                              "country": inst.get("country_code")})
        out.append({
            "id": aid,
            "name": (a.get("author") or {}).get("display_name"),
            "pos": a.get("author_position"),
            "insts": insts,
        })
    return out


def venue_name(w: dict) -> str | None:
    loc = w.get("primary_location") or {}
    src = loc.get("source") or {}
    return src.get("display_name")


def main() -> None:
    universe = load_universe()
    ids = [r["id"] for r in universe]
    print(f"== Stage 2: harvest works for {len(ids)} researchers ==", flush=True)

    seen: set[str] = set()
    n_authors = 0
    with open(WORKS_OUT, "w") as wf, open(REFS_OUT, "w") as rf:
        for aid in ids:
            n_authors += 1
            got = 0
            for w in oa.paginate("works",
                                 {"filter": f"author.id:{aid}", "select": SELECT},
                                 per_page=200):
                wid = oa.short_id(w.get("id"))
                if not wid or wid in seen:
                    continue
                seen.add(wid)
                got += 1
                pt = w.get("primary_topic") or {}
                rec = {
                    "id": wid,
                    "doi": w.get("doi"),
                    "title": w.get("title"),
                    "year": w.get("publication_year"),
                    "date": w.get("publication_date"),
                    "type": w.get("type"),
                    "cited_by": w.get("cited_by_count", 0),
                    "fwci": w.get("fwci"),
                    "venue": venue_name(w),
                    "topic": oa.short_id(pt.get("id")),
                    "topic_name": pt.get("display_name"),
                    "subfield": (pt.get("subfield") or {}).get("display_name"),
                    "field": (pt.get("field") or {}).get("display_name"),
                    "topic_ids": [oa.short_id(t.get("id")) for t in (w.get("topics") or [])],
                    "authorships": compact_authorships(w),
                    "abstract": oa.reconstruct_abstract(w.get("abstract_inverted_index")),
                }
                wf.write(json.dumps(rec) + "\n")
                refs = [oa.short_id(x) for x in (w.get("referenced_works") or [])]
                if refs:
                    rf.write(json.dumps({"id": wid, "refs": refs}) + "\n")
            if n_authors % 50 == 0 or got == 0:
                print(f"  [{n_authors}/{len(ids)}] {aid}: +{got} works "
                      f"(total unique {len(seen)})", flush=True)

    print(f"\nHarvest done: {len(seen)} unique works -> {WORKS_OUT}", flush=True)


if __name__ == "__main__":
    main()
