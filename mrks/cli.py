#!/usr/bin/env python3

import argparse

from mrks.scraper import regenerate, scrape


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--scrape", action="store_true", help="Scrape & save results")
    parser.add_argument("-r", "--regenerate", action="store_true", help="Regenerate entries from saved raw HTML")

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
        print("Nothing to do!")
        parser.print_help()


if __name__ == "__main__":
    main()
