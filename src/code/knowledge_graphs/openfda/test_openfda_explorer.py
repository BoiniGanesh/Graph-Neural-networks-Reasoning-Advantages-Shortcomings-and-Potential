
"""
Comprehensive openFDA API Explorer with Examples

This script demonstrates how to access and explore the main openFDA datasets.
Each function includes:
- A description of what it does
- Sample usage
- What kind of results you can expect

Sections:
1. Drug Labeling
2. Drug Adverse Events
3. Drug Recalls / Enforcement
4. Drug NDC Directory
5. Device Event Reports
6. Food Recalls

"""

import requests
import pprint

BASE_URL = "https://api.fda.gov"

def fetch_data(endpoint, params):
    """Send request to openFDA API and return JSON response."""
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# 1. Drug Labeling
def query_drug_label(brand_name, limit=1):
    """
    Get FDA-approved label information for a brand-name drug.

    Examples:
        query_drug_label("Tylenol")
        query_drug_label("Zyrtec")
        query_drug_label("Aleve", limit=2)

    Expected Output:
        {'results': [{'indications_and_usage': [...], 'warnings': [...]}]}
    """
    return fetch_data("drug/label.json", {"search": f"openfda.brand_name:{brand_name}", "limit": limit})

# 2. Drug Adverse Events
def get_adverse_events(drug_name, limit=5):
    """
    Get recent adverse event reports related to a specific drug.

    Examples:
        get_adverse_events("Ibuprofen")
        get_adverse_events("Amoxicillin")
        get_adverse_events("Metformin", limit=10)

    Expected Output:
        {'results': [{'patient': {'reaction': [{'reactionmeddrapt': 'Headache'}]}}]}
    """
    return fetch_data("drug/event.json", {"search": f"patient.drug.medicinalproduct:{drug_name}", "limit": limit})

def get_top_adverse_reactions(drug_name):
    """
    Get the most common side effects for a drug.

    Examples:
        get_top_adverse_reactions("Ibuprofen")
        get_top_adverse_reactions("Aspirin")
        get_top_adverse_reactions("Lisinopril")

    Expected Output:
        {'results': [{'term': 'Nausea', 'count': 345}, ...]}
    """
    return fetch_data("drug/event.json", {
        "search": f"patient.drug.medicinalproduct:{drug_name}",
        "count": "patient.reaction.reactionmeddrapt.exact"
    })

# 3. Drug Recalls / Enforcement
def get_drug_recalls(substance, limit=3):
    """
    Retrieve recent recalls for a drug or ingredient.

    Examples:
        get_drug_recalls("Valsartan")
        get_drug_recalls("Losartan")
        get_drug_recalls("Metformin", limit=5)

    Expected Output:
        {'results': [{'reason_for_recall': 'NDMA contamination', 'status': 'Ongoing'}, ...]}
    """
    return fetch_data("drug/enforcement.json", {"search": f"product_description:{substance}", "limit": limit})

# 4. Drug NDC Directory
def get_ndc_info(drug_name, limit=3):
    """
    Fetch National Drug Code (NDC) directory information for a drug.

    Examples:
        get_ndc_info("Advil")
        get_ndc_info("Tylenol")
        get_ndc_info("Lipitor", limit=2)

    Expected Output:
        {'results': [{'brand_name': 'Advil', 'route': 'oral', ...}]}
    """
    return fetch_data("drug/ndc.json", {"search": f"brand_name:{drug_name}", "limit": limit})

# 5. Device Event Reports
def get_device_events(device_name, limit=3):
    """
    Get adverse event reports for a specific medical device.

    Examples:
        get_device_events("Insulin Pump")
        get_device_events("Pacemaker")
        get_device_events("Blood Glucose Monitor", limit=4)

    Expected Output:
        {'results': [{'event_type': 'Malfunction', 'date_of_event': '2021XXXX'}, ...]}
    """
    return fetch_data("device/event.json", {"search": f"device.brand_name:{device_name}", "limit": limit})

# 6. Food Recalls
def get_food_recalls(product, limit=3):
    """
    Get food or supplement recall data.

    Examples:
        get_food_recalls("Peanut Butter")
        get_food_recalls("Spinach")
        get_food_recalls("Baby Formula", limit=5)

    Expected Output:
        {'results': [{'product_description': '...', 'reason_for_recall': '...'}, ...]}
    """
    return fetch_data("food/enforcement.json", {"search": f"product_description:{product}", "limit": limit})

# Sample Execution
if __name__ == "__main__":
    results = {
        " Drug Label (Tylenol)": query_drug_label("Tylenol"),
        " Drug Label (Zyrtec)": query_drug_label("Zyrtec"),
        " Adverse Events (Ibuprofen)": get_adverse_events("Ibuprofen"),
        " Adverse Events (Metformin)": get_adverse_events("Metformin"),
        "Top Adverse Reactions (Aspirin)": get_top_adverse_reactions("Aspirin"),
        "Drug Recalls (Valsartan)": get_drug_recalls("Valsartan"),
        "Drug Recalls (Losartan)": get_drug_recalls("Losartan"),
        "Drug NDC Info (Lipitor)": get_ndc_info("Lipitor"),
        "Device Events (Insulin Pump)": get_device_events("Insulin Pump"),
        "Device Events (Pacemaker)": get_device_events("Pacemaker"),
        "Food Recalls (Peanut Butter)": get_food_recalls("Peanut Butter"),
        " Food Recalls (Spinach)": get_food_recalls("Spinach")
    }

    for key, value in results.items():
        print(f"\n=== {key} ===")
        pprint.pprint(value)
