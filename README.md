# Firefox History Stats

## Description

Command line script to create statistics about work-related the usage of the Firefox browser. 

The script will fetch the browsing history from the SQLite database `places.sqlite` of the Firefox browser.

The script will always create a temporary copy of the database to bypass the exclusive lock of Firefox!

## Visuals

![Screenshot](screenshot.png)  
*Work related hits using the Firefox browser*

## Installation

- Python 3.9
- Install dependencies from `requirements.txt`
- Run the app according to "Usage"

## Usage

```bash
usage: firefox-history-stats.py [-h] [--db DB] [--days DAYS] [--match MATCH] [--tz TZ]

Read browsing history of Firefox and create report.

optional arguments:
  -h, --help     show this help message and exit
  --db DB        Path to 'places.sqlite' file of Firefox
  --days DAYS    Number of days from the past
  --match MATCH  Regex match for domain filter
  --tz TZ        Timezone (default: Europe/Berlin)
```
### Examples

Help about the command line script:  
`python3.9 firefox-history-stats.py -h`

How often has a search engine being used:  
`python3.9 firefox-history-stats.py --match google|bing --days 10`

Specify the full path to the Firefox places database:  
`python3.9 firefox-history-stats.py --db ./../places.sqlite`

## Authors and acknowledgment
Roland Ortner
