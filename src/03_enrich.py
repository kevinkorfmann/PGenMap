"""Stage 3 — Enrich the corpus.

1. Tag each work against the method lexicon (regex on title + abstract) ->
   DuckDB table work_methods(work_id, method).
2. Embed each work (title + abstract) with a sentence-transformers model ->
   data/embeddings.npy (float32 NxD) + data/emb_ids.json (row order).

Embeddings use the Apple-Silicon MPS backend when available; the model choice
falls back gracefully if HuggingFace is unreachable.
"""
from __future__ import annotations
import json
import os
import re
import sys

import duckdb
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

EMB_NPY = os.path.join(config.DATA, "embeddings.npy")
EMB_IDS = os.path.join(config.DATA, "emb_ids.json")
MODEL_CANDIDATES = ["all-MiniLM-L6-v2", "paraphrase-MiniLM-L3-v2"]


def compile_lexicon():
    compiled = {}
    for method, pats in config.METHOD_LEXICON.items():
        compiled[method] = [re.compile(p, re.IGNORECASE) for p in pats]
    return compiled


def tag_methods(con, df) -> None:
    lex = compile_lexicon()
    con.execute("DROP TABLE IF EXISTS work_methods")
    con.execute("CREATE TABLE work_methods(work_id TEXT, method TEXT)")
    rows = []
    for wid, title, abstract in zip(df["id"], df["title"], df["abstract"]):
        title = title if isinstance(title, str) else ""
        abstract = abstract if isinstance(abstract, str) else ""
        text = (title + " " + abstract).strip()
        if not text:
            continue
        for method, patterns in lex.items():
            if any(p.search(text) for p in patterns):
                rows.append([wid, method])
        if len(rows) >= 50000:
            con.executemany("INSERT INTO work_methods VALUES (?,?)", rows)
            rows = []
    if rows:
        con.executemany("INSERT INTO work_methods VALUES (?,?)", rows)
    n = con.execute("SELECT count(*) FROM work_methods").fetchone()[0]
    print(f"method tags: {n} (work,method) pairs")


def pick_device():
    try:
        import torch
        if torch.backends.mps.is_available():
            return "mps"
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def embed(df) -> bool:
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as e:
        print(f"sentence-transformers unavailable ({e}); skipping embeddings")
        return False
    device = pick_device()
    model = None
    for name in MODEL_CANDIDATES:
        try:
            model = SentenceTransformer(name, device=device)
            print(f"embedding with {name} on {device}")
            break
        except Exception as e:
            print(f"  model {name} failed to load: {e}")
    if model is None:
        print("no embedding model could load (HuggingFace unreachable?); "
              "topic stage will fall back to OpenAlex topics")
        return False

    texts, ids = [], []
    for wid, title, abstract in zip(df["id"], df["title"], df["abstract"]):
        title = title if isinstance(title, str) else ""
        abstract = abstract if isinstance(abstract, str) else ""
        t = title.strip()
        if abstract:
            t = (t + ". " + abstract).strip()
        texts.append(t if t else "untitled")
        ids.append(wid)
    print(f"encoding {len(texts)} works...", flush=True)
    emb = model.encode(texts, batch_size=128, show_progress_bar=True,
                       convert_to_numpy=True, normalize_embeddings=True)
    np.save(EMB_NPY, emb.astype(np.float32))
    with open(EMB_IDS, "w") as fh:
        json.dump(ids, fh)
    print(f"embeddings: {emb.shape} -> {EMB_NPY}")
    return True


def main() -> None:
    con = duckdb.connect(config.DB_PATH)
    df = con.execute("SELECT id, title, abstract FROM works").fetchdf()
    print(f"== Stage 3: enrich {len(df)} works ==", flush=True)
    tag_methods(con, df)
    con.close()
    embed(df)


if __name__ == "__main__":
    main()
