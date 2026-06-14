"""Warstwa analityczna projektu - punkt wejscia.

Spina pozostale moduly i wykonuje zapytania:
- db.py      - polaczenie z baza,
- queries.py - zapytania SQL (filtry + raporty),
- cli.py     - parsowanie argumentow,
- display.py - wydruk wynikow.

Przyklady uruchomienia (z aktywnym .venv):
    python analyze_data.py filter --min-magnitude 5 --country Japan --limit 20
    python analyze_data.py filter --from 2024-01-01 --to 2024-02-01 --tsunami
    python analyze_data.py report                 # wszystkie raporty
    python analyze_data.py report --name top      # jeden wybrany raport
"""

from cli import parse_args
from db import get_connection
from display import print_rows
from queries import REPORTS, build_filter_query


def run_filter(args):
    query, params, columns = build_filter_query(args)

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            rows = cursor.fetchall()

    print_rows(columns, rows)


def run_report(args):
    names = [args.name] if args.name else list(REPORTS)

    with get_connection() as connection:
        for name in names:
            report = REPORTS[name]
            print(f"\n=== {report['title']} ===")
            with connection.cursor() as cursor:
                cursor.execute(report["sql"])
                rows = cursor.fetchall()
            print_rows(report["columns"], rows)


if __name__ == "__main__":
    args = parse_args()
    if args.command == "filter":
        run_filter(args)
    elif args.command == "report":
        run_report(args)