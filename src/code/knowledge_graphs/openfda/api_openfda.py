# openfda.py
"""
Modular openFDA Agent for integration with LLM-driven pipeline
- Provides structured access to key openFDA endpoints
- Can be used similar to ToolAgent: OpenFDAAgent().answer_question(prompt)
"""

import requests

BASE_URL = "https://api.fda.gov"

class OpenFDAAgent:
    def __init__(self):
        self.tool_map = {
            "label": self.query_drug_label,
            "adverse event": self.get_adverse_events,
            "side effect": self.get_top_adverse_reactions,
            "recall": self.get_drug_recalls,
            "ndc": self.get_ndc_info,
            "device": self.get_device_events,
            "food": self.get_food_recalls
        }

    def fetch_data(self, endpoint, params):
        try:
            response = requests.get(f"{BASE_URL}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def query_drug_label(self, drug, limit=1):
        return self.fetch_data("drug/label.json", {"search": f"openfda.brand_name:{drug}", "limit": limit})

    def get_adverse_events(self, drug, limit=5):
        return self.fetch_data("drug/event.json", {"search": f"patient.drug.medicinalproduct:{drug}", "limit": limit})

    def get_top_adverse_reactions(self, drug):
        return self.fetch_data("drug/event.json", {
            "search": f"patient.drug.medicinalproduct:{drug}",
            "count": "patient.reaction.reactionmeddrapt.exact"
        })

    def get_drug_recalls(self, substance, limit=3):
        return self.fetch_data("drug/enforcement.json", {"search": f"product_description:{substance}", "limit": limit})

    def get_ndc_info(self, name, limit=3):
        return self.fetch_data("drug/ndc.json", {"search": f"brand_name:{name}", "limit": limit})

    def get_device_events(self, device, limit=3):
        return self.fetch_data("device/event.json", {"search": f"device.brand_name:{device}", "limit": limit})

    def get_food_recalls(self, product, limit=3):
        return self.fetch_data("food/enforcement.json", {"search": f"product_description:{product}", "limit": limit})

    def identify_tool(self, question):
        for keyword, func in self.tool_map.items():
            if keyword in question.lower():
                return func
        return None

    def extract_entity(self, question):
        words = question.split()
        for w in reversed(words):
            if w[0].isalpha():
                return w.strip("?.")
        return "Tylenol"

    def answer_question(self, question):
        tool = self.identify_tool(question)
        if not tool:
            return {"error": "No FDA tool matched."}

        arg = self.extract_entity(question)
        return tool(arg)


if __name__ == "__main__":
    fda = OpenFDAAgent()
    samples = [
        "Get drug label for Tylenol",
        "Show adverse events for Ibuprofen",
        "What are side effects of Aspirin",
        "List drug recalls for Valsartan",
        "NDC info for Lipitor",
        "Device problems with Pacemaker",
        "Food recalls involving Spinach"
    ]

    for q in samples:
        print(f"\n🔎 {q}")
        print(fda.answer_question(q))
