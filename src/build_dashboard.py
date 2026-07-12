"""Generate the GitHub Pages dashboard (docs/index.html) from whatever data
exists so far. Designed to be run repeatedly as the pipeline fills in:

  after discovery      -> universe stats + researcher directory
  after build_db       -> corpus stats + works-per-year
  after analyze        -> method trajectories, topics, network, pivotal papers

Each section renders only if its data is present; missing sections show a
"building" note. Output is a single self-contained HTML file with data inlined.
"""
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

import re

DOCS = os.path.join(config.ROOT, "docs")
ANALYSIS = os.path.join(config.OUT, "analysis.json")
NETWORK = os.path.join(config.OUT, "network.json")
RESEARCHERS = os.path.join(config.DATA, "researchers.jsonl")

_INST_KW = re.compile(r"(universit|instituto?|institut|laborat/?|laboratoire|college|"
                      r"max planck|max-planck|hospital|academ|museum|polytechni|"
                      r"cnrs|centre national|national institute|broad institute|"
                      r"cold spring harbor|wellcome|sanger|crick institute|"
                      r"école|escuela|université|universidad|universität)", re.IGNORECASE)


def clean_inst(s):
    """Reduce a verbose Crossref affiliation string to a readable institution name."""
    if not s:
        return None
    parts = [p.strip() for p in re.split(r"[,;]", s) if p.strip()]
    for p in parts:
        if _INST_KW.search(p) and len(p) < 60:
            return re.sub(r"\s+", " ", p)
    # fallback: shortest part that still names something (skip 'Department of ...')
    cand = [p for p in parts if not p.lower().startswith(("department", "dept", "division",
            "school of", "faculty", "unit", "laboratory of"))]
    pick = (cand or parts or [s])[0]
    return re.sub(r"\s+", " ", pick)[:60]


def read_db_context():
    """After build_db (before full analysis): accurate corpus + per-researcher
    stats straight from DuckDB, so counts reflect the harvested corpus."""
    import duckdb
    con = duckdb.connect(config.DB_PATH, read_only=True)
    n_works = con.execute("SELECT count(*) FROM works").fetchone()[0]
    n_abs = con.execute("SELECT count(*) FROM works WHERE abstract IS NOT NULL").fetchone()[0]
    n_res = con.execute("SELECT count(*) FROM researchers").fetchone()[0]
    n_seed = con.execute("SELECT count(*) FROM researchers WHERE seed").fetchone()[0]
    yr = con.execute("SELECT min(year), max(year) FROM works WHERE year IS NOT NULL").fetchone()
    rows = con.execute("""
        SELECT name, institution, cited_by_count, works_count, recent_year, seed
        FROM researchers ORDER BY cited_by_count DESC NULLS LAST LIMIT 1200
    """).fetchall()
    con.close()
    researchers = [{
        "name": r[0], "inst": clean_inst(r[1]), "cites": r[2], "works": r[3],
        "last": r[4], "seed": bool(r[5]), "methods": [], "topics": [], "collab": [],
    } for r in rows]
    meta = {"researchers": n_res, "works": n_works, "works_with_abstract": n_abs,
            "seeds": n_seed, "year_min": yr[0] or config.YEAR_MIN, "year_max": yr[1] or config.YEAR_MAX}
    return {"meta": meta, "researchers": researchers}


def load_context():
    """Assemble whatever data is available into a compact context for the page."""
    ctx = {"stage": "seed"}
    if os.path.exists(ANALYSIS):
        with open(ANALYSIS) as fh:
            ctx["analysis"] = json.load(fh)
        ctx["stage"] = "full"
    elif os.path.exists(config.DB_PATH):
        ctx["db"] = read_db_context()
        ctx["stage"] = "corpus"
    elif os.path.exists(RESEARCHERS):
        rows = [json.loads(l) for l in open(RESEARCHERS) if l.strip()]
        rows.sort(key=lambda r: r.get("score", 0), reverse=True)
        ctx["researchers_partial"] = rows
        ctx["stage"] = "universe"
    if os.path.exists(NETWORK):
        with open(NETWORK) as fh:
            ctx["network"] = json.load(fh)
    return ctx


def compact_for_page(ctx):
    """Trim to what the page needs, keeping the inlined payload small."""
    out = {"stage": ctx["stage"]}
    if "analysis" in ctx:
        a = ctx["analysis"]
        out["meta"] = a.get("meta", {})
        out["years"] = a.get("years", [])
        out["field_totals"] = a.get("field_totals", [])
        out["methods"] = a.get("methods", [])[:24]
        out["method_groups"] = a.get("method_groups", {})
        out["method_share"] = {m: a["method_share"][m] for m in out["methods"] if m in a.get("method_share", {})}
        out["method_milestones"] = a.get("method_milestones", [])
        out["topics"] = [{k: t[k] for k in ("id", "label", "keywords", "size", "share", "peak_year", "trend") if k in t}
                         for t in a.get("topics", [])[:28]]
        out["communities"] = a.get("communities", [])[:14]
        out["pivotal"] = a.get("pivotal_papers", [])[:30]
        # researcher directory: keep compact fields, cap count
        R = a.get("researchers", [])
        R.sort(key=lambda r: (r.get("cites") or 0), reverse=True)
        out["researchers"] = [{
            "name": r.get("name"), "inst": clean_inst(r.get("inst")), "country": r.get("country"),
            "cites": r.get("cites"), "works": r.get("works"), "seed": r.get("seed"),
            "community": r.get("community"),
            "first": r.get("first_year"), "last": r.get("last_year"),
            "methods": (r.get("top_methods") or [])[:4],
            "topics": (r.get("top_topics") or [])[:3],
            "collab": [c.get("name") for c in (r.get("collaborators") or [])[:4]],
        } for r in R[:1200]]
    elif "db" in ctx:
        out["meta"] = ctx["db"]["meta"]
        out["researchers"] = ctx["db"]["researchers"]
    elif "researchers_partial" in ctx:
        rows = ctx["researchers_partial"]
        out["researchers"] = [{
            "name": r.get("name"), "inst": clean_inst((r.get("institutions") or [None])[0]),
            "cites": r.get("cited_by_count"), "works": r.get("popgen_works"),
            "seed": r.get("seed"), "last": r.get("recent_year"),
            "methods": [], "topics": [], "collab": [],
        } for r in rows[:1200]]
        out["meta"] = {"researchers": len(rows),
                       "seeds": sum(1 for r in rows if r.get("seed"))}
    if "network" in ctx:
        net = ctx["network"]
        # keep top nodes by degree + their edges for a lightweight graph
        nodes = sorted(net.get("nodes", []), key=lambda n: n.get("degree", 0), reverse=True)[:450]
        keep = {n["id"] for n in nodes}
        edges = [e for e in net.get("edges", []) if e["s"] in keep and e["t"] in keep][:2500]
        out["net"] = {"nodes": nodes, "edges": edges,
                      "snapshots": net.get("snapshots", []),
                      "communities": net.get("communities", [])[:14]}
    return out


def render(payload):
    data_json = json.dumps(payload, separators=(",", ":"))
    return HTML_TEMPLATE.replace("/*__DATA__*/", data_json)


def main():
    ctx = load_context()
    payload = compact_for_page(ctx)
    os.makedirs(DOCS, exist_ok=True)
    html = render(payload)
    with open(os.path.join(DOCS, "index.html"), "w") as fh:
        fh.write(html)
    size = len(html) / 1024
    print(f"dashboard -> docs/index.html  (stage={payload['stage']}, {size:.0f} KB)")


# The page template lives in a sibling module string to keep this file readable.
from dashboard_template import HTML_TEMPLATE  # noqa: E402

if __name__ == "__main__":
    main()
