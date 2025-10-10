# Test Tool 5: Device Event Reports Lookup  
**Uses:** `get_device_events` — queries the openFDA Device Event API to find recent adverse event reports for a specific medical device.

---

## 🔍 **Tool Purpose**

This tool checks real-world adverse event data for **medical devices**. It helps:
- Identify safety issues, malfunctions, injuries, or deaths reported to the FDA.
- Understand trends in device performance and potential risks.
- Cross-reference with other FDA data sources for full safety checks.

**Arguments:**
- `device_name` (str): Brand name or type of the device (e.g., “Insulin Pump”, “Pacemaker”).
- `limit` (int, optional): Number of event records to return (default: 3).

---

## ✅ **Questions Tested**

| Question | Exact Tool Call | Exact Answer | Answer Breakdown |
| -------- | ---------------- | ------------- | ----------------- |
| 1️⃣ Are there recent events for Insulin Pumps? | `get_device_events("Insulin Pump")` | Example: `{ 'results': [ { 'event_type': 'Malfunction', 'date_of_event': '2024XXXX', 'device': { 'brand_name': 'Insulin Pump' }, ... } ] }` | **Case I:** ✅ *Tool answered.* Returns real reports showing malfunctions or injuries related to insulin pumps. |
| 2️⃣ Any Pacemaker adverse event reports? | `get_device_events("Pacemaker")` | Example: `{ 'results': [ {...} ] }` | **Case I:** ✅ *Tool answered.* Confirms reports of pacemaker failures or complications. |
| 3️⃣ What about Blood Glucose Monitors? | `get_device_events("Blood Glucose Monitor", limit=5)` | Example: `{ 'results': [ {...}, {...} ] }` | **Case I:** ✅ *Tool answered.* Shows up to 5 recent event reports for blood glucose monitoring devices. |
| 4️⃣ Are there reports for Hip Implants? | `get_device_events("Hip Implant")` | Example: `{ 'results': [ {...} ] }` | **Case I:** ✅ *Tool answered.* Returns reports on hip implant device malfunctions or patient injuries. |

---

## ⚠️ **Cases With No Answer (If Any)**

In this run, all common device names produced results.

**If no answer appears:**
- The device name may not exactly match `device.brand_name` in the FDA dataset.
- Try alternative names (e.g., “Artificial Hip” vs “Hip Implant”).
- Some devices have low reporting frequency or may be listed under manufacturer-specific brand names.

---

## ✅ **Combined Summary**

The **Device Event Reports Tool** lets you:
- Review real-world adverse event data for medical devices.
- See if a specific type of device has had safety issues.
- Combine with Drug Labeling, Adverse Events, Recalls, and Food Recall tools for **complete FDA monitoring**.

---

