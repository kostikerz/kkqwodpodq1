"""CLI end-to-end checks with offline test repositories."""

import contextlib
import io
import unittest
import zlib
from http.client import IncompleteRead
from unittest.mock import patch

from src.cli import main


class CliTests(unittest.TestCase):
    """Check stage dispatch and human-readable failures."""

    def test_stages(self):
        """All non-rendering stages work with the demonstration graph."""
        for stage in range(1, 5):
            stream = io.StringIO()
            with self.subTest(stage=stage), contextlib.redirect_stdout(stream):
                code = main(["configs/demo.csv", "--stage", str(stage)])
            self.assertEqual(code, 0)
            self.assertTrue(stream.getvalue())

    def test_missing_config(self):
        """Errors have nonzero status and go to stderr."""
        stream = io.StringIO()
        with contextlib.redirect_stderr(stream):
            self.assertEqual(main(["absent.csv"]), 1)
        self.assertIn("Error:", stream.getvalue())

    def test_transport_and_compression_errors(self):
        """Broken downloads and compressed streams must not leak traces."""
        errors = [zlib.error("invalid compressed data"),
                  IncompleteRead(b"partial", 100)]
        for error in errors:
            stream = io.StringIO()
            with self.subTest(error=error), \
                    patch("src.cli.fetch_index", side_effect=error), \
                    contextlib.redirect_stderr(stream):
                code = main(["configs/apt.csv", "--stage", "2"])
            self.assertEqual(code, 1)
            self.assertIn("Error:", stream.getvalue())
            self.assertNotIn("Traceback", stream.getvalue())
