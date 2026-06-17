"""Moduł tworzący wizualizację na podstawie wybranych fitrów.

Przykladowe wywolania pliku visualize_data.py:
    python visualize_data.py visualize --type 1
    python visualize_data.py visualize --type 2
"""

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
from db import get_connection
import argparse



def run_report_visualization(args):
    names = args.type

    with get_connection() as connection:
        match names:
            case 1:
                with connection.cursor() as cursor:
                    name = "top"
                    report = REPORTS_TO_VISUALIZE[name]
                    cursor.execute(report["sql"])
                    rows = cursor.fetchall()
                    map = Basemap(resolution="i")
                    map.shadedrelief()
                    longitude = [x[4] for x in rows] 
                    latitude = [x[5] for x in rows]
                    country = [x[3] for x in rows]
                    mag = [x[1] for x in rows]

                    for x in range(len(longitude)):
                        if x == mag.index(max(mag)):
                            plt.text(longitude[x], latitude[x], f"Max magnitude: {mag[x]} dB \n {country[x]}",fontsize=7,fontweight='bold',
                                    ha='center',va='center',color='r')
                        if x == mag.index(min(mag)):
                            plt.text(longitude[x], latitude[x], f"Min magnitude: {mag[x]} dB \n {country[x]}",fontsize=7,fontweight='bold',
                                    ha='center',va='center',color='g')
                        map.tissot(longitude[x], latitude[x], 4, 50)
                    plt.title("Top 10 most powerful earthquakes within database")
                    plt.show()

            case 2:
                with connection.cursor() as cursor:
                    name = "by_category"
                    report = REPORTS_TO_VISUALIZE[name]
                    cursor.execute(report["sql"])
                    rows = cursor.fetchall()
                    categories = [x[0] for x in rows]
                    amount = [x[1] for x in rows]
                    average = [x[2] for x in rows]
                    colors = [((1/(x**1.02)), 1, (1/(x**1.05))) for x in range(2, len(rows)+2)]

                    fig,ax = plt.subplots()
                    ax.bar(categories, amount, color=colors)
                    ax.set_title("Earthquake types divided into categories within database")
                    ax.set_xlabel("Category")
                    ax.set_ylabel("Amount")
                    ax.set_facecolor((0.1, 0.8, 0.8))
                    plt.show() 

                pass
            case 3:
                with connection.cursor() as cursor:
                    name = "magnitude_dist"
                    report = REPORTS_TO_VISUALIZE[name]
                    cursor.execute(report["sql"])
                    rows = cursor.fetchall()
                    intervals = [x[0] for x in rows]
                    values = [x[1] for x in rows]  
                    colors = [(1, (1/(x**1.02)), (1/(x**1.05))) for x in range(2, len(rows)+2)]  
                    
                    fig,ax = plt.subplots()
                    ax.bar(intervals, values, color=colors)
                    ax.set_title("Magnitude distribution from earthquakes within database")
                    ax.set_xlabel("Magnitude intervals [dB]")
                    ax.set_ylabel("Amount")
                    ax.set_facecolor((0.1, 0.8, 0.8))
                    plt.show() 

                pass
            # case 4:
            #     with connection.cursor() as cursor:
            #         name = "by_country"
            #         report = REPORTS_TO_VISUALIZE[name]
            #         cursor.execute(report["sql"])
            #         rows = cursor.fetchall()
            #         # world = gpd.read_file('ne_110m_admin_0_countries.zip')
            #         # print(world)        


        
REPORTS_TO_VISUALIZE = {

    "top": {
        "title": "Top 10 najsilniejszych trzesien ziemi",
        "columns": ["event_time", "magnitude", "place", "country", "longitude", "latitude", "depth"],
        "sql": """
            SELECT
                e.event_time,
                p.magnitude,
                l.place,
                l.country,
                c.longitude,
                c.latitude,
                p.depth
            FROM events e
            JOIN parameters p ON p.event_id = e.event_id
            LEFT JOIN location l ON l.location_id = e.location_id
            inner join coordinates c on c.location_id = l.location_id
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
   
}



if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description="Wizualizacja danych o trzesieniach ziemi (USGS)."
    )
    
    sub = parser.add_subparsers(dest="command", required=True)
    r = sub.add_parser("visualize", help="Uruchom wizualizację")
    r.add_argument("--type",type=int, default=1, choices=[1,2,3],
                   help="Podaj opcję 1-3 [top, by_category, magnitude_dist]")

    args = parser.parse_args()
    parser.print_help()
    if args.command == "visualize":
        run_report_visualization(args)



