"""Central configuration for PGenMap.

Holds the OpenAlex polite-pool contact, the seed researcher list, the popgen
topic/concept anchors used for discovery + relevance filtering, and the method
lexicon used to tag papers for the method-trajectory analysis.
"""
from __future__ import annotations
import os

# --- Contact / polite pool -------------------------------------------------
MAILTO = "smathi@sas.upenn.edu"

# --- Paths -----------------------------------------------------------------
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
CACHE = os.path.join(DATA, "cache")
DB_PATH = os.path.join(DATA, "pgenmap.duckdb")
EMB_PATH = os.path.join(DATA, "embeddings.parquet")
OUT = os.path.join(ROOT, "outputs")
FIG = os.path.join(OUT, "figures")

# --- Scope -----------------------------------------------------------------
YEAR_MIN = 1985          # focus window start
YEAR_MAX = 2025
TARGET_UNIVERSE = 2200   # keep roughly this many top-ranked researchers

# --- Seed researchers ------------------------------------------------------
# (display name, institution hint or None). The hint disambiguates common
# names; discovery scores candidates on institution + popgen-topic share +
# citations and picks the best match. Topic crawl expands well beyond these.
SEED_RESEARCHERS: list[tuple[str, str | None]] = [
    # given seeds
    ("Rasmus Nielsen", "Berkeley"),
    ("Yun S. Song", "Berkeley"),
    ("Aurelien Tellier", "Munich"),
    ("Matteo Fumagalli", "London"),
    ("Iain Mathieson", "Pennsylvania"),
    ("Sara Mathieson", "Haverford"),
    ("Andrew D. Kern", "Oregon"),
    ("Peter L. Ralph", "Oregon"),
    ("John Novembre", "Chicago"),
    # coalescent / statistical / theory
    ("Richard Durbin", "Cambridge"),
    ("Gil McVean", "Oxford"),
    ("Jonathan K. Pritchard", "Stanford"),
    ("Molly Przeworski", "Columbia"),
    ("Guy Sella", "Columbia"),
    ("Graham Coop", "Davis"),
    ("Kelley Harris", "Washington"),
    ("Simon Myers", "Oxford"),
    ("Nicholas H. Barton", "Institute of Science and Technology Austria"),
    ("Brian Charlesworth", "Edinburgh"),
    ("Deborah Charlesworth", "Edinburgh"),
    ("Joachim Hermisson", "Vienna"),
    ("Pleuni S. Pennings", "San Francisco State"),
    ("Michael Lynch", "Arizona State"),
    ("Bret A. Payseur", "Wisconsin"),
    ("Jeffrey D. Jensen", "Arizona State"),
    ("Ryan N. Gutenkunst", "Arizona"),
    ("Daniel Wegmann", "Fribourg"),
    ("Laurent Excoffier", "Bern"),
    ("Montgomery Slatkin", "Berkeley"),
    ("John Wakeley", "Harvard"),
    ("Noah A. Rosenberg", "Stanford"),
    ("Marcus W. Feldman", "Stanford"),
    ("Carlos D. Bustamante", "Stanford"),
    ("Sohini Ramachandran", "Brown"),
    # ancient DNA / human evolution
    ("David Reich", "Harvard"),
    ("Pontus Skoglund", "Francis Crick Institute"),
    ("Johannes Krause", "Max Planck"),
    ("Eske Willerslev", "Copenhagen"),
    ("Svante Paabo", "Max Planck"),
    ("Beth Shapiro", "Santa Cruz"),
    ("Ludovic Orlando", "Toulouse"),
    ("Mattias Jakobsson", "Uppsala"),
    ("Priya Moorjani", "Berkeley"),
    ("Fernando Racimo", "Copenhagen"),
    ("Vagheesh M. Narasimhan", "Texas"),
    ("Nick Patterson", "Broad Institute"),
    ("Iosif Lazaridis", "Harvard"),
    ("Anna-Sapfo Malaspinas", "Lausanne"),
    ("Benjamin M. Peter", "Max Planck"),
    ("Kay Pruefer", "Max Planck"),
    ("Janet Kelso", "Max Planck"),
    # selection / adaptation
    ("Pardis C. Sabeti", "Harvard"),
    ("Hopi E. Hoekstra", "Harvard"),
    ("David Enard", "Arizona"),
    ("Emilia Huerta-Sanchez", "Brown"),
    ("Kirk E. Lohmueller", "Los Angeles"),
    ("Ryan D. Hernandez", "San Francisco"),
    ("Arbel Harpak", "Texas"),
    # phylogenetics / bayesian / methods
    ("Bruce Rannala", "Davis"),
    ("Ziheng Yang", "University College London"),
    ("Jotun Hein", "Oxford"),
    ("Alexei J. Drummond", "Auckland"),
    ("Jerome Kelleher", "Oxford"),
    ("Adam Siepel", "Cold Spring Harbor"),
    ("Ilan Gronau", "Reichman"),
    ("Melissa J. Hubisz", "Cornell"),
    # ML in popgen
    ("Daniel R. Schrider", "North Carolina"),
    ("Lex Flagel", "Minnesota"),
    ("Flora Jay", "Paris-Saclay"),
    # demographic inference / coalescent HMM
    ("Stephan Schiffels", "Max Planck"),
    ("Heng Li", "Dana-Farber"),
    ("Aylwyn Scally", "Cambridge"),
    ("Jonathan Terhorst", "Michigan"),
    ("Matthias Steinruecken", "Chicago"),
    ("Anand Bhaskar", "Stanford"),
    ("Simon Gravel", "McGill"),
    # structure / admixture
    ("Daniel Falush", "Shanghai"),
    ("Garrett Hellenthal", "University College London"),
    ("Alkes L. Price", "Harvard"),
    # French / European school
    ("Lounes Chikhi", "Toulouse"),
    ("Lluis Quintana-Murci", "Pasteur"),
    ("Etienne Patin", "Pasteur"),
    ("Olivier Francois", "Grenoble"),
    ("Renaud Vitalis", "Montpellier"),
    ("Raphael Leblois", "Montpellier"),
    ("Simon Boitard", "Toulouse"),
    ("Nicolas Bierne", "Montpellier"),
    ("Thomas Bataillon", "Aarhus"),
    ("Asger Hobolth", "Aarhus"),
    ("Mikkel H. Schierup", "Aarhus"),
    ("Kasper Munch", "Aarhus"),
    ("Bernard Y. Kim", "Stanford"),
    # plant / agricultural / non-human
    ("Jeffrey Ross-Ibarra", "Davis"),
    ("Brandon S. Gaut", "Irvine"),
    ("Michael D. Purugganan", "New York University"),
    ("Love Dalen", "Stockholm"),
    ("Rasmus Heller", "Copenhagen"),
]

# --- Popgen topic / concept anchors (OpenAlex) -----------------------------
# Verified live. Used both to seed discovery and to score relevance.
POPGEN_TOPIC_IDS = [
    "T10012",   # Genetic diversity and population structure
    "T11764",   # Evolution and Genetic Dynamics
    "T10261",   # Genetic Associations and Epidemiology (overlap; weighted low)
    "T10751",   # Forensic and Genetic Research (overlap; weighted low)
]
# Topics whose overlap with popgen is partial -> down-weight in scoring.
TOPIC_WEIGHTS = {
    "T10012": 1.0,
    "T11764": 1.0,
    "T10261": 0.3,
    "T10751": 0.3,
}
POPGEN_CONCEPT_IDS = [
    "C85721925",    # Population genetics
    "C146249460",   # Fixation (population genetics)
    "C24218269",    # Genetic load
    "C45091019",    # Coalescent theory-ish / evolutionary biology umbrella
]

# Search phrases used to enumerate more popgen topics during discovery.
TOPIC_SEARCH_PHRASES = [
    "population genetics",
    "coalescent theory",
    "natural selection genome",
    "demographic inference",
    "ancient DNA",
    "molecular evolution",
    "phylogenetics",
    "genome-wide association",
]

# --- Method lexicon --------------------------------------------------------
# canonical label -> list of case-insensitive regex alternatives.
# Applied to (title + abstract). Word boundaries handled in enrich step.
METHOD_LEXICON: dict[str, list[str]] = {
    "Coalescent theory":        [r"coalescent", r"\bcoalescence\b"],
    "Site frequency spectrum":  [r"site frequency spectr", r"\bSFS\b", r"allele frequency spectrum"],
    "ABC (approx. Bayesian)":   [r"approximate bayesian comput", r"\bABC\b(?!-)"],
    "PSMC / MSMC":              [r"\bPSMC\b", r"\bMSMC\b", r"pairwise sequentially markov", r"multiple sequentially markov"],
    "SMC++ / sequential MC":    [r"SMC\+\+", r"sequential markov coalescent"],
    "Ancient DNA":              [r"ancient DNA", r"\baDNA\b", r"paleogenom", r"archaic genom"],
    "STRUCTURE / ADMIXTURE":    [r"\bSTRUCTURE\b program", r"\bADMIXTURE\b", r"admixture proportion", r"population structure inference"],
    "F-statistics / qpAdm":     [r"\bqpAdm\b", r"\bqpGraph\b", r"\bf3[- ]statistic", r"\bf4[- ]statistic", r"\bD-statistic", r"patterson.?s d"],
    "Selection scan (iHS/EHH)": [r"\biHS\b", r"\bXP-?EHH\b", r"\bnSL\b", r"\bSDS\b", r"extended haplotype homozygosity", r"selective sweep", r"selection scan"],
    "Tajima's D / neutrality":  [r"tajima'?s d", r"neutrality test", r"fay and wu", r"\bHKA test"],
    "SLiM (forward sim)":       [r"\bSLiM\b", r"forward[- ]time simulation", r"forward genetic simulation"],
    "msprime / tskit / ARG":    [r"\bmsprime\b", r"\btskit\b", r"tree sequence", r"ancestral recombination graph", r"\bARG\b", r"succinct tree"],
    "Deep learning":            [r"deep learning", r"convolutional neural", r"\bCNN\b", r"neural network", r"deep neural"],
    "Machine learning (other)": [r"machine learning", r"random forest", r"support vector", r"gradient boost", r"supervised learning"],
    "GWAS":                     [r"genome[- ]wide association", r"\bGWAS\b"],
    "Polygenic scores":         [r"polygenic (score|risk|adaptation)", r"\bPRS\b", r"polygenic selection"],
    "Background/linked select.": [r"background selection", r"linked selection", r"hitchhiking", r"hill[- ]robertson"],
    "Introgression / gene flow": [r"introgress", r"gene flow", r"hybridization", r"admixture graph"],
    "Effective population size": [r"effective population size", r"\bNe\b", r"population size history"],
    "Recombination / LD maps":  [r"recombination rate", r"linkage disequilibrium map", r"recombination map", r"\bLDhat\b", r"\bhotspot"],
    "Whole-genome sequencing":  [r"whole[- ]genome sequenc", r"\bWGS\b", r"next[- ]generation sequenc", r"resequenc"],
    "SNP arrays / genotyping":  [r"SNP array", r"SNP chip", r"genotyping array", r"HapMap"],
    "Demographic inference":    [r"demographic (inference|history|model)", r"\bdadi\b", r"\bmomi\b", r"fastsimcoal", r"\bmoments\b population", r"bottleneck.*expansion"],
    "Conservation genomics":    [r"conservation genom", r"endangered.*genom", r"inbreeding depression", r"genetic rescue"],
}

# UI-friendly grouping of methods into eras/themes for the dashboard.
METHOD_GROUPS = {
    "Classical / theory": ["Coalescent theory", "Site frequency spectrum", "Tajima's D / neutrality",
                            "Effective population size", "Recombination / LD maps", "Background/linked select."],
    "Selection": ["Selection scan (iHS/EHH)", "Polygenic scores", "GWAS"],
    "Ancient DNA era": ["Ancient DNA", "F-statistics / qpAdm", "STRUCTURE / ADMIXTURE", "Introgression / gene flow"],
    "Inference machinery": ["ABC (approx. Bayesian)", "PSMC / MSMC", "SMC++ / sequential MC",
                            "Demographic inference"],
    "Simulation / ARG": ["SLiM (forward sim)", "msprime / tskit / ARG"],
    "ML turn": ["Deep learning", "Machine learning (other)"],
    "Sequencing tech": ["Whole-genome sequencing", "SNP arrays / genotyping"],
    "Applied": ["Conservation genomics"],
}
