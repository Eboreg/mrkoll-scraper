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
    from typing import List, Iterator, Dict, Union


MRKOLL_BASE_URL = "https://mrkoll.se/"
SWEDEN_TOPLIST_URL = MRKOLL_BASE_URL + "topplistor/sverigetoppen/"
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

    def _extract_data(self) -> "Iterator[Dict[str, Union[str, int]]]":
        if not hasattr(self, "raw_html"):
            self.fetch()
        soup = BeautifulSoup(self.raw_html, "html.parser")
        # MrKoll's HTML is broken (the p.infoLine2 tags are not closed)
        person_list = soup.select(".infoLine2 a")
        for person in person_list:
            name, location = person.select_one("span.topp1").contents
            name = name.text
            location = re.sub(r"^\si\s", "", location)
            search_term = quote_plus(name)
            result = {
                "name": name,
                "location": location,
                "search_count": int(re.sub(r"\D", "", person.select_one("span.topp2").text)),
                "mrkoll_link": urljoin(MRKOLL_BASE_URL, person.attrs["href"]),
                "flashback_link": FLASHBACK_BASE_URL + search_term,
                "ddg_link": DDG_BASE_URL + search_term,
                "facebook_link": FACEBOOK_BASE_URL + search_term,
            }
            yield result

    def _generate_entry_html(self) -> str:
        jinja = Environment(loader=PackageLoader("mrks", "templates"), autoescape=select_autoescape(["html"]))
        template = jinja.get_template("entry.html")
        return template.render({"persons": self._extract_data(), "date": self.date_str})


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


if __name__ == "__main__":
    print(generate_rss().decode())
