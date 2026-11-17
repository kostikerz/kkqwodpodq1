"""Strict CSV configuration and validation."""

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Config:
    """User settings; paths are relative to the configuration file."""

    package: str
    repository: str
    test_mode: bool
    output: Path
    max_depth: int
    filter_substring: str


def read_rows(path):
    """Read key,value CSV, rejecting duplicates and unknown settings."""
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        if next(reader, None) != ["key", "value"]:
            raise ValueError("CSV header must be key,value")
        values = {}
        for row in reader:
            if len(row) != 2:
                raise ValueError("Each CSV row must have two columns")
            key, value = row
            if key in values:
                raise ValueError(f"Duplicate setting: {key}")
            values[key] = value.strip()
    if set(values) != set(Config.__dataclass_fields__):
        raise ValueError("CSV must contain exactly the six required keys")
    return values


def validate_repository(value, test_mode, base):
    """Validate a test file or an HTTP(S) Packages index URL."""
    if test_mode:
        path = (base / value).resolve()
        if not value or not path.is_file():
            raise ValueError("repository must name an existing test file")
        return str(path)
    url = urlsplit(value)
    if url.scheme not in {"https", "http"} or not url.hostname:
        raise ValueError("repository must be an HTTP(S) URL")
    if url.username or url.password or url.fragment:
        raise ValueError("repository URL cannot contain credentials/fragment")
    return value


def load_config(filename):
    """Load all six settings and report invalid values."""
    path = Path(filename).resolve()
    values = read_rows(path)
    mode = values["test_mode"].lower()
    if mode not in {"true", "false"}:
        raise ValueError("test_mode must be true or false")
    test_mode = mode == "true"
    pattern = r"[A-Z]+" if test_mode else r"[a-z0-9][a-z0-9+.-]*"
    if not re.fullmatch(pattern, values["package"]):
        raise ValueError("Invalid package name")
    depth = values["max_depth"]
    if not re.fullmatch(r"[0-9]+", depth):
        raise ValueError("max_depth must be a non-negative integer")
    output = Path(values["output"])
    if output.suffix.lower() != ".png" or output.name == ".png":
        raise ValueError("output must name a PNG file")
    output = (path.parent / output).resolve()
    if output.is_dir() or (output.parent.exists()
                           and not output.parent.is_dir()):
        raise ValueError("output parent must be a directory")
    substring = values["filter_substring"]
    if any(ord(char) < 32 for char in substring):
        raise ValueError("filter_substring cannot contain control characters")
    repository = validate_repository(
        values["repository"], test_mode, path.parent
    )
    return Config(values["package"], repository, test_mode, output,
                  int(depth), substring)
