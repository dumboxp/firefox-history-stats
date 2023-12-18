import argparse
import sys
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
import pandas as pd
import matplotlib.pyplot as plt
import tempfile, shutil
import sqlite3

def main(config):
    df = fetch_history(config)

    # convert unix timestamp to localtime
    df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_localize('UTC').dt.tz_convert('Europe/Paris')

    # create domain from url
    df["domain"] = ""
    for i, row in df.iterrows():
        df.at[i, 'domain'] = urlparse(row['url']).netloc

    # filter for work-related domains
    df = df[df['domain'].str.contains(config.match, na=False, case=False)]
    print(f"{len(df)} filtered rows matching /{config.match}/i")

    if len(df) <= 0:
        print(f"Empty filtered browser history!")
        sys.exit()
    else:
        print(df.tail())

    top = (df.groupby(pd.Grouper(key='domain'), sort=True)['domain'].agg([('count', 'count')]))
    top = top.sort_values('count')
    print(top.head())
    top.plot.barh(
        title="Top Domains",
        xlabel="Hits",
        ylabel="Domain",
        figsize=(5, 5),
        alpha = 0.4,
        grid=False,
        legend=False
    )
    # group by 15min
    grouped = (df.groupby(pd.Grouper(key='datetime', freq='15T'), sort=False)['visit_count'].agg([('hits', 'count')]))
    if len(grouped) <= 0:
        print(f"Empty grouped browser statistics!")
        sys.exit()
    else:
        print(grouped.tail())

    # generate a plot
    grouped = grouped.sort_values('datetime')
    grouped.plot(kind='line',
                 drawstyle='steps',
                 # alpha = 0.4,
                 y=['hits'],
                 figsize=(10, 3),
                 fontsize=7,
                 grid=True,
                 legend=False,
                 title="Worktime using Firefox",
                 xlabel="Datetime",
                 ylabel="Hits")
    plt.fill_between(grouped.index, grouped.hits, alpha=0.4, step='pre')
    plt.show()


def create_temporary_copy(path):
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, 'temp_file_name')
    shutil.copy2(path, temp_path)
    return temp_path

def fetch_history(config):
    temp_db = create_temporary_copy(config.db)
    print(f"Connecting to database '{temp_db}' which is a temp copy of {config.db}")
    con = sqlite3.connect(temp_db)
    con.row_factory = sqlite3.Row  # simple row factory
    cur = con.cursor()
    # fetch browsing history from sqlite database
    if config.date:
        sql = """SELECT datetime(moz_historyvisits.visit_date/1000000,'unixepoch') AS datetime, 
        moz_places.url, 
        title, 
        moz_places.visit_count, 
        moz_places.frecency 
        FROM moz_places, moz_historyvisits 
        WHERE moz_places.id = moz_historyvisits.place_id 
        AND date(moz_historyvisits.visit_date/1000000,'unixepoch') = ?
        ORDER BY visit_date"""
        df = pd.read_sql_query(sql, con, params=[config.date])
        print(f"{len(df)} row for date {config.date} read from browser history")

    else:
        sql = """SELECT datetime(moz_historyvisits.visit_date/1000000,'unixepoch') AS datetime, 
        moz_places.url, 
        title, 
        moz_places.visit_count, 
        moz_places.frecency 
        FROM moz_places, moz_historyvisits 
        WHERE moz_places.id = moz_historyvisits.place_id 
        AND moz_historyvisits.visit_date/1000000 >= (unixepoch() - ?)
        ORDER BY visit_date"""
        df = pd.read_sql_query(sql, con, params=[60 * 60 * 24 * int(config.days)])
        print(f"{len(df)} rows of past {config.days} days read from browser history")

    cur.close()
    con.close()
    return df


if __name__ == '__main__':
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Generates statistics about the work-related usage of the Firefox browser.",
        epilog="Author: Roland Ortner")
    parser.add_argument('--db',
                        help="Full path to the 'places.sqlite' file of Firefox",
                        default='/Users/rolandortner/Library/Application Support/Firefox/Profiles/1zo7bw4o.default/places.sqlite'
                        )
    parser.add_argument('--days',
                        help="Number of past days to consider (default: 2)",
                        default=2
                        )
    parser.add_argument('--date',
                        help="Exact date (format: yyyy-mm-dd)",
                        )
    parser.add_argument('--match',
                        help="Regex match for domain filter",
                        default="symptoma\.|chatgpt|openai|figma|miro|office\.com|husanalytics"
                        )
    parser.add_argument('--tz',
                        help="Timezone (default: Europe/Paris)",
                        default='Europe/Paris'
                        )
    args = parser.parse_args()

    if not args.db or not os.path.exists(args.db):
        parser.print_usage()
        print("Database file could not be found! Provide full path to the database file as an argument.")
        sys.exit()

    main(args)
