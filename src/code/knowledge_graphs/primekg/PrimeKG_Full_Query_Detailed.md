
# Test Script: PrimeKG Full Query & Entity Relationship Lookup

This test script demonstrates a **full pipeline** for working with the **Prime Knowledge Graph (PrimeKG)** using Python, **pandas**, and **NetworkX** — without needing a dedicated graph database.  
It shows how to **verify source files**, **query for diseases, drugs, or genes**, and **extract related entities** for deeper biomedical analysis.

Below is a clear breakdown of the **main workflow**, **test examples**, the **type of output**, and detailed explanations for each step.

---

## 📌 1️⃣ Initial File Check

**Purpose:**  
Verify that all required input files exist and are structured correctly before running any query logic.

**What happens:**  
- Loads the core files:  
  - `kg.csv` (edges: relationships between nodes)  
  - `nodes.csv` (master list of all nodes)  
  - `disease_features.csv`  
  - `drug_features.csv`  
  - `gene_features.csv` (if available)
- Prints basic stats:  
  - Number of nodes and edges  
  - Checks for expected columns (e.g., `node_index`, `name`, `description`).

**Why it matters:**  
This step ensures that all CSVs are in place and have the right schema, preventing downstream errors during filtering, joining, or graph building.

---

## 🧬 2️⃣ Disease Query Example — *osteogenesis imperfecta*

**Goal:**  
Find a specific disease (**osteogenesis imperfecta**) and all directly related **genes**, **drugs**, and other diseases.

**What happens:**  
- Searches `disease_features.csv` for the keyword in:
  - `mondo_name`
  - `umls_description`
  - `orphanet_definition`
- Extracts the matching `node_index` for the disease.
- Uses `kg.csv` to find all edges where this node is connected:
  - `relation` like *indication*, *disease_protein*, *disease_drug*, etc.
- Identifies related genes, drugs, or other diseases.
- Optionally merges back descriptive fields (names, definitions) for related nodes from `nodes.csv` and feature files.
- Prints:
  - Matched disease details.
  - List of connected nodes with basic metadata.

**Output Example:**

\`\`\`plaintext
Disease match: osteogenesis imperfecta
Node index: 1423

Connected genes: TP53, COL1A1
Connected drugs: bisphosphonates
Other related diseases: Ehlers-Danlos syndrome

Descriptions:
- TP53: Tumor suppressor protein.
- COL1A1: Collagen Type I Alpha 1 chain.
\`\`\`

**Why it’s useful:**  
Quickly shows how a single disease is embedded in the graph — revealing possible targets, pathways, or treatment options.

---

## 💊 3️⃣ Drug Query Example — *aspirin*

**Goal:**  
Find a specific drug (**aspirin**) and all directly related **diseases**, **genes**, or other drugs.

**What happens:**  
- Searches `drug_features.csv` for the drug name in:
  - `drug_name`
  - `drug_description`
- Extracts the drug `node_index`.
- Filters `kg.csv` to find edges linked to this drug.
  - Relations might include: *indication*, *drug_protein*, *drug_disease*, or *drug_drug*.
- Merges in extra data:
  - Disease names from `disease_features.csv`.
  - Gene/protein names from `nodes.csv` or `gene_features.csv`.
- Prints:
  - Drug details.
  - Related diseases with indications.
  - Associated genes/proteins.
  - Other drugs it might interact with.

**Output Example:**

\`\`\`plaintext
Drug match: aspirin
Node index: 5732

Indications:
- Myocardial infarction
- Stroke prevention

Associated genes: COX1, COX2

Related drugs: clopidogrel

Descriptions:
- COX1: Cyclooxygenase-1 enzyme.
- COX2: Cyclooxygenase-2 enzyme.
\`\`\`

**Why it’s useful:**  
Reveals how a drug interacts in the biomedical network — relevant for repurposing, safety checks, or target validation.

---

## 🧬 4️⃣ Gene/Protein Query Example — *BRCA1*

**Goal:**  
Find a specific gene or protein (**BRCA1**) and all directly connected diseases, drugs, and other genes.

**What happens:**  
- Searches `nodes.csv` or `gene_features.csv` for the gene name in:
  - `gene_name`
  - `gene_description`
- Extracts the gene’s `node_index`.
- Finds edges where this gene is source or target.
  - Common relations: *gene_disease*, *gene_protein*, *gene_drug*.
- Pulls related diseases and drugs:
  - Merges in disease or drug descriptions.
- Prints:
  - Gene details.
  - Associated diseases (e.g., breast cancer, ovarian cancer).
  - Related drugs (e.g., PARP inhibitors).
  - Other linked genes (e.g., TP53).

**Output Example:**

\`\`\`plaintext
Gene match: BRCA1
Node index: 7211

Associated diseases: Breast cancer, Ovarian cancer
Related drugs: olaparib, rucaparib
Other connected genes: BRCA2, TP53

Descriptions:
- olaparib: PARP inhibitor.
\`\`\`

**Why it’s useful:**  
Maps a gene’s known disease associations and possible therapeutic interventions — helpful for biomarker research, drug development, or pathway modeling.

---

## ⚠️ Handling Missing Results

If no match is found:  
- The script prints a clear message:
  \`\`\`plaintext
  No match found for 'XYZ'.
  \`\`\`
- Possible reasons:
  - The keyword does not exist in the dataset.
  - The name is listed under a synonym.
  - Spelling or casing mismatch.
- Suggested actions:
  - Try alternative terms.
  - Inspect the raw CSV for variants.
  - Expand search with regex or fuzzy matching.

---

## ✅ Final Output Summary

| Component | Description |
|-----------|--------------|
| File Check | Confirms files exist, readable, and contain expected columns. |
| Disease Query | Outputs matched disease node, related nodes, plus descriptions. |
| Drug Query | Shows drug node, linked diseases, genes, other drugs. |
| Gene Query | Reveals gene/protein node, related diseases, drugs, genes. |
| Format | All results printed in terminal/console; ready for further filtering or graph extraction. |

---

## 📊 Simple Metrics

| Metric         | Description                                      | Example/Result                           |
|----------------|--------------------------------------------------|------------------------------------------|
| Coverage       | Can find most common biomedical entities         | High for well-known diseases, drugs, genes |
| Precision      | Exact substring match in multiple description fields | Good, but can be expanded with fuzzy match |
| Extensibility  | Easy to expand with new entity types or relations | Yes — supports adding more relations     |
| Output         | Printed matches plus `node_index` for graph ops  | Ready for subgraph extraction            |
| Performance    | Fast — suitable for large CSVs in-memory         | Lightweight compared to full Neo4j DB    |

---

## 🧩 Next Steps

- **Use extracted node indices** to build subgraphs in `networkx`.
- **Visualize** results with `matplotlib`, `GraphML` → Cytoscape, Gephi, or Neo4j Bloom.
- **Chain queries:** e.g., start from a disease → genes → pathways → drugs → clinical trial hypotheses.

---

## 🔑 Key Takeaway

**PrimeKG Query** provides a **lightweight, reproducible template** for exploring biomedical knowledge graphs using simple Python and CSV workflows — no database deployment needed.

---
