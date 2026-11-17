"""PlantUML serialization and renderer failure handling."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.graph import Graph
from src.visualization import PNG_SIGNATURE, plantuml, render_png


class VisualizationTests(unittest.TestCase):
    """Check graph fidelity and local Java process integration."""

    def test_edges_and_missing(self):
        """Generate all edges, root styling and missing-node labels."""
        graph = Graph({"A": ["B"], "B": ["A"]}, missing={"B"})
        source = plantuml(graph, "A")
        self.assertEqual(source.count(" --> "), 2)
        self.assertIn("B [missing]", source)
        self.assertIn("#D6EAF8", source)
        self.assertTrue(source.endswith("@enduml\n"))
        self.assertEqual(source, plantuml(graph, "A"))

    def test_isolated(self):
        """An isolated package still has one visible rectangle."""
        source = plantuml(Graph({"A": []}), "A")
        self.assertEqual(source.count("rectangle"), 1)

    @patch("src.visualization.subprocess.run")
    def test_renderer(self, run):
        """Check PNG write, subprocess failures and bad output rejection."""
        with tempfile.TemporaryDirectory() as directory:
            jar = Path(directory) / "plantuml.jar"
            jar.touch()
            output = Path(directory) / "images" / "graph.png"
            with patch.dict(os.environ, {"PLANTUML_JAR": str(jar)}):
                run.return_value = subprocess.CompletedProcess(
                    [], 0, PNG_SIGNATURE + b"data", b""
                )
                render_png("@startuml\n@enduml", output)
                self.assertTrue(output.exists())
                for code, data in [(1, PNG_SIGNATURE), (0, b"bad")]:
                    run.return_value = subprocess.CompletedProcess(
                        [], code, data, b"failure"
                    )
                    with self.assertRaises(ValueError):
                        render_png("bad", output)

    def test_missing_jar(self):
        """Report a missing renderer before spawning Java."""
        with patch.dict(os.environ, {"PLANTUML_JAR": "absent.jar"}):
            with self.assertRaises(ValueError):
                render_png("source", "out.png")
