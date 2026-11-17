"""Debian metadata and HTTP transport tests."""

import bz2
import gzip
import lzma
import unittest
from unittest.mock import MagicMock, patch

from src.repository import (
    AptRepository,
    decode_index,
    dependency_groups,
    fetch_index,
)

SAMPLE = """Package: app
Version: 1.0
Pre-Depends: base (>= 1)
Depends: lib:any (>= 2), alt | virtual,
 other

Package: provider
Provides: virtual (= 1)
"""


class RepositoryTests(unittest.TestCase):
    """Check native parsing without package manager libraries."""

    def test_direct_dependencies(self):
        """Preserve alternatives and continuation lines."""
        repo = AptRepository(SAMPLE)
        self.assertEqual(repo.dependencies("app"),
                         ["base", "lib", "alt", "virtual", "other"])
        self.assertEqual(repo.dependencies("virtual"), ["provider"])
        self.assertEqual(repo.dependencies("provider"), [])
        with self.assertRaises(KeyError):
            repo.dependencies("missing")

    def test_groups(self):
        """Retain OR grouping while dropping architecture qualifiers."""
        self.assertEqual(dependency_groups("x:any | y, z (>= 1)"),
                         [["x", "y"], ["z"]])
        with self.assertRaises(ValueError):
            dependency_groups("???")

    def test_invalid_dependency_suffixes(self):
        """Do not silently truncate corrupt dependency metadata."""
        for value in ["libc6???", "libc6 (nonsense)", "libc6,",
                      "libc6 |", ",libc6", "libc6 (>= 2.0) junk"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                dependency_groups(value)
        self.assertEqual(dependency_groups("libc6:any (>= 2:2.39-0~1)"),
                         [["libc6"]])

    def test_formats(self):
        """Read each supported compressed format using magic bytes."""
        raw = SAMPLE.encode()
        for compress in [bytes, gzip.compress, lzma.compress, bz2.compress]:
            with self.subTest(compress=compress):
                self.assertEqual(decode_index(compress(raw)), SAMPLE)

    def test_invalid_metadata(self):
        """Reject invalid or ambiguous indexes."""
        for text in ["", "Version: 1", "Package: a\nPackage: b",
                     "Package: a\n\nPackage: a", "garbage"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                AptRepository(text)

    @patch("src.repository.urlopen")
    def test_http(self, open_url):
        """Exercise the network boundary without an internet dependency."""
        response = MagicMock()
        response.read.return_value = gzip.compress(SAMPLE.encode())
        open_url.return_value.__enter__.return_value = response
        self.assertEqual(fetch_index("https://example.org/Packages.gz"),
                         SAMPLE)
        self.assertEqual(open_url.call_args.kwargs["timeout"], 45)
