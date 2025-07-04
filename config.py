# Configuration for Bilbasen scraper

# Search filters - modify these to change what cars to scrape
SEARCH_FILTERS = {
    "pageSize": 30,
    "selectedFilters": {
        "Ownership": {
            "value": {
                "value": "Retail"  # Options: "Retail", "Leasing", etc.
            }
        },
        "Category": {
            "value": {
                "value": "Car"  # Options: "Car", "Van", etc.
            }
        },
        "PriceRange": {
            "value": {
                "fromValue": 250000,  # Minimum price in kr
                "toValue": 300000     # Maximum price in kr
            }
        },
        "FirstRegistration": {
            "value": {
                "fromValue": 2024  # Minimum registration year
            }
        },
        "FuelType": {
            "values": [
                {
                    "value": "Electric"  # Options: "Electric", "Petrol", "Diesel", etc.
                }
            ]
        },
        "Model":{
            "values":[
                {
                    "parent": {"key":"Make","value":"Mercedes"},
                    "values": ["ms-EQB-Klasse"]
                }
            ]
        }
    }
}

# Scraping settings
DELAY_BETWEEN_REQUESTS = 1  # seconds
MAX_PAGES = None  # Set to a number to limit pages, None for all pages
TIMEOUT = 30  # Request timeout in seconds

# Output settings
OUTPUT_DIR = "data"