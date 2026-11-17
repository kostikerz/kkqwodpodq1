"""Independent finite-model checks for traversal and SCC ordering."""

import itertools
import unittest
from collections import deque

from src.graph import build_graph
from src.order import load_order
from tests.test_graph import MemoryRepository

NAMES = ("A", "B", "C")
DEPTH_LIMITS = range(4)


def all_graphs():
    """Enumerate all 512 directed graphs, including self loops."""
    pairs = list(itertools.product(NAMES, repeat=2))
    for bits in itertools.product((False, True), repeat=len(pairs)):
        edges = {name: [] for name in NAMES}
        for (parent, child), present in zip(pairs, bits):
            if present:
                edges[parent].append(child)
        yield edges


def distances(edges, root):
    """Use independent breadth-first search as the DFS depth oracle."""
    result, queue = {root: 0}, deque([root])
    while queue:
        parent = queue.popleft()
        for child in edges[parent]:
            if child not in result:
                result[child] = result[parent] + 1
                queue.append(child)
    return result


def without_package(edges, excluded):
    """Build the filtered model independently from the DFS implementation."""
    return {name: [child for child in children if child != excluded]
            for name, children in edges.items() if name != excluded}


class ExhaustiveTests(unittest.TestCase):
    """Validate against reachability rather than duplicate the algorithms."""

    def test_dfs_depth_and_filter(self):
        """Check every graph, root, depth and an excluded-node variant."""
        for edges, root, limit, excluded in itertools.product(
                all_graphs(), NAMES, DEPTH_LIMITS, ("", "B")):
            if root == excluded:
                continue
            filtered = without_package(edges, excluded)
            expected = {name: depth for name, depth
                        in distances(filtered, root).items()
                        if depth <= limit}
            graph = build_graph(MemoryRepository(edges), root,
                                limit, excluded)
            self.assertEqual(graph.depths, expected)
            self.assertEqual(graph.edges, {
                name: filtered[name] if depth < limit else []
                for name, depth in expected.items()
            })

    def test_scc_order(self):
        """Components equal mutual reachability and obey every DAG edge."""
        for edges in all_graphs():
            groups = load_order(edges)
            flattened = [name for group in groups for name in group]
            self.assertCountEqual(flattened, NAMES)
            position = {name: i for i, group in enumerate(groups)
                        for name in group}
            reachable = {name: distances(edges, name) for name in NAMES}
            for parent, child in itertools.product(NAMES, repeat=2):
                same = child in reachable[parent] and parent in reachable[child]
                self.assertEqual(position[parent] == position[child], same)
                if child in edges[parent]:
                    self.assertLessEqual(position[child], position[parent])
