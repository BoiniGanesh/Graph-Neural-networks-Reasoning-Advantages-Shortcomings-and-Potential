"""
Drug Labeling Explorer

This script demonstrates how to query FDA-approved drug labeling data
from the openFDA API. It is self-contained and includes:

- Function to query drug label information
- Clear examples of how to call it
- Expected output structure
- Sample execution block

Author: Your Name
"""

import requests
import pprint

# Base URL for openFDA API
BASE_URL = "https://api.fda.gov"

def fetch_data(endpoint, params):
    """
    Generic helper to send a GET request to openFDA and return JSON.
    """
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def query_drug_label(brand_name, limit=1):
    """
    Get FDA-approved label information for a given brand-name drug.

    Parameters:
        brand_name (str): Name of the drug brand, e.g., "Tylenol"
        limit (int): Number of records to return (default = 1)

    Example Usage:
        query_drug_label("Tylenol")
        query_drug_label("Zyrtec", limit=2)

    Expected Output:
        {
            'results': [
                {
                    'indications_and_usage': [...],
                    'warnings': [...],
                    ...
                }
            ]
        }
    """
    params = {
        "search": f"openfda.brand_name:{brand_name}",
        "limit": limit
    }
    return fetch_data("drug/label.json", params)

def run_demo():
    drugs = [
        ("Tylenol", 1),
        ("Zyrtec", 2),
        ("Aleve", 1),
        ("Ibuprofen", 1),
        ("Lipitor", 1)
    ]

    for brand, limit in drugs:
        print(f"\n=== Drug Label: {brand} ===")
        pprint.pprint(query_drug_label(brand, limit=limit))

if __name__ == "__main__":
    run_demo()
