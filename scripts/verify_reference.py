"""Compare captured apt outputs with the independently built graph."""

import json
import re
import sys
from collections import deque
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from src.graph import build_graph  # noqa: E402
from src.repository import AptRepository  # noqa: E402

DEPTH = 2
PACKAGES = ("apt", "bash", "coreutils")
EDGE_PATTERN = re.compile(r'^"([^"]+)" -> "([^"]+)"(\[[^\]]*\])?;')
DIRECT_PATTERN = re.compile(r"^\s*\|?(?:PreDepends|Depends):\s+<?([^>\s]+)")


def reference_edges(text):
    """Keep ordinary Depends and blue PreDepends edges from apt DOT."""
    result = set()
    for line in text.splitlines():
        match = EDGE_PATTERN.match(line)
        if match and (match[3] or "") in {"", "[color=blue]"}:
            result.add((match[1], match[2]))
    return result


def bounded_reference(edges, root):
    """Apply depth two using independent BFS, rather than the tool's DFS."""
    adjacent = {}
    for parent, child in sorted(edges):
        adjacent.setdefault(parent, []).append(child)
    depths, queue = {root: 0}, deque([root])
    while queue:
        parent = queue.popleft()
        if depths[parent] >= DEPTH:
            continue
        for child in adjacent.get(parent, []):
            if child not in depths:
                depths[child] = depths[parent] + 1
                queue.append(child)
    bounded = {(parent, child) for parent, child in edges
               if parent in depths and depths[parent] < DEPTH}
    return set(depths), bounded


def compare(repository, root):
    """Return measured differences for one captured Ubuntu package."""
    reference = BASE / "docs" / "reference"
    dot = (reference / f"{root}.dot").read_text(encoding="utf-8")
    depends = (reference / f"{root}-depends.txt").read_text(encoding="utf-8")
    direct = {match[1] for line in depends.splitlines()
              if (match := DIRECT_PATTERN.match(line))}
    nodes, edges = bounded_reference(reference_edges(dot), root)
    own = build_graph(repository, root, DEPTH)
    own_edges = {(parent, child) for parent, children in own.edges.items()
                 for child in children}
    direct_match = direct == set(repository.dependencies(root))
    return {
        "package": root,
        "nodes": len(own.edges),
        "edges": len(own_edges),
        "direct_match": direct_match,
        "nodes_match": nodes == set(own.edges),
        "edges_match": edges == own_edges,
        "only_in_tool": sorted(own_edges - edges),
        "only_in_apt": sorted(edges - own_edges),
    }


def main():
    """Check all three packages without apt, internet or third-party libs."""
    fixture = BASE / "tests" / "fixtures" / "ubuntu.Packages"
    repository = AptRepository(fixture.read_text(encoding="utf-8"))
    results = [compare(repository, root) for root in PACKAGES]
    print(json.dumps(results, indent=2))
    success = all(row["direct_match"] and row["nodes_match"]
                  and row["edges_match"] for row in results)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
