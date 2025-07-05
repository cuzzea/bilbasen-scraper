import requests
import json
import time
from datetime import datetime
from pathlib import Path

class BilbasenScraper:
    def __init__(self):
        self.base_url = "https://www.bilbasen.dk/api/search/by-request"
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Sec-Fetch-Site': 'same-origin',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Sec-Fetch-Mode': 'cors',
            'Host': 'www.bilbasen.dk',
            'Origin': 'https://www.bilbasen.dk',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
            'Referer': 'https://www.bilbasen.dk/brugt/bil?includeengroscvr=true&includeleasing=false&pricefrom=250000&priceto=300000&regfrom=2024-01',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty'
        }

        self.search_payload = {
            "pageSize": 100,
            "selectedFilters": {
                "Ownership": {
                    "value": {
                        "value": "Retail"
                    }
                },
                "Category": {
                    "value": {
                        "value": "Car"
                    }
                },
                "PriceRange": {
                    "value": {
                        "fromValue": 100000,
                        "toValue": 300000
                    }
                },
                "FirstRegistration": {
                    "value": {
                        "fromValue": 2020
                    }
                },
                # "FuelType": {
                #     "values": [
                #         {
                #             "value": "Electric"
                #         }
                #     ]
                # },
                "InteriorComfortEquipments":{
                    "values":[
                        {
                            "value":"HeadupDisplay"
                        }
                    ]
                },
                # "DriveWheel":{"values":[{"value":"Four"}]}
                # "Make":{"values":[{"value":"Mercedes"}]},
                # "Model":{
                #     "values":[
                #         {
                #             "parent": {"key":"Make","value":"Mercedes"},
                #             "values": ["ms-EQB-Klasse"]
                #         }
                #     ]
                # }
            }
        }

    def fetch_page(self, page_number=1):
        """Fetch a single page of results"""
        payload = self.search_payload.copy()
        payload["page"] = page_number

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching page {page_number}: {e}")
            return None

    def save_partial_data(self, listings, filename="bilbasen_cars_partial.json"):
        """Save the current scraped data to a partial JSON file after each batch/page"""
        # This method is now disabled to avoid creating partial files
        pass

    def scrape_all_pages(self, max_pages=None, delay=1):
        """Scrape all pages of results, saving after each batch and printing progress info"""
        all_listings = []
        page = 1
        total_items = None
        unique_brands = set()
        min_price = float('inf')
        max_price = 0
        print("Starting to scrape Bilbasen...")
        while True:
            print(f"Fetching page {page}...")
            data = self.fetch_page(page)
            if not data:
                print(f"Failed to fetch page {page}, stopping.")
                break
            # Get total items from first page
            if total_items is None and 'pulse' in data:
                total_items = data['pulse']['object']['numItems']
                print(f"Total items found: {total_items}")
            # Add listings from this page
            listings = data.get('listings', [])
            if not listings:
                print("No more listings found, stopping.")
                break
            all_listings.extend(listings)
            # Update unique brands and price range
            for listing in listings:
                make = listing.get('make', 'Unknown')
                unique_brands.add(make)
                price = listing.get('price', {}).get('price', 0)
                if price > 0:
                    min_price = min(min_price, price)
                    max_price = max(max_price, price)
            print(f"Collected {len(listings)} listings from page {page} (Total: {len(all_listings)})")
            # Print first car name/title for pagination validation
            first_car = listings[0] if listings else None
            first_car_name = first_car.get('title') or first_car.get('make', 'Unknown') if first_car else 'N/A'
            print(f"First car on this page: {first_car_name}")
            # Print current price range and unique brands
            price_from = min_price if min_price != float('inf') else 'N/A'
            price_to = max_price if max_price != 0 else 'N/A'
            print(f"Current price range: {price_from:,} - {price_to:,} kr")
            print(f"Unique brands so far: {sorted(unique_brands)}")
            # Save after each batch/page (disabled to avoid partial files)
            # self.save_partial_data(all_listings)
            # Check if we've reached the maximum pages
            if max_pages and page >= max_pages:
                print(f"Reached maximum pages limit ({max_pages})")
                break
            # Check if we've collected all available items
            if total_items and len(all_listings) >= total_items:
                print("Collected all available listings")
                break
            page += 1
            # Add delay between requests to be respectful
            if delay > 0:
                time.sleep(delay)
        return all_listings, total_items

    def save_data(self, listings, filename=None):
        """Save the scraped data to a JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bilbasen_cars_{timestamp}.json"

        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        filepath = data_dir / filename

        # Prepare data structure
        output_data = {
            "scraped_at": datetime.now().isoformat(),
            "total_listings": len(listings),
            "filters": {
                "price_range": "250,000 - 300,000 kr",
                "fuel_type": "Electric",
                "first_registration": "2024+",
                "ownership": "Retail",
                "category": "Car"
            },
            "listings": listings
        }

        # Save to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"Data saved to: {filepath}")
        return filepath

    def extract_car_summary(self, listings):
        """Extract a summary of the scraped cars"""
        summary = {
            "total_cars": len(listings),
            "makes": {},
            "price_range": {"min": float('inf'), "max": 0},
            "locations": {},
            "registration_years": {}
        }

        for listing in listings:
            # Count makes
            make = listing.get('make', 'Unknown')
            summary['makes'][make] = summary['makes'].get(make, 0) + 1

            # Track price range
            price = listing.get('price', {}).get('price', 0)
            if price > 0:
                summary['price_range']['min'] = min(summary['price_range']['min'], price)
                summary['price_range']['max'] = max(summary['price_range']['max'], price)

            # Count locations
            location = listing.get('location', {})
            city = location.get('city', 'Unknown')
            summary['locations'][city] = summary['locations'].get(city, 0) + 1

            # Count registration years
            reg_date = listing.get('properties', {}).get('firstregistrationdate', {}).get('displayTextShort', '')
            if reg_date:
                year = reg_date.split('/')[-1] if '/' in reg_date else reg_date
                summary['registration_years'][year] = summary['registration_years'].get(year, 0) + 1

        return summary

def main():
    scraper = BilbasenScraper()

    # Scrape all pages (with a 1-second delay between requests)
    listings, total_items = scraper.scrape_all_pages(delay=1)

    if listings:
        # Save the data
        filepath = scraper.save_data(listings, "latest_cars.json")

        # Print summary
        summary = scraper.extract_car_summary(listings)
        print("\n" + "="*50)
        print("SCRAPING SUMMARY")
        print("="*50)
        print(f"Total cars scraped: {summary['total_cars']}")
        print(f"Price range: {summary['price_range']['min']:,} - {summary['price_range']['max']:,} kr")

        print(f"\nTop car makes:")
        for make, count in sorted(summary['makes'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {make}: {count}")

        print(f"\nTop locations:")
        for city, count in sorted(summary['locations'].items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  {city}: {count}")

        print(f"\nRegistration years:")
        for year, count in sorted(summary['registration_years'].items()):
            print(f"  {year}: {count}")

        print(f"\nData saved to: {filepath}")
    else:
        print("No data was scraped.")

if __name__ == "__main__":
    main()