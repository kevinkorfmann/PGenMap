"""Build the DuckDB analytic store from the harvested JSONL files.

Tables:
  researchers(id, name, ...)                 the universe
  works(id, title, year, ..., abstract)      unique works
  authorship(work_id, author_id, name, pos, ord)
  work_topics(work_id, topic_id)
  citations(src, dst)                        refs restricted to the corpus
"""
from __future__ import annotations
import json
import os
import sys

import duckdb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

DATA = config.DATA


def read_jsonl(path):
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                yield json.loads(line)


def _flush(con, work_rows, auth_rows, wt_rows):
    """Insert batches, skipping empties (DuckDB executemany rejects []; Crossref
    works carry no topic ids so wt_rows is always empty)."""
    if work_rows:
        con.executemany("INSERT INTO works VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", work_rows)
    if auth_rows:
        con.executemany("INSERT INTO authorship VALUES (?,?,?,?,?,?)", auth_rows)
    if wt_rows:
        con.executemany("INSERT INTO work_topics VALUES (?,?)", wt_rows)


def main() -> None:
    if os.path.exists(config.DB_PATH):
        os.remove(config.DB_PATH)
    con = duckdb.connect(config.DB_PATH)

    # --- researchers ---
    researchers = list(read_jsonl(os.path.join(DATA, "researchers.jsonl")))
    for r in researchers:
        r["institution"] = (r.get("institutions") or [None])[0]
        r["provenance"] = ",".join(r.get("provenance") or [])
        r["top_topics"] = " | ".join(r.get("top_topics") or [])
    con.execute("""
        CREATE TABLE researchers(
            id TEXT PRIMARY KEY, name TEXT, orcid TEXT, institution TEXT,
            country TEXT, works_count INT, cited_by_count BIGINT, h_index INT,
            field TEXT, popgen_works DOUBLE, popgen_core INT, popgen_share DOUBLE,
            seed BOOLEAN, seed_links INT, recent_year INT, top_topics TEXT,
            score DOUBLE, provenance TEXT)
    """)
    con.executemany(
        "INSERT INTO researchers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [[r["id"], r["name"], r.get("orcid"), r["institution"], r.get("country"),
          r.get("works_count"), r.get("cited_by_count"), r.get("h_index"),
          r.get("field"), r.get("popgen_works"), r.get("popgen_core"),
          r.get("popgen_share"), bool(r.get("seed")), r.get("seed_links"),
          r.get("recent_year"), r["top_topics"], r.get("score"), r["provenance"]]
         for r in researchers])
    universe = set(r["id"] for r in researchers)
    print(f"researchers: {len(researchers)}")

    # --- works, authorship, work_topics ---
    con.execute("""CREATE TABLE works(
        id TEXT PRIMARY KEY, doi TEXT, title TEXT, year INT, date TEXT, type TEXT,
        cited_by BIGINT, fwci DOUBLE, venue TEXT, topic TEXT, topic_name TEXT,
        subfield TEXT, field TEXT, abstract TEXT, n_authors INT)""")
    con.execute("""CREATE TABLE authorship(
        work_id TEXT, author_id TEXT, name TEXT, position TEXT, ord INT,
        in_universe BOOLEAN)""")
    con.execute("CREATE TABLE work_topics(work_id TEXT, topic_id TEXT)")

    work_rows, auth_rows, wt_rows = [], [], []
    corpus: set[str] = set()
    n = 0
    for w in read_jsonl(os.path.join(DATA, "works.jsonl")):
        corpus.add(w["id"])
        aships = w.get("authorships") or []
        work_rows.append([
            w["id"], w.get("doi"), w.get("title"), w.get("year"), w.get("date"),
            w.get("type"), w.get("cited_by", 0), w.get("fwci"), w.get("venue"),
            w.get("topic"), w.get("topic_name"), w.get("subfield"), w.get("field"),
            w.get("abstract"), len(aships)])
        for i, a in enumerate(aships):
            auth_rows.append([w["id"], a["id"], a.get("name"), a.get("pos"), i,
                              a["id"] in universe])
        for tid in (w.get("topic_ids") or []):
            if tid:
                wt_rows.append([w["id"], tid])
        n += 1
        if len(work_rows) >= 20000:
            _flush(con, work_rows, auth_rows, wt_rows)
            work_rows, auth_rows, wt_rows = [], [], []
    _flush(con, work_rows, auth_rows, wt_rows)
    print(f"works: {n}")

    # recompute accurate per-researcher stats from the harvested corpus
    con.execute("""
        UPDATE researchers SET
          works_count = COALESCE((SELECT count(DISTINCT a.work_id) FROM authorship a
                                  WHERE a.author_id = researchers.id), 0),
          cited_by_count = COALESCE((SELECT sum(w.cited_by) FROM authorship a
                                     JOIN works w ON a.work_id = w.id
                                     WHERE a.author_id = researchers.id), 0),
          recent_year = (SELECT max(w.year) FROM authorship a JOIN works w ON a.work_id = w.id
                         WHERE a.author_id = researchers.id)
    """)

    # --- citations (restricted to corpus) ---
    con.execute("CREATE TABLE citations(src TEXT, dst TEXT)")
    refs_path = os.path.join(DATA, "refs.jsonl")
    cite_rows = []
    n_edges = 0
    if os.path.exists(refs_path):
        for rec in read_jsonl(refs_path):
            src = rec["id"]
            if src not in corpus:
                continue
            for dst in rec.get("refs", []):
                if dst in corpus:
                    cite_rows.append([src, dst])
                    n_edges += 1
            if len(cite_rows) >= 50000:
                con.executemany("INSERT INTO citations VALUES (?,?)", cite_rows)
                cite_rows = []
        if cite_rows:
            con.executemany("INSERT INTO citations VALUES (?,?)", cite_rows)
    print(f"in-corpus citation edges: {n_edges}")

    # indexes
    con.execute("CREATE INDEX ix_auth_work ON authorship(work_id)")
    con.execute("CREATE INDEX ix_auth_author ON authorship(author_id)")
    con.execute("CREATE INDEX ix_wt_work ON work_topics(work_id)")
    con.execute("CREATE INDEX ix_cite_src ON citations(src)")

    # quick summary
    yr = con.execute("SELECT min(year), max(year) FROM works WHERE year IS NOT NULL").fetchone()
    print(f"work year range: {yr[0]}-{yr[1]}")
    con.close()
    print(f"DB written -> {config.DB_PATH}")


if __name__ == "__main__":
    main()
