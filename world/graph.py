from __future__ import annotations

from typing import Any


def generate_mermaid_html(world: Any) -> str:
    nodes = []
    for name, info in world.entities.items():
        label = name.replace('"', '\\"')
        color = {
            "agent": "#dbeafe",
            "objective": "#dcfce7",
            "environment": "#fef3c7",
            "task": "#fce7f3",
        }.get(info.get("type", "task"), "#e5e7eb")
        nodes.append(f'{name}["{label}\n{info.get("status", "active")}"]')

    edges = []
    for src, dst in world.relations:
        edges.append(f'{src} --> {dst}')

    graph = "graph TD\n" + "\n".join(["    " + item for item in nodes + edges])

    return f"""
    <style>
      .mermaid {{
        width: 100%;
        min-height: 320px;
        background: white;
        border-radius: 12px;
        padding: 8px;
      }}
    </style>
    <pre class="mermaid">{graph}</pre>
    <script type="module">
      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
      mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
    """
