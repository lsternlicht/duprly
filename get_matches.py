#!/usr/bin/env python3
"""Deprecated shim for compatibility.

Use: duprly browse profile-matches
"""

import argparse
import sys

from duprly.cli import main


def run() -> None:
    parser = argparse.ArgumentParser(description="[deprecated] Use 'duprly browse profile-matches'")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("-o", "--output", default="matches.json", help="Output file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logs")
    args = parser.parse_args()

    print("[deprecated] get_matches.py -> use `duprly browse profile-matches`")

    argv = ["duprly"]
    if args.verbose:
        argv.append("--verbose")
    argv.extend(["browse", "profile-matches"])
    if args.start_date:
        argv.extend(["--start-date", args.start_date])
    if args.end_date:
        argv.extend(["--end-date", args.end_date])
    argv.extend(["--output", args.output])

    sys.argv = argv
    main()


if __name__ == "__main__":
    run()
