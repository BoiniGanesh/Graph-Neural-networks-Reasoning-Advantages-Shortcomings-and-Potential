"""
Device Event Reports Explorer

This script demonstrates how to query FDA-reported adverse events
for medical devices using the openFDA Device Event API. It includes:

- Function to fetch recent event reports for a given device name.
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

def get_device_events(device_name, limit=3):
    """
    Fetch recent adverse event reports for a specific medical device.

    Parameters:
        device_name (str): Brand name or type of the medical device.
        limit (int): Number of event reports to return (default: 3).

    Example Usage:
        get_device_events("Insulin Pump")
        get_device_events("Pacemaker")
        get_device_events("Blood Glucose Monitor", limit=5)

    Expected Output:
        {
            'results': [
                {
                    'event_type': 'Malfunction',
                    'date_of_event': 'YYYYMMDD',
                    'device': {
                        'brand_name': 'Insulin Pump'
                    },
                    'patient': {...},
                    'mdr_text': {...},
                    ...
                },
                ...
            ]
        }
    """
    params = {
        "search": f"device.brand_name:{device_name}",
        "limit": limit
    }
    return fetch_data("device/event.json", params)

def run_demo():
    print("\n=== Device Events: Insulin Pump ===")
    pprint.pprint(get_device_events("Insulin Pump"))

    print("\n=== Device Events: Pacemaker ===")
    pprint.pprint(get_device_events("Pacemaker"))

    print("\n=== Device Events: Blood Glucose Monitor ===")
    pprint.pprint(get_device_events("Blood Glucose Monitor", limit=5))

    print("\n=== Device Events: Hip Implant ===")
    pprint.pprint(get_device_events("Hip Implant"))

if __name__ == "__main__":
    run_demo()
