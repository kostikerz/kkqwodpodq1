"""Command line entry point."""

import argparse
import csv
import lzma
import subprocess
import sys
import zlib
from dataclasses import asdict
from http.client import HTTPException

from .config import load_config
from .graph import TestRepository, build_graph
from .order import format_order
from .repository import AptRepository, fetch_index
from .visualization import save_diagram

CONFIG_STAGE = 1
DIRECT_STAGE = 2
GRAPH_STAGE = 3
ORDER_STAGE = 4
VISUAL_STAGE = 5


def execute(config, stage):
    """Run a selected completed stage using the same CSV settings."""
    if stage == CONFIG_STAGE:
        for key, value in asdict(config).items():
            print(f"{key}={value}")
        return
    repository = (TestRepository(config.repository) if config.test_mode
                  else AptRepository(fetch_index(config.repository)))
    if stage == DIRECT_STAGE:
        print("\n".join(repository.dependencies(config.package)))
        return
    graph = build_graph(repository, config.package, config.max_depth,
                        config.filter_substring)
    if stage == VISUAL_STAGE:
        print(save_diagram(graph, config.package, config.output))
        print(f"PNG: {config.output}")
    elif stage == ORDER_STAGE:
        print(format_order(graph.edges))
    else:
        for name, children in graph.edges.items():
            print(f"{name}: {' '.join(children)}")
    if graph.missing:
        print("Warning: absent in index: " + ", ".join(sorted(graph.missing)),
              file=sys.stderr)


def main(argv=None):
    """Run the selected stage and return a process exit code."""
    parser = argparse.ArgumentParser(description="Ubuntu dependency graph")
    parser.add_argument("config", help="CSV configuration filename")
    parser.add_argument("--stage", type=int,
                        choices=range(CONFIG_STAGE, VISUAL_STAGE + 1),
                        default=VISUAL_STAGE)
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        execute(config, args.stage)
    except (OSError, ValueError, KeyError, csv.Error, EOFError, lzma.LZMAError,
            HTTPException, zlib.error,
            subprocess.TimeoutExpired) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
