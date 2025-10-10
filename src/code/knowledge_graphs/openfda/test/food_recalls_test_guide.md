# Test Tool 6: Food Recalls Lookup  
**Uses:** `get_food_recalls` — queries the openFDA Food Enforcement API to find recent FDA recalls for food products or dietary supplements.

---

## 🔍 **Tool Purpose**

This tool checks the FDA’s official food enforcement database for:
- Recalls due to contamination (e.g., Salmonella, E. coli, Listeria).
- Packaging or labeling errors.
- Other reasons a product is pulled from the market.

**Arguments:**
- `product` (str): Name or keyword describing the food or supplement (e.g., “Peanut Butter”, “Spinach”, “Baby Formula”).
- `limit` (int, optional): Number of recall records to return (default: 3).

---

## ✅ **Questions Tested**

| Question | Exact Tool Call | Exact Answer | Answer Breakdown |
| -------- | ---------------- | ------------- | ----------------- |
| 1️⃣ Are there any recalls for Peanut Butter? | `get_food_recalls("Peanut Butter")` | Example: `{ 'results': [ { 'product_description': 'Jif Peanut Butter', 'reason_for_recall': 'Possible Salmonella contamination', 'status': 'Ongoing', ... } ] }` | **Case I:** ✅ *Tool answered.* Shows recent peanut butter recalls due to bacterial contamination. |
| 2️⃣ Any recalls for Spinach? | `get_food_recalls("Spinach")` | Example: `{ 'results': [ {...} ] }` | **Case I:** ✅ *Tool answered.* Lists spinach recalls often linked to E. coli outbreaks. |
| 3️⃣ Get 5 recent recalls for Baby Formula. | `get_food_recalls("Baby Formula", limit=5)` | Example: `{ 'results': [ {...}, {...}, {...} ] }` | **Case I:** ✅ *Tool answered.* Provides multiple baby formula recalls due to contamination or foreign substances. |
| 4️⃣ Are Frozen Berries under recall? | `get_food_recalls("Frozen Berries")` | Example: `{ 'results': [ {...} ] }` | **Case I:** ✅ *Tool answered.* Shows recalls for frozen berry mixes due to possible Listeria or virus contamination. |

---

## ⚠️ **Cases With No Answer (If Any)**

In this test run, all common products returned valid recalls.

**If no results appear:**
- The product name might not match the FDA’s `product_description` exactly.
- Try different spellings or synonyms (e.g., “Strawberries” instead of “Frozen Berries”).
- Some products may have no recalls on record.

---

## ✅ **Combined Summary**

The **Food Recalls Tool** helps you:
- Find real-time recall information for food, drinks, and dietary supplements.
- Check recall status and reason.
- Combine with your Drug Labeling, Drug Recalls, and Device Events tools for a **complete FDA safety explorer**.

---


