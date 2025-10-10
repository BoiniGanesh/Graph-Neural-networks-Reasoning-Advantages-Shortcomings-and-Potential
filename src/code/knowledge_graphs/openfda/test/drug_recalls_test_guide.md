# Test Tool 3: Drug Recalls & Enforcement Lookup  
**Uses:** `get_drug_recalls` — queries the openFDA Drug Enforcement API to find recent FDA recalls for a given drug or ingredient.

---

## 🔍 **Tool Purpose**

This tool checks for:
- Official FDA recall and enforcement actions related to contamination, mislabeling, or manufacturing defects.
- Detailed info about recall status, reason, product description, and the recalling firm.
- Recent or historical drug recall records.

**Arguments:**
- `substance` (str): Name of the drug, generic name, or ingredient (e.g., "Valsartan", "Losartan", "Metformin").
- `limit` (int, optional): Number of recall records to return (default: 3).

---

## ✅ **Questions Tested**

| Question | Exact Tool Call | Exact Answer | Answer Breakdown |
| -------- | ---------------- | ------------- | ----------------- |
| 1️⃣ Are there any recalls for Valsartan? | `get_drug_recalls("Valsartan")` | Example: `{ 'results': [ { 'reason_for_recall': 'NDMA contamination', 'status': 'Ongoing', 'product_description': '...', ... } ] }` | **Case I:** ✅ *Tool answered.* Confirms multiple recalls for Valsartan due to NDMA contamination. |
| 2️⃣ Show Losartan recalls. | `get_drug_recalls("Losartan")` | Example: `{ 'results': [ {...} ] }` | **Case I:** ✅ *Tool answered.* Similar contamination recalls as Valsartan. |
| 3️⃣ Get Metformin recalls (5 records). | `get_drug_recalls("Metformin", limit=5)` | Example: `{ 'results': [ {...}, {...}, ... ] }` | **Case I:** ✅ *Tool answered.* Shows several Metformin recalls related to NDMA impurities. |
| 4️⃣ Any recalls for Ranitidine? | `get_drug_recalls("Ranitidine")` | Example: `{ 'results': [ {...} ] }` | **Case I:** ✅ *Tool answered.* Shows recalls for Ranitidine due to carcinogenic impurities (NDMA). |

---

## ⚠️ **Cases With No Answer (If Any)**

In this test run, all queries returned valid recalls.

**Possible reasons for no answer:**
- Drug or ingredient is not covered by the `drug/enforcement.json` dataset.
- No recall events were ever reported for the given name.
- Spelling mismatch in the `product_description` search.

---

## ✅ **Combined Summary**

The **Drug Recalls & Enforcement Tool** helps you:
- Check whether a drug or ingredient has been subject to FDA recall.
- Understand why the recall was issued and its current status.
- Combine with labeling and adverse event tools for a full FDA risk check.

---
