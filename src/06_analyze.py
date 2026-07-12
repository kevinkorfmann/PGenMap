"""Stage 6 — Analyses + export analysis.json.

Pulls everything together into the compact aggregates that back the report and
the dashboard:
  - method / keyword adoption curves over time
  - topic prevalence over time (from the Stage-4 model)
  - per-researcher cards (focus, collaborators, notable papers)
  - in-corpus citation flow -> pivotal papers
  - computed field milestones (adoption inflection years)
"""
from __future__ import annotations
import json
import os
import sys
from collections import defaultdict

import duckdb
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

OUT_JSON = os.path.join(config.OUT, "analysis.json")
Y0, Y1 = config.YEAR_MIN, config.YEAR_MAX
YEARS = list(range(Y0, Y1 + 1))


def yearly_totals(con):
    rows = con.execute(
        "SELECT year, count(*) FROM works WHERE year BETWEEN ? AND ? GROUP BY year",
        [Y0, Y1]).fetchall()
    d = {y: 0 for y in YEARS}
    for y, n in rows:
        d[y] = n
    return d


def method_series(con, totals):
    rows = con.execute("""
        SELECT wm.method, w.year, count(*) FROM work_methods wm
        JOIN works w ON wm.work_id = w.id
        WHERE w.year BETWEEN ? AND ? GROUP BY wm.method, w.year
    """, [Y0, Y1]).fetchall()
    counts = defaultdict(lambda: {y: 0 for y in YEARS})
    for method, year, n in rows:
        counts[method][year] = n
    methods = sorted(counts, key=lambda m: sum(counts[m].values()), reverse=True)
    out_counts, out_share = {}, {}
    for m in methods:
        out_counts[m] = [counts[m][y] for y in YEARS]
        out_share[m] = [round(counts[m][y] / totals[y], 4) if totals[y] else 0.0 for y in YEARS]
    return methods, out_counts, out_share


def method_milestones(methods, share):
    """Adoption year = first year a method's share stays >= 2% for 2+ years."""
    out = []
    for m in methods:
        s = share[m]
        for i in range(len(YEARS) - 1):
            if s[i] >= 0.02 and s[i + 1] >= 0.02:
                out.append({"year": YEARS[i], "method": m,
                            "peak_share": round(max(s), 4),
                            "peak_year": YEARS[int(np.argmax(s))]})
                break
    return sorted(out, key=lambda d: d["year"])


def topic_series(con, totals):
    have = con.execute("SELECT count(*) FROM topic_meta WHERE topic_id >= 0").fetchone()[0]
    if not have:
        return []
    meta = {r[0]: {"label": r[1], "size": r[2], "keywords": r[3]}
            for r in con.execute("SELECT topic_id, label, size, keywords FROM topic_meta").fetchall()}
    rows = con.execute("""
        SELECT wc.topic_id, w.year, count(*) FROM work_cluster wc
        JOIN works w ON wc.work_id = w.id
        WHERE w.year BETWEEN ? AND ? AND wc.topic_id >= 0
        GROUP BY wc.topic_id, w.year
    """, [Y0, Y1]).fetchall()
    by_topic = defaultdict(lambda: {y: 0 for y in YEARS})
    for tid, year, n in rows:
        by_topic[tid][year] = n
    topics = []
    for tid, ymap in by_topic.items():
        counts = [ymap[y] for y in YEARS]
        share = [round(ymap[y] / totals[y], 4) if totals[y] else 0.0 for y in YEARS]
        # trend: slope of share over the last 12 yrs
        recent = np.array(share[-12:])
        slope = float(np.polyfit(range(len(recent)), recent, 1)[0]) if recent.any() else 0.0
        m = meta.get(tid, {})
        topics.append({
            "id": tid, "label": m.get("label", str(tid)), "keywords": m.get("keywords", ""),
            "size": m.get("size", sum(counts)),
            "counts": counts, "share": share,
            "peak_year": YEARS[int(np.argmax(counts))] if any(counts) else None,
            "trend": "rising" if slope > 1e-4 else ("declining" if slope < -1e-4 else "stable"),
        })
    topics.sort(key=lambda t: t["size"], reverse=True)
    return topics


def researcher_cards(con):
    R = {r[0]: dict(id=r[0], name=r[1], inst=r[2], country=r[3], cites=r[4],
                    core=r[5], works=r[6], seed=r[7], community=r[8], degree=r[9])
         for r in con.execute("""SELECT id, name, institution, country, cited_by_count,
                popgen_core, works_count, seed, community, degree FROM researchers""").fetchall()}

    # active years per author (within corpus)
    for aid, lo, hi in con.execute("""
            SELECT a.author_id, min(w.year), max(w.year)
            FROM authorship a JOIN works w ON a.work_id=w.id
            WHERE a.in_universe=TRUE AND w.year IS NOT NULL GROUP BY a.author_id""").fetchall():
        if aid in R:
            R[aid]["first_year"], R[aid]["last_year"] = lo, hi

    # top methods per author
    meth = defaultdict(list)
    for aid, method, n in con.execute("""
            SELECT a.author_id, wm.method, count(*) c FROM authorship a
            JOIN work_methods wm ON a.work_id=wm.work_id
            WHERE a.in_universe=TRUE GROUP BY a.author_id, wm.method""").fetchall():
        meth[aid].append((n, method))
    for aid in R:
        R[aid]["top_methods"] = [m for _, m in sorted(meth.get(aid, []), reverse=True)[:5]]

    # top model-topics per author
    tmeta = {r[0]: r[1] for r in con.execute("SELECT topic_id, label FROM topic_meta").fetchall()}
    topi = defaultdict(list)
    for aid, tid, n in con.execute("""
            SELECT a.author_id, wc.topic_id, count(*) c FROM authorship a
            JOIN work_cluster wc ON a.work_id=wc.work_id
            WHERE a.in_universe=TRUE AND wc.topic_id>=0 GROUP BY a.author_id, wc.topic_id""").fetchall():
        topi[aid].append((n, tid))
    for aid in R:
        R[aid]["top_topics"] = [tmeta.get(t, str(t)) for _, t in sorted(topi.get(aid, []), reverse=True)[:3]]

    # top collaborators (in-universe)
    collab = defaultdict(lambda: defaultdict(int))
    for a, b, n in con.execute("""
            SELECT x.author_id a, y.author_id b, count(*) c
            FROM authorship x JOIN authorship y ON x.work_id=y.work_id
            WHERE x.in_universe AND y.in_universe AND x.author_id<>y.author_id
            GROUP BY x.author_id, y.author_id""").fetchall():
        collab[a][b] = n
    for aid in R:
        cs = sorted(collab.get(aid, {}).items(), key=lambda kv: kv[1], reverse=True)[:5]
        R[aid]["collaborators"] = [{"id": b, "name": R.get(b, {}).get("name"), "n": n}
                                   for b, n in cs if b in R]

    # notable papers (author's most-cited)
    for aid in R:
        R[aid]["papers"] = []
    for aid, title, year, cites, _rn in con.execute("""
            SELECT a.author_id, w.title, w.year, w.cited_by,
                   row_number() OVER (PARTITION BY a.author_id ORDER BY w.cited_by DESC) rn
            FROM authorship a JOIN works w ON a.work_id=w.id
            WHERE a.in_universe=TRUE QUALIFY rn <= 3""").fetchall():
        if aid in R:
            R[aid]["papers"].append({"title": title, "year": year, "cites": cites})
    return list(R.values())


def pivotal_papers(con, limit=50):
    rows = con.execute("""
        SELECT w.id, w.title, w.year, w.topic_name, w.cited_by,
               count(c.src) AS in_cites
        FROM works w LEFT JOIN citations c ON c.dst = w.id
        GROUP BY w.id, w.title, w.year, w.topic_name, w.cited_by
        ORDER BY in_cites DESC, w.cited_by DESC LIMIT ?
    """, [limit]).fetchall()
    return [{"id": r[0], "title": r[1], "year": r[2], "topic": r[3],
             "cites": r[4], "in_corpus_cites": r[5]} for r in rows]


def main() -> None:
    con = duckdb.connect(config.DB_PATH)
    print("== Stage 6: analyze + export ==", flush=True)
    totals = yearly_totals(con)

    methods, m_counts, m_share = method_series(con, totals)
    topics = topic_series(con, totals)
    cards = researcher_cards(con)
    pivotal = pivotal_papers(con)

    n_works = con.execute("SELECT count(*) FROM works").fetchone()[0]
    n_abs = con.execute("SELECT count(*) FROM works WHERE abstract IS NOT NULL").fetchone()[0]
    n_res = con.execute("SELECT count(*) FROM researchers").fetchone()[0]
    n_countries = con.execute("SELECT count(DISTINCT country) FROM researchers WHERE country IS NOT NULL").fetchone()[0]
    n_comm = con.execute("SELECT count(DISTINCT community) FROM researchers WHERE community IS NOT NULL").fetchone()[0]
    n_edges = con.execute("SELECT count(*) FROM citations").fetchone()[0]

    net = {}
    net_path = os.path.join(config.OUT, "network.json")
    if os.path.exists(net_path):
        with open(net_path) as fh:
            net = json.load(fh)

    analysis = {
        "meta": {
            "researchers": n_res, "works": n_works, "works_with_abstract": n_abs,
            "countries": n_countries, "communities": n_comm,
            "citation_edges": n_edges, "year_min": Y0, "year_max": Y1,
        },
        "years": YEARS,
        "field_totals": [totals[y] for y in YEARS],
        "methods": methods,
        "method_groups": config.METHOD_GROUPS,
        "method_counts": m_counts,
        "method_share": m_share,
        "method_milestones": method_milestones(methods, m_share),
        "topics": topics,
        "researchers": cards,
        "communities": net.get("communities", []),
        "network_snapshots": net.get("snapshots", []),
        "pivotal_papers": pivotal,
    }
    os.makedirs(config.OUT, exist_ok=True)
    with open(OUT_JSON, "w") as fh:
        json.dump(analysis, fh)
    size_mb = os.path.getsize(OUT_JSON) / 1e6
    con.close()
    print(f"analysis.json -> {OUT_JSON}  ({size_mb:.1f} MB)")
    print(f"  {n_res} researchers | {n_works} works ({n_abs} w/ abstract) | "
          f"{len(methods)} methods | {len(topics)} topics | {n_comm} communities")
    print("  method adoption milestones:")
    for m in analysis["method_milestones"][:12]:
        print(f"    {m['year']}  {m['method']}  (peak {m['peak_year']}, {m['peak_share']:.1%})")


if __name__ == "__main__":
    main()
