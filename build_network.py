#!/usr/bin/env python3
import re
import json
import csv
from collections import defaultdict
from pathlib import Path

IN_PATH = Path("input/names.txt")
OUT_DIR = Path("out")
OUT_DIR.mkdir(parents=True, exist_ok=True)

STOP_FRAGMENTS = {
    "anderson", "cata", "alan", "mary", "max", "michel", "pobil",
    "d", "da", "de", "vi", "sk", "l", "ag", "at", "cp", "na"
}

def clean_line(s: str) -> str:
    s = s.strip()
    s = s.replace("\u200b", "")
    s = s.replace("™","").replace("“","\"").replace("”","\"").replace("’","'")
    s = s.replace("–","-").replace("—","-")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"^[\-\*\•\|]+", "", s).strip()
    return s.strip()

def looks_like_fragment(s: str) -> bool:
    s2 = re.sub(r"[^A-Za-z]", "", s).lower()
    if len(s2) <= 4 and s2 in STOP_FRAGMENTS:
        return True
    if len(s) < 3:
        return True
    if " " not in s and "," not in s and len(s) <= 6:
        return True
    return False

def canonical_key(s: str) -> str:
    s2 = s.lower()
    s2 = re.sub(r"\(.*?\)", "", s2)
    s2 = s2.replace('"', '')
    s2 = re.sub(r"[^a-z0-9,\s\-']", " ", s2)
    s2 = re.sub(r"\s+", " ", s2).strip()
    s2 = re.sub(r"\s*,\s*", ", ", s2)
    return s2

def display_name(variants):
    return sorted(variants, key=lambda x: len(x), reverse=True)[0]

def main():
    if not IN_PATH.exists():
        raise SystemExit(
            "Missing input/names.txt\n"
            "Tip: copy input/names.example.txt to input/names.txt and edit.\n"
        )

    raw = IN_PATH.read_text(encoding="utf-8", errors="ignore")
    lines = []
    for ln in raw.splitlines():
        ln = clean_line(ln)
        if not ln:
            continue
        if looks_like_fragment(ln):
            continue
        lines.append(ln)

    variants_by_key = defaultdict(set)
    for ln in lines:
        key = canonical_key(ln)
        if key:
            variants_by_key[key].add(ln)

    people_nodes = []
    for key, variants in variants_by_key.items():
        people_nodes.append({
            "id": f"person:{key}",
            "label": display_name(list(variants)),
            "type": "person",
            "aliases": sorted(list(variants)),
        })

    inst_nodes = [
        {"id":"inst:un", "label":"United Nations", "type":"institution"},
        {"id":"inst:un-agency", "label":"UN Agencies (generic)", "type":"institution"},
        {"id":"inst:un-mission", "label":"Permanent Missions to the UN (generic)", "type":"institution"},
        {"id":"inst:imf", "label":"International Monetary Fund", "type":"institution"},
        {"id":"inst:worldbank", "label":"World Bank Group", "type":"institution"},
        {"id":"inst:bis", "label":"Bank for International Settlements", "type":"institution"},
        {"id":"inst:centralbank", "label":"Central Banking System (generic)", "type":"institution"},
        {"id":"inst:ngo", "label":"NGO / Foundation (generic)", "type":"institution"},
        {"id":"inst:media", "label":"Media Organization (generic)", "type":"institution"},
        {"id":"inst:royal", "label":"Royal House / Court (generic)", "type":"institution"},
    ]

    nodes = {n["id"]: n for n in (people_nodes + inst_nodes)}
    edges = []
    network = {"nodes": list(nodes.values()), "edges": edges}

    (OUT_DIR / "network_base.json").write_text(json.dumps(network, indent=2), encoding="utf-8")

    with (OUT_DIR / "people_clean.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id","label","type","aliases"])
        w.writeheader()
        for p in people_nodes:
            w.writerow({
                "id": p["id"],
                "label": p["label"],
                "type": p["type"],
                "aliases": " | ".join(p.get("aliases", [])),
            })

    print(f"Raw lines kept: {len(lines)}")
    print(f"People nodes (deduped): {len(people_nodes)}")
    print("Wrote: out/network_base.json, out/people_clean.csv")

if __name__ == "__main__":
    main()
