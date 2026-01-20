# atlas-institutional-gravity
OSINT for UN and the committee of 300
# UN NetMap (UN / Political / Financial Network Mapper)

UN NetMap builds an evidence-backed relationship graph from a raw list of names.
It normalizes/deduplicates messy OCR-like input and enriches entities using public sources
(UN-related pages, government mission pages, major institutions), then exports a network
map for D3/Sigma/Neo4j/Gephi.

## What it does

- Ingests raw names (copy/paste, OCR dumps, mixed formatting)
- Normalizes + deduplicates entities (aliases preserved)
- Enriches with automated web lookups (cached + rate-limited)
- Produces an evidence-backed graph:
  - nodes: people + institutions
  - edges: relationship types with confidence + citations (URL + snippet)
- Exports:
  - `out/network.json` (D3/Sigma/Cytoscape ready)
  - `out/nodes.csv`, `out/edges.csv`
  - `out/matches_report.csv`
  - Optional: `out/graph.html` interactive viewer

## Install

# Update
   create the following tree

un-netmap/
  input/
    names.txt
  out/
    .gitkeep
  cache/
    .gitkeep
  scripts/
    build_network.py
    enrich_web.py
    render_html.py
  docs/
    methodology.md
  .gitignore
  LICENSE
  README.md
  requirements.txt

```bash
git clone https://github.com/jedisecx/atlas-institutional-gravity
cd un-netmap
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

