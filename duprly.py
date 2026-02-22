#!/usr/bin/env python3
"""Backward-compatible wrapper for the new package CLI.

This file intentionally remains so existing invocations like:
  python duprly.py <command>
continue to work after the package refactor.
"""

from duprly.cli import main


if __name__ == "__main__":
    main()
