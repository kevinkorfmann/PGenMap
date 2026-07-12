# How Population Genetics Evolved, 1985–2025

*A bibliometric map of the field, built from 28,885 population-genetics
publications by 2,200 researchers, harvested from Crossref and analysed by
topic, method, collaboration, and citation.*

---

## What this is, and how to read it

This report accompanies the interactive dashboard at
[kevinkorfmann.github.io/PGenMap](https://kevinkorfmann.github.io/PGenMap/). It
is a data-driven attempt to watch a scientific field change shape over four
decades. Starting from ninety-seven seed researchers — Rasmus Nielsen, the
Charlesworths, Montgomery Slatkin, Yun Song, David Reich, Aurélien Tellier,
Andrew Kern, Peter Ralph, John Novembre and others — the pipeline expanded
outward through co-authorship to a universe of 2,200 population and evolutionary
geneticists, then harvested every population-genetics-relevant paper it could
attribute to them. The result is a corpus of 28,885 works spanning 1985 to 2025,
of which 11,891 carry abstracts, connected by 213,647 within-corpus citations.

The numbers below should be read as *field-scale signal, not exact
bibliometrics*. The corpus comes from Crossref, which has no canonical author
identities, so a paper is attributed to a researcher through a normalized
name key filtered by venue and title relevance. That approach recovers the bulk
of a person's population-genetics output but undercounts authors who publish
under initials or whose names carry diacritics, and it cannot perfectly separate
same-named researchers. Method "shares" are the fraction of a year's papers
whose title or abstract mentions a method; they track attention and vocabulary,
not a census of techniques. With those caveats, the temporal patterns are
strikingly coherent — and they line up with the field's lived history.

## The field widened faster than it grew

The most basic signal is expansion. Annual output in the corpus climbs from
under 200 papers around 1990 to roughly a thousand a year through the 2010s.
But the more telling change is not how much the field published — it is what it
published *about*. The topic model, which clusters papers by the meaning of
their abstracts, shows the centre of gravity migrating away from the classical
model organisms that defined twentieth-century genetics and toward the wild,
the microbial, and the human at genome scale.

The themes in visible decline all peaked early and all name a model system of
the old order: *Drosophila melanogaster* variation (peaking around 2000),
*Arabidopsis thaliana* (2009), yeast transcription and expression (2014),
maize and rice domestication genetics (2005), and mitochondrial-DNA
phylogeography (2009). Against them, the rising themes are conspicuously
organismally diverse and applied: fish and Atlantic salmonid population
structure, insect and host–parasite systems, bacterial and microbial
populations, viral evolution, sex-chromosome biology, crop domestication at
genomic scale, and genome-wide association. In one sentence: population genetics
stopped being a discipline practised mostly on a handful of laboratory species
and became a way of reading the genomes of anything that has one — wild
vertebrates, pathogens, crops, and ourselves.

## The methodological arc

Tracking specific methods year by year turns that migration into a sequence of
overlapping waves. Each entry below is the method's share of corpus papers at
five snapshots (1990 / 2000 / 2010 / 2020 / 2025).

**The coalescent as connective tissue.** Coalescent theory is the one idea that
grows monotonically across the whole period — from essentially nothing in 1990
to 2.2% in 2000, 3.3% in 2020 and 4.5% by 2025. It is not a wave so much as a
rising tide: the theoretical language in which almost everything else came to be
expressed.

**The clustering revolution (2000s).** The first great empirical wave is
model-based clustering. STRUCTURE-style admixture inference goes from 0.5% in
2000 to 1.6% in 2010 and 5.0% by 2020, and its fingerprints are everywhere in
the citation graph (see below). This is the decade in which "what populations
are these individuals from, and in what proportions?" became a question you
answered with software rather than with allozymes and intuition.

**The sequencing and association surge (2010s).** Whole-genome sequencing
appears from nowhere to 2.7% in 2010 and 5.6% by 2020; genome-wide association
studies arrive on the same schedule, holding around 3.3–3.7% from 2010 onward.
The technology of the genome and the epidemiology of complex traits enter the
population-genetics vocabulary together.

**Demographic inference comes of age.** Reconstructing population history from
data grows steadily throughout — 0.6% (2000) → 1.8% (2010) → 2.8% (2020) →
5.8% (2025) — until, by the end of the period, it is the single most prominent
method in the corpus. Ancient DNA rises in parallel (0.3% → 1.8% → 2.6% →
3.6%), giving the history inference a direct empirical anchor in the past.

**The simulation-and-learning turn (2020s).** The most recent wave is
computational. The tree-sequence toolkit — `msprime`, `tskit`, and the ancestral
recombination graph — is flat and marginal until about 2020 and then jumps to
1.5% by 2025. Deep learning follows the same late, steep curve: undetectable
before the late 2010s, 0.5% in 2020, and 2.5% by 2025, a fivefold rise in half a
decade. Together they mark population genetics acquiring, for the first time, a
native simulation-and-inference stack built for genome-scale data and a
machine-learning idiom to go with it.

Smaller methods punctuate the story rather than dominate it: approximate
Bayesian computation flares in the late 2000s and recedes; selection scans
(iHS, XP-EHH and kin) climb to 2.6%; the site-frequency-spectrum vocabulary
roughly doubles after 2010. None of these is the headline, but each is a legible
thread in the weave.

## The software that holds the field together

Ranking papers by how often they are cited *by other papers within this corpus*
— the field's internal load-bearing references — produces a list that is almost
entirely method and software. Pritchard, Stephens and Donnelly's 2000 STRUCTURE
paper is the single most-cited work in the corpus (881 internal citations),
followed by Hudson's 2002 `ms` coalescent simulator (652) and Evanno's 2005
method for choosing the number of clusters (630). ADMIXTURE (2009), Gutenkunst's
`∂a∂i` demographic-inference framework (2009), RAxML (2014), the MrBayes and
BEAST Bayesian-phylogenetics engines, Excoffier's 1992 AMOVA, Voight et al.'s
2006 "Map of Recent Positive Selection in the Human Genome," and — reaching back
furthest — Tajima's neutrality test all sit near the top. The field's
shared foundation, in other words, is not a canon of famous findings but a
toolkit of shared methods; population genetics coheres around the programs it
runs.

## Schools of thought

The co-authorship network resolves into twenty-five communities, and once each
community is described by the methods that are *distinctively* enriched in it
(rather than the ones common to everyone), the schools become legible. A large
computational cluster is fingerprinted by the tree-sequence toolkit, the site
frequency spectrum, and selection scans. A theoretical-population-genetics
community centred on Brian Charlesworth is marked by background and linked
selection, `tskit`, and effective-population-size inference — a precise echo of
the linked-selection research programme he helped found. A human-genetics
cluster around David Reich is defined by GWAS, polygenic scores, and SNP arrays;
a distinct ancient-DNA community is marked by F-statistics, qpAdm, and
admixture-graph methods; and a conservation-and-molecular-ecology community
around Jérôme Goudet is characterised by approximate Bayesian computation and
conservation genomics. The social structure of the field, read blind from who
writes with whom, reconstructs the intellectual structure that practitioners
would recognise.

## What changed, in one paragraph

Over forty years population genetics broadened its subjects from a few model
organisms to the whole tree of life and to human medicine; it re-tooled from
single-locus, allozyme-and-mtDNA methods to model-based clustering, then to
whole-genome sequencing and association, then to demographic and ancient-DNA
inference, and most recently to a simulation-and-deep-learning stack; and
throughout, it held itself together not with a canon of results but with a
shared library of software. The coalescent runs underneath all of it, the one
idea that only ever grew.

---

## Method

Data were harvested from the Crossref REST API (no key required; the OpenAlex
plan was abandoned when OpenAlex moved to paid credits mid-project, and Semantic
Scholar's free tier began requiring a key). Researcher identity is a normalized
`family-initial` key; population-genetics relevance is gated by specialist-venue
membership or population-genetic title keywords. Abstracts were embedded with a
sentence-transformer model and clustered with BERTopic (UMAP + HDBSCAN) into 52
topics; methods were tagged by a curated regular-expression lexicon; communities
were detected with Louvain on the weighted co-authorship graph; and the citation
graph was restricted to within-corpus references. Full code, the DuckDB store,
and the interactive dashboard are in the repository. Figures and per-researcher
detail are best explored on the
[dashboard](https://kevinkorfmann.github.io/PGenMap/).
