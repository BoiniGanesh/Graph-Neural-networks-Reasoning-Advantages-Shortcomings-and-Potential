"""
Drug Adverse Events Explorer

This script demonstrates how to query FDA-reported drug adverse events
using the openFDA Drug Event API. It includes:

- Functions to get recent adverse event reports
- Functions to get top reported side effects (aggregated)
- Example calls with usage and expected outputs
- Clear structure for testing or reuse

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

def get_adverse_events(drug_name, limit=5):
    """
    Get recent individual adverse event reports related to a specific drug.

    Parameters:
        drug_name (str): Name of the drug (brand or generic)
        limit (int): Number of reports to return (default: 5)

    Example Usage:
        get_adverse_events("Ibuprofen")
        get_adverse_events("Amoxicillin")
        get_adverse_events("Metformin", limit=10)

    Expected Output:
        {
            'results': [
                {
                    'patient': {
                        'reaction': [
                            {'reactionmeddrapt': 'Headache'},
                            {'reactionmeddrapt': 'Nausea'}
                        ]
                    },
                    ...
                },
                ...
            ]
        }
    """
    params = {
        "search": f"patient.drug.medicinalproduct:{drug_name}",
        "limit": limit
    }
    return fetch_data("drug/event.json", params)

def get_top_adverse_reactions(drug_name):
    """
    Get the most frequently reported side effects for a given drug.

    Parameters:
        drug_name (str): Name of the drug (brand or generic)

    Example Usage:
        get_top_adverse_reactions("Ibuprofen")
        get_top_adverse_reactions("Aspirin")
        get_top_adverse_reactions("Lisinopril")

    Expected Output:
        {
            'results': [
                {'term': 'Nausea', 'count': 345},
                {'term': 'Headache', 'count': 210},
                ...
            ]
        }
    """
    params = {
        "search": f"patient.drug.medicinalproduct:{drug_name}",
        "count": "patient.reaction.reactionmeddrapt.exact"
    }
    return fetch_data("drug/event.json", params)

def run_demo():
    print("\n=== Recent Adverse Events: Ibuprofen ===")
    pprint.pprint(get_adverse_events("Ibuprofen"))

    print("\n=== Recent Adverse Events: Metformin ===")
    pprint.pprint(get_adverse_events("Metformin", limit=3))

    print("\n=== Top Adverse Reactions: Aspirin ===")
    pprint.pprint(get_top_adverse_reactions("Aspirin"))

    print("\n=== Top Adverse Reactions: Lisinopril ===")
    pprint.pprint(get_top_adverse_reactions("Lisinopril"))

if __name__ == "__main__":
    run_demo()