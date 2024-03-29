#!/usr/bin/env python3

import argparse

from mrks import __version__
from mrks.scraper import regenerate, scrape, generate_rss


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--scrape", action="store_true", help="Scrape & save results")
    parser.add_argument("-r", "--regenerate", action="store_true", help="Regenerate entries from saved raw HTML")
    parser.add_argument("-V", "--version", action="version", version="mrkoll-scraper " + __version__)

    args = parser.parse_args()

    if args.regenerate:
        print("Regenerating ...")
        regenerate()
        print("... done!")
    if args.scrape:
        print("Scraping & saving ...")
        scrape()
        print("... done!")

    if not args.regenerate and not args.scrape:
        print(generate_rss().decode())


if __name__ == "__main__":
    main()
