"""Dependency loading tests for DAGs and strongly connected graphs."""

import unittest

from src.order import format_order, load_order


class OrderTests(unittest.TestCase):
    """Check dependency-before-dependent ordering between components."""

    def assert_dependency_order(self, edges):
        """Every inter-component edge must point to an earlier group."""
        groups = load_order(edges)
        positions = {name: i for i, group in enumerate(groups)
                     for name in group}
        self.assertEqual(set(positions), set(edges))
        for parent, children in edges.items():
            for child in children:
                self.assertLessEqual(positions[child], positions[parent])
        return groups

    def test_diamond(self):
        """A shared dependency loads before both of its dependents."""
        edges = {"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []}
        groups = self.assert_dependency_order(edges)
        self.assertEqual(groups[0], ["D"])
        self.assertEqual(groups[-1], ["A"])

    def test_cycle(self):
        """Collapse a cycle and load its external dependencies first."""
        edges = {"A": ["B"], "B": ["A", "C"], "C": []}
        self.assertEqual(self.assert_dependency_order(edges),
                         [["C"], ["A", "B"]])
        self.assertIn("cycle group: A, B", format_order(edges))

    def test_self_loop_and_isolated(self):
        """Handle single-node cycles and disconnected leaves."""
        self.assertIn("cycle group: A", format_order({"A": ["A"]}))
        self.assert_dependency_order({"A": [], "B": []})

    def test_long_chain(self):
        """Ordering remains nonrecursive for large dependency chains."""
        size = 2000
        edges = {str(i): [str(i + 1)] for i in range(size)}
        edges[str(size)] = []
        self.assertEqual(load_order(edges)[0], [str(size)])
