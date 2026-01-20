#!/usr/bin/env python3
import json
from pathlib import Path

OUT = Path("out")
net_path = OUT / "network.json"
if not net_path.exists():
    net_path = OUT / "network_base.json"
if not net_path.exists():
    raise SystemExit("Missing out/network.json or out/network_base.json. Run scripts/build_network.py first.")

net = json.loads(net_path.read_text(encoding="utf-8"))

html = f'''<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>ATLAS - Institutional Gravity</title>
  <style>
    html, body {{ height: 100%; margin: 0; background:#000; color:#0f0; font-family: monospace; }}
    #graph {{ position: absolute; inset: 0; }}
    #bar {{ position: absolute; top: 8px; left: 8px; right: 8px; padding: 10px; background: rgba(0,0,0,.6); border:1px solid #0f0; }}
  </style>
  <script src="https://cdn.jsdelivr.net/npm/graphology@0.25.4/dist/graphology.umd.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/sigma@2.4.0/build/sigma.min.js"></script>
</head>
<body>
  <div id="graph"></div>
  <div id="bar">
    <b>ATLAS - Institutional Gravity</b><br/>
    Nodes: {len(net["nodes"])} | Edges: {len(net["edges"])}<br/>
    Click nodes to inspect (details in browser console).
  </div>
  <script>
    const data = {json.dumps(net)};
    const Graph = graphology.Graph;
    const graph = new Graph();

    function hashPos(id) {{
      let h=0; for (let i=0;i<id.length;i++) h=(h*31 + id.charCodeAt(i))>>>0;
      const x = (h % 1000) / 100;
      const y = ((h/1000|0) % 1000) / 100;
      return [x,y];
    }}

    data.nodes.forEach(n => {{
      const [x,y] = hashPos(n.id);
      graph.addNode(n.id, {{
        label: n.label,
        x, y,
        size: n.type === "institution" ? 8 : 3
      }});
    }});

    data.edges.forEach((e, idx) => {{
      if (graph.hasNode(e.source) && graph.hasNode(e.target)) {{
        graph.addEdge(e.source, e.target, {{
          label: (e.relation || "LINK") + " (" + (e.confidence || "n/a") + ")"
        }});
      }}
    }});

    const renderer = new sigma.Sigma(graph, document.getElementById("graph"));
    renderer.on("clickNode", (event) => {{
      const id = event.node;
      console.log("NODE:", id, graph.getNodeAttributes(id));
    }});
  </script>
</body>
</html>
'''

(OUT / "graph.html").write_text(html, encoding="utf-8")
print("Wrote: out/graph.html")
