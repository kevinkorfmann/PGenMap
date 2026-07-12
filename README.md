# PGenMap — Mapping the Evolution of Population Genetics (1985–2025)

A data-science project that reconstructs the global **population-genetics /
evolutionary-genomics** research community from bibliometric data and studies
**how the field has changed over ~40 years** — its questions, its methods, and
its social structure (labs and schools of thought).

Starting from a seed of well-known researchers (Rasmus Nielsen, Yun Song,
Aurélien Tellier, Matteo Fumagalli, the Mathiesons, Andrew Kern, Peter Ralph,
John Novembre, …) the pipeline expands to **1500+ researchers** via topic
crawling and co-authorship-network expansion, harvests their publications, and
analyses the corpus along four time axes.

## Why not Google Scholar?

Google Scholar has **no API** and actively blocks scraping. This project is
built on **[OpenAlex](https://openalex.org)** (primary) — a free, open scholarly
database that returns *canonically disambiguated* authors with institutions,
per-work year, topics, citations, reference lists, and reconstructable
abstracts — with **Semantic Scholar** / **Crossref** as fallbacks. OpenAlex
cleanly resolves the real Rasmus Nielsen (`A5088476239`, 79k citations); Google
Scholar and Semantic Scholar's raw author search fragment him into dozens of
"R. Nielsen" stubs.

## The four time-axis analyses

1. **Topic evolution** — embedding-based topic modelling of abstracts, tracked
   year-by-year (classical coalescent → SNP arrays → ancient-DNA revolution →
   the machine-learning turn → the ARG / tree-sequence era).
2. **Method / keyword trajectories** — adoption curves for specific methods
   (coalescent, ABC, PSMC/MSMC, ancient DNA, SLiM, `msprime`/`tskit`, deep
   learning, selection scans …).
3. **Collaboration networks** — co-authorship communities ("schools"),
   snapshotted in 5-year windows to show how they form and merge.
4. **Career trajectories & citation flow** — how individual labs shift focus
   over a career, and which ideas became influential when.

## Pipeline

```
src/openalex.py     cached, resumable OpenAlex client (stdlib only)
src/01_discover.py  build the 1500+ researcher universe
src/02_harvest.py   pull all works, dedupe
src/03_enrich.py    reconstruct abstracts, embed, tag methods
src/04_topics.py    topic model + per-year prevalence
src/05_network.py   co-authorship / citation graphs, communities
src/06_analyze.py   trajectories, career drift, export analysis.json
```

Run end-to-end (resumable — every API response is cached under `data/cache/`):

```bash
uv venv --python 3.12 && uv pip install -e .
bash run.sh
```

## Outputs

- `outputs/report.md` — narrative "How Population Genetics Evolved, 1985–2025"
- `outputs/figures/` — publication-quality figures
- `outputs/dashboard.html` — self-contained interactive dashboard
- `outputs/analysis.json` — compact aggregates behind the dashboard
- `data/pgenmap.duckdb` — the analytic store (regenerable; not committed)

## Data sources & licensing

OpenAlex data is CC0. This repository contains code and derived aggregates, not
bulk redistribution of the source databases. Please cite OpenAlex, Semantic
Scholar, and Crossref if you build on this.

---

*Built with [Claude Code](https://claude.com/claude-code).*
