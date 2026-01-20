#!/usr/bin/env python3
import re
import json
import csv
import time
import hashlib
from pathlib import Path
from typing import List, Tuple
import requests
from bs4 import BeautifulSoup

OUT_DIR = Path("out")
CACHE_DIR = Path("cache/http")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BASE_PATH = OUT_DIR / "network_base.json"
PEOPLE_CSV = OUT_DIR / "people_clean.csv"

UA = "Mozilla/5.0 (compatible; atlas-institutional-gravity/1.0; +local)"
TIMEOUT = 30
SLEEP = 1.0

def ddg_search_url(q: str) -> str:
    from urllib.parse import quote_plus
    return f"https://duckduckgo.com/html/?q={quote_plus(q)}"

def cache_get(url: str) -> str:
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    fp = CACHE_DIR / f"{key}.html"
    if fp.exists():
        return fp.read_text(encoding="utf-8", errors="ignore")
    r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    r.raise_for_status()
    fp.write_text(r.text, encoding="utf-8", errors="ignore")
    time.sleep(SLEEP)
    return r.text

def search_ddg(q: str, max_results=5) -> List[str]:
    html = cache_get(ddg_search_url(q))
    soup = BeautifulSoup(html, "lxml")
    links = []
    for a in soup.select("a.result__a"):
        href = a.get("href", "")
        if href:
            links.append(href)
        if len(links) >= max_results:
            break
    return links

def extract_text_snippet(html: str, needle: str, max_len=240) -> str:
    t = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
    i = t.lower().find(needle.lower())
    if i == -1:
        return t[:max_len]
    start = max(0, i - 80)
    end = min(len(t), i + max_len)
    return t[start:end]

def load_people() -> List[dict]:
    people = []
    with PEOPLE_CSV.open("r", encoding="utf-8", errors="ignore") as f:
        r = csv.DictReader(f)
        for row in r:
            people.append(row)
    return people

def add_node(nodes: dict, node_id: str, label: str, ntype: str):
    if node_id not in nodes:
        nodes[node_id] = {"id": node_id, "label": label, "type": ntype}

def add_edge(edges: list, src: str, dst: str, rel: str, confidence: str, source_url: str, snippet: str):
    edges.append({
        "source": src,
        "target": dst,
        "relation": rel,
        "confidence": confidence,
        "source_url": source_url,
        "evidence": snippet
    })

def main():
    if not BASE_PATH.exists():
        raise SystemExit("Missing out/network_base.json. Run scripts/build_network.py first.")
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in base["nodes"]}
    edges = base.get("edges", [])

    inst_defaults = {
        "inst:un": "United Nations",
        "inst:un-mission": "Permanent Missions to the UN",
        "inst:un-agency": "UN Agencies",
        "inst:imf": "International Monetary Fund",
        "inst:worldbank": "World Bank Group",
        "inst:bis": "Bank for International Settlements",
        "inst:centralbank": "Central Banking (generic)",
        "inst:royal": "Royal House / Court (generic)",
    }
    for inst_id, label in inst_defaults.items():
        add_node(nodes, inst_id, label, "institution")

    KEY_RELATIONS = [
        ("inst:un", "HELD_ROLE", ["secretary-general", "un secretary-general"], ["un.org"]),
        ("inst:un-mission", "REPRESENTED_AT", ["permanent representative", "mission to the united nations", "un ambassador"], ["unmissions.org", "un.org"]),
        ("inst:un", "HELD_ROLE", ["special envoy", "un envoy", "srsg", "special representative"], ["un.org"]),
        ("inst:un-agency", "LED", ["unicef", "who", "unesco", "undp", "unhcr", "wfp"], ["un.org", "unicef.org", "who.int", "unesco.org"]),
        ("inst:imf", "HELD_ROLE", ["imf"], ["imf.org"]),
        ("inst:worldbank", "HELD_ROLE", ["world bank"], ["worldbank.org"]),
        ("inst:bis", "HELD_ROLE", ["bank for international settlements", "bis"], ["bis.org"]),
        ("inst:centralbank", "HELD_ROLE", ["central bank", "governor", "chair", "ecb", "federal reserve", "bank of england"], ["ecb.europa.eu", "federalreserve.gov", "bankofengland.co.uk", "banque-france.fr"]),
    ]

    people = load_people()
    report_rows = []

    for row in people:
        pid = row["id"]
        label = row["label"]

        queries = [
            f"\"{label}\" United Nations",
            f"\"{label}\" Permanent Representative United Nations",
            f"\"{label}\" IMF World Bank BIS central bank",
        ]

        hits: List[Tuple[str, str, str, str, str]] = []

        for q in queries:
            try:
                urls = search_ddg(q, max_results=5)
            except Exception:
                urls = []
            for url in urls:
                try:
                    html = cache_get(url)
                except Exception:
                    continue
                low = BeautifulSoup(html, "lxml").get_text(" ", strip=True).lower()

                for inst_id, rel, needles, high_domains in KEY_RELATIONS:
                    if any(n in low for n in needles):
                        snippet = extract_text_snippet(html, needles[0])
                        conf = "medium"
                        if any(dom in url for dom in high_domains):
                            conf = "high"
                        hits.append((url, rel, inst_id, conf, snippet))
                        break

        seen = set()
        for url, rel, inst_id, conf, snippet in hits:
            k = (inst_id, rel)
            if k in seen:
                continue
            seen.add(k)
            add_edge(edges, pid, inst_id, rel, conf, url, snippet)
            report_rows.append({
                "person": label,
                "relation": rel,
                "institution": nodes[inst_id]["label"],
                "confidence": conf,
                "source_url": url,
                "evidence": snippet
            })

        if re.search(r"\b(prince|queen|duke|duchess|king|archduke|grand duke)\b", label.lower()):
            add_edge(edges, pid, "inst:royal", "HAS_TITLE", "high", "local:heuristic", "Title detected in label")

    out = {"nodes": list(nodes.values()), "edges": edges}
    (OUT_DIR / "network.json").write_text(json.dumps(out, indent=2), encoding="utf-8")

    with (OUT_DIR / "matches_report.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["person","relation","institution","confidence","source_url","evidence"])
        w.writeheader()
        for r in report_rows:
            w.writerow(r)

    print(f"Nodes: {len(out['nodes'])}")
    print(f"Edges: {len(out['edges'])}")
    print("Wrote: out/network.json, out/matches_report.csv")

if __name__ == "__main__":
    main()
