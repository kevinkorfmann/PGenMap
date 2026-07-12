"""Stage 5 — Collaboration network + communities.

Builds the co-authorship graph among universe researchers (edge weight = shared
works), detects communities (Louvain) = "schools", computes centrality, and
snapshots communities in 5-year windows. Writes results back to DuckDB and a
compact network.json for the dashboard.
"""
from __future__ import annotations
import itertools
import json
import os
import sys
from collections import defaultdict

import duckdb
import networkx as nx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

MAX_AUTHORS_PER_WORK = 30    # skip mega-consortium papers for pairwise edges
OUT_JSON = os.path.join(config.OUT, "network.json")


def load_coauthor_edges(con, year_lo=None, year_hi=None):
    """Return {(a,b): shared_work_count} among in-universe authors."""
    q = """
        SELECT a.work_id, list(a.author_id) AS authors
        FROM authorship a JOIN works w ON a.work_id = w.id
        WHERE a.in_universe = TRUE
    """
    if year_lo is not None:
        q += f" AND w.year >= {year_lo} AND w.year <= {year_hi}"
    q += " GROUP BY a.work_id"
    edges = defaultdict(int)
    for _, authors in con.execute(q).fetchall():
        authors = sorted(set(authors))
        if len(authors) < 2 or len(authors) > MAX_AUTHORS_PER_WORK:
            continue
        for a, b in itertools.combinations(authors, 2):
            edges[(a, b)] += 1
    return edges


def build_graph(edges, min_weight=1):
    g = nx.Graph()
    for (a, b), w in edges.items():
        if w >= min_weight:
            g.add_edge(a, b, weight=w)
    return g


def main() -> None:
    con = duckdb.connect(config.DB_PATH)
    print("== Stage 5: collaboration network ==", flush=True)

    names = {r[0]: r[1] for r in con.execute("SELECT id, name FROM researchers").fetchall()}
    meta = {r[0]: {"inst": r[1], "country": r[2], "cites": r[3], "core": r[4],
                   "seed": r[5], "recent": r[6]}
            for r in con.execute("""SELECT id, institution, country, cited_by_count,
                                    popgen_core, seed, recent_year FROM researchers""").fetchall()}

    edges = load_coauthor_edges(con)
    g = build_graph(edges)
    print(f"graph: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges", flush=True)

    # add isolated universe members so every researcher appears
    for aid in names:
        if aid not in g:
            g.add_node(aid)

    # communities via Louvain on the weighted graph
    try:
        comms = nx.community.louvain_communities(g, weight="weight", seed=42)
    except Exception:
        import community as community_louvain
        part = community_louvain.best_partition(g, weight="weight", random_state=42)
        by_c = defaultdict(set)
        for n, c in part.items():
            by_c[c].add(n)
        comms = list(by_c.values())
    comm_of = {}
    for ci, members in enumerate(sorted(comms, key=len, reverse=True)):
        for n in members:
            comm_of[n] = ci
    print(f"communities: {len(comms)}", flush=True)

    # centrality (degree everywhere; betweenness on giant component)
    deg = dict(g.degree(weight="weight"))
    if g.number_of_edges():
        gc_nodes = max(nx.connected_components(g), key=len)
        gc = g.subgraph(gc_nodes)
        btw = nx.betweenness_centrality(gc, weight=None, k=min(400, gc.number_of_nodes()), seed=42)
    else:
        btw = {}

    # persist community + centrality on researchers
    con.execute("ALTER TABLE researchers ADD COLUMN IF NOT EXISTS community INT")
    con.execute("ALTER TABLE researchers ADD COLUMN IF NOT EXISTS degree INT")
    con.execute("ALTER TABLE researchers ADD COLUMN IF NOT EXISTS betweenness DOUBLE")
    for aid in names:
        con.execute("UPDATE researchers SET community=?, degree=?, betweenness=? WHERE id=?",
                    [comm_of.get(aid), int(deg.get(aid, 0)), float(btw.get(aid, 0.0)), aid])

    # community profiles: dominant institutions, methods, topics, top members
    # global method rates, so community fingerprints show *distinctive* methods
    # (enriched vs the field baseline) rather than the ubiquitous ones.
    gm = con.execute("""SELECT wm.method, count(*) FROM work_methods wm
                        JOIN authorship a ON wm.work_id=a.work_id
                        WHERE a.in_universe GROUP BY wm.method""").fetchall()
    g_total = sum(c for _, c in gm) or 1
    global_share = {m: c / g_total for m, c in gm}

    def community_profile(ci, members):
        mem = [m for m in members]
        top_members = sorted(mem, key=lambda a: meta.get(a, {}).get("cites", 0) or 0,
                             reverse=True)[:8]
        placeholders = ",".join("?" for _ in mem) or "''"
        rows = con.execute(f"""
            SELECT wm.method, count(*) c FROM work_methods wm
            JOIN authorship a ON wm.work_id=a.work_id
            WHERE a.author_id IN ({placeholders}) GROUP BY wm.method
        """, mem).fetchall() if mem else []
        ctot = sum(c for _, c in rows) or 1
        scored = sorted(
            (((c / ctot) / global_share.get(m, 1e-9), c, m) for m, c in rows if c >= 4),
            reverse=True)
        methods = [(m, c) for _, c, m in scored[:6]]
        insts = defaultdict(int)
        countries = defaultdict(int)
        for m in mem:
            if meta.get(m, {}).get("inst"):
                insts[meta[m]["inst"]] += 1
            if meta.get(m, {}).get("country"):
                countries[meta[m]["country"]] += 1
        return {
            "community": ci,
            "size": len(mem),
            "top_members": [{"id": a, "name": names.get(a), "cites": meta.get(a, {}).get("cites")}
                            for a in top_members],
            "top_methods": [m for m, _ in methods],
            "top_institutions": sorted(insts, key=insts.get, reverse=True)[:5],
            "countries": sorted(countries, key=countries.get, reverse=True)[:5],
        }

    profiles = []
    for ci, members in enumerate(sorted(comms, key=len, reverse=True)):
        if len(members) >= 5:
            profiles.append(community_profile(ci, list(members)))

    # decade snapshots: community count + largest community size per window
    snapshots = []
    for lo in range(1990, config.YEAR_MAX + 1, 5):
        hi = lo + 4
        e = load_coauthor_edges(con, lo, hi)
        gg = build_graph(e)
        try:
            cc = nx.community.louvain_communities(gg, weight="weight", seed=42) if gg.number_of_edges() else []
        except Exception:
            cc = []
        snapshots.append({
            "window": f"{lo}-{hi}",
            "nodes": gg.number_of_nodes(),
            "edges": gg.number_of_edges(),
            "communities": len(cc),
            "largest_community": max((len(c) for c in cc), default=0),
        })

    # compact JSON for the dashboard: keep the strongest edges + all nodes
    top_edges = sorted(((a, b, w) for (a, b), w in edges.items() if w >= 2),
                       key=lambda x: x[2], reverse=True)[:4000]
    node_ids = set(names)
    nodes = [{
        "id": a, "name": names.get(a), "community": comm_of.get(a),
        "degree": int(deg.get(a, 0)), "betweenness": round(float(btw.get(a, 0.0)), 4),
        "inst": meta.get(a, {}).get("inst"), "country": meta.get(a, {}).get("country"),
        "cites": meta.get(a, {}).get("cites"), "core": meta.get(a, {}).get("core"),
        "seed": meta.get(a, {}).get("seed"), "recent": meta.get(a, {}).get("recent"),
    } for a in node_ids]
    net = {
        "nodes": nodes,
        "edges": [{"s": a, "t": b, "w": w} for a, b, w in top_edges],
        "communities": profiles,
        "snapshots": snapshots,
    }
    os.makedirs(config.OUT, exist_ok=True)
    with open(OUT_JSON, "w") as fh:
        json.dump(net, fh)
    con.close()
    print(f"network.json -> {OUT_JSON}  ({len(nodes)} nodes, {len(top_edges)} edges, "
          f"{len(profiles)} communities)")


if __name__ == "__main__":
    main()
