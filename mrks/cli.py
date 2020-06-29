#!/usr/bin/env python3

import argparse

from mrks.scraper import save_current_entry


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--scrape", action="store_true", help="Scrape & save results")

    args = parser.parse_args()

    if not args.scrape:
        print("Nothing to do!")
        parser.print_usage()
    else:
        print("Scraping & saving ...")
        save_current_entry()
        print("... done!")


if __name__ == "__main__":
    main()
