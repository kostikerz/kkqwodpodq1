"""Command line entry point."""

import argparse
import csv
import sys
from dataclasses import asdict

from .config import load_config
from .repository import AptRepository, fetch_index
from .graph import TestRepository, build_graph


def execute(config, stage):
    """Run a selected completed stage using the same CSV settings."""
    if stage == 1:
        for key, value in asdict(config).items():
            print(f"{key}={value}")
        return
    repository = (TestRepository(config.repository) if config.test_mode
                  else AptRepository(fetch_index(config.repository)))
    if stage == 2:
        print("\n".join(repository.dependencies(config.package)))
        return
    graph = build_graph(repository, config.package, config.max_depth,
                        config.filter_substring)
    for name, children in graph.edges.items():
        print(f"{name}: {' '.join(children)}")
    if graph.missing:
        print("Warning: absent in index: " + ", ".join(sorted(graph.missing)),
              file=sys.stderr)


def main(argv=None):
    """Print validated configuration and return a process exit code."""
    parser = argparse.ArgumentParser(description="Ubuntu dependency graph")
    parser.add_argument("config", help="CSV configuration filename")
    parser.add_argument("--stage", type=int, choices=range(1, 4), default=3)
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        execute(config, args.stage)
    except (OSError, ValueError, KeyError, csv.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
