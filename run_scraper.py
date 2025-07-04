#!/usr/bin/env python3
"""
Simple runner script for the Bilbasen scraper
"""

import argparse
from get_cars import BilbasenScraper

def main():
    parser = argparse.ArgumentParser(description='Scrape cars from Bilbasen')
    parser.add_argument('--max-pages', type=int, help='Maximum number of pages to scrape')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests in seconds')
    parser.add_argument('--output', type=str, help='Output filename')

    args = parser.parse_args()

    scraper = BilbasenScraper()

    print("Starting Bilbasen scraper...")
    print(f"Filters: Electric cars, 250k-300k kr, registered 2024+")

    # Scrape data
    listings, total_items = scraper.scrape_all_pages(
        max_pages=args.max_pages,
        delay=args.delay
    )

    if listings:
        # Save data
        filepath = scraper.save_data(listings, args.output)

        # Show summary
        summary = scraper.extract_car_summary(listings)
        print(f"\nSuccessfully scraped {len(listings)} cars!")
        print(f"Data saved to: {filepath}")
    else:
        print("No data was scraped.")

if __name__ == "__main__":
    main()