"""
Drug NDC Directory Explorer

This script demonstrates how to query the openFDA Drug NDC Directory API.
It includes:

- Function to fetch National Drug Code (NDC) information for a drug.
- Clear docstring with parameters, examples, and expected output.
- A sample execution block for quick testing.

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

def get_ndc_info(drug_name, limit=3):
    """
    Fetch National Drug Code (NDC) directory information for a drug.

    Parameters:
        drug_name (str): The brand name or generic name of the drug.
        limit (int): Number of NDC records to return (default: 3).

    Example Usage:
        get_ndc_info("Advil")
        get_ndc_info("Tylenol")
        get_ndc_info("Lipitor", limit=2)

    Expected Output:
        {
            'results': [
                {
                    'brand_name': 'Advil',
                    'generic_name': 'Ibuprofen',
                    'product_ndc': 'XXX-XXX',
                    'dosage_form': 'Tablet',
                    'route': 'oral',
                    ...
                },
                ...
            ]
        }
    """
    params = {
        "search": f"brand_name:{drug_name}",
        "limit": limit
    }
    return fetch_data("drug/ndc.json", params)

def run_demo():
    print("\n=== NDC Info: Advil ===")
    pprint.pprint(get_ndc_info("Advil"))

    print("\n=== NDC Info: Tylenol ===")
    pprint.pprint(get_ndc_info("Tylenol"))

    print("\n=== NDC Info: Lipitor ===")
    pprint.pprint(get_ndc_info("Lipitor", limit=2))

    print("\n=== NDC Info: Zyrtec ===")
    pprint.pprint(get_ndc_info("Zyrtec"))

if __name__ == "__main__":
    run_demo()
