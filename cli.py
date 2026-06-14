"""Definicja interfejsu wiersza polecen i przekazywanie argumentow."""

import argparse
from datetime import datetime

from queries import REPORTS


def parse_date(value):
    """Akceptuje 'YYYY-MM-DD' lub pelny timestamp ISO."""
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"Nieprawidlowa data: {value!r} (oczekiwano YYYY-MM-DD)"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Filtrowanie i analiza danych o trzesieniach ziemi (USGS)."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- filter ---
    f = sub.add_parser("filter", help="Filtruj zdarzenia (>= 10 filtrow).")
    f.add_argument("--min-magnitude", type=float, help="Minimalna magnituda.")
    f.add_argument("--max-magnitude", type=float, help="Maksymalna magnituda.")
    f.add_argument("--min-depth", type=float, help="Minimalna glebokosc [km].")
    f.add_argument("--max-depth", type=float, help="Maksymalna glebokosc [km].")
    f.add_argument("--from", dest="date_from", type=parse_date, help="Data od (YYYY-MM-DD).")
    f.add_argument("--to", dest="date_to", type=parse_date, help="Data do (YYYY-MM-DD).")
    f.add_argument("--category", help="Kategoria zdarzenia (np. earthquake).")
    f.add_argument("--country", help="Kraj (czesciowe dopasowanie).")
    f.add_argument("--city", help="Miasto / region (czesciowe dopasowanie).")
    f.add_argument("--place", help="Szukaj w nazwie miejsca (czesciowe dopasowanie).")
    f.add_argument("--alert", help="Poziom alertu (green/yellow/orange/red).")
    f.add_argument("--magnitude-type", help="Typ magnitudy (np. mb, ml, mw).")
    f.add_argument("--status", help="Status (reviewed / automatic).")
    f.add_argument("--min-significance", type=int, help="Minimalna istotnosc (significance).")
    f.add_argument("--tsunami", action="store_true", help="Tylko zdarzenia z tsunami.")
    f.add_argument("--order-by", choices=["time", "magnitude", "depth", "significance"],
                   default="time", help="Kolumna sortowania.")
    f.add_argument("--asc", action="store_true", help="Sortuj rosnaco (domyslnie malejaco).")
    f.add_argument("--limit", type=int, default=50, help="Maksymalna liczba wierszy.")

    # --- report ---
    r = sub.add_parser("report", help="Uruchom raporty analityczne (>= 5 zapytan SQL).")
    r.add_argument("--name", choices=list(REPORTS),
                   help="Nazwa pojedynczego raportu (domyslnie: wszystkie).")

    return parser.parse_args()
