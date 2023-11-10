import argparse
import sys
import os
from dotenv import load_dotenv
from urllib.parse import urlparse
import pandas as pd
import matplotlib.pyplot as plt
import tempfile, shutil
import sqlite3


def create_temporary_copy(path):
    temp_dir = tempfile.gettempdir()
    temp_path = os.path.join(temp_dir, 'temp_file_name')
    shutil.copy2(path, temp_path)
    return temp_path

def main(config):
    temp_db = create_temporary_copy(config.db)
    print(f"Connecting to database '{temp_db}' which is a temp copy of {config.db}")
    con = sqlite3.connect(temp_db)
    con.row_factory = sqlite3.Row  # simple row factory
    cur = con.cursor()

    # fetch browsing history from sqlite database
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

    # convert unix timestamp to localtime
    df['datetime'] = pd.to_datetime(df['datetime']).dt.tz_localize('UTC').dt.tz_convert('Europe/Paris')
    print(df.tail())

    # create domain from url
    df["domain"] = ""
    for i, row in df.iterrows():
        df.at[i, 'domain'] = urlparse(row['url']).netloc

    # filter for work-related domains
    df = df[df['domain'].str.contains(config.match)]

    # group by 15min
    df['datetime'] = pd.to_datetime(df['datetime'])
    grouped = (df.groupby(pd.Grouper(key='datetime', freq='15T'), sort=False)['visit_count']
               .agg([('hits', 'count')]))
    print(grouped.tail())

    # generate a plot
    grouped.sort_values('datetime')
    grouped.plot(kind='line',
                 drawstyle='steps',
                 # alpha = 0.4,
                 y=['hits'],
                 figsize=(10, 6),
                 fontsize=7,
                 # x_compat=True,
                 grid=True,
                 legend=False,
                 title="Worktime in the Browser",
                 xlabel="Datetime",
                 ylabel="Hits")
    plt.fill_between(grouped.index, grouped.hits, alpha=0.4, step='pre')
    plt.show()

    cur.close()
    con.close()


if __name__ == '__main__':
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Read browsing history of Firefox and create report.",
        epilog="Author: Roland Ortner")
    parser.add_argument('--db',
                        help="Path to 'places.sqlite' file of Firefox",
                        # default="places.sqlite"
                        default='/Users/rolandortner/Library/Application Support/Firefox/Profiles/1zo7bw4o.default/places.sqlite'
                        )
    parser.add_argument('--days',
                        help="Number of days from the past",
                        default=2
                        )
    parser.add_argument('--match',
                        help="Regex match for domain filter",
                        default="symptoma|chatgpt|citrix"
                        )
    parser.add_argument('--tz',
                        help="Timezone",
                        default='Europe/Paris'
                        )
    args = parser.parse_args()

    if not args.db or not os.path.exists(args.db):
        parser.print_usage()
        print("Database file could not be found! Provide full path to the database file as an argument.")
        sys.exit()

    main(args)
