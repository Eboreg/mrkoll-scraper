import re
from urllib.parse import urljoin, quote_plus

import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator


MRKOLL_BASE_URL = "https://mrkoll.se/"
SWEDEN_TOPLIST_URL = MRKOLL_BASE_URL + "topplistor/sverigetoppen/"
DDG_BASE_URL = "https://duckduckgo.com/?q="
FLASHBACK_BASE_URL = "https://www.flashback.org/sok/?query="


def make_search_term(name, location=None):
    search_term = name
    if location:
        search_term += " " + location
    return quote_plus(search_term)


def scrape():
    r = requests.get(SWEDEN_TOPLIST_URL)
    soup = BeautifulSoup(r.content, "html.parser")
    # MrKoll's HTML is broken (the p.infoLine2 tags are not closed)
    person_list = soup.select(".infoLine2 a")
    for person in person_list:
        name, location = person.select_one("span.topp1").contents
        name = name.text
        location = re.sub(r"^\si\s", "", location)
        result = {
            "name": name,
            "location": location,
            "search_count": int(re.sub(r"\D", "", person.select_one("span.topp2").text)),
            "mrkoll_link": urljoin(MRKOLL_BASE_URL, person.attrs["href"]),
            "flashback_link": FLASHBACK_BASE_URL + make_search_term(name, location),
            "ddg_link": DDG_BASE_URL + make_search_term(name, location),
        }
        yield result


def generate_rss():
    fg = FeedGenerator()
    fg.title("mrkoll.se Swedish toplist")
    fg.link(href=SWEDEN_TOPLIST_URL, rel="via")
    fg.description("An RSS feed of mrkoll.se's Swedish toplist")
    for person in scrape():
        fe = fg.add_entry(order="append")
        fe.title(", ".join((person["name"], person["location"])))
        fe.link(href=person["mrkoll_link"], rel="alternate")
        # Description is automatically HTML escaped by feedgen
        # https://stackoverflow.com/questions/9866472/rss-specification-html-code-inside-rss-feed
        fe.description(
            '<a href="{}">Duckduckgo search</a><br>'
            '<a href="{}">Flashback search</a>'
            .format(person["ddg_link"], person["flashback_link"])
        )
    return fg.rss_str(pretty=True)


if __name__ == "__main__":
    print(generate_rss().decode())
