"""Command line entry point."""

import argparse
import csv
import sys
from dataclasses import asdict

from .config import load_config
from .repository import AptRepository, fetch_index


def main(argv=None):
    """Print validated configuration and return a process exit code."""
    parser = argparse.ArgumentParser(description="Ubuntu dependency graph")
    parser.add_argument("config", help="CSV configuration filename")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        if config.test_mode:
            raise ValueError("Test graph mode is introduced in stage 3")
        repository = AptRepository(fetch_index(config.repository))
        for name in repository.dependencies(config.package):
            print(name)
    except (OSError, ValueError, KeyError, csv.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
