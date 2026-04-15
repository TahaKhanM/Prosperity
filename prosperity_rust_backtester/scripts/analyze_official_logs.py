#!/usr/bin/env python3

import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from official_log_analyzer.cli import main as analyzer_main

    analyzer_main()


if __name__ == "__main__":
    main()
