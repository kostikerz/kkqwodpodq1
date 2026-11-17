"""Configuration validation tests."""

import csv
import tempfile
import unittest
from pathlib import Path

from src.config import load_config


class ConfigTests(unittest.TestCase):
    """Exercise every configurable parameter and CSV structure."""

    def setUp(self):
        """Prepare an isolated valid configuration."""
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        (self.base / "graph.csv").write_text("package,dependencies\nA,\n")
        self.values = dict(package="A", repository="graph.csv",
                           test_mode="true", output="out.png",
                           max_depth="2", filter_substring="")

    def load(self):
        """Write settings and load them."""
        path = self.base / "config.csv"
        with path.open("w", encoding="utf-8", newline="") as stream:
            csv.writer(stream).writerows(
                [("key", "value"), *self.values.items()]
            )
        return load_config(path)

    def test_valid(self):
        """Resolve paths relative to CSV and accept zero depth."""
        self.values["max_depth"] = "0"
        config = self.load()
        self.assertEqual(config.max_depth, 0)
        self.assertEqual(config.output, self.base / "out.png")

    def test_invalid_parameters(self):
        """Reject an invalid value for each setting."""
        invalid = dict(package="a!", repository="missing",
                       test_mode="maybe", output="out.jpg",
                       max_depth="-1", filter_substring="x\x00y")
        for key, value in invalid.items():
            with self.subTest(key=key):
                old = self.values[key]
                self.values[key] = value
                with self.assertRaises(ValueError):
                    self.load()
                self.values[key] = old

    def test_invalid_csv(self):
        """Reject wrong headers, duplicate keys and missing settings."""
        path = self.base / "bad.csv"
        for text in ["a,b\n", "key,value\npackage,A\npackage,B\n",
                     "key,value\npackage,A,extra\n", "key,value\n"]:
            with self.subTest(text=text):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    load_config(path)

    def test_real_repository(self):
        """Validate addresses in real repository mode."""
        self.values.update(test_mode="false", package="apt")
        for url in ["file:///tmp/Packages", "https://", "ftp://host/x"]:
            self.values["repository"] = url
            with self.assertRaises(ValueError):
                self.load()
        self.values["repository"] = "https://archive.ubuntu.com/Packages"
        self.assertFalse(self.load().test_mode)
