"""Read Ubuntu Packages directly with the Python standard library."""

import bz2
import gzip
import lzma
import re
from urllib.request import Request, urlopen


def parse_control(text):
    """Parse Debian control paragraphs and continuation lines."""
    records, record, previous = [], {}, None
    for line in [*text.splitlines(), ""]:
        if not line.strip():
            if record:
                records.append(record)
            record, previous = {}, None
        elif line[0].isspace() and previous:
            record[previous] += " " + line.strip()
        elif ":" in line:
            previous, value = line.split(":", 1)
            if previous in record:
                raise ValueError(f"Duplicate control field: {previous}")
            record[previous] = value.strip()
        else:
            raise ValueError(f"Malformed Packages line: {line}")
    return records


def dependency_groups(value):
    """Extract alternative groups, stripping versions and qualifiers."""
    groups = []
    for group in value.split(","):
        if not group.strip():
            continue
        names = []
        for alternative in group.split("|"):
            match = re.match(r"\s*([a-z0-9][a-z0-9+.-]*)", alternative)
            if not match:
                raise ValueError(f"Invalid dependency: {alternative}")
            names.append(match[1])
        groups.append(names)
    return groups


def decode_index(data):
    """Decode plain, gzip, xz or bzip2 Packages by magic bytes."""
    if data.startswith(b"\x1f\x8b"):
        data = gzip.decompress(data)
    elif data.startswith(b"\xfd7zXZ\x00"):
        data = lzma.decompress(data)
    elif data.startswith(b"BZh"):
        data = bz2.decompress(data)
    return data.decode("utf-8")


def fetch_index(url):
    """Fetch an explicit Packages URL; never invoke a package manager."""
    request = Request(url, headers={"User-Agent": "variant3-depgraph/1.0"})
    with urlopen(request, timeout=45) as response:
        return decode_index(response.read())


class AptRepository:
    """Conservative graph of all Depends/Pre-Depends alternatives."""

    def __init__(self, text):
        """Index one repository component/architecture and its providers."""
        self.records = {}
        self.providers = {}
        for record in parse_control(text):
            name = record.get("Package")
            if not name:
                raise ValueError("Packages paragraph has no Package field")
            if name in self.records:
                raise ValueError(f"Multiple versions in index: {name}")
            self.records[name] = record
            for group in dependency_groups(record.get("Provides", "")):
                for virtual in group:
                    self.providers.setdefault(virtual, []).append(name)
        if not self.records:
            raise ValueError("Packages index is empty")

    def dependencies(self, name):
        """Return all alternatives, or provider edges for virtual names."""
        if name not in self.records:
            if name in self.providers:
                return sorted(self.providers[name])
            raise KeyError(f"Package absent from this index: {name}")
        record = self.records[name]
        fields = (record.get("Pre-Depends", ""), record.get("Depends", ""))
        names = []
        for field in fields:
            for group in dependency_groups(field):
                names.extend(group)
        return list(dict.fromkeys(names))
