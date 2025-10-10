"""
Food Recalls Explorer

This script demonstrates how to query FDA food recall and enforcement data
using the openFDA Food Enforcement API. It includes:

- Function to fetch recent recall reports for a given food product.
- Clear docstring with parameters, usage examples, and expected output.
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

def get_food_recalls(product, limit=3):
    """
    Get recent food or dietary supplement recall data.

    Parameters:
        product (str): Name or keyword describing the food product.
        limit (int): Number of recall records to return (default: 3).

    Example Usage:
        get_food_recalls("Peanut Butter")
        get_food_recalls("Spinach")
        get_food_recalls("Baby Formula", limit=5)

    Expected Output:
        {
            'results': [
                {
                    'product_description': 'Jif Peanut Butter',
                    'reason_for_recall': 'Possible Salmonella contamination',
                    'status': 'Ongoing',
                    'recalling_firm': 'XYZ Foods Inc.',
                    ...
                },
                ...
            ]
        }
    """
    params = {
        "search": f"product_description:{product}",
        "limit": limit
    }
    return fetch_data("food/enforcement.json", params)

def run_demo():
    print("\n=== Food Recalls: Peanut Butter ===")
    pprint.pprint(get_food_recalls("Peanut Butter"))

    print("\n=== Food Recalls: Spinach ===")
    pprint.pprint(get_food_recalls("Spinach"))

    print("\n=== Food Recalls: Baby Formula ===")
    pprint.pprint(get_food_recalls("Baby Formula", limit=5))

    print("\n=== Food Recalls: Frozen Berries ===")
    pprint.pprint(get_food_recalls("Frozen Berries"))

if __name__ == "__main__":
    run_demo()
