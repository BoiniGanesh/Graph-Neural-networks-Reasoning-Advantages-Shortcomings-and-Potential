
---

# 5.2.2 R-GCN on OpenFDA

This section documents the R-GCN implementation on the OpenFDA knowledge graph within **GRASP: Where Do Graphs Shine?**.  
The same relational GCN framework was applied to OpenFDA, following the standardized workflow used for Hetionet and PrimeKG.

---

## Overview

The OpenFDA dataset introduces a distinct challenge for graph reasoning. Unlike Hetionet or PrimeKG, which focus on molecular and biological relations, OpenFDA contains **regulatory and textual relations** extracted from FDA drug labeling.  
These include **warnings**, **dosage**, **contraindications**, and **interactions**, which exhibit weaker graph connectivity and less consistent structure.

R-GCN was trained and evaluated on 287 relation types from OpenFDA, with performance summarized in Table 22 of the paper.  
The overall AUC (0.5690) and F1 (0.382) indicate reduced predictive strength compared to other biomedical graphs.  
Certain relation types, such as *brand–warnings* and *drug–drug_interactions*, achieved higher accuracy, but most relations approached random baselines.

---

## OpenFDA Graph Construction Workflow

The OpenFDA knowledge graph was constructed using an automated multi-stage pipeline from raw API data to a structured KG format.

**Figure: OpenFDA Knowledge Graph Construction Pipeline**  
*(openfda_pipeline.pdf)*  
![OpenFDA Knowledge Graph Construction Pipeline](OpenFDA_Construction_pipeline_horizontal.pdf)

**Workflow Summary:**
1. **Connect to OpenFDA API** — Retrieve raw drug data including labeling, warnings, dosage, and adverse events.  
2. **Preprocess with LLaMA3 (Ollama Framework)** — Normalize text into consistent JSON schema using few-shot prompt engineering.  
3. **Clean and Structure JSON** — Remove duplicates, standardize terminology, and ensure valid formatting.  
4. **Batch Process and Chunk Outputs** — Prepare batches of normalized data for graph ingestion.  
5. **Construct Knowledge Graph** — Represent drugs, labels, and warnings as typed nodes and edges.  
6. **Applications** — Enable downstream tasks such as link prediction, drug safety, and pharmacovigilance.

This pipeline corresponds to **Figure 3 in the paper**, visualizing how text-based FDA records are transformed into structured graph data.

---

## Example OpenFDA Subgraph and Schema

The OpenFDA KG captures fine-grained relationships from drug labeling sections.

**Figure: Example OpenFDA Subgraph (Cobalt Node)**  
*(openfda_subgraph.pdf)*  
![Example OpenFDA Subgraph](openfda_subgraph.pdf)

**Figure: Internal Structure of the OpenFDA Graph**  
*(openfda_structure.pdf)*  
![Internal Structure of the OpenFDA Graph](openfda_internal.pdf)

Figure 4 illustrates a representative subgraph for a specific compound, showing linked nodes such as active ingredients, dosage information, and warnings.  
Figure 5 expands this to a schema-level view, mapping entity classes (drugs, labeling sections, adverse events) and their semantic relationships.

---

## R-GCN Implementation on OpenFDA

R-GCN was used to model the relational structure of OpenFDA’s knowledge graph.  
The same core architecture and training pipeline used for Hetionet and PrimeKG were applied here, ensuring comparability across datasets.


**Implementation Steps:**
- Load and normalize OpenFDA graph (nodes, relations, types).
- Build per-type mappings and edge-type relations.
= Split each relation’s edges into train/val/test sets.
- Generate type-consistent negative samples.
- Train a 2-layer R-GCN encoder with relation-specific transformations.
- Use DistMult (or dot-product) decoder with binary cross-entropy loss.
- Evaluate per relation and overall using AUC, precision, recall, F1.

Despite the consistent workflow, R-GCN performance decreased significantly on OpenFDA.  
The model’s lower AUC (0.5690) and F1 (0.382) highlight the difficulty of reasoning over regulatory, text-derived relationships.  
While structured relations such as *drug–drug_interaction* or *brand–warning* achieved moderate performance, most relations lacked meaningful graph signals for predictive learning.

---

## Summary

The OpenFDA experiments reveal that R-GCN’s strength lies in **structural and relational graphs**, while **regulatory-text graphs** like OpenFDA provide weaker signals for graph-based reasoning.  
This demonstrates that performance is contingent on graph composition — semantic graphs with consistent relations (e.g., Hetionet, PrimeKG) outperform regulatory graphs with high textual heterogeneity.

---

