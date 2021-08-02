import re
import shelve
from datetime import datetime
from typing import TYPE_CHECKING
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup
from dateutil.tz import gettz
from feedgen.entry import FeedEntry
from feedgen.feed import FeedGenerator
from jinja2 import Environment, PackageLoader, select_autoescape

if TYPE_CHECKING:
    from typing import List, Dict, Union, Optional


MRKOLL_BASE_URL = "https://mrkoll.se/"
SWEDEN_TOPLIST_URL = MRKOLL_BASE_URL + "topplistor/sverigetoppen/"
SWEDEN_TOPLIST_YESTERDAY_URL = SWEDEN_TOPLIST_URL + "?t=2"
DDG_BASE_URL = "https://duckduckgo.com/?q="
FLASHBACK_BASE_URL = "https://www.flashback.org/sok/?query="
FACEBOOK_BASE_URL = "https://www.facebook.com/search/people/?q="
SHELVE_DB = "mrks"


class Entry:
    datetime: datetime
    raw_html: bytes
    feed_entry: FeedEntry

    @classmethod
    def fetch_and_save(cls) -> "Entry":
        entry = cls()
        entry.fetch()
        entry.generate_feed_entry()
        entry.save()
        return entry

    @property
    def date_str(self):
        return str(self.datetime.date())

    def __init__(self):
        if not hasattr(self, "datetime"):
            self.datetime = datetime.now(tz=gettz("Europe/Stockholm"))

    def fetch(self):
        self.raw_html = requests.get(SWEDEN_TOPLIST_URL).content
        # Ugly hack; on the 1st of each month the list is empty and we are
        # told to get yesterday's list instead. So do a quick check for that
        # here and fetch yesterday's list if necessary.
        soup = BeautifulSoup(self.raw_html, "html.parser")
        person_list = soup.select(".infoLine2 a")
        if not person_list:
            self.raw_html = requests.get(SWEDEN_TOPLIST_YESTERDAY_URL).content

    def generate_feed_entry(self):
        self.feed_entry = FeedEntry()
        self.feed_entry.title(self.date_str)
        self.feed_entry.published(self.datetime)
        self.feed_entry.description(self._generate_entry_html())

    def save(self):
        with shelve.open(SHELVE_DB, writeback=True) as db:
            if "entries" not in db:
                db["entries"] = {}
            db["entries"][self.date_str] = self

    def _extract_data(self, raw_html) -> "List[Dict[str, Union[str, int]]]":
        soup = BeautifulSoup(raw_html, "html.parser")
        # MrKoll's HTML is broken (the p.infoLine2 tags are not closed)
        person_list = soup.select(".infoLine2 a")
        results = []
        for person in person_list:
            name, location = person.select_one("span.topp1").contents
            name = name.text
            location = re.sub(r"^\si\s", "", location)
            search_term = quote_plus(name)
            search_term_location = quote_plus(name + " " + location) if location else search_term
            results.append({
                "name": name,
                "location": location,
                "search_count": int(re.sub(r"\D", "", person.select_one("span.topp2").text)),
                "mrkoll_link": urljoin(MRKOLL_BASE_URL, person.attrs["href"]),
                "flashback_link": FLASHBACK_BASE_URL + search_term,
                "ddg_link": DDG_BASE_URL + search_term_location,
                "facebook_link": FACEBOOK_BASE_URL + search_term,
            })
        return results

    def _get_last_entry(self) -> "Optional[Entry]":
        with shelve.open(SHELVE_DB) as db:
            try:
                return [db["entries"][key] for key in sorted(db["entries"]) if key < self.date_str][-1]
            except (IndexError, KeyError):
                return None

    def _generate_entry_html(self) -> str:
        jinja = Environment(loader=PackageLoader("mrks", "templates"), autoescape=select_autoescape(["html"]))
        template = jinja.get_template("entry.html")
        persons = self._extract_data(self.raw_html)
        last_entry = self._get_last_entry()
        if last_entry is not None:
            persons_last_entry = self._extract_data(last_entry.raw_html)
            for person in persons:
                last_placement = "NEW"
                for idx, person_last_entry in enumerate(persons_last_entry):
                    if person["mrkoll_link"] == person_last_entry["mrkoll_link"]:
                        last_placement = str(idx + 1)
                        break
                person["last_placement"] = last_placement
        return template.render({"persons": persons, "date": self.date_str})


def get_entries() -> "List[Entry]":
    with shelve.open(SHELVE_DB) as db:
        if "entries" in db:
            return db["entries"].values()
        return []


def generate_rss() -> bytes:
    fg = FeedGenerator()
    fg.title("Mrkoll.se Swedish toplist")
    fg.link(href=SWEDEN_TOPLIST_URL, rel="via")

    fg.description("An weekly RSS feed of mrkoll.se's Swedish toplist")

    for entry in get_entries():
        fg.add_entry(entry.feed_entry)

    return fg.rss_str(pretty=True)


def regenerate():
    for entry in get_entries():
        entry.generate_feed_entry()
        entry.save()


def scrape():
    Entry.fetch_and_save()
