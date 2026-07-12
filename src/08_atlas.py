"""Build the static data payload for the interactive PGenMap atlas."""
from __future__ import annotations
import json
import os
import shutil
import sys
from collections import defaultdict

import duckdb
import numpy as np
from sklearn.neighbors import NearestNeighbors

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

OUT = os.path.join(config.OUT, "atlas.json")
DOC_OUT = os.path.join(config.ROOT, "docs", "data", "atlas.json")
EMB = os.path.join(config.DATA, "embeddings.npy")
EMB_IDS = os.path.join(config.DATA, "emb_ids.json")


def has_table(con, name):
    return bool(con.execute("SELECT count(*) FROM information_schema.tables WHERE table_name=?", [name]).fetchone()[0])


def projection(emb):
    from umap import UMAP
    return UMAP(n_neighbors=18, n_components=2, min_dist=0.08, metric="cosine",
                random_state=42, low_memory=True).fit_transform(emb)


def main():
    if not (os.path.exists(EMB) and os.path.exists(EMB_IDS)):
        raise SystemExit("atlas needs embeddings; run src/03_enrich.py first")
    con = duckdb.connect(config.DB_PATH, read_only=True)
    ids = json.load(open(EMB_IDS))
    emb = np.load(EMB)
    if len(ids) != len(emb):
        raise SystemExit("embedding IDs and rows differ")
    print(f"== Stage 8: atlas ({len(ids)} papers) ==", flush=True)
    xy = projection(emb)
    xlo, xhi = np.percentile(xy[:, 0], [1, 99]); ylo, yhi = np.percentile(xy[:, 1], [1, 99])
    xy[:, 0] = np.clip((xy[:, 0] - xlo) / (xhi - xlo), 0, 1)
    xy[:, 1] = np.clip((xy[:, 1] - ylo) / (yhi - ylo), 0, 1)

    fine = has_table(con, "work_fine_cluster") and has_table(con, "fine_topic_meta")
    if fine:
        topic_rows = con.execute("SELECT topic_id, parent_topic_id, label, size, keywords FROM fine_topic_meta").fetchall()
        fine_parent = {r[0]: r[1] for r in topic_rows}
        assignments = {wid: (tid, fine_parent.get(tid, -1))
                       for wid, tid in con.execute("SELECT work_id, topic_id FROM work_fine_cluster").fetchall()}
    else:
        topic_rows = [(r[0] * 10000, r[0], r[1], r[2], r[3]) for r in con.execute("SELECT topic_id, label, size, keywords FROM topic_meta WHERE topic_id>=0").fetchall()]
        assignments = {r[0]: (r[1] * 10000, r[1]) for r in con.execute("SELECT work_id, topic_id FROM work_cluster WHERE topic_id>=0").fetchall()}
    macro_label = {r[0]: r[1] for r in con.execute("SELECT topic_id, label FROM topic_meta").fetchall()}
    work = {r[0]: r[1:] for r in con.execute("SELECT id, title, year, doi FROM works").fetchall()}
    methods = defaultdict(list)
    for wid, m in con.execute("SELECT work_id, method FROM work_methods").fetchall(): methods[wid].append(m)

    macro_for_index = np.array([assignments.get(w, (-1, -1))[1] for w in ids])
    neigh = NearestNeighbors(n_neighbors=min(13, len(ids)), metric="cosine").fit(emb)
    near = neigh.kneighbors(return_distance=False)
    bridge_by_fine = defaultdict(list)
    for i, wid in enumerate(ids):
        fine_id, macro = assignments.get(wid, (-1, -1))
        if fine_id >= 0 and macro >= 0:
            other = macro_for_index[near[i][1:]]
            bridge_by_fine[fine_id].append(float(np.mean((other >= 0) & (other != macro))))

    end_year = min(config.YEAR_MAX - 1, max((v[1] for v in work.values() if v[1]), default=config.YEAR_MAX - 1))
    recent, prior = range(end_year - 4, end_year + 1), range(end_year - 9, end_year - 4)
    totals, counts = defaultdict(int), defaultdict(lambda: defaultdict(int))
    for wid, (_, year, _) in work.items():
        if year:
            totals[year] += 1
            tid = assignments.get(wid, (-1, -1))[0]
            if tid >= 0: counts[tid][year] += 1
    scores = []
    for tid, parent, label, size, keywords in topic_rows:
        r, p = sum(counts[tid][y] for y in recent), sum(counts[tid][y] for y in prior)
        scores.append({"id": tid, "parent": parent, "label": label, "keywords": keywords or "", "size": size,
                       "recent": r, "prior": p, "growth_raw": (r + 1) / (p + 1),
                       "bridge_raw": float(np.mean(bridge_by_fine[tid])) if bridge_by_fine[tid] else 0.0,
                       "share_raw": r / max(1, sum(totals[y] for y in recent))})
    def percentile(key, reverse=False):
        ordered = sorted((x[key], i) for i, x in enumerate(scores)); den = max(1, len(ordered) - 1)
        return {i: (1 - rank / den if reverse else rank / den) for rank, (_, i) in enumerate(ordered)}
    growth_rank, bridge_rank, niche_rank = percentile("growth_raw"), percentile("bridge_raw"), percentile("share_raw", True)
    reps = defaultdict(list)
    for wid, (title, year, doi) in work.items():
        tid = assignments.get(wid, (-1, -1))[0]
        if tid >= 0 and title and len(reps[tid]) < 3: reps[tid].append({"title": title, "year": year, "doi": doi})
    for i, t in enumerate(scores):
        eligible = t["size"] >= 30 and t["recent"] >= 10
        t["opportunity"] = round(100 * (.45 * growth_rank[i] + .35 * bridge_rank[i] + .20 * niche_rank[i])) if eligible else None
        t["components"] = {"growth": round(100 * growth_rank[i]), "bridge": round(100 * bridge_rank[i]), "niche": round(100 * niche_rank[i])}
        t["trend"] = "emerging" if t["growth_raw"] > 1.25 else ("declining" if t["growth_raw"] < .8 else "established")
        t["macro_label"], t["representative"] = macro_label.get(t["parent"], str(t["parent"])), reps[t["id"]]

    points = []
    for i, wid in enumerate(ids):
        title, year, doi = work.get(wid, (None, None, None)); tid, macro = assignments.get(wid, (-1, -1))
        points.append({"x": round(float(xy[i, 0]), 5), "y": round(float(xy[i, 1]), 5), "id": wid, "title": title or "Untitled", "year": year, "doi": doi, "fine": tid, "macro": macro, "methods": methods[wid][:4]})
    actual_years = [v[1] for v in work.values() if v[1]]
    payload = {"version": 1, "range": [min(actual_years), max(actual_years)],
               "configured_range": [config.YEAR_MIN, config.YEAR_MAX], "analysis_end": end_year,
               "coverage": {"papers": len(points), "abstracts": con.execute("SELECT count(*) FROM works WHERE abstract IS NOT NULL").fetchone()[0]},
               "macros": [{"id": k, "label": v} for k, v in macro_label.items() if k >= 0],
               "topics": sorted(scores, key=lambda t: (t["opportunity"] is None, -(t["opportunity"] or 0))), "points": points}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh: json.dump(payload, fh, separators=(",", ":"))
    os.makedirs(os.path.dirname(DOC_OUT), exist_ok=True); shutil.copyfile(OUT, DOC_OUT)
    con.close(); print(f"atlas -> {OUT} ({os.path.getsize(OUT) / 1e6:.1f} MB)")


if __name__ == "__main__": main()
