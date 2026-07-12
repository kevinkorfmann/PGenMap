# PGenMap — Mapping the Evolution of Population Genetics (1985–2025)

**▶ Live interactive dashboard: https://kevinkorfmann.github.io/PGenMap/**
· **Narrative report: [outputs/report.md](outputs/report.md)**

A data-science project that reconstructs the global **population-genetics /
evolutionary-genomics** research community from bibliometric data and studies
**how the field has changed over ~40 years** — its questions, its methods, and
its social structure (labs and schools of thought).

Built from **28,885 population-genetics papers** by **2,200 researchers**
(Crossref), analysed into **52 topics**, **24 tracked methods**, **25
co-authorship communities**, and **213,647 within-corpus citations**.

Starting from a seed of well-known researchers (Rasmus Nielsen, Yun Song,
Aurélien Tellier, Matteo Fumagalli, the Mathiesons, Andrew Kern, Peter Ralph,
John Novembre, …) the pipeline expands to **1500+ researchers** via topic
crawling and co-authorship-network expansion, harvests their publications, and
analyses the corpus along four time axes.

## Data source

Google Scholar has **no API** and actively blocks scraping, so it is not usable
as a backbone. The project was designed for **OpenAlex**, but mid-build OpenAlex
moved to a **paid credit model** (the free tier now allows only ~100 requests
before an 8-hour lockout) and Semantic Scholar's free tier began requiring an
API key. The pipeline therefore harvests from **[Crossref](https://www.crossref.org)**,
which is fully free and open with a generous polite pool.

Crossref has no canonical author entities, so PGenMap builds researcher identity
from a normalized `family-initial` key (ORCID tracked as metadata) and uses
**venue + title-keyword relevance + collaborator overlap** to disambiguate — a
population geneticist's papers appear in specialist journals (*Molecular Biology
and Evolution*, *Genetics*, *Molecular Ecology*, *PLoS Genetics*, …) or carry
population-genetic titles, which separates them from same-named authors in other
fields. Trade-off vs. OpenAlex: thinner abstract coverage (so topic modelling
leans more on titles) and coarser disambiguation. The stdlib OpenAlex client
(`src/openalex.py`) remains in the repo for anyone with credits.

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

Crossref metadata is openly available. This repository contains code and derived
aggregates, not bulk redistribution of the source database. Please cite Crossref
(and OpenAlex / Semantic Scholar if you extend the pipeline to those sources).
