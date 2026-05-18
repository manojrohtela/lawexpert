from __future__ import annotations

import argparse

from .runner import rebuild_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Build legal RAG assets.")
    parser.add_argument("--case-limit", type=int, default=None, help="Limit the number of cases processed.")
    parser.add_argument("--skip-laws", action="store_true", help="Skip rebuilding laws.json.")
    parser.add_argument("--skip-cases", action="store_true", help="Skip rebuilding cases.json.")
    args = parser.parse_args()
    result = rebuild_pipeline(
        case_limit=args.case_limit,
        build_laws=not args.skip_laws,
        build_cases=not args.skip_cases,
    )
    print(result)


if __name__ == "__main__":
    main()
