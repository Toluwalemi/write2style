import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .harness import load_authors, run_eval
from .report import format_report

DEFAULT_DATA = Path(__file__).parent / "data"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the Write2Style evaluation harness.",
    )
    parser.add_argument(
        "--data", type=Path, default=DEFAULT_DATA, help="Path to eval data directory"
    )
    parser.add_argument(
        "--authors",
        nargs="*",
        default=None,
        help="Restrict to these author directory names (default: all)",
    )
    parser.add_argument("--report", type=Path, default=None, help="Write markdown report to file")
    parser.add_argument(
        "--raw", type=Path, default=None, help="Write raw JSON results to file"
    )
    args = parser.parse_args()

    authors = load_authors(args.data)
    if args.authors:
        wanted = set(args.authors)
        authors = [a for a in authors if a.name in wanted]
    if not authors:
        print("No authors loaded. Check --data path.", file=sys.stderr)
        return 1

    print(f"Running eval on {len(authors)} author(s)...", file=sys.stderr)
    results = run_eval(authors)

    report = format_report(results)
    if args.report:
        args.report.write_text(report, encoding="utf-8")
        print(f"Report written to {args.report}", file=sys.stderr)
    else:
        print(report)

    if args.raw:
        args.raw.write_text(
            json.dumps([asdict(r) for r in results], indent=2),
            encoding="utf-8",
        )
        print(f"Raw results written to {args.raw}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
