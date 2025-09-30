# 📘 PrimeKG — Data Dictionary & Sample Heads

**PrimeKG** (Precision Medicine Knowledge Graph) is a rich, multimodal knowledge graph curated from **20 high-quality datasets**, including biorepositories and ontologies. It connects **17,080 diseases** to **4,050,249 relationships** across diverse biological entities such as drugs, genes, phenotypes, pathways, and more.

Disease nodes are densely connected to other node types, and both drug and disease entities come with clinical text descriptions. For an overview and hands-on tutorial, please visit our GitHub repository:
🔗 [https://github.com/mims-harvard/PrimeKG](https://github.com/mims-harvard/PrimeKG)

---

## 📂 File Overview

| **Filename**                       | **Description**                                           |
| ---------------------------------- | --------------------------------------------------------- |
| `nodes.csv`                        | Node metadata (index, name, type, source)                 |
| `edges.csv`                        | Undirected relationships between nodes                    |
| `kg.csv`                           | Main multi-relational knowledge graph                     |
| `disease_features.csv`             | Clinical text features and metadata for diseases          |
| `drug_features.csv`                | Clinical and pharmacological features for drugs           |
| `kg_raw.csv`                       | Raw intermediate graph with external IDs (pre-processed)  |
| `kg_giant.csv`                     | Largest connected component (LCC) of `kg_raw.csv`         |
| `kg_grouped.csv`                   | Disease-grouped version of the graph                      |
| `kg_grouped_diseases.csv`          | Disease nodes and their auto and BERT-derived group names |
| `kg_grouped_diseases_bert_map.csv` | BERT cluster mappings with shared group IDs               |

---

## 📁 `nodes.csv` — Node Metadata

### Column Definitions

| Column        | Description                                    |
| ------------- | ---------------------------------------------- |
| `node_index`  | Internal graph index                           |
| `node_id`     | External ID (e.g., NCBI Gene, MONDO, DrugBank) |
| `node_type`   | Entity type (`gene/protein`, `disease`, etc.)  |
| `node_name`   | Human-readable name                            |
| `node_source` | Origin database                                |

### Sample (First 5 Rows)

```text
node_index node_id     node_type     node_name node_source
0           0          9796          gene/protein PHYHIP     NCBI
1           1          7918          gene/protein GPANK1     NCBI
2           2          8233          gene/protein ZRSR2      NCBI
3           3          4899          gene/protein NRF1       NCBI
4           4          5297          gene/protein PI4KA      NCBI
```

---

## 🔗 `edges.csv` — Simplified Edge List

### Column Definitions

| Column             | Description          |
| ------------------ | -------------------- |
| `relation`         | Relation type        |
| `display_relation` | Abbreviated relation |
| `x_index`          | Source node index    |
| `y_index`          | Target node index    |

### Sample (First 5 Rows)

```text
relation         display_relation  x_index  y_index
protein_protein  ppi               0        8889
protein_protein  ppi               1        2798
protein_protein  ppi               2        5646
protein_protein  ppi               3        11592
protein_protein  ppi               4        2122
```

---

## 🧠 `kg.csv` — Core Knowledge Graph

### Column Definitions

| Column                 | Description                              |
| ---------------------- | ---------------------------------------- |
| `relation`             | Type of relation (e.g., drug\_disease)   |
| `display_relation`     | Short relation alias (e.g., ppi)         |
| `x_index`, `y_index`   | Node indices                             |
| `x_id`, `y_id`         | External node IDs                        |
| `x_type`, `y_type`     | Node types (e.g., gene/protein, disease) |
| `x_name`, `y_name`     | Node names                               |
| `x_source`, `y_source` | Source databases                         |

### Sample (First 5 Rows)

```text
relation         display_relation  x_index  x_id  x_type       x_name   x_source  y_index  y_id   y_type       y_name  y_source
protein_protein  ppi               0        9796  gene/protein PHYHIP   NCBI      8889     56992  gene/protein KIF15   NCBI
protein_protein  ppi               1        7918  gene/protein GPANK1   NCBI      2798     9240   gene/protein PNMA1   NCBI
protein_protein  ppi               2        8233  gene/protein ZRSR2    NCBI      5646     23548  gene/protein TTC33   NCBI
protein_protein  ppi               3        4899  gene/protein NRF1     NCBI      11592    11253  gene/protein MAN1B1  NCBI
protein_protein  ppi               4        5297  gene/protein PI4KA    NCBI      2122     8601   gene/protein RGS20   NCBI
```

---

## 🦠 `disease_features.csv` — Disease Metadata

### Column Definitions

| Column                | Description                                     |
| --------------------- | ----------------------------------------------- |
| `node_index`          | Link to node in `nodes.csv`                     |
| `mondo_id`            | MONDO disease ID                                |
| `mondo_name`          | Disease name                                    |
| `mondo_definition`    | Official MONDO definition                       |
| `umls_description`    | Description from UMLS                           |
| `orphanet_definition` | Rare disease definition from Orphanet           |
| `mayo_symptoms`, etc. | Clinical symptoms from Mayo Clinic (if present) |

### Sample (First 5 Rows)

```text
node_index mondo_name                                mondo_definition
27165      mullerian aplasia and hyperandrogenism   Deficiency of the glycoprotein WNT4...
27165      mullerian aplasia and hyperandrogenism   Deficiency of the glycoprotein WNT4...
27166      myelodysplasia, immunodeficiency...      <NA>
27168      bone dysplasia, lethal Holmgren type     Bone dysplasia lethal Holmgren type...
27169      predisposition to invasive fungal...     <NA>
```

---

## 💊 `drug_features.csv` — Drug Metadata

### Column Definitions

| Column                | Description                            |
| --------------------- | -------------------------------------- |
| `node_index`          | Link to `nodes.csv`                    |
| `description`         | Drug summary                           |
| `indication`          | Approved indication                    |
| `mechanism_of_action` | Pharmacological mechanism              |
| `pharmacodynamics`    | Drug effects on the body               |
| `category`, `atc_*`   | Drug classification (e.g., ATC system) |

### Sample (First 5 Rows)

```text
node_index description                        indication
14012      Copper is a transition metal...    Parenteral nutrition supplement
14013      Oxygen element...                  Oxygen therapy
14014      Flunisolide corticosteroid...      Maintenance treatment of asthma
14015      Alclometasone steroid...           Relief of inflammatory dermatoses
14016      Medrysone corticosteroid...        Treatment of allergic conjunctivitis
```

---

## 🧱 `kg_raw.csv`, `kg_giant.csv`, `kg_grouped.csv` — KG Variants

### Column Definitions

| Column                 | Description           |
| ---------------------- | --------------------- |
| `relation`             | Edge type             |
| `display_relation`     | Short alias           |
| `x_id`, `y_id`         | External IDs of nodes |
| `x_type`, `y_type`     | Node types            |
| `x_name`, `y_name`     | Node names            |
| `x_source`, `y_source` | Source databases      |

### Sample (First 5 Rows)

```text
relation         display_relation  x_id  x_type       x_name   x_source  y_id   y_type       y_name  y_source
protein_protein  ppi               9796  gene/protein PHYHIP   NCBI      56992 gene/protein  KIF15   NCBI
protein_protein  ppi               7918  gene/protein GPANK1   NCBI      9240  gene/protein  PNMA1   NCBI
protein_protein  ppi               8233  gene/protein ZRSR2    NCBI      23548 gene/protein  TTC33   NCBI
protein_protein  ppi               4899  gene/protein NRF1     NCBI      11253 gene/protein  MAN1B1  NCBI
protein_protein  ppi               5297  gene/protein PI4KA    NCBI      8601  gene/protein  RGS20   NCBI
```

---

## 🧬 `kg_grouped_diseases.csv` — Disease Group Mapping

### Column Definitions

| Column            | Description                 |
| ----------------- | --------------------------- |
| `node_id`         | Disease node ID             |
| `node_type`       | Always `disease`            |
| `node_name`       | Human-readable disease name |
| `group_name_auto` | Auto-generated group label  |
| `group_name_bert` | BERT-embedded group label   |

### Sample (First 5 Rows)

```text
node_id node_name                                 group_name_auto
13924   osteogenesis imperfecta type 13           osteogenesis imperfecta
11160   autosomal recessive nonsyndromic deafness autosomal recessive nonsyndromic deafness
8099    congenital stationary night blindness... congenital stationary night blindness...
```

---

## 🤖 `kg_grouped_diseases_bert_map.csv` — BERT Group Cluster IDs

### Column Definitions

| Column            | Description                                 |
| ----------------- | ------------------------------------------- |
| `node_id`         | Disease node ID                             |
| `node_type`       | Always `disease`                            |
| `node_name`       | Disease name                                |
| `group_name_auto` | Auto name-matched group label               |
| `group_name_bert` | BERT embedding-based label                  |
| `group_id_bert`   | Group ID — list of disease nodes in cluster |

### Sample (First 5 Rows)

```text
node_id node_name                        group_name_auto          group_name_bert           group_id_bert
13924   osteogenesis imperfecta type 13  osteogenesis imperfecta  osteogenesis imperfecta   13924_12592_...
12592   osteogenesis imperfecta type 11  osteogenesis imperfecta  osteogenesis imperfecta   13924_12592_...
```

---

🗓️ *Last updated: 2025‑06‑11*
