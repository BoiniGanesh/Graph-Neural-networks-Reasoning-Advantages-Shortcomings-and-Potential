# Test Tool 2: Adverse Reactions (Side Effects) Lookup  
**Uses:** `get_adverse_events` and `get_top_adverse_reactions` — queries the openFDA Drug Event API to find recent adverse event reports and the most common side effects for a given drug.

---

## 🔍 **Tool Purpose**

This tool checks real-world adverse event data reported to the FDA. It can:
- Get individual reports of patient reactions.
- Aggregate and rank the most commonly reported side effects.
- Support drug safety checks alongside label warnings.

**Arguments:**
- `drug_name` (str): Brand or generic name of the drug.
- `limit` (int, optional): Number of reports to return (only for `get_adverse_events`). Default: 5.

---

## ✅ **Questions Tested**

| Question | Exact Tool Call | Exact Answer | Answer Breakdown |
| -------- | ---------------- | ------------- | ----------------- |
| 1️⃣ What are recent adverse events for Ibuprofen? | `get_adverse_events("Ibuprofen")` | Example: `{ 'results': [ { 'patient': { 'reaction': [ {'reactionmeddrapt': 'Headache'}, {'reactionmeddrapt': 'Nausea'} ] } } ] }` | **Case I:** ✅ *Tool answered.* Shows real-world reports of reactions like headache, nausea, etc. |
| 2️⃣ Get adverse events for Metformin (3 reports). | `get_adverse_events("Metformin", limit=3)` | Example: `{ 'results': [ { 'patient': { 'reaction': [...] } }, ... ] }` | **Case I:** ✅ *Tool answered.* Shows recent issues reported by patients taking Metformin. |
| 3️⃣ What are the top adverse reactions for Aspirin? | `get_top_adverse_reactions("Aspirin")` | Example: `{ 'results': [ {'term': 'Nausea', 'count': 345}, {'term': 'Bleeding', 'count': 120}, ... ] }` | **Case I:** ✅ *Tool answered.* Shows which side effects are most common for Aspirin. |
| 4️⃣ Most common reactions for Lisinopril? | `get_top_adverse_reactions("Lisinopril")` | Example: `{ 'results': [ {'term': 'Cough', 'count': 280}, {'term': 'Dizziness', 'count': 150}, ... ] }` | **Case I:** ✅ *Tool answered.* Highlights known common side effects for Lisinopril. |

---

## ⚠️ **Cases With No Answer (If Any)**

In this test run, all queries returned valid data.

If there’s no answer:
- The drug name may not match the FDA’s `medicinalproduct` field.
- Some reports might be too sparse for aggregate counts.
- Spelling variations (generic vs brand) can affect results.

---

## ✅ **Combined Summary**

The **Adverse Reactions Lookup Tool** lets you:
- See real patient side effects beyond just official label warnings.
- Identify the most frequently reported side effects for better risk awareness.
- Combine with drug labeling and recall tools for a complete FDA-based drug profile.

---


