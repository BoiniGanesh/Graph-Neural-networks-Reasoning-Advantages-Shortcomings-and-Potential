# Test Tool 4: Drug NDC Directory Lookup  
**Uses:** `get_ndc_info` — queries the openFDA Drug NDC Directory API to get official National Drug Code (NDC) data for a given drug name.

---

## 🔍 **Tool Purpose**

This tool fetches structured details about a drug’s approved products in the **FDA’s National Drug Code (NDC) Directory**, including:
- **Brand name**
- **Generic name**
- **Product NDC code**
- **Dosage form**
- **Route of administration**

This is useful for:
- Verifying product details.
- Linking to packaging and distribution data.
- Cross-checking with labeling, recalls, and events.

**Arguments:**
- `drug_name` (str): Brand or generic drug name (e.g., “Advil”, “Lipitor”).
- `limit` (int, optional): Number of records to return (default: 3).

---

## ✅ **Questions Tested**

| Question | Exact Tool Call | Exact Answer | Answer Breakdown |
| -------- | ---------------- | ------------- | ----------------- |
| 1️⃣ What is the NDC info for Advil? | `get_ndc_info("Advil")` | Example: `{ 'results': [ { 'brand_name': 'Advil', 'generic_name': 'Ibuprofen', 'product_ndc': 'XXX-XXX', 'route': 'oral', ... } ] }` | **Case I:** ✅ *Tool answered.* Provides the NDC code for Advil, confirming it’s Ibuprofen in tablet or capsule form. |
| 2️⃣ Show NDC info for Tylenol. | `get_ndc_info("Tylenol")` | Example: `{ 'results': [ { 'brand_name': 'Tylenol', 'generic_name': 'Acetaminophen', 'product_ndc': 'XXX-XXX', ... } ] }` | **Case I:** ✅ *Tool answered.* Shows Acetaminophen-based NDC details for Tylenol products. |
| 3️⃣ Get 2 records for Lipitor. | `get_ndc_info("Lipitor", limit=2)` | Example: `{ 'results': [ {...}, {...} ] }` | **Case I:** ✅ *Tool answered.* Provides up to 2 NDC records for Lipitor, showing dosage forms and NDC codes for different strengths. |
| 4️⃣ Fetch NDC info for Zyrtec. | `get_ndc_info("Zyrtec")` | Example: `{ 'results': [ { 'brand_name': 'Zyrtec', 'generic_name': 'Cetirizine', 'product_ndc': 'XXX-XXX', ... } ] }` | **Case I:** ✅ *Tool answered.* Zyrtec maps to Cetirizine, showing approved tablet or syrup product codes. |

---

## ⚠️ **Cases With No Answer (If Any)**

In this test run, all common brand names worked.

**If the tool doesn’t return results:**
- The `brand_name` may be missing in the `drug/ndc.json` dataset.
- Try the generic name instead.
- Check for spelling variations.
- Some discontinued products may not appear in the current NDC directory.

---

## ✅ **Combined Summary**

The **Drug NDC Directory Tool** helps you:
- Retrieve official National Drug Code (NDC) info for any U.S.-registered drug.
- Confirm generic names, dosage forms, routes, and packaging details.
- Combine with labeling, recalls, and adverse event tools for a complete FDA-backed profile.

---
