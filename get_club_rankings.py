#!/usr/bin/env python3
"""Deprecated shim for compatibility.

Use: duprly export rankings CLUB_ID
"""

import argparse
import sys

from duprly.cli import main


def run() -> None:
    parser = argparse.ArgumentParser(description="[deprecated] Use 'duprly export rankings'")
    parser.add_argument("club_id", help="DUPR club ID")
    parser.add_argument("-o", "--output", help="Output JSON file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logs")
    args = parser.parse_args()

    print("[deprecated] get_club_rankings.py -> use `duprly export rankings`")

    argv = ["duprly"]
    if args.verbose:
        argv.append("--verbose")
    argv.extend(["export", "rankings", args.club_id])
    if args.output:
        argv.extend(["--output", args.output])

    sys.argv = argv
    main()


if __name__ == "__main__":
    run()
