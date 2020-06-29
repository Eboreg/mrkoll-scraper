import re
import shelve
from datetime import date, datetime
from typing import TYPE_CHECKING
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup
from dateutil.tz import gettz
from feedgen.entry import FeedEntry
from feedgen.feed import FeedGenerator
from jinja2 import Environment, PackageLoader, select_autoescape

if TYPE_CHECKING:
    from typing import List, Iterator, Dict, Union, Optional


MRKOLL_BASE_URL = "https://mrkoll.se/"
SWEDEN_TOPLIST_URL = MRKOLL_BASE_URL + "topplistor/sverigetoppen/"
DDG_BASE_URL = "https://duckduckgo.com/?q="
FLASHBACK_BASE_URL = "https://www.flashback.org/sok/?query="
FACEBOOK_BASE_URL = "https://www.facebook.com/search/people/?q="
SHELVE_DB = "mrks"


def make_search_term(name: str, location: "Optional[str]" = None) -> str:
    search_term = name
    if location:
        search_term += " " + location
    return quote_plus(search_term)


def scrape() -> "Iterator[Dict[str, Union[str, int]]]":
    r = requests.get(SWEDEN_TOPLIST_URL)
    soup = BeautifulSoup(r.content, "html.parser")
    # MrKoll's HTML is broken (the p.infoLine2 tags are not closed)
    person_list = soup.select(".infoLine2 a")
    for person in person_list:
        name, location = person.select_one("span.topp1").contents
        name = name.text
        location = re.sub(r"^\si\s", "", location)
        search_term = make_search_term(name, location)
        result = {
            "name": name,
            "location": location,
            "search_count": int(re.sub(r"\D", "", person.select_one("span.topp2").text)),
            "mrkoll_link": urljoin(MRKOLL_BASE_URL, person.attrs["href"]),
            "flashback_link": FLASHBACK_BASE_URL + search_term,
            "ddg_link": DDG_BASE_URL + search_term,
            "facebook_link": FACEBOOK_BASE_URL + make_search_term(name),
        }
        yield result


def get_current_toplist_html() -> str:
    jinja = Environment(loader=PackageLoader("mrks", "templates"), autoescape=select_autoescape(["html"]))
    template = jinja.get_template("entry.html")
    return template.render({"persons": scrape(), "date": date.today()})


def save_current_entry():
    fe = FeedEntry()
    fe.title(str(date.today()))
    fe.published(datetime.now(tz=gettz("Europe/Stockholm")))
    fe.description(get_current_toplist_html())
    with shelve.open(SHELVE_DB, writeback=True) as db:
        if "entries" not in db:
            db["entries"] = []
        db["entries"].append(fe)


def get_entries() -> "List[FeedEntry]":
    with shelve.open(SHELVE_DB) as db:
        if "entries" in db:
            return db["entries"]
        return []


def generate_rss() -> bytes:
    fg = FeedGenerator()
    fg.title("Mrkoll.se Swedish toplist")
    fg.link(href=SWEDEN_TOPLIST_URL, rel="via")

    fg.description("An weekly RSS feed of mrkoll.se's Swedish toplist")

    for entry in get_entries():
        fg.add_entry(entry)

    return fg.rss_str(pretty=True)


if __name__ == "__main__":
    print(generate_rss().decode())
