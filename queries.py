"""Definicje zapytan SQL do bazy danych.

- build_filter_query: buduje dynamiczne zapytanie filtrujace (>= 10 filtrow),
- REPORTS: gotowe zapytania analityczne / raportowe (>= 5 zapytan SQL).
"""

# Kolumny zwracane przez zapytanie filtrujace.
FILTER_COLUMNS = [
    "event_id", "event_time", "magnitude", "depth", "category",
    "place", "country", "alert", "tsunami", "significance",
]

# Whitelist kolumn sortowania (idzie do zapytania jako tekst).
ORDER_COLUMNS = {
    "time": "e.event_time",
    "magnitude": "p.magnitude",
    "depth": "p.depth",
    "significance": "p.significance",
}


def build_filter_query(args):
    """Buduje zapytanie WHERE na podstawie filtrow z argumentow.

    Zwraca krotke: (query, params, columns).
    """
    conditions = []
    params = []

    # 1. minimalna magnituda
    if args.min_magnitude is not None:
        conditions.append("p.magnitude >= %s")
        params.append(args.min_magnitude)

    # 2. maksymalna magnituda
    if args.max_magnitude is not None:
        conditions.append("p.magnitude <= %s")
        params.append(args.max_magnitude)

    # 3. minimalna glebokosc
    if args.min_depth is not None:
        conditions.append("p.depth >= %s")
        params.append(args.min_depth)

    # 4. maksymalna glebokosc
    if args.max_depth is not None:
        conditions.append("p.depth <= %s")
        params.append(args.max_depth)

    # 5. data od (event_time)
    if args.date_from is not None:
        conditions.append("e.event_time >= %s")
        params.append(args.date_from)

    # 6. data do (event_time)
    if args.date_to is not None:
        conditions.append("e.event_time <= %s")
        params.append(args.date_to)

    # 7. kategoria (tabela slownikowa)
    if args.category is not None:
        conditions.append("c.category_name = %s")
        params.append(args.category)

    # 8. kraj
    if args.country is not None:
        conditions.append("l.country ILIKE %s")
        params.append(f"%{args.country}%")

    # 9. miasto / region
    if args.city is not None:
        conditions.append("l.city ILIKE %s")
        params.append(f"%{args.city}%")

    # 10. wyszukiwanie po nazwie miejsca
    if args.place is not None:
        conditions.append("l.place ILIKE %s")
        params.append(f"%{args.place}%")

    # 11. poziom alertu
    if args.alert is not None:
        conditions.append("e.alert_level = %s")
        params.append(args.alert)

    # 12. typ magnitudy
    if args.magnitude_type is not None:
        conditions.append("p.magnitude_type = %s")
        params.append(args.magnitude_type)

    # 13. status (reviewed / automatic)
    if args.status is not None:
        conditions.append("p.status = %s")
        params.append(args.status)

    # 14. minimalna istotnosc zdarzenia
    if args.min_significance is not None:
        conditions.append("p.significance >= %s")
        params.append(args.min_significance)

    # 15. tylko zdarzenia z ostrzezeniem tsunami
    if args.tsunami:
        conditions.append("p.tsunami = TRUE")

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    order_col = ORDER_COLUMNS.get(args.order_by, "e.event_time")
    direction = "ASC" if args.asc else "DESC"

    query = f"""
        SELECT
            e.event_id,
            e.event_time,
            p.magnitude,
            p.depth,
            c.category_name,
            l.place,
            l.country,
            e.alert_level,
            p.tsunami,
            p.significance
        FROM events e
        JOIN parameters p ON p.event_id = e.event_id
        LEFT JOIN category c ON c.category_id = e.category_id
        LEFT JOIN location l ON l.location_id = e.location_id
        {where_clause}
        ORDER BY {order_col} {direction} NULLS LAST
        LIMIT %s
    """
    params.append(args.limit)

    return query, params, FILTER_COLUMNS


REPORTS = {
    "summary": {
        "title": "Podsumowanie ogolne",
        "columns": ["liczba_zdarzen", "srednia_mag", "max_mag", "min_mag", "max_glebokosc"],
        "sql": """
            SELECT
                COUNT(*)                       AS liczba_zdarzen,
                ROUND(AVG(p.magnitude), 2)     AS srednia_mag,
                MAX(p.magnitude)               AS max_mag,
                MIN(p.magnitude)               AS min_mag,
                MAX(p.depth)                   AS max_glebokosc
            FROM events e
            JOIN parameters p ON p.event_id = e.event_id;
        """,
    },
    "top": {
        "title": "Top 10 najsilniejszych trzesien ziemi",
        "columns": ["event_time", "magnitude", "place", "country", "depth"],
        "sql": """
            SELECT
                e.event_time,
                p.magnitude,
                l.place,
                l.country,
                p.depth
            FROM events e
            JOIN parameters p ON p.event_id = e.event_id
            LEFT JOIN location l ON l.location_id = e.location_id
            ORDER BY p.magnitude DESC NULLS LAST
            LIMIT 10;
        """,
    },
    "by_category": {
        "title": "Liczba zdarzen wg kategorii (tabela slownikowa)",
        "columns": ["category_name", "liczba_zdarzen", "srednia_mag"],
        "sql": """
            SELECT
                c.category_name,
                COUNT(*)                    AS liczba_zdarzen,
                ROUND(AVG(p.magnitude), 2)  AS srednia_mag
            FROM events e
            JOIN parameters p ON p.event_id = e.event_id
            LEFT JOIN category c ON c.category_id = e.category_id
            GROUP BY c.category_name
            ORDER BY liczba_zdarzen DESC;
        """,
    },
    "by_country": {
        "title": "Statystyki wg kraju (top 15)",
        "columns": ["country", "liczba_zdarzen", "srednia_mag", "max_mag"],
        "sql": """
            SELECT
                COALESCE(l.country, 'nieznany') AS country,
                COUNT(*)                        AS liczba_zdarzen,
                ROUND(AVG(p.magnitude), 2)      AS srednia_mag,
                MAX(p.magnitude)                AS max_mag
            FROM events e
            JOIN parameters p ON p.event_id = e.event_id
            LEFT JOIN location l ON l.location_id = e.location_id
            GROUP BY COALESCE(l.country, 'nieznany')
            ORDER BY liczba_zdarzen DESC
            LIMIT 15;
        """,
    },
    "by_day": {
        "title": "Liczba zdarzen w podziale na dni (dane historyczne)",
        "columns": ["dzien", "liczba_zdarzen", "srednia_mag"],
        "sql": """
            SELECT
                DATE(e.event_time)          AS dzien,
                COUNT(*)                    AS liczba_zdarzen,
                ROUND(AVG(p.magnitude), 2)  AS srednia_mag
            FROM events e
            JOIN parameters p ON p.event_id = e.event_id
            WHERE e.event_time IS NOT NULL
            GROUP BY DATE(e.event_time)
            ORDER BY dzien DESC
            LIMIT 30;
        """,
    },
    "magnitude_dist": {
        "title": "Rozklad zdarzen wg przedzialu magnitudy",
        "columns": ["przedzial_mag", "liczba_zdarzen"],
        "sql": """
            SELECT
                CASE
                    WHEN p.magnitude < 3 THEN '< 3.0'
                    WHEN p.magnitude < 4 THEN '3.0 - 3.9'
                    WHEN p.magnitude < 5 THEN '4.0 - 4.9'
                    WHEN p.magnitude < 6 THEN '5.0 - 5.9'
                    WHEN p.magnitude < 7 THEN '6.0 - 6.9'
                    ELSE '>= 7.0'
                END                         AS przedzial_mag,
                COUNT(*)                    AS liczba_zdarzen
            FROM events e
            JOIN parameters p ON p.event_id = e.event_id
            WHERE p.magnitude IS NOT NULL
            GROUP BY przedzial_mag
            ORDER BY przedzial_mag;
        """,
    },
    "tsunami": {
        "title": "Zdarzenia z ostrzezeniem tsunami",
        "columns": ["event_time", "magnitude", "place", "country"],
        "sql": """
            SELECT
                e.event_time,
                p.magnitude,
                l.place,
                l.country
            FROM events e
            JOIN parameters p ON p.event_id = e.event_id
            LEFT JOIN location l ON l.location_id = e.location_id
            WHERE p.tsunami = TRUE
            ORDER BY e.event_time DESC
            LIMIT 25;
        """,
    },
    "imports": {
        "title": "Log importow (tabela techniczna)",
        "columns": ["import_id", "started_at", "finished_at", "records_received", "imported_amount", "import_status"],
        "sql": """
            SELECT
                import_id,
                started_at,
                finished_at,
                records_received,
                imported_amount,
                import_status
            FROM imports
            ORDER BY started_at DESC
            LIMIT 15;
        """,
    },
}
