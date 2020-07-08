# mrkoll-scraper

Tool to scrape and generate an RSS feed from the incredibly creepy [mrkoll.se Swedish toplist](https://mrkoll.se/topplistor/sverigetoppen/). Each RSS entry represents the list as it looked at a given point in time, plus convenience links to search for the person's name on Duckduckgo, Flashback, and The Facebook.

## Installation

```shell
pip install mrkoll-scraper
```

## Usage

### CLI

```shell
mrks --scrape
```

Scrapes the current list and saves it to the [Shelve database](https://docs.python.org/3.7/library/shelve.html) `mrks.db` in the current working directory. This operation saves the raw scraped HTML as well as a generated [feedgen](https://feedgen.kiesow.be/) `FeedEntry`. The data is saved in a dictionary with the current date as key, so multiple scrapes during the same day doesn't save a new entry, they only update the existing one.

```shell
mrks --regenerate
```

Iterates through the saved lists and re-generates `FeedEntry`'s from the raw HTML, in case you've made some changes in the HTML template or so, and want them applied retroactively.

### WSGI

`mrks.wsgi` contains a beautifully simple WSGI application, that simply outputs an RSS feed based on the data currently saved.

### Cron

Crontab to run `--scrape` every Monday at midnight:

`0 0 * * 1 cd /home/robert/mrkoll-scraper && /home/robert/mrkoll-scraper/venv/bin/mrks -s`
