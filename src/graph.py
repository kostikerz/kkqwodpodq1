"""Iterative depth-first graph construction with bounded shortest depth."""

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

CSV_COLUMNS = 2


class TestRepository:
    """Strict CSV graph of upper-case Latin package names."""

    def __init__(self, filename):
        """Read package,dependencies rows; dependencies use spaces."""
        self.graph = {}
        with Path(filename).open(encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file, strict=True)
            if next(reader, None) != ["package", "dependencies"]:
                raise ValueError("Test graph header: package,dependencies")
            for row in reader:
                if len(row) != CSV_COLUMNS:
                    raise ValueError("Test graph row needs two columns")
                name, raw = row
                children = raw.split()
                if not all(re.fullmatch(r"[A-Z]+", item)
                           for item in [name, *children]):
                    raise ValueError("Test package names must match [A-Z]+")
                if name in self.graph:
                    raise ValueError(f"Duplicate test package: {name}")
                self.graph[name] = list(dict.fromkeys(children))
        referenced = {item for row in self.graph.values() for item in row}
        if referenced - self.graph.keys():
            raise ValueError("Test graph must declare all referenced nodes")

    def dependencies(self, name):
        """Return direct dependencies or raise for an unknown root."""
        return self.graph[name]


@dataclass
class Graph:
    """Adjacency and metadata for a bounded dependency graph."""

    edges: dict = field(default_factory=dict)
    depths: dict = field(default_factory=dict)
    missing: set = field(default_factory=set)


def filter_children(children, substring):
    """Remove excluded names and duplicates while preserving order."""
    included = (child for child in children
                if not substring or substring not in child)
    return list(dict.fromkeys(included))


def build_graph(repository, root, max_depth, substring=""):
    """Use a LIFO stack, revisiting nodes reached by a shorter path."""
    if substring and substring in root:
        raise ValueError("The root package is excluded by the filter")
    repository.dependencies(root)
    result, stack = Graph(), [(root, 0)]
    while stack:
        name, depth = stack.pop()
        if name in result.depths and depth >= result.depths[name]:
            continue
        result.depths[name] = depth
        result.edges.setdefault(name, [])
        if depth >= max_depth:
            continue
        try:
            children = repository.dependencies(name)
        except KeyError:
            result.missing.add(name)
            continue
        children = filter_children(children, substring)
        result.edges[name] = children
        stack.extend((child, depth + 1) for child in reversed(children))
    return result
