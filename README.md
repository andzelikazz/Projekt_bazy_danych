# Projekt bazy danych

Projekt pobiera dane o trzesieniach ziemi z API USGS Earthquake
i zapisuje je w bazie.

## Struktura

- `schema.sql` - definicja tabel, kluczy i indeksow.
- `config.py` - konfiguracja API, bazy i harmonogramu importu.
- `create_database.py` - tworzy baze danych.
- `create_tables.py` - tworzy tabele na podstawie `schema.sql`.
- `import_data.py` - pobiera dane z USGS i zapisuje je do bazy.
- `setup.py` - uruchamia tworzenie bazy oraz tabel.


## Instalacja

```powershell
py setup.py
```

## Import danych

Jednorazowy import z ostatnich 24 godzin:

```powershell
py import_data.py
'''
Import cykliczny co `IMPORT_INTERVAL_MINUTES` minut:

```powershell
py import_data.py --loop
```
