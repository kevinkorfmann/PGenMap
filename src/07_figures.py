"""Stage 7 — Publication figures.

Computes a 2D UMAP projection of the paper embeddings and renders a set of
static figures (PNG) into outputs/figures/ and docs/figures/:
  umap_topics        2D embedding scatter, coloured by topic
  method_adoption    signature-method share over time
  method_heatmap     method x year prevalence heatmap
  topic_streamgraph  top-topic share over time (stacked)
  growth             corpus size per year
  community_sizes    largest co-authorship communities + distinctive method
"""
from __future__ import annotations
import json
import os
import shutil
import sys

import duckdb
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager  # noqa: F401

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

FIGDIR = config.FIG
DOCFIG = os.path.join(config.ROOT, "docs", "figures")
PAL = ['#0f8f80', '#c9821f', '#3f7fd6', '#c94f74', '#7d5bc0', '#5a9e2f', '#c79a2a',
       '#2aa5b8', '#d1683f', '#7d9160', '#a869c0', '#3f8f7f', '#b8605a', '#5f8fb5']
INK = "#1a2b2f"
MUTED = "#5b7178"

plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white", "font.size": 11, "font.family": "sans-serif",
    "axes.edgecolor": "#c9d4d2", "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.titlecolor": INK,
    "axes.grid": True, "grid.color": "#eef2f1", "grid.linewidth": 1,
    "axes.spines.top": False, "axes.spines.right": False,
})

Y0, Y1 = config.YEAR_MIN, config.YEAR_MAX
YEARS = list(range(Y0, Y1 + 1))


def clean_topic(label):
    # drop the leading topic number, split multiword tokens, dedupe words
    raw = (label or "").split("_")[1:]
    out = []
    for tok in raw:
        for w in tok.split():
            if w and w.lower() not in {x.lower() for x in out}:
                out.append(w)
    return " ".join(out[:3]) or (label or "topic")


def save(fig, name):
    for d in (FIGDIR, DOCFIG):
        os.makedirs(d, exist_ok=True)
        fig.savefig(os.path.join(d, name), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  figure -> {name}")


def fig_umap(con):
    from umap import UMAP
    emb = np.load(os.path.join(config.DATA, "embeddings.npy"))
    ids = json.load(open(os.path.join(config.DATA, "emb_ids.json")))
    idx = {w: i for i, w in enumerate(ids)}
    rows = con.execute("SELECT work_id, topic_id FROM work_cluster").fetchall()
    topic_of = {w: t for w, t in rows}
    tmeta = {r[0]: r[1] for r in con.execute("SELECT topic_id, label FROM topic_meta").fetchall()}
    tsize = {r[0]: r[1] for r in con.execute("SELECT topic_id, size FROM topic_meta").fetchall()}
    print("  computing 2D UMAP (this is the slow figure)...", flush=True)
    xy = UMAP(n_neighbors=15, n_components=2, min_dist=0.15, metric="cosine",
              random_state=42, low_memory=True).fit_transform(emb)

    top_topics = [t for t, _ in sorted(((t, s) for t, s in tsize.items() if t >= 0),
                                        key=lambda x: -x[1])[:14]]
    color_of = {t: PAL[i] for i, t in enumerate(top_topics)}
    tid_arr = np.array([topic_of.get(w, -1) for w in ids])

    fig, ax = plt.subplots(figsize=(11, 8.6))
    # background: non-top-topic points in light grey
    other = ~np.isin(tid_arr, top_topics)
    ax.scatter(xy[other, 0], xy[other, 1], s=2, c="#d7dedc", alpha=0.35, linewidths=0)
    for t in top_topics:
        mask = tid_arr == t
        ax.scatter(xy[mask, 0], xy[mask, 1], s=3, c=color_of[t], alpha=0.55, linewidths=0)
    # label each top topic at its median position
    for t in top_topics:
        mask = tid_arr == t
        if mask.sum() < 5:
            continue
        cx, cy = np.median(xy[mask, 0]), np.median(xy[mask, 1])
        ax.text(cx, cy, clean_topic(tmeta.get(t, str(t))), fontsize=9, weight="bold",
                ha="center", va="center", color=INK,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color_of[t], alpha=0.85, lw=1.2))
    # A handful of UMAP outliers can otherwise reserve most of the canvas for
    # empty space.  Crop only the extreme 0.5% tails; the dense field remains
    # intact and the semantic structure becomes legible at dashboard size.
    for axis, vals in ((ax.set_xlim, xy[:, 0]), (ax.set_ylim, xy[:, 1])):
        lo, hi = np.percentile(vals, [0.5, 99.5])
        pad = (hi - lo) * 0.055
        axis(lo - pad, hi + pad)
    ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(f"Semantic map of the corpus — {len(ids):,} papers by topic (UMAP of abstract embeddings)",
                 fontsize=13, weight="bold", loc="left", pad=12)
    ax.set_xlabel("Each point is a paper; nearby points read similarly. Colour = one of the 14 largest topics.",
                  fontsize=9.5, color=MUTED)
    save(fig, "umap_topics.png")


def fig_methods(analysis):
    ms = analysis["method_share"]
    sig = ['Coalescent theory', 'STRUCTURE / ADMIXTURE', 'Whole-genome sequencing', 'GWAS',
           'Demographic inference', 'Ancient DNA', 'Selection scan (iHS/EHH)',
           'msprime / tskit / ARG', 'Deep learning']
    fig, ax = plt.subplots(figsize=(10, 6))
    for i, m in enumerate([m for m in sig if m in ms]):
        vals = np.array(ms[m]) * 100
        ax.plot(YEARS, vals, color=PAL[i % len(PAL)], lw=2.2, label=m)
        li = len(vals) - 1
        ax.scatter([YEARS[li]], [vals[li]], color=PAL[i % len(PAL)], s=18, zorder=3)
    ax.set_xlim(1990, Y1); ax.set_ylabel("share of yearly papers (%)")
    ax.set_title("Method adoption over time", fontsize=13, weight="bold", loc="left")
    ax.legend(frameon=False, fontsize=9, ncol=2, loc="upper left")
    save(fig, "method_adoption.png")


def fig_heatmap(analysis):
    methods = analysis["methods"]
    order = sorted(methods, key=lambda m: -sum(analysis["method_share"].get(m, [0])))
    M = np.array([analysis["method_share"][m] for m in order]) * 100
    fig, ax = plt.subplots(figsize=(11, 8))
    im = ax.imshow(M, aspect="auto", cmap="YlGnBu",
                   extent=[Y0, Y1, len(order), 0], vmax=np.percentile(M, 99))
    ax.set_yticks(np.arange(len(order)) + 0.5); ax.set_yticklabels(order, fontsize=8.5)
    ax.set_xlabel("year"); ax.grid(False)
    ax.set_title("Method prevalence heatmap (share of yearly papers, %)",
                 fontsize=13, weight="bold", loc="left", pad=10)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02); cb.outline.set_visible(False)
    save(fig, "method_heatmap.png")


def fig_topics(analysis):
    topics = sorted(analysis["topics"], key=lambda t: -t["size"])[:12]
    shares = np.array([t["share"] for t in topics]) * 100
    labels = [clean_topic(t["label"]) for t in topics]
    fig, ax = plt.subplots(figsize=(11, 6.4))
    ax.stackplot(YEARS, shares, colors=[PAL[i % len(PAL)] for i in range(len(topics))],
                 labels=labels, alpha=0.9, edgecolor="white", linewidth=0.3)
    ax.set_xlim(Y0, Y1); ax.set_ylabel("share of yearly papers (%)")
    ax.set_title("Topic evolution — the 12 largest themes over time", fontsize=13, weight="bold", loc="left")
    ax.legend(frameon=False, fontsize=8, ncol=3, loc="upper left")
    save(fig, "topic_streamgraph.png")


def fig_growth(analysis):
    tot = analysis["field_totals"]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.fill_between(YEARS, tot, color=PAL[0], alpha=0.18)
    ax.plot(YEARS, tot, color=PAL[0], lw=2.4)
    ax.set_xlim(Y0, Y1); ax.set_ylabel("papers in corpus")
    ax.set_title(f"Corpus growth, {Y0}–{Y1}", fontsize=13, weight="bold", loc="left")
    save(fig, "growth.png")


def fig_communities():
    net = json.load(open(os.path.join(config.OUT, "network.json")))
    comms = [c for c in net.get("communities", []) if c.get("size", 0) >= 20][:12]
    comms.sort(key=lambda c: c["size"])
    labels = []
    for c in comms:
        meth = (c.get("top_methods") or ["—"])[0]
        who = ""
        if c.get("top_members"):
            who = c["top_members"][0]["name"].split()[-1]
        labels.append(f"{meth}  ·  {who}")
    sizes = [c["size"] for c in comms]
    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.barh(range(len(comms)), sizes, color=PAL[3], alpha=0.85)
    ax.set_yticks(range(len(comms))); ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("researchers in community"); ax.grid(axis="y", visible=False)
    ax.set_title("Schools of thought — largest co-authorship communities\n(labelled by distinctive method · notable member)",
                 fontsize=12.5, weight="bold", loc="left", pad=10)
    save(fig, "community_sizes.png")


def main():
    con = duckdb.connect(config.DB_PATH, read_only=True)
    analysis = json.load(open(os.path.join(config.OUT, "analysis.json")))
    print("== Stage 7: figures ==", flush=True)
    if os.path.exists(DOCFIG):
        shutil.rmtree(DOCFIG)
    fig_methods(analysis)
    fig_heatmap(analysis)
    fig_topics(analysis)
    fig_growth(analysis)
    fig_communities()
    fig_umap(con)          # last: the slow one
    con.close()
    print("figures done")


if __name__ == "__main__":
    main()
