"""
Drug Recalls & Enforcement Explorer

This script demonstrates how to query drug recalls and enforcement reports
using the openFDA Drug Enforcement API. It includes:

- Function to fetch recent recalls for a given drug or ingredient.
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

def get_drug_recalls(substance, limit=3):
    """
    Retrieve recent recall/enforcement reports for a given drug or ingredient.

    Parameters:
        substance (str): The drug's brand, generic, or active ingredient name.
        limit (int): Number of recall records to return (default: 3).

    Example Usage:
        get_drug_recalls("Valsartan")
        get_drug_recalls("Losartan")
        get_drug_recalls("Metformin", limit=5)

    Expected Output:
        {
            'results': [
                {
                    'reason_for_recall': 'NDMA contamination',
                    'status': 'Ongoing',
                    'product_description': '...',
                    'recalling_firm': '...',
                    ...
                },
                ...
            ]
        }
    """
    params = {
        "search": f"product_description:{substance}",
        "limit": limit
    }
    return fetch_data("drug/enforcement.json", params)

def run_demo():
    print("\n=== Drug Recalls: Valsartan ===")
    pprint.pprint(get_drug_recalls("Valsartan"))

    print("\n=== Drug Recalls: Losartan ===")
    pprint.pprint(get_drug_recalls("Losartan"))

    print("\n=== Drug Recalls: Metformin ===")
    pprint.pprint(get_drug_recalls("Metformin", limit=5))

    print("\n=== Drug Recalls: Ranitidine ===")
    pprint.pprint(get_drug_recalls("Ranitidine"))

if __name__ == "__main__":
    run_demo()
