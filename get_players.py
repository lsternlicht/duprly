#!/usr/bin/env python3
"""Deprecated shim for compatibility.

Use: duprly export club-players ...
"""

import argparse
import sys

from duprly.cli import main


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="[deprecated] Use 'duprly export club-players'",
    )
    parser.add_argument("club_query", nargs="?", help="Club search query")
    parser.add_argument("-o", "--output", help="Output JSON file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logs")
    parser.add_argument("--club-id", help="Exact club ID")
    parser.add_argument("--non-interactive", action="store_true", help="Use first club result automatically")
    return parser.parse_args()


def run() -> None:
    args = _parse_args()
    print("[deprecated] get_players.py -> use `duprly export club-players`")

    club_query = args.club_query
    if not club_query and not args.club_id:
        try:
            club_query = input("Enter club name to search for: ").strip()
        except EOFError:
            club_query = ""

    argv = ["duprly"]
    if args.verbose:
        argv.append("--verbose")
    argv.extend(["export", "club-players"])

    if club_query:
        argv.append(club_query)
    if args.club_id:
        argv.extend(["--club-id", args.club_id])
    if args.output:
        argv.extend(["--output", args.output])
    if args.non_interactive:
        argv.append("--non-interactive")

    sys.argv = argv
    main()


if __name__ == "__main__":
    run()
