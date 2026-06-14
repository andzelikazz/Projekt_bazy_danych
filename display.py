"""Formatowanie i wyswietlanie wynikow zapytan w konsoli."""


def print_rows(columns, rows):
    """Prosty wydruk tabelaryczny w konsoli."""
    if not rows:
        print("Brak wynikow dla podanych kryteriow.")
        return

    widths = [len(col) for col in columns]
    str_rows = []
    for row in rows:
        str_row = ["" if v is None else str(v) for v in row]
        str_rows.append(str_row)
        for i, cell in enumerate(str_row):
            widths[i] = max(widths[i], len(cell))

    header = " | ".join(col.ljust(widths[i]) for i, col in enumerate(columns))
    print(header)
    print("-+-".join("-" * w for w in widths))
    for str_row in str_rows:
        print(" | ".join(cell.ljust(widths[i]) for i, cell in enumerate(str_row)))
    print(f"\nWierszy: {len(rows)}")
