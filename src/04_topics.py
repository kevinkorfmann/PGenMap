"""Stage 4 — Topic model over paper embeddings + per-year prevalence.

Clusters the corpus embeddings with BERTopic (UMAP + HDBSCAN), labels topics by
c-TF-IDF, and writes topic assignments + metadata to DuckDB. Falls back to
OpenAlex primary topics if embeddings are unavailable.

Outputs (DuckDB):
  topic_meta(topic_id, label, size, keywords, kind)
  work_cluster(work_id, topic_id)
"""
from __future__ import annotations
import json
import os
import sys

import duckdb
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

EMB_NPY = os.path.join(config.DATA, "embeddings.npy")
EMB_IDS = os.path.join(config.DATA, "emb_ids.json")
MIN_TOPIC_SIZE = 120     # macro topics -> interpretable field themes
MIN_FINE_TOPIC_SIZE = 30


def write_tables(con, meta_rows, cluster_rows) -> None:
    con.execute("DROP TABLE IF EXISTS topic_meta")
    con.execute("DROP TABLE IF EXISTS work_cluster")
    con.execute("CREATE TABLE topic_meta(topic_id INT, label TEXT, size INT, keywords TEXT, kind TEXT)")
    con.execute("CREATE TABLE work_cluster(work_id TEXT, topic_id INT)")
    con.executemany("INSERT INTO topic_meta VALUES (?,?,?,?,?)", meta_rows)
    con.executemany("INSERT INTO work_cluster VALUES (?,?)", cluster_rows)


def write_fine_topics(con, ids, macro_topics, emb, docs, macro_meta) -> None:
    """Create a drill-down layer inside each macro topic.

    Fine IDs are stable within a run (macro_id * 10,000 + local id). Small or
    noisy macro clusters retain one explicitly labelled catch-all topic rather
    than manufacturing false precision.
    """
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer

    by_macro = {}
    for i, macro in enumerate(macro_topics):
        if macro >= 0:
            by_macro.setdefault(int(macro), []).append(i)
    meta, rows = [], []
    for macro, ix in by_macro.items():
        base_label = macro_meta.get(macro, str(macro))
        local = np.zeros(len(ix), dtype=int)
        if len(ix) >= MIN_FINE_TOPIC_SIZE * 2:
            labels = HDBSCAN(min_cluster_size=MIN_FINE_TOPIC_SIZE, min_samples=5,
                             metric="euclidean", cluster_selection_method="eom").fit_predict(emb[ix])
            # Assign noise to a per-macro catch-all; valid clusters start at 1.
            unique = sorted(x for x in set(labels) if x >= 0)
            remap = {old: n + 1 for n, old in enumerate(unique)}
            local = np.array([remap.get(x, 0) for x in labels], dtype=int)
        for sub in sorted(set(local)):
            members = [j for j, val in enumerate(local) if val == sub]
            fine_id = macro * 10000 + int(sub)
            texts = [docs[ix[j]] for j in members]
            keywords = ""
            if len(texts) >= 3:
                try:
                    vec = CountVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1,
                                          max_features=12).fit(texts)
                    keywords = ", ".join(vec.get_feature_names_out()[:10])
                except ValueError:
                    pass
            label = f"{base_label} · {'shared methods' if sub == 0 else 'subtopic ' + str(sub)}"
            meta.append([fine_id, macro, label, len(members), keywords, "fine"])
            rows.extend([[ids[ix[j]], fine_id] for j in members])
    con.execute("DROP TABLE IF EXISTS fine_topic_meta")
    con.execute("DROP TABLE IF EXISTS work_fine_cluster")
    con.execute("CREATE TABLE fine_topic_meta(topic_id INT, parent_topic_id INT, label TEXT, size INT, keywords TEXT, kind TEXT)")
    con.execute("CREATE TABLE work_fine_cluster(work_id TEXT, topic_id INT)")
    con.executemany("INSERT INTO fine_topic_meta VALUES (?,?,?,?,?,?)", meta)
    con.executemany("INSERT INTO work_fine_cluster VALUES (?,?)", rows)
    print(f"fine topics: {len(meta)} ({len(rows)} assignments)")


def fallback_openalex_topics(con) -> None:
    """No embeddings -> use OpenAlex primary topic as the topic assignment."""
    print("FALLBACK: clustering by OpenAlex primary topic")
    rows = con.execute("""
        SELECT topic, any_value(topic_name) AS label, count(*) AS n
        FROM works WHERE topic IS NOT NULL GROUP BY topic ORDER BY n DESC
    """).fetchall()
    tid_map = {r[0]: i for i, r in enumerate(rows)}
    meta = [[tid_map[r[0]], r[1], r[2], r[1], "openalex"] for r in rows]
    clusters = []
    for wid, topic in con.execute("SELECT id, topic FROM works WHERE topic IS NOT NULL").fetchall():
        clusters.append([wid, tid_map[topic]])
    write_tables(con, meta, clusters)
    con.execute("DROP TABLE IF EXISTS fine_topic_meta")
    con.execute("DROP TABLE IF EXISTS work_fine_cluster")
    con.execute("CREATE TABLE fine_topic_meta(topic_id INT, parent_topic_id INT, label TEXT, size INT, keywords TEXT, kind TEXT)")
    con.execute("CREATE TABLE work_fine_cluster(work_id TEXT, topic_id INT)")
    fine_meta = [[m[0] * 10000, m[0], m[1], m[2], m[3], "fallback"] for m in meta]
    con.executemany("INSERT INTO fine_topic_meta VALUES (?,?,?,?,?,?)", fine_meta)
    con.executemany("INSERT INTO work_fine_cluster VALUES (?,?)", [[wid, tid * 10000] for wid, tid in clusters])
    print(f"  {len(meta)} OpenAlex topics, {len(clusters)} assignments")


def run_bertopic(con) -> None:
    from bertopic import BERTopic
    from umap import UMAP
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer

    emb = np.load(EMB_NPY)
    with open(EMB_IDS) as fh:
        ids = json.load(fh)
    print(f"loaded embeddings {emb.shape} for {len(ids)} works")

    df = con.execute("SELECT id, title, abstract FROM works").fetchdf()

    def _s(x):
        return x if isinstance(x, str) else ""
    text_by_id = {r.id: (_s(r.title) + ". " + _s(r.abstract)).strip()
                  for r in df.itertuples()}
    docs = [text_by_id.get(i, "") or "untitled" for i in ids]

    umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0,
                      metric="cosine", low_memory=True, random_state=42)
    hdbscan_model = HDBSCAN(min_cluster_size=MIN_TOPIC_SIZE, min_samples=10,
                            metric="euclidean", cluster_selection_method="eom",
                            prediction_data=True)
    vectorizer = CountVectorizer(stop_words="english", ngram_range=(1, 2), min_df=10)
    topic_model = BERTopic(umap_model=umap_model, hdbscan_model=hdbscan_model,
                           vectorizer_model=vectorizer, calculate_probabilities=False,
                           verbose=True)
    print("fitting BERTopic (UMAP + HDBSCAN)... this is the slow step", flush=True)
    topics, _ = topic_model.fit_transform(docs, embeddings=emb)

    info = topic_model.get_topic_info()
    meta = []
    for row in info.itertuples():
        tid = int(row.Topic)
        kws = topic_model.get_topic(tid)
        kw_str = ", ".join(w for w, _ in kws[:10]) if kws else ""
        label = row.Name
        meta.append([tid, label, int(row.Count), kw_str,
                     "outlier" if tid == -1 else "bertopic"])
    clusters = [[wid, int(t)] for wid, t in zip(ids, topics)]
    write_tables(con, meta, clusters)
    write_fine_topics(con, ids, topics, emb, docs, {m[0]: m[1] for m in meta})
    n_topics = sum(1 for m in meta if m[0] != -1)
    print(f"BERTopic: {n_topics} topics ({len(clusters)} assignments)")


def main() -> None:
    con = duckdb.connect(config.DB_PATH)
    print("== Stage 4: topic model ==", flush=True)
    if os.path.exists(EMB_NPY) and os.path.exists(EMB_IDS):
        try:
            run_bertopic(con)
        except Exception as e:
            print(f"BERTopic failed ({e}); falling back to OpenAlex topics")
            fallback_openalex_topics(con)
    else:
        fallback_openalex_topics(con)
    con.close()


if __name__ == "__main__":
    main()
