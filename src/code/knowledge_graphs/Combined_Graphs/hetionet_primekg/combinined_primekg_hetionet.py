# -*- coding: utf-8 -*-


import networkx as nx
import pickle


hetionet_path = "hetionet.graphml"

hetionet = nx.read_graphml(hetionet_path)


Primekg_path = "PrimeKG_&_Data/primekg_graph.pkl"
with open(Primekg_path, "rb") as f:
    primekg = pickle.load(f)

# =========================
# @hetionet: Graph Summary
# =========================


import networkx as nx
from collections import defaultdict

# === Summarize Node Types ===
node_type_map = {}
hetionet_node_types = defaultdict(int)

for node, data in hetionet.nodes(data=True):
    node_type = data.get("kind", "Unknown")
    node_type_map[node] = node_type
    hetionet_node_types[node_type] += 1

# === Summarize Metaedges + (src_type, relation, dst_type) triples ===
hetionet_edge_types = defaultdict(int)
edge_type_map = defaultdict(list)

for u, v, attr in hetionet.edges(data=True):
    rel = attr.get("relation", "Unknown")  # Use 'relation' or 'metaedge' depending on your file
    src_type = node_type_map.get(u, "Unknown")
    dst_type = node_type_map.get(v, "Unknown")

    hetionet_edge_types[rel] += 1
    edge_type_map[(src_type, rel, dst_type)].append((u, v))

# === Extract edge_type_keys ===
edge_type_keys = list(edge_type_map.keys())

# === Print Summary ===
print("✅ Hetionet Node Types:")
for k, v in sorted(hetionet_node_types.items()):
    print(f"  - {k}: {v} nodes")

print("\n✅ Hetionet Edge Types (relation codes):")
for k, v in sorted(hetionet_edge_types.items()):
    print(f"  - {k}: {v} edges")

print(f"\n✅ Total edge types (src_type, relation, dst_type): {len(edge_type_keys)}")
for etype, edges in sorted(edge_type_map.items()):
    print(f"  - {etype}: {len(edges)} edges")

# =========================
# @primekg: Graph Summary (Fixed node_type key)
# =========================

from collections import defaultdict

primekg_node_types = defaultdict(int)
node_type_map = {}

for node, data in primekg.nodes(data=True):
    node_type = data.get("node_type", "Unknown")  # ✅ fixed here
    node_type_map[node] = node_type
    primekg_node_types[node_type] += 1

# === Summarize Relation Types and Triples
relation_counts = defaultdict(int)
edge_type_map = defaultdict(list)

for u, v, data in primekg.edges(data=True):
    rel = data.get("relation", "Unknown")
    src_type = node_type_map.get(u, "Unknown")
    dst_type = node_type_map.get(v, "Unknown")

    relation_counts[rel] += 1
    edge_type_map[(src_type, rel, dst_type)].append((u, v))

edge_type_keys = list(edge_type_map.keys())

# === Print Final Summary
print("✅ PrimeKG Node Types:")
for k, v in sorted(primekg_node_types.items()):
    print(f"  - {k}: {v} nodes")

print("\n✅ PrimeKG Edge Types (relation names):")
for k, v in sorted(relation_counts.items(), key=lambda x: x[0]):
    print(f"  - {k}: {v} edges")

print(f"\n✅ Total edge types (src_type, relation, dst_type): {len(edge_type_keys)}")
for etype, edges in sorted(edge_type_map.items()):
    print(f"  - {etype}: {len(edges)} edges")

from collections import defaultdict

# === 1. Mapping from Hetionet's node kind → PrimeKG style ===
node_type_map_hetionet_to_primekg = {
    "Gene": "gene/protein",
    "Compound": "drug",
    "Side Effect": "effect/phenotype",
    "Symptom": "effect/phenotype",
    "Anatomy": "anatomy",
    "Disease": "disease",
    "Pathway": "pathway",
    "Molecular Function": "molecular_function",
    "Biological Process": "biological_process",
    "Cellular Component": "cellular_component",
    "Pharmacologic Class": "drug",  # best fit
}

# === 2. Mapping from relation codes (metaedge) to full names (if needed) ===
metaedge_fullnames = {
    "AdG": "anatomy_gene", "AeG": "anatomy_gene", "AuG": "anatomy_gene",
    "CbG": "drug_gene", "CdG": "drug_gene", "CuG": "drug_gene",
    "CpD": "drug_disease", "CtD": "drug_disease", "CrC": "drug_drug",
    "DaG": "disease_gene", "DdG": "disease_gene", "DuG": "disease_gene",
    "DrD": "disease_disease", "DpS": "disease_phenotype",
    "DlA": "disease_anatomy",
    "GiG": "protein_protein", "GcG": "gene_gene",
    "GpPW": "gene_pathway", "Gr>G": "gene_regulates_gene"
}

# === 3. Normalize Nodes ===
normalized_nodes = []
node_idx_map = {}  # {old_id: new_idx}
for idx, (node, data) in enumerate(hetionet.nodes(data=True)):
    old_type = data.get("kind", "Unknown")
    new_type = node_type_map_hetionet_to_primekg.get(old_type, old_type.lower())

    node_dict = {
        "node_index": idx,
        "node_id": node,
        "node_type": new_type,
        "node_name": data.get("name", node),
        "node_source": "hetionet"
    }
    normalized_nodes.append(node_dict)
    node_idx_map[node] = idx

# === 4. Normalize Edges ===
normalized_edges = []
for u, v, attr in hetionet.edges(data=True):
    rel_code = attr.get("relation", "Unknown")
    relation_name = metaedge_fullnames.get(rel_code, rel_code.lower())

    edge_dict = {
        "relation": relation_name,
        "display_relation": rel_code,
        "x_index": node_idx_map[u],
        "y_index": node_idx_map[v],
    }
    normalized_edges.append(edge_dict)

import pandas as pd

# Count node types in normalized version
normalized_node_df = pd.DataFrame(normalized_nodes)
node_type_counts = normalized_node_df["node_type"].value_counts()

print("✅ Normalized Hetionet Node Type Counts:")
print(node_type_counts)

# Count edge types in normalized version
normalized_edge_df = pd.DataFrame(normalized_edges)
edge_type_counts = normalized_edge_df["relation"].value_counts()

print("\n✅ Normalized Hetionet Edge Type Counts:")
print(edge_type_counts)

"""# === Hetionet Metaedge → PrimeKG Relation Mapping Explained ===
# | Hetionet Code | Biological Interpretation                              | Mapped Relation        |
# |---------------|--------------------------------------------------------|------------------------|
# | `AdG`         | Anatomy **expresses/associated with/upregulates** Gene | `anatomy_gene`         |
# | `AeG`         | Anatomy **associated with** Gene                       | `anatomy_gene`         |
# | `AuG`         | Anatomy **upregulates** Gene                           | `anatomy_gene`         |
# | `CbG`         | Compound (Drug) **binds** Gene                         | `drug_gene`            |
# | `CdG`         | Compound (Drug) **downregulates** Gene                | `drug_gene`            |
# | `CuG`         | Compound (Drug) **upregulates** Gene                  | `drug_gene`            |
# | `CpD`         | Compound (Drug) **causes** a Disease                  | `drug_disease`         |
# | `CtD`         | Compound (Drug) **treats** a Disease                  | `drug_disease`         |
# | `CrC`         | Compound **resembles** another Compound               | `drug_drug`            |
# | `DaG`         | Disease **associated with** Gene                      | `disease_gene`         |
# | `DdG`         | Disease **downregulates** Gene                        | `disease_gene`         |
# | `DuG`         | Disease **upregulates** Gene                          | `disease_gene`         |
# | `DrD`         | Disease **resembles** another Disease                 | `disease_disease`      |
# | `DpS`         | Disease **presents with** Symptom                     | `disease_phenotype`    |
# | `DlA`         | Disease **localizes to** Anatomy                      | `disease_anatomy`      |
# | `GiG`         | Gene ↔ Gene interaction (via **protein products**)    | ✅ `protein_protein`    |
# | `GcG`         | Gene **covaries** with Gene                           | `gene_gene`            |
# | `GpPW`        | Gene **participates in** Pathway                      | `gene_pathway`         |
# | `Gr>G`        | Gene **regulates** Gene                               | `gene_regulates_gene`  |
# | `metaedge`    | Invalid/unclassified/malformed relation               | `metaedge`             |
"""
print(" ")

#combining graphs


import networkx as nx

# 1. Clone the primekg graph to avoid overwriting
combined_graph = primekg.copy()

# 2. Get the max index in PrimeKG to offset Hetionet indices
max_index = max(int(n) for n in combined_graph.nodes)
offset = max_index + 1

# 3. Add Hetionet nodes to combined_graph with new indices
hetionet_new_id_map = {}  # {old_hetionet_id: new_combined_index}
for node in normalized_nodes:
    new_idx = str(node["node_index"] + offset)
    combined_graph.add_node(
        new_idx,
        node_id=node["node_id"],
        node_type=node["node_type"],
        node_name=node["node_name"],
        node_source="hetionet"
    )
    hetionet_new_id_map[node["node_index"]] = new_idx

# 4. Add Hetionet edges to combined_graph
for edge in normalized_edges:
    src = hetionet_new_id_map[edge["x_index"]]
    dst = hetionet_new_id_map[edge["y_index"]]
    combined_graph.add_edge(
        src, dst,
        relation=edge["relation"],
        display_relation=edge["display_relation"],
        source="hetionet"
    )

print(f"✅ Combined graph now has {combined_graph.number_of_nodes()} nodes and {combined_graph.number_of_edges()} edges.")

# --- Step 1: Count PrimeKG stats ---
primekg_node_count = primekg.number_of_nodes()
primekg_edge_count = primekg.number_of_edges()
print(f"🔹 PrimeKG: {primekg_node_count} nodes, {primekg_edge_count} edges")

# --- Step 2: Count normalized Hetionet stats ---
hetionet_node_count = len(normalized_nodes)
hetionet_edge_count = len(normalized_edges)
print(f"🔹 Normalized Hetionet: {hetionet_node_count} nodes, {hetionet_edge_count} edges")

# --- Step 3: Count combined graph stats ---
combined_node_count = combined_graph.number_of_nodes()
combined_edge_count = combined_graph.number_of_edges()
print(f"🔹 Combined Graph: {combined_node_count} nodes, {combined_edge_count} edges")

# --- Step 4: Validate ---
expected_nodes = primekg_node_count + hetionet_node_count
expected_edges = primekg_edge_count + hetionet_edge_count

print("\n✅ Validation:")
print(f"  - Expected nodes: {expected_nodes} | Match: {expected_nodes == combined_node_count}")
print(f"  - Expected edges: {expected_edges} | Match: {expected_edges == combined_edge_count}")

import pickle

# --- File Paths ---
pkl_path = "primekg_hetionet_combined.pkl"
graphml_path = "primekg_hetionet_combined.graphml"

# --- Save as Pickle ---
with open(pkl_path, "wb") as f:
    pickle.dump(combined_graph, f)
print(f"✅ Saved combined graph as Pickle at: {pkl_path}")

graphml_path = "primekg_hetionet_combined.graphml"

# --- Save as GraphML ---
nx.write_graphml(combined_graph, graphml_path)
print(f"✅ Saved combined graph as GraphML at: {graphml_path}")

import pickle
from collections import defaultdict

# --- Load the combined graph from Pickle ---
pkl_path = "primekg_hetionet_combined.pkl"
with open(pkl_path, "rb") as f:
    combined_graph = pickle.load(f)

# --- Basic Summary ---
print(f"✅ Total Nodes: {combined_graph.number_of_nodes()}")
print(f"✅ Total Edges: {combined_graph.number_of_edges()}")

# --- Node Type Breakdown ---
node_type_counts = defaultdict(int)
for _, data in combined_graph.nodes(data=True):
    node_type = data.get("node_type", "unknown")
    node_type_counts[node_type] += 1

print("\n📊 Node Type Counts:")
for node_type, count in sorted(node_type_counts.items()):
    print(f"  - {node_type}: {count} nodes")

# === Node Type Summary ===
combined_node_types = defaultdict(int)
node_type_map = {}

for node, data in combined_graph.nodes(data=True):
    node_type = data.get("node_type", "Unknown")
    node_type_map[node] = node_type
    combined_node_types[node_type] += 1

# === Edge Relation Summary and Triples ===
combined_relation_counts = defaultdict(int)
combined_edge_type_map = defaultdict(list)

for u, v, data in combined_graph.edges(data=True):
    rel = data.get("relation", "Unknown")
    src_type = node_type_map.get(u, "Unknown")
    dst_type = node_type_map.get(v, "Unknown")

    combined_relation_counts[rel] += 1
    combined_edge_type_map[(src_type, rel, dst_type)].append((u, v))

# === Print Summary ===
print("✅ Combined Graph Node Types:")
for node_type, count in sorted(combined_node_types.items()):
    print(f"  - {node_type}: {count} nodes")

print("\n✅ Combined Graph Edge Types (relation names):")
for rel, count in sorted(combined_relation_counts.items()):
    print(f"  - {rel}: {count} edges")

print(f"\n✅ Total edge types (src_type, relation, dst_type): {len(combined_edge_type_map)}")
for etype, edges in sorted(combined_edge_type_map.items()):
    print(f"  - {etype}: {len(edges)} edges")

from collections import defaultdict

# 1. Define the mapping to check
relation_remap = {
    "disease_protein": "disease_gene",
    "drug_protein": "drug_gene",
    "anatomy_protein_present": "anatomy_gene",
    "anatomy_protein_absent": "anatomy_gene",
    "pathway_protein": "gene_pathway",
    "molfunc_protein": "molecular_function_gene",
    "cellcomp_protein": "cellular_component_gene",
    "bioprocess_protein": "biological_process_gene",
    "phenotype_protein": "effect_protein",
}

# 2. Extract node type mapping from combined_graph
node_type_map = {
    node: data.get("node_type", "unknown")
    for node, data in combined_graph.nodes(data=True)
}

# 3. Collect edge metadata per relation
relation_edges = defaultdict(list)
for u, v, data in combined_graph.edges(data=True):
    rel = data.get("relation")
    src_type = node_type_map.get(u, "unknown")
    dst_type = node_type_map.get(v, "unknown")
    relation_edges[rel].append((src_type, dst_type))

# 4. Compare the type signatures before renaming
print("🔍 Checking consistency of relation remaps:\n")
for old_rel, new_rel in relation_remap.items():
    edges = relation_edges.get(old_rel, [])
    if not edges:
        print(f"⚠️  Relation '{old_rel}' not found in combined graph.")
        continue

    # Count src/dst types
    type_pairs = defaultdict(int)
    for src_type, dst_type in edges:
        type_pairs[(src_type, dst_type)] += 1

    print(f"🔸 Relation: '{old_rel}' → To be renamed as → '{new_rel}'")
    for (src, dst), count in type_pairs.items():
        print(f"    → ({src} → {dst}): {count} edges")
    print()

# Mapping semantically similar relations to PrimeKG standard
relation_merge_map = {
    "disease_gene": "disease_protein",
    "drug_gene": "drug_protein",
    "anatomy_gene": "anatomy_protein_present",  # All Hetionet anatomy_gene → protein_present
    "gene_pathway": "pathway_protein",
    "molecular_function_gene": "molfunc_protein",
    "cellular_component_gene": "cellcomp_protein",
    "biological_process_gene": "bioprocess_protein",
    "effect_protein": "phenotype_protein"
}

# Counters
from collections import Counter
merged_counter = Counter()

# Perform in-place update on combined graph
for u, v, data in combined_graph.edges(data=True):
    rel = data.get("relation", None)
    if rel in relation_merge_map:
        target_rel = relation_merge_map[rel]
        data["display_relation"] = rel  # keep original
        data["relation"] = target_rel
        merged_counter[rel] += 1

print("✅ Completed relation merging.")
print("🔍 Merged relation counts:")
for old_rel, count in merged_counter.items():
    print(f"  - {old_rel} → {relation_merge_map[old_rel]}: {count} edges")

from collections import defaultdict

# === 1. Initialize Counters ===
node_type_counts = defaultdict(int)
edge_relation_counts = defaultdict(int)

# === 2. Count Node Types ===
for _, data in combined_graph.nodes(data=True):
    node_type = data.get("node_type", "unknown")
    node_type_counts[node_type] += 1

# === 3. Count Edge Relations ===
for _, _, data in combined_graph.edges(data=True):
    relation = data.get("relation", "unknown")
    edge_relation_counts[relation] += 1

# === 4. Print Node Type Counts ===
print("✅ Combined Graph Node Types:")
for node_type, count in sorted(node_type_counts.items()):
    print(f"  - {node_type}: {count} nodes")

# === 5. Print Edge Relation Counts ===
print("\n✅ Combined Graph Edge Types (relation names):")
for relation, count in sorted(edge_relation_counts.items()):
    print(f"  - {relation}: {count} edges")

"""| Merged Relation           | Hetionet | PrimeKG   | Expected Combined | Combined Actual | ✅ Status                   |
| ------------------------- | -------- | --------- | ----------------- | --------------- | -------------------------- |
| anatomy\_protein\_present | 726,495  | 3,036,402 | 3,762,897         | 3,624,231       | ⚠ \~3.7% drop (acceptable) |
| disease\_protein          | 27,977   | 160,820   | 188,797           | 188,520         | ✅ \~close                  |
| drug\_protein             | 51,429   | 50,928    | 102,357           | 102,292         | ✅ \~close                  |
| pathway\_protein          | 84,372   | 85,292    | 169,664           | 169,664         | ✅ Exact                    |
| molfunc\_protein          | —        | 139,060   | 139,060           | 139,060         | ✅ Exact                    |
| cellcomp\_protein         | —        | 166,804   | 166,804           | 166,804         | ✅ Exact                    |
| bioprocess\_protein       | —        | 289,610   | 289,610           | 289,610         | ✅ Exact                    |
| phenotype\_protein        | —        | 6,660     | 6,660             | 6,660           | ✅ Exact                    |
| protein\_protein          | 147,164  | 642,116   | 789,280           | 788,421         | ✅ \~close                  |
| drug\_drug                | 6,486    | 2,671,334 | 2,677,820         | 2,677,820       | ✅ Exact                    |
| disease\_disease          | 543      | 64,386    | 64,929            | 64,929          | ✅ Exact                    |
"""
print("")

import pickle
import networkx as nx

# --- File Paths ---
pkl_path = "primekg_hetionet_combined.pkl"

"primekg_hetionet_combined.graphml"
# --- Load from Pickle ---
with open(pkl_path, "rb") as f:
    combined_graph = pickle.load(f)
print("✅ Loaded graph from Pickle.")
print(f"📦 Pickle Graph - Nodes: {combined_graph.number_of_nodes()}, Edges: {combined_graph.number_of_edges()}")

