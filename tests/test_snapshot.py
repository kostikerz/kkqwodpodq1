"""Regression tests on a recorded subset of real Ubuntu noble metadata."""

import unittest
from pathlib import Path

from src.graph import build_graph
from src.repository import AptRepository


class SnapshotTests(unittest.TestCase):
    """Keep real-index integration results reproducible without internet."""

    def test_real_graphs(self):
        """Compare three real bounded graphs with the verified snapshot."""
        path = Path(__file__).parent / "fixtures" / "ubuntu.Packages"
        repository = AptRepository(path.read_text(encoding="utf-8"))
        expected = {"apt": (35, 55), "bash": (8, 10), "coreutils": (9, 13)}
        for root, counts in expected.items():
            with self.subTest(root=root):
                graph = build_graph(repository, root, 2)
                actual = (len(graph.edges),
                          sum(map(len, graph.edges.values())))
                self.assertEqual(actual, counts)
                self.assertFalse(graph.missing)
