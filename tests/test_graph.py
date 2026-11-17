"""Depth, cycles, filtering, joins and large nonrecursive graphs."""

import tempfile
import unittest
from pathlib import Path

from src.graph import TestRepository, build_graph


class MemoryRepository:
    """Small in-memory dependency source for algorithm tests."""

    def __init__(self, edges):
        """Store a test adjacency mapping."""
        self.edges = edges

    def dependencies(self, name):
        """Retrieve a row from the fixture."""
        return self.edges[name]


class GraphTests(unittest.TestCase):
    """Verify iterative DFS and strict file loading."""

    def test_diamond(self):
        """Shared dependency is present once, with both incoming edges."""
        repo = TestRepository("examples/graph.csv")
        graph = build_graph(repo, "A", 10)
        self.assertEqual(list(graph.edges), ["A", "B", "D", "C"])
        self.assertEqual(graph.edges["C"], ["D"])

    def test_cycle(self):
        """Cycles terminate without losing the back edge."""
        graph = build_graph(TestRepository("examples/cycle.csv"), "A", 99)
        self.assertEqual(graph.edges["C"], ["A"])

    def test_depth(self):
        """Boundary nodes are included and shallower paths re-expand."""
        repo = TestRepository("examples/shorter.csv")
        graph = build_graph(repo, "A", 3)
        self.assertEqual(graph.depths["D"], 1)
        self.assertIn("F", graph.edges)
        self.assertEqual(build_graph(repo, "A", 0).edges, {"A": []})
        self.assertEqual(build_graph(repo, "A", 1).edges,
                         {"A": ["B", "D"], "B": [], "D": []})

    def test_filter(self):
        """Excluded packages and their exclusive subtrees disappear."""
        repo = TestRepository("examples/graph.csv")
        self.assertNotIn("B", build_graph(repo, "A", 10, "B").edges)
        with self.assertRaises(ValueError):
            build_graph(repo, "A", 10, "A")

    def test_missing(self):
        """Missing dependencies remain leaves; unknown roots fail."""
        repo = MemoryRepository({"A": ["B"]})
        self.assertEqual(build_graph(repo, "A", 3).missing, {"B"})
        with self.assertRaises(KeyError):
            build_graph(repo, "Z", 3)

    def test_long_chain(self):
        """A 2000-edge chain must not depend on Python recursion."""
        length = 2000
        edges = {str(i): [str(i + 1)] for i in range(length)}
        edges[str(length)] = []
        graph = build_graph(MemoryRepository(edges), "0", length)
        self.assertEqual(len(graph.edges), length + 1)

    def test_invalid_fixture(self):
        """Validate fixture header, names, duplicates and references."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.csv"
            for body in ["x,y\n", "package,dependencies\nA,B\n",
                         "package,dependencies\na,\n",
                         "package,dependencies\nA,\nA,\n"]:
                path.write_text(body)
                with self.assertRaises(ValueError):
                    TestRepository(path)
