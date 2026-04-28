"""
Query whereistheplanet.com to predict planet locations.

This module provides a CLI for querying the "Where is the Planet?" website
to get predicted locations of exoplanets and brown dwarfs at a given date.
"""

from pathlib import Path
import argparse
import sys

import requests

from querytheplanet import query


def main() -> int:
    """Main entry point for the CLI application.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(
        description="Query whereistheplanet.com to predict planet locations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
        "  querytheplanet 51erib\n"
        "  querytheplanet 51erib betapicb\n"
        "  querytheplanet 51erib --date 2026-05-01\n"
        "  querytheplanet 51erib betapicb --output results.csv\n"
        "  querytheplanet --list",
    )

    parser.add_argument(
        "planets",
        nargs="*",
        help="Name(s) of planet(s) to query",
    )

    parser.add_argument(
        "--dates",
        "--date",
        nargs="*",
        default=None,
        help="Dates in YYYY-MM-DD format (default: today)",
    )

    parser.add_argument(
        "--output",
        help="Save results to CSV file (append if file exists)",
    )

    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List all available planets",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Print formatted results to terminal"
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite the output file if it exists",
    )

    args = parser.parse_args()

    try:
        if args.list:
            planets = query.fetch_available_planets()
            print("Available planets:")
            print(" ".join(planets))
            return 0

        if not args.planets:
            parser.error("planet name(s) required unless --list is used")

        results_df = query.query_planet_locations(
            args.planets, dates=args.dates, verbose=args.verbose
        )

        if args.output:
            outpath = Path(args.output)
            if outpath.is_file() and not args.overwrite:
                raise FileExistsError(
                    f"File {outpath} already exists. Use --overwrite to overwrite."
                )
            query.write_to_csv(outpath, results_df, overwrite=args.overwrite)
        else:
            print(results_df)

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except requests.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
