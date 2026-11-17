"""Command line entry point."""

import argparse
import csv
import sys
from dataclasses import asdict

from .config import load_config


def main(argv=None):
    """Print validated configuration and return a process exit code."""
    parser = argparse.ArgumentParser(description="Ubuntu dependency graph")
    parser.add_argument("config", help="CSV configuration filename")
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        for key, value in asdict(config).items():
            print(f"{key}={value}")
    except (OSError, ValueError, csv.Error) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
