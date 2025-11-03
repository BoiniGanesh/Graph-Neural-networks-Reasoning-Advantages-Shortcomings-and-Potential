# -*- coding: utf-8 -*-
import pandas as pd
import os

# Define your local directory path
data_dir = "dataverse_files"

# List of all important CSV files
file_names = [
    "nodes.csv",
    "edges.csv",
    "kg.csv",
    "disease_features.csv",
    "drug_features.csv",
    "kg_raw.csv",
    "kg_giant.csv",
    "kg_grouped.csv",
    "kg_grouped_diseases.csv",
    "kg_grouped_diseases_bert_map.csv"
]

# Read and print head of each file
for file in file_names:
    path = os.path.join(data_dir, file)
    try:
        df = pd.read_csv(path)
        print(f"\n=== {file} ===")
        print(df.head())
    except Exception as e:
        print(f"Failed to read {file}: {e}")

import pandas as pd
import os

# Define your local directory path
data_dir = "dataverse_files"

# List of all important CSV files
file_names = [
    "kg.csv"
]

# Read and print head of each file
for file in file_names:
    path = os.path.join(data_dir, file)
    df = pd.DataFrame(pd.read_csv(path))
    print(f"\n=== {file} ===")
    print(df.head(20))

sf=df['relation']
sf.unique()

import pandas as pd


# Set your actual data path
base_path = "dataverse_files"

# Load kg.csv
kg_df = pd.read_csv(base_path + "kg.csv", low_memory=False)

# Load feature files
disease_df = pd.read_csv(base_path + "disease_features.csv", low_memory=False)
drug_df = pd.read_csv(base_path + "drug_features.csv", low_memory=False)

# Prepare disease descriptions
disease_desc = disease_df[['node_index', 'mondo_name', 'mondo_definition', 'umls_description',
                           'orphanet_definition', 'orphanet_clinical_description',
                           'mayo_symptoms', 'mayo_causes', 'mayo_complications']].drop_duplicates()
disease_desc['node_type'] = 'disease'

# Prepare drug descriptions
drug_desc = drug_df[['node_index', 'description', 'indication', 'mechanism_of_action',
                     'protein_binding', 'pharmacodynamics']].drop_duplicates()
drug_desc['node_type'] = 'drug'

# Prepare unique node list from kg.csv
kg_nodes_x = kg_df[['x_index', 'x_name', 'x_type']].rename(columns={
    'x_index': 'node_index',
    'x_name': 'node_name',
    'x_type': 'node_type'
})
kg_nodes_y = kg_df[['y_index', 'y_name', 'y_type']].rename(columns={
    'y_index': 'node_index',
    'y_name': 'node_name',
    'y_type': 'node_type'
})
all_nodes = pd.concat([kg_nodes_x, kg_nodes_y]).drop_duplicates('node_index')

# Merge all descriptions
desc_combined = pd.concat([disease_desc, drug_desc], axis=0, ignore_index=True)

# Merge descriptions with node list
enriched_nodes = pd.merge(all_nodes, desc_combined, on=['node_index', 'node_type'], how='left')

# Fill NaNs with empty strings for agent usage
enriched_nodes.fillna('', inplace=True)

# Optionally, create a "summary" field for agent consumption
def summarize_row(row):
    if row['node_type'] == 'disease':
        return f"Disease: {row['node_name']}. Description: {row['mondo_definition'] or row['umls_description'] or row['orphanet_definition']}"
    elif row['node_type'] == 'drug':
        return f"Drug: {row['node_name']}. Use: {row['indication']}. Mechanism: {row['mechanism_of_action']}"
    else:
        return f"{row['node_type'].capitalize()}: {row['node_name']}."

enriched_nodes['node_summary'] = enriched_nodes.apply(summarize_row, axis=1)


# Save to writable local path
enriched_nodes.to_csv("kg_nodes_enriched.csv", index=False)

import pandas as pd

# Load the KG file
kg_path = "kg_nodes_enriched.csv"
kg_df = pd.read_csv(kg_path)
kg_df.head()

import pandas as pd

# Load the KG file
kg_path = "dataverse_files/kg.csv"
kg_df = pd.read_csv(kg_path)

# Get unique relation types
relations = kg_df['relation'].unique()

# Collect 5 rows per relation
samples = []
for rel in relations:
    sample_rows = kg_df[kg_df['relation'] == rel].head(5)
    sample_rows['relation_type'] = rel  # tag each row
    samples.append(sample_rows)

# Combine and display
result_df = pd.concat(samples)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
print(result_df)


kg_path = "dataverse_files/kg.csv"
kg_df = pd.read_csv(kg_path)

unique_values_per_column = {col: kg_df[col].dropna().unique().tolist() for col in kg_df.columns}
unique_values_per_column

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os

# File path
data_dir = "dataverse_files"

# Load all necessary CSV files
nodes = pd.read_csv(os.path.join(data_dir, "nodes.csv"))
edges = pd.read_csv(os.path.join(data_dir, "kg.csv"))
disease_feat = pd.read_csv(os.path.join(data_dir, "disease_features.csv"))
drug_feat = pd.read_csv(os.path.join(data_dir, "drug_features.csv"))
grouped = pd.read_csv(os.path.join(data_dir, "kg_grouped_diseases.csv"))
bert_grouped = pd.read_csv(os.path.join(data_dir, "kg_grouped_diseases_bert_map.csv"))

# Initialize Graph
G = nx.Graph()

# Add nodes
for _, row in nodes.iterrows():
    G.add_node(row['node_index'], label=row['node_name'], type=row['node_type'], source=row['node_source'])

# Add disease features
for _, row in disease_feat.iterrows():
    if row['node_index'] in G.nodes:
        G.nodes[row['node_index']].update({
            'mondo_def': row.get('mondo_definition', ''),
            'umls_desc': row.get('umls_description', ''),
            'group_bert': row.get('group_name_bert', '')
        })

# Add drug features
for _, row in drug_feat.iterrows():
    if row['node_index'] in G.nodes:
        G.nodes[row['node_index']].update({
            'drug_description': row.get('description', ''),
            'indication': row.get('indication', ''),
            'mechanism': row.get('mechanism_of_action', '')
        })

# Add grouped diseases (auto)
for _, row in grouped.iterrows():
    node_id = row['node_id']
    if node_id in G.nodes:
        G.nodes[node_id]['group_auto'] = row.get('group_name_auto', '')

# Add grouped diseases (bert)
for _, row in bert_grouped.iterrows():
    node_id = row['node_id']
    if node_id in G.nodes:
        G.nodes[node_id]['group_bert_id'] = row.get('group_id_bert', '')

# Add edges with relation label
for _, row in edges.iterrows():
    G.add_edge(row['x_index'], row['y_index'], relation=row['relation'])

# Select a sample subgraph
largest_cc = max(nx.connected_components(G), key=len)
sample_nodes = list(largest_cc)[:50]
subgraph = G.subgraph(sample_nodes)

# Color by type
color_map = []
for _, attr in subgraph.nodes(data=True):
    ntype = attr.get('type', '')
    if 'disease' in ntype:
        color_map.append('red')
    elif 'drug' in ntype:
        color_map.append('blue')
    elif 'gene' in ntype or 'protein' in ntype:
        color_map.append('green')
    else:
        color_map.append('gray')

# Plot
plt.figure(figsize=(18, 14))
pos = nx.spring_layout(subgraph, seed=42)
nx.draw_networkx_nodes(subgraph, pos, node_color=color_map, node_size=500, alpha=0.8)
nx.draw_networkx_labels(subgraph, pos, labels=nx.get_node_attributes(subgraph, 'label'), font_size=8)
nx.draw_networkx_edges(subgraph, pos, edge_color='gray')
edge_labels = nx.get_edge_attributes(subgraph, 'relation')
nx.draw_networkx_edge_labels(subgraph, pos, edge_labels=edge_labels, font_size=7)

plt.title("Fully Enriched PrimeKG Knowledge Graph Subgraph (Using All Files)", fontsize=16)
plt.axis('off')
plt.show()

import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os

# Load data
data_dir = "dataverse_files"
nodes_df = pd.read_csv(os.path.join(data_dir, "nodes.csv"))
kg_df = pd.read_csv(os.path.join(data_dir, "kg.csv"))

# Build graph
G = nx.Graph()
for _, row in nodes_df.iterrows():
    G.add_node(row['node_index'], label=row['node_name'], type=row['node_type'])

for _, row in kg_df.iterrows():
    G.add_edge(row['x_index'], row['y_index'], relation=row['relation'])

# Sample a meaningful connected subgraph
largest_cc = max(nx.connected_components(G), key=len)
subgraph_nodes = list(largest_cc)[:50]
subgraph = G.subgraph(subgraph_nodes)

# Color by node type
color_map = []
for node in subgraph.nodes(data=True):
    ntype = node[1].get('type', '')
    if 'disease' in ntype:
        color_map.append('red')
    elif 'drug' in ntype:
        color_map.append('blue')
    elif 'gene' in ntype or 'protein' in ntype:
        color_map.append('green')
    else:
        color_map.append('gray')

# Draw
plt.figure(figsize=(18, 14))
pos = nx.spring_layout(subgraph, seed=42)
nx.draw(subgraph, pos, node_color=color_map, with_labels=True,
        labels=nx.get_node_attributes(subgraph, 'label'),
        node_size=400, font_size=7, edge_color='gray', alpha=0.8)
plt.title("Labeled PrimeKG Subgraph with Node Types", fontsize=16)
plt.show()

# Commented out IPython magic to ensure Python compatibility.
#──────────────────────────────────────────────#
# 1.  PREP — upgrade pip & wheel (always helps)
#──────────────────────────────────────────────#
!pip install -qU pip wheel setuptools


#──────────────────────────────────────────────#
# 2.  CLONE + INSTALL ToolUniverse
#──────────────────────────────────────────────#
!git clone -q https://github.com/mims-harvard/ToolUniverse.git
# %cd ToolUniverse

# -→ regular install (works because repo uses pyproject.toml + hatch)
!pip install -q .

#  (If you ever need editable mode: `pip install --no-build-isolation -e .`)


#──────────────────────────────────────────────#
# 3.  QUICK SANITY CHECK
#──────────────────────────────────────────────#
python_code = r"""
from tooluniverse import ToolUniverse

# create the engine
engine = ToolUniverse()
#   → load ONLY the categories you need.  Here we load them all.
engine.load_tools()     # or tool_type=['opentarget', 'monarch', 'fda_drug_label']

print(f"\nLoaded {len(engine.return_all_loaded_tools())} tools.")

# Look at the first 5 tool names with descriptions
for t in engine.return_all_loaded_tools()[:5]:
    print(f"‣ {t['name']} – {t['description'][:60]}…")

# Inspect one tool's JSON schema (parameters etc.)
example = engine.get_one_tool_by_one_name('FDA_get_dosage_info_by_drug_name',
                                          return_prompt=True)
print("\nSchema for one FDA tool:\n", example)

# Actually call it – ask for dosage info of Ibuprofen
query = {
    "name": "FDA_get_dosage_info_by_drug_name",
    "arguments": {"drug_name": "ibuprofen", "limit": 1, "skip": 0}
}
result = engine.run_one_function(query)
print("\nAPI response snippet:\n", result['results'][:1])
"""
print(python_code)  # so you can read it

from tooluniverse import ToolUniverse

engine = ToolUniverse()
engine.load_tools(tool_type=['fda_drug_label'])   # just the FDA bundle

# show every tool name that mentions "dosage"
[d for d in engine.all_tool_dict if 'dosage' in d.lower()]

tool_name = 'FDA_get_drug_names_by_dosage_forms_and_strengths_info'
schema = engine.get_one_tool_by_one_name(tool_name, return_prompt=True)
print(schema)

query = {
    "name": tool_name,
    "arguments": {"drug_name": "ibuprofen", "limit": 1, "skip": 0}
}

result = engine.run_one_function(query)

# guard in case the API returns None / error
if isinstance(result, dict) and 'results' in result:
    print(result['results'][:1])           # first item only
else:
    print("API call failed:", result)

tool_name = 'FDA_get_drug_names_by_dosage_forms_and_strengths_info'
schema = engine.get_one_tool_by_one_name(tool_name, return_prompt=True)
print(schema)

query = {
    "name": tool_name,
    "arguments": {
        "dosage_forms_and_strengths": "oral tablet 200mg",
        "limit": 1,
        "skip": 0
    }
}

result = engine.run_one_function(query)

if isinstance(result, dict) and 'results' in result:
    print(result['results'][:1])  # show only the first item
else:
    print("API call failed:", result)

engine.get_one_tool_by_one_name(tool_name, return_prompt=True)

from tooluniverse import ToolUniverse
import json

# Initialize and load all tools
engine = ToolUniverse()
engine.load_tools()

# Collect all loaded tools
tools = engine.return_all_loaded_tools()

# Group by type
grouped_tools = {}
for tool in tools:
    tool_type = tool.get("tool_type", "unknown")
    if tool_type not in grouped_tools:
        grouped_tools[tool_type] = []
    grouped_tools[tool_type].append({
        "name": tool["name"],
        "description": tool["description"],
        "source": tool.get("source", "N/A")
    })

# Print summary and preview tools in each group
for group, tool_list in grouped_tools.items():
    print(f"\n🧰 Tool Category: {group} ({len(tool_list)} tools)\n{'-'*50}")
    for tool in tool_list[:3]:  # Show first 3 tools per category
        print(f"🔹 Name: {tool['name']}")
        print(f"   Description: {tool['description']}")
        print(f"   Source: {tool['source']}\n")

# Sample mock functions to simulate the ToolUniverse tools
# Replace these with actual imports if using the real framework

def FDA_search_labels_by_keyword(keyword: str):
    return {"query": keyword, "result": f"Simulated search result for keyword '{keyword}'"}

def get_ingredients_by_drug_name(drug_name: str):
    return {"drug_name": drug_name, "ingredients": ["Pseudoephedrine", "Acetaminophen", "Guaifenesin"]}

def get_adverse_events_by_drug_name(drug_name: str):
    return {"drug_name": drug_name, "adverse_events": ["Drowsiness", "Dry mouth", "Nausea"]}

def FDA_get_brand_names_for_active_ingredient(active_ingredient: str):
    return {"active_ingredient": active_ingredient, "brands": ["Sudafed", "Zyrtec-D", "Advil Cold & Sinus"]}

def get_pregnancy_information_by_drug(drug_name: str):
    return {"drug_name": drug_name, "pregnancy_info": "Use with caution during pregnancy."}


# List of queries for each tool
test_queries = {
    "FDA_search_labels_by_keyword": ["cold", "nasal congestion", "runny nose", "flu"],
    "get_ingredients_by_drug_name": ["Vicks", "Nyquil", "Dolo Cold", "Zicam"],
    "get_adverse_events_by_drug_name": ["Nyquil", "Mucinex", "Zyrtec-D", "Advil Cold & Sinus"],
    "FDA_get_brand_names_for_active_ingredient": ["pseudoephedrine", "acetaminophen", "phenylephrine", "chlorpheniramine"],
    "get_pregnancy_information_by_drug": ["Nyquil", "Benadryl", "Sudafed", "Theraflu"]
}


# Tool mapping
tool_functions = {
    "FDA_search_labels_by_keyword": FDA_search_labels_by_keyword,
    "get_ingredients_by_drug_name": get_ingredients_by_drug_name,
    "get_adverse_events_by_drug_name": get_adverse_events_by_drug_name,
    "FDA_get_brand_names_for_active_ingredient": FDA_get_brand_names_for_active_ingredient,
    "get_pregnancy_information_by_drug": get_pregnancy_information_by_drug
}


# Run tests and collect results
results = {}

for tool_name, queries in test_queries.items():
    results[tool_name] = []
    for query in queries:
        try:
            response = tool_functions[tool_name](query)
            results[tool_name].append({"input": query, "response": response})
        except Exception as e:
            results[tool_name].append({"input": query, "error": str(e)})

# Display results
import pprint
pprint.pprint(results)

# -------------------------------
# MOCK FUNCTIONS for Testing
# Replace these with actual tool functions if available
# -------------------------------

def get_HPO_ID_by_phenotype(phenotype): return {"phenotype": phenotype, "HPO_ID": "HP:XXXX"}
def get_disease_phenotype_overlap(d1, d2): return {"disease1": d1, "disease2": d2, "shared_phenotypes": ["HP:0000001", "HP:0000002"]}
def get_gene_phenotypes(gene): return {"gene": gene, "phenotypes": ["HP:0000001", "HP:0000003"]}

def get_drug_targets(drug): return {"drug": drug, "targets": ["GeneA", "GeneB"]}
def get_gene_drug_interactions(gene): return {"gene": gene, "interacting_drugs": ["DrugX", "DrugY"]}
def get_disease_pathways(disease): return {"disease": disease, "pathways": ["PathwayA", "PathwayB"]}

def get_drug_gene_interactions_by_drug_name(drug): return {"drug": drug, "genes": ["Gene1", "Gene2"]}
def get_pathway_nodes_by_disease_name(disease): return {"disease": disease, "nodes": ["Node1", "Node2"]}
def get_gene_ontology_terms(gene): return {"gene": gene, "GO_terms": ["GO:0008150", "GO:0003674"]}

# -------------------------------
# QUERY EXECUTION
# -------------------------------

# Monarch Tools
monarch_queries = {
    "get_HPO_ID_by_phenotype": ["chronic cough", "muscle weakness", "hearing loss"],
    "get_disease_phenotype_overlap": [("Asthma", "COPD"), ("Autism", "Epilepsy"), ("Diabetes", "Hypertension")],
    "get_gene_phenotypes": ["CFTR", "TP53", "BRCA1"]
}

# Open Targets Tools
open_targets_queries = {
    "get_drug_targets": ["Metformin", "Ibuprofen", "Loratadine"],
    "get_gene_drug_interactions": ["EGFR", "BRAF", "TNF"],
    "get_disease_pathways": ["Parkinson's disease", "Lung cancer", "Crohn's disease"]
}

# openFDA KG Tools
openfda_kg_queries = {
    "get_drug_gene_interactions_by_drug_name": ["Warfarin", "Clopidogrel", "Tamoxifen"],
    "get_pathway_nodes_by_disease_name": ["Alzheimer's disease", "Type 2 diabetes", "Colorectal cancer"],
    "get_gene_ontology_terms": ["FOXP2", "MYH7", "APP"]
}

# -------------------------------
# RUN AND COLLECT RESULTS
# -------------------------------

import pprint

def run_queries(tool_name, tool_fn, queries):
    results = []
    for query in queries:
        if isinstance(query, tuple):
            result = tool_fn(*query)
        else:
            result = tool_fn(query)
        results.append({"input": query, "output": result})
    return {tool_name: results}

final_results = {}

# Monarch
final_results.update(run_queries("get_HPO_ID_by_phenotype", get_HPO_ID_by_phenotype, monarch_queries["get_HPO_ID_by_phenotype"]))
final_results.update(run_queries("get_disease_phenotype_overlap", get_disease_phenotype_overlap, monarch_queries["get_disease_phenotype_overlap"]))
final_results.update(run_queries("get_gene_phenotypes", get_gene_phenotypes, monarch_queries["get_gene_phenotypes"]))

# Open Targets
final_results.update(run_queries("get_drug_targets", get_drug_targets, open_targets_queries["get_drug_targets"]))
final_results.update(run_queries("get_gene_drug_interactions", get_gene_drug_interactions, open_targets_queries["get_gene_drug_interactions"]))
final_results.update(run_queries("get_disease_pathways", get_disease_pathways, open_targets_queries["get_disease_pathways"]))

# openFDA KG Tools
final_results.update(run_queries("get_drug_gene_interactions_by_drug_name", get_drug_gene_interactions_by_drug_name, openfda_kg_queries["get_drug_gene_interactions_by_drug_name"]))
final_results.update(run_queries("get_pathway_nodes_by_disease_name", get_pathway_nodes_by_disease_name, openfda_kg_queries["get_pathway_nodes_by_disease_name"]))
final_results.update(run_queries("get_gene_ontology_terms", get_gene_ontology_terms, openfda_kg_queries["get_gene_ontology_terms"]))

# -------------------------------
# DISPLAY
# -------------------------------
pprint.pprint(final_results)

!pip install torch transformers requests

!pip install tooluniverse

!pip install bitsandbytes accelerate

from huggingface_hub import login
login("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")

from tooluniverse.execute_function import ToolUniverse
import json
import os

# Initialize and load tools
tooluni = ToolUniverse()
tooluni.load_tools()

# Set paths to known tool definition files
base_path = "/usr/local/lib/python3.11/dist-packages/tooluniverse/data"
tool_files = {
    "opentarget": os.path.join(base_path, "opentarget_tools.json"),
    "fda_drug_label": os.path.join(base_path, "fda_drug_labeling_tools.json"),
    "special_tools": os.path.join(base_path, "special_tools.json"),
    "monarch": os.path.join(base_path, "monarch_tools.json"),
}

# Print file locations
print("\U0001F4C1 Tool files:")
print(json.dumps(tool_files, indent=2))

# Count and print tools in each category
print("\n\U0001F4CA Tool counts by category:")
for group, path in tool_files.items():
    try:
        with open(path, "r") as f:
            tools = json.load(f)
            print(f"- {group}: {len(tools)} tools")
    except FileNotFoundError:
        print(f"- {group}: ❌ File not found")

# Print all tool names and descriptions
tools, descriptions = tooluni.refresh_tool_name_desc()
print(f"\n\U0001F9E0 Total tools loaded into ToolUniverse: {len(tools)}")
print("\n=== All Available Tools ===")
for name, desc in zip(tools, descriptions):
    print(f"{name}\n  \u27A4 {desc}\n")

# test_tool_OpenTargets_get_diseases_phenotypes_by_target_ensembl.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_diseases_phenotypes_by_target_ensembl"

    # Corrected argument name: 'ensemblId'
    # Example argument: Ensembl ID for 'TP53' gene (ENSG00000141510)
    arguments = {
        "ensemblId": "ENSG00000141510"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_target_disease_evidence.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_target_disease_evidence"

    # Corrected argument names: 'efoId' and 'ensemblId'
    # This tool requires both disease EFO ID and target Ensembl ID.
    # Example: Disease 'diabetes mellitus' (EFO_0000540) and Target 'TP53' (ENSG00000141510)
    arguments = {
        "efoId": "EFO_0000540",
        "ensemblId": "ENSG00000141510"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_drug_warnings_by_chemblId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_drug_warnings_by_chemblId"

    # Corrected argument name: 'chemblId'
    # Example argument: ChEMBL ID for 'Ibuprofen' (CHEMBL112)
    arguments = {
        "chemblId": "CHEMBL112"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_drug_mechanisms_of_action_by_chemblId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_drug_mechanisms_of_action_by_chemblId"

    # Corrected argument name: 'chemblId'
    # Example argument: ChEMBL ID for 'Ibuprofen' (CHEMBL112)
    arguments = {
        "chemblId": "CHEMBL112"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_associated_drugs_by_disease_efoId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_associated_drugs_by_disease_efoId"

    # Corrected arguments: 'efoId' and added 'size'
    # Example argument: EFO ID for 'diabetes mellitus' (EFO_0000540)
    arguments = {
        "efoId": "EFO_0000540",
        "size": 10 # Added required 'size' parameter with a default value
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_similar_entities_by_disease_efoId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_similar_entities_by_disease_efoId"

    # Corrected arguments: 'efoId' and added 'threshold', 'size'
    # Example argument: EFO ID for 'diabetes mellitus' (EFO_0000540)
    arguments = {
        "efoId": "EFO_0000540",
        "threshold": 0.5, # Added required 'threshold' parameter
        "size": 10      # Added required 'size' parameter
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_similar_entities_by_drug_chemblId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_similar_entities_by_drug_chemblId"

    # Corrected arguments: 'chemblId' and added 'threshold', 'size'
    # Example argument: ChEMBL ID for 'Ibuprofen' (CHEMBL112)
    arguments = {
        "chemblId": "CHEMBL112",
        "threshold": 0.5, # Added required 'threshold' parameter
        "size": 10      # Added required 'size' parameter
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_similar_entities_by_target_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_similar_entities_by_target_ensemblID"

    # Corrected arguments: 'ensemblId' and added 'threshold', 'size'
    # Example argument: Ensembl ID for 'TP53' gene (ENSG00000141510)
    arguments = {
        "ensemblId": "ENSG00000141510",
        "threshold": 0.5, # Added required 'threshold' parameter
        "size": 10      # Added required 'size' parameter
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_associated_phenotypes_by_disease_efoId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_associated_phenotypes_by_disease_efoId"

    # Corrected argument name: 'efoId'
    # Example argument: EFO ID for 'diabetes mellitus' (EFO_0000540)
    arguments = {
        "efoId": "EFO_0000540"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()







# Cell 1: tool_universe.py
import json
import os

class ToolUniverse:
    def __init__(self):
        self.tool_files = {
            'opentarget': '/usr/local/lib/python3.11/dist-packages/tooluniverse/data/opentarget_tools.json',
            'fda_drug_label': '/usr/local/lib/python3.11/dist-packages/tooluniverse/data/fda_drug_labeling_tools.json',
            'special_tools': '/usr/local/lib/python3.11/dist-packages/tooluniverse/data/special_tools.json',
            'monarch': '/usr/local/lib/python3.11/dist-packages/tooluniverse/data/monarch_tools.json'
        }
        self.tools = []

    def load_tools(self):
        print("\n📁 Tool files:")
        print(json.dumps(self.tool_files, indent=2))

        for name, path in self.tool_files.items():
            try:
                with open(path, 'r') as f:
                    tool_list = json.load(f)
                    self.tools.extend(tool_list)
                    print(f"- Loaded {len(tool_list)} tools from {name}")
            except Exception as e:
                print(f"Failed to load {name}: {e}")

        print(f"\n🧠 Total tools loaded into ToolUniverse: {len(self.tools)}")

    def get_tool_names(self):
        return [t['name'] for t in self.tools] if self.tools else []

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
        import requests
        BASE_URL = "https://api.fda.gov"
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

import os
import json
import importlib
from types import SimpleNamespace


def load_tools_from_json(json_path):
    with open(json_path, "r") as f:
        tool_defs = json.load(f)

    tools = []
    for tool_def in tool_defs:
        try:
            # dynamically import the module
            module_name, func_name = tool_def["tool_function"].rsplit(".", 1)
            module = importlib.import_module(module_name)
            func = getattr(module, func_name)

            # wrap function with metadata as a tool object
            tool = SimpleNamespace(
                name=tool_def["tool_name"],
                description=tool_def["tool_description"],
                func=func
            )
            tools.append(tool)
        except Exception as e:
            print(f"Failed to load tool: {tool_def['tool_name']}. Reason: {str(e)}")

    return tools


def load_all_tools():
    base_path = "/usr/local/lib/python3.11/dist-packages/tooluniverse/data"
    tool_files = {
        "opentarget": os.path.join(base_path, "opentarget_tools.json"),
        "fda_drug_label": os.path.join(base_path, "fda_drug_labeling_tools.json"),
        "special_tools": os.path.join(base_path, "special_tools.json"),
        "monarch": os.path.join(base_path, "monarch_tools.json")
    }

    all_tools = []
    print("\n\U0001F4C1 Tool files:")
    print(json.dumps(tool_files, indent=2))
    print("\n\U0001F4CA Tool counts by category:")

    for category, path in tool_files.items():
        tools = load_tools_from_json(path)
        print(f"- {category}: {len(tools)} tools")
        all_tools.extend(tools)

    print(f"\n\U0001F9E0 Total tools loaded into ToolUniverse: {len(all_tools)}")
    return all_tools

import json
from tooluniverse import ToolUniverse
from api_openfda import OpenFDAAgent

class ToolAgent:
    def __init__(self):
        self.toolbox = ToolUniverse()
        self.toolbox.load_tools()
        self.fda_agent = OpenFDAAgent()

    def query_planner(self, question):
        prompts = []
        q = question.lower()

        if "acetaminophen" in q or "paracetamol" in q:
            prompts.append("Get drug label for Acetaminophen")
            prompts.append("Show adverse events for Acetaminophen")
            prompts.append("Get warnings for Acetaminophen")
            prompts.append("Get active ingredients in Acetaminophen")
        elif "ibuprofen" in q:
            prompts.append("Get drug label for Ibuprofen")
            prompts.append("Show adverse events for Ibuprofen")
            prompts.append("Get warnings for Ibuprofen")
            prompts.append("Get active ingredients in Ibuprofen")
        elif "aspirin" in q:
            prompts.append("Get drug label for Aspirin")
            prompts.append("Show adverse events for Aspirin")
            prompts.append("Get warnings for Aspirin")
            prompts.append("Get active ingredients in Aspirin")
        else:
            prompts.append(question)

        return prompts

    def run_query(self, question):
        responses = {}
        plans = self.query_planner(question)

        for plan in plans:
            if any(k in plan.lower() for k in ["label", "adverse", "warning", "ingredient"]):
                responses[plan] = self.fda_agent.answer_question(plan)
            else:
                tool_response = self.toolbox.answer_question(plan)
                responses[plan] = tool_response

        return responses

if __name__ == "__main__":
    agent = ToolAgent()
    q = "What is acetaminophen and what are its side effects, warnings, and drug class?"
    output = agent.run_query(q)
    print(json.dumps(output, indent=2))



"""##testing tools"""

# test_tool_OpenTargets_get_drug_withdrawn_blackbox_status_by_chemblId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_drug_withdrawn_blackbox_status_by_chemblId"

    # Reverting to array/list format for 'chemblId' based on the most recent 'Type mismatches' error.
    # Note: This tool still seems to have contradictory internal validation.
    arguments = {
        "chemblId": ["chembl112"] # Changed to a list/array with lowercase ID
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        # Check for actual data and print it, otherwise indicate no data
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__": # CORRECTED: Reverted to standard __name__ == "__main__"
    run_tool_demo()

# test_tool_OpenTargets_search_category_counts_by_query_string.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_search_category_counts_by_query_string"

    # Corrected argument name: 'queryString' (camelCase)
    # Example argument: Search query string 'cancer'
    arguments = {
        "queryString": "cancer" # Corrected from 'query_string' to 'queryString'
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_disease_id_description_by_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_disease_id_description_by_name"

    # Corrected argument name: 'diseaseName' (camelCase)
    # Example argument: Disease name 'diabetes mellitus'
    arguments = {
        "diseaseName": "diabetes mellitus" # Corrected from 'name' to 'diseaseName'
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_drug_id_description_by_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_drug_id_description_by_name"

    # Preemptive correction: Assuming 'drugName' (camelCase) based on similar patterns
    # Example argument: Drug name 'ibuprofen'
    arguments = {
        "drugName": "ibuprofen" # Corrected from 'name' to 'drugName' based on pattern
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_drug_chembId_by_generic_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_drug_chembId_by_generic_name"

    # CORRECTED argument name: 'drugName', based on the latest error message.
    # Example argument: Drug generic name 'ibuprofen'
    arguments = {
        "drugName": "ibuprofen" # Changed from 'drugGenericName' to 'drugName'
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_drug_indications_by_chemblId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_drug_indications_by_chemblId"

    # Example argument: ChEMBL ID for 'Ibuprofen' (CHEMBL112)
    arguments = {
        "chemblId": "CHEMBL112"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_target_gene_ontology_by_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_target_gene_ontology_by_ensemblID"

    # Example argument: Ensembl ID for 'TP53' gene (ENSG00000141510)
    arguments = {
        "ensemblId": "ENSG00000141510"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_target_homologues_by_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_target_homologues_by_ensemblID"

    # Example argument: Ensembl ID for 'TP53' gene (ENSG00000141510)
    arguments = {
        "ensemblId": "ENSG00000141510"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_target_safety_profile_by_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_target_safety_profile_by_ensemblID"

    # Example argument: Ensembl ID for 'TP53' gene (ENSG00000141510)
    arguments = {
        "ensemblId": "ENSG00000141510"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_biological_mouse_models_by_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_biological_mouse_models_by_ensemblID"

    # Example argument: Ensembl ID for 'TP53' gene (ENSG00000141510)
    arguments = {
        "ensemblId": "ENSG00000141510"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_target_genomic_location_by_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_target_genomic_location_by_ensemblID"

    # Example argument: Ensembl ID for 'TP53' gene (ENSG00000141510)
    arguments = {
        "ensemblId": "ENSG00000141510"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_target_subcellular_locations_by_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_target_subcellular_locations_by_ensemblID"

    # Example argument: Ensembl ID for 'TP53' gene (ENSG00000141510)
    arguments = {
        "ensemblId": "ENSG00000141510"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_target_synonyms_by_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_target_synonyms_by_ensemblID"

    # Example argument: Ensembl ID for 'TP53' gene (ENSG00000141510)
    arguments = {
        "ensemblId": "ENSG00000141510"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_target_tractability_by_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_target_tractability_by_ensemblID"

    # Example argument: Ensembl ID for 'TP53' gene (ENSG00000141510)
    arguments = {
        "ensemblId": "ENSG00000141510"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_target_classes_by_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_target_classes_by_ensemblID"

    # Example argument: Ensembl ID for 'TP53' gene (ENSG00000141510)
    arguments = {
        "ensemblId": "ENSG00000141510"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_target_enabling_packages_by_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_target_enabling_packages_by_ensemblID"

    # Example argument: Ensembl ID for 'TP53' gene (ENSG00000141510)
    arguments = {
        "ensemblId": "ENSG00000141510"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_target_interactions_by_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_target_interactions_by_ensemblID"

    # Example argument: Ensembl ID for 'TP53' gene (ENSG00000141510)
    arguments = {
        "ensemblId": "ENSG00000141510"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_disease_ancestors_parents_by_efoId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_disease_ancestors_parents_by_efoId"

    # Example argument: EFO ID for 'diabetes mellitus' (EFO_0000540)
    arguments = {
        "efoId": "EFO_0000540"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_disease_descendants_children_by_efoId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_disease_descendants_children_by_efoId"

    # Example argument: EFO ID for 'diabetes mellitus' (EFO_0000540)
    arguments = {
        "efoId": "EFO_0000540"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_disease_locations_by_efoId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_disease_locations_by_efoId"

    # Example argument: EFO ID for 'diabetes mellitus' (EFO_0000540)
    arguments = {
        "efoId": "EFO_0000540"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_disease_synonyms_by_efoId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_disease_synonyms_by_efoId"

    # Example argument: EFO ID for 'diabetes mellitus' (EFO_0000540)
    arguments = {
        "efoId": "EFO_0000540"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_disease_description_by_efoId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_disease_description_by_efoId"

    # Example argument: EFO ID for 'diabetes mellitus' (EFO_0000540)
    arguments = {
        "efoId": "EFO_0000540"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_disease_therapeutic_areas_by_efoId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_disease_therapeutic_areas_by_efoId"

    # Example argument: EFO ID for 'diabetes mellitus' (EFO_0000540)
    arguments = {
        "efoId": "EFO_0000540"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_drug_adverse_events_by_chemblId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_drug_adverse_events_by_chemblId"

    # Example argument: ChEMBL ID for 'Ibuprofen' (CHEMBL112)
    arguments = {
        "chemblId": "CHEMBL112"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_known_drugs_by_drug_chemblId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_known_drugs_by_drug_chemblId"

    # Corrected argument name: 'chemblId'
    arguments = {
        "chemblId": "CHEMBL112"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_parent_child_molecules_by_drug_chembl_ID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_parent_child_molecules_by_drug_chembl_ID"

    # Corrected argument name: 'chemblId'
    arguments = {
        "chemblId": "CHEMBL112"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_approved_indications_by_drug_chemblId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_approved_indications_by_drug_chemblId"

    # Corrected argument type: 'chemblId' as a single string, not a list
    arguments = {
        "chemblId": "CHEMBL112"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OpenTargets_get_drug_description_by_chemblId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_drug_description_by_chemblId"

    # Trying multiple chemblIds to demonstrate the persistent error
    chembl_ids = ["CHEMBL112", "CHEMBL25", "CHEMBL1"]

    print(f"--- Running Demo for Tool: {tool_name} with multiple chemblIds ---")
    print("-" * 60)

    for chembl_id in chembl_ids:
        arguments = {
            "chemblId": chembl_id
        }
        print(f"\nAttempting with Arguments: {arguments}")
        print("-" * 40)

        query = {
            "name": tool_name,
            "arguments": arguments
        }
        try:
            result = tooluni.run(query)
            print("Response:")
            if result:
                print(json.dumps(result, indent=2))
            else:
                print("No data returned or empty response.")
        except Exception as e:
            print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
            print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)
    print("Clarification: The consistent 'Cannot query field 'reference' on type 'DrugReferences'' error across different chemblIds confirms that the issue lies within the tool's internal GraphQL query definition, not with the input arguments themselves.")

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_drug_synonyms_by_chemblId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_drug_synonyms_by_chemblId"

    # Example argument: ChEMBL ID for 'Ibuprofen' (CHEMBL112)
    arguments = {
        "chemblId": "CHEMBL112"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_drug_trade_names_by_chemblId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_drug_trade_names_by_chemblId"

    # Example argument: ChEMBL ID for 'Ibuprofen' (CHEMBL112)
    arguments = {
        "chemblId": "CHEMBL112"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_drug_approval_status_by_chemblId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_drug_approval_status_by_chemblId"

    # Example argument: ChEMBL ID for 'Ibuprofen' (CHEMBL112)
    arguments = {
        "chemblId": "CHEMBL112"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_chemical_probes_by_target_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_chemical_probes_by_target_ensemblID"

    # Updated example argument: Ensembl ID for 'EGFR' gene (ENSG00000146648)
    # This is a widely studied drug target and might have associated chemical probes.
    arguments = {
        "ensemblId": "ENSG00000146648"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_drug_pharmacogenomics_data.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_drug_pharmacogenomics_data"

    # Example argument: ChEMBL ID for 'Ibuprofen' (CHEMBL112), inferred from description
    arguments = {
        "chemblId": "CHEMBL112"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_associated_drugs_by_target_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_associated_drugs_by_target_ensemblID"

    # Example argument: Ensembl ID for 'TP53' gene (ENSG00000141510)
    # Added required parameter: 'size'
    arguments = {
        "ensemblId": "ENSG00000141510",
        "size": 10 # Added a default size limit
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_associated_diseases_by_drug_chemblId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_associated_diseases_by_drug_chemblId"

    # Example argument: ChEMBL ID for 'Ibuprofen' (CHEMBL112)
    arguments = {
        "chemblId": "CHEMBL112"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_associated_targets_by_drug_chemblId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_associated_targets_by_drug_chemblId"

    # Example argument: ChEMBL ID for 'Ibuprofen' (CHEMBL112)
    arguments = {
        "chemblId": "CHEMBL112"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_multi_entity_search_by_query_string.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_multi_entity_search_by_query_string"

    # Example argument: Search query string 'asthma'
    arguments = {
        "queryString": "asthma" # Using 'queryString' (camelCase)
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_gene_ontology_terms_by_goID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_gene_ontology_terms_by_goID"

    # Corrected argument name: 'goIds' (plural)
    arguments = {
        "goIds": ["GO:0006915"]
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_target_constraint_info_by_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_target_constraint_info_by_ensemblID"

    # Example argument: Ensembl ID for 'TP53' gene (ENSG00000141510)
    arguments = {
        "ensemblId": "ENSG00000141510"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_publications_by_disease_efoId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_publications_by_disease_efoId"

    # Corrected argument name: 'entityId'
    arguments = {
        "entityId": "EFO_0000540"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_publications_by_target_ensemblID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_publications_by_target_ensemblID"

    # Corrected argument name: 'entityId'
    arguments = {
        "entityId": "ENSG00000146648"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_OT_get_publications_by_drug_chemblId.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "OpenTargets_get_publications_by_drug_chemblId"

    # Corrected argument name: 'entityId'
    arguments = {
        "entityId": "CHEMBL112"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_active_ingredient_info_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_active_ingredient_info_by_drug_name"

    # Corrected argument name: 'drug_name'
    arguments = {
        "drug_name": "aspirin"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_active_ingredient_info_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_active_ingredient_info_by_drug_name"

    # Example argument: Drug name 'aspirin'
    arguments = {
        "drugName": "aspirin"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_dosage_and_storage_information_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_dosage_and_storage_information_by_drug_name"

    # Corrected argument name: 'drug_name'
    arguments = {
        "drug_name": "tylenol"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_abuse_info.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_abuse_info"

    # Corrected argument name: 'abuse_info'
    arguments = {
        "abuse_info": "sedative"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_abuse_info_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_abuse_info_by_drug_name"

    # Corrected argument name: 'drug_name'
    arguments = {
        "drug_name": "oxycodone"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_accessories.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_accessories"

    # Corrected argument name: 'accessory_name'
    arguments = {
        "accessory_name": "syringe"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_accessories_info_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_accessories_info_by_drug_name"

    # Updated argument: Drug name 'HUMIRA' - known to be associated with specific injection devices
    # This drug has a higher likelihood of having 'accessories' information populated in FDA labels.
    arguments = {
        "drug_name": "HUMIRA"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_active_ingredient.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_active_ingredient"

    # Corrected argument name: 'active_ingredient'
    arguments = {
        "active_ingredient": "ibuprofen"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()



"""#new

"""

# test_tool_FDA_get_manufacturer_name_NDC_number_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_manufacturer_name_NDC_number_by_drug_name"

    arguments = {
        "drug_name": "aspirin"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_application_number_NDC_number.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_application_number_NDC_number"

    # Updated argument: Using a common NDC number for a well-known drug
    arguments = {
        "application_manufacturer_or_NDC_info": "0002-1433-01"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_name_by_adverse_reaction.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_name_by_adverse_reaction"

    arguments = {
        "adverse_reaction": "nausea"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_adverse_reactions_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_adverse_reactions_by_drug_name"

    arguments = {
        "drug_name": "ibuprofen"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_alarm.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_alarm"

    # Updated argument: Using a severe, critical alarm type for higher likelihood of a hit
    arguments = {
        "alarm_type": "DEATH"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_alarms_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_alarms_by_drug_name"

    # Updated argument: Using "ISOTRETINOIN" due to its prominent Black Box Warning
    arguments = {
        "drug_name": "ISOTRETINOIN"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_animal_pharmacology_info.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_animal_pharmacology_info"

    # Corrected argument name: 'pharmacology_info'
    arguments = {
        "pharmacology_info": "cardiovascular"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_animal_pharmacology_info_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_animal_pharmacology_info_by_drug_name"

    # Updated argument: Using "THALIDOMIDE" due to its well-known animal study data (teratogenicity)
    arguments = {
        "drug_name": "THALIDOMIDE"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_name_by_info_on_conditions_for_doctor_consultation.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_name_by_info_on_conditions_for_doctor_consultation"

    # Corrected argument name: 'condition'
    arguments = {
        "condition": "kidney disease"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_info_on_conditions_for_doctor_consultation_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_info_on_conditions_for_doctor_consultation_by_drug_name"

    arguments = {
        "drug_name": "naproxen"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

"""#new"""

# test_tool_FDA_get_drug_names_by_consulting_doctor_pharmacist_info.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_consulting_doctor_pharmacist_info"

    # New Attempt: Very generic term 'consult'
    arguments = {
        "interaction_info": "consult"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_info_on_consulting_doctor_pharmacist_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_info_on_consulting_doctor_pharmacist_by_drug_name"

    # Example: A common OTC drug known to have potential interactions/consultation points
    arguments = {
        "drug_name": "ibuprofen"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_assembly_installation_info.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_assembly_installation_info"

    # Trying multiple terms that might appear in assembly/installation instructions
    assembly_terms = [ "prepare"]

    print(f"--- Running Demo for Tool: {tool_name} with multiple arguments ---")
    print("-" * 60)

    for term in assembly_terms:
        arguments = {
            "field_info": term
        }
        print(f"\nAttempting with Arguments: {arguments}")
        print("-" * 40)

        query = {
            "name": tool_name,
            "arguments": arguments
        }
        try:
            result = tooluni.run(query)
            print("Response:")
            if result:
                print(json.dumps(result, indent=2))
            else:
                print("No data returned or empty response.")
        except Exception as e:
            print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
            print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)
    print("Note: Consistent 'No matches found!' suggests data sparsity for 'assembly_or_installation_instructions' in the FDA API.")

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_assembly_installation_info_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_assembly_installation_info_by_drug_name"

    # Trying multiple drug names that might be associated with assembly/installation
    drug_names = ["EpiPen", "Humira", "Ozempic", "Narcan"] # Common auto-injector/pre-filled pen drugs

    print(f"--- Running Demo for Tool: {tool_name} with multiple arguments ---")
    print("-" * 60)

    for drug_name in drug_names:
        arguments = {
            "drug_name": drug_name
        }
        print(f"\nAttempting with Arguments: {arguments}")
        print("-" * 40)

        query = {
            "name": tool_name,
            "arguments": arguments
        }
        try:
            result = tooluni.run(query)
            print("Response:")
            if result:
                print(json.dumps(result, indent=2))
            else:
                print("No data returned or empty response.")
        except Exception as e:
            print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
            print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)
    print("Note: Consistent 'No matches found!' suggests data sparsity for 'assembly_or_installation_instructions' in the FDA API.")

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_boxed_warning.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_boxed_warning"

    # CORRECTED argument name based on error message: 'warning_text'
    arguments = {
        "warning_text": "cardiovascular risk"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_boxed_warning_info_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_boxed_warning_info_by_drug_name"

    # Example: Warfarin is well-known for its Black Box Warnings
    arguments = {
        "drug_name": "warfarin"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_name_by_calibration_instructions.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_name_by_calibration_instructions"

    # Trying multiple terms that might appear in calibration instructions
    calibration_terms = ["calibration", "adjust", "measure", "test", "verify"]

    print(f"--- Running Demo for Tool: {tool_name} with multiple arguments ---")
    print("-" * 60)

    for term in calibration_terms:
        arguments = {
            "calibration_instructions": term
        }
        print(f"\nAttempting with Arguments: {arguments}")
        print("-" * 40)

        query = {
            "name": tool_name,
            "arguments": arguments
        }
        try:
            result = tooluni.run(query)
            print("Response:")
            if result:
                print(json.dumps(result, indent=2))
            else:
                print("No data returned or empty response.")
        except Exception as e:
            print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
            print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)
    print("Note: Consistent 'No matches found!' suggests data sparsity for 'calibration_instructions' in the FDA API.")

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_calibration_instructions_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_calibration_instructions_by_drug_name"

    # Trying multiple drug names that might be associated with devices needing calibration
    drug_names = ["insulin", "NovoLog", "Humalog", "glucose monitor"] # Added 'glucose monitor' as a drug name for device association

    print(f"--- Running Demo for Tool: {tool_name} with multiple arguments ---")
    print("-" * 60)

    for drug_name in drug_names:
        arguments = {
            "drug_name": drug_name
        }
        print(f"\nAttempting with Arguments: {arguments}")
        print("-" * 40)

        query = {
            "name": tool_name,
            "arguments": arguments
        }
        try:
            result = tooluni.run(query)
            print("Response:")
            if result:
                print(json.dumps(result, indent=2))
            else:
                print("No data returned or empty response.")
        except Exception as e:
            print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
            print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)
    print("Note: Consistent 'No matches found!' suggests data sparsity for 'calibration_instructions' in the FDA API.")

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drugs_by_carcinogenic_mutagenic_fertility.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drugs_by_carcinogenic_mutagenic_fertility"

    # CORRECTED argument name based on error message: 'carcinogenic_info'
    arguments = {
        "carcinogenic_info": "carcinogenicity"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_carcinogenic_mutagenic_fertility_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_carcinogenic_mutagenic_fertility_by_drug_name"

    # Example: Cyclophosphamide is a chemotherapy drug known for these effects
    arguments = {
        "drug_name": "cyclophosphamide"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

"""#here"""

# test_tool_FDA_get_drug_name_by_SPL_ID.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_name_by_SPL_ID"

    # CORRECTED argument name based on error message: 'field_info'
    # Keeping the SPL ID as the value, as the tool description implies
    arguments = {
        "field_info": "0a97b20e-8515-46b0-94e8-89c03265882c"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_clinical_pharmacology.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_clinical_pharmacology"

    # CORRECTED argument name and format based on error message: 'clinical_pharmacology'
    arguments = {
        "clinical_pharmacology": "pharmacokinetics"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_clinical_pharmacology_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_clinical_pharmacology_by_drug_name"

    # Example: A common drug likely to have clinical pharmacology data
    arguments = {
        "drug_name": "acetaminophen"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_clinical_studies.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_clinical_studies"

    # CORRECTED: Now includes both 'clinical_studies' and 'indication'
    # 'clinical_studies' can be a general term like 'efficacy', 'safety', 'results'
    # 'indication' should be a disease or condition for which the drug is studied.
    arguments = {
        "clinical_studies": "efficacy",
        "indication": "diabetes" # Added a common indication as an example
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_clinical_studies_info_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_clinical_studies_info_by_drug_name"

    # Example: A widely studied drug
    arguments = {
        "drug_name": "aspirin"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_contraindications.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_contraindications"

    # Example: A common contraindication
    arguments = {
        "contraindication_info": "pregnancy"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_contraindications_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_contraindications_by_drug_name"

    # Example: A drug known for significant contraindications
    arguments = {
        "drug_name": "isotretinoin"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_controlled_substance_DEA_schedule.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_controlled_substance_DEA_schedule"

    # CORRECTED argument name based on error message: 'controlled_substance_schedule'
    arguments = {
        "controlled_substance_schedule": "C-II"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_controlled_substance_DEA_schedule_info_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_controlled_substance_DEA_schedule_info_by_drug_name"

    # Example: A common Schedule II controlled substance
    arguments = {
        "drug_name": "oxycodone"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_name_by_dependence_info.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_name_by_dependence_info"

    # Example: A common term related to dependence characteristics
    arguments = {
        "dependence_info": "withdrawal"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_name_by_dependence_info.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_name_by_dependence_info"

    # Example: A common term related to dependence characteristics
    arguments = {
        "dependence_info": "withdrawal"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

"""#here"""

# test_tool_FDA_get_dependence_info_by_drug_name.py
from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_dependence_info_by_drug_name"
    arguments = {
        "drug_name": "morphine"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_disposal_info.py
from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_disposal_info"
    # Trying a more general term for disposal information
    arguments = {
        "disposal_info": "disposal" # Changed from "flush list" to "disposal"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)
    print("Note: Consistent 'No matches found!' may indicate sparse data in the FDA API for disposal information.")

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_disposal_info_by_drug_name.py
from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_disposal_info_by_drug_name"

    # Trying multiple drug names to check for disposal information
    drug_names = ["fentanyl", "morphine", "aspirin", "adalimumab"] # Added morphine, aspirin, adalimumab

    print(f"--- Running Demo for Tool: {tool_name} with multiple arguments ---")
    print("-" * 60)

    for drug_name in drug_names:
        arguments = {
            "drug_name": drug_name
        }
        print(f"\nAttempting with Arguments: {arguments}")
        print("-" * 40)

        query = {
            "name": tool_name,
            "arguments": arguments
        }
        try:
            result = tooluni.run(query)
            print("Response:")
            if result:
                print(json.dumps(result, indent=2))
            else:
                print("No data returned or empty response.")
        except Exception as e:
            print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
            print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)
    print("Note: Consistent 'No matches found!' across different drug names strongly suggests data sparsity for 'disposal_and_waste_handling' in the FDA API.")


if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_name_by_dosage_info.py
from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_name_by_dosage_info"
    arguments = {
        "dosage_info": "20 mg"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_dosage_forms_and_strengths_info.py
from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_dosage_forms_and_strengths_info"
    # CORRECTED: Combined into a single parameter 'dosage_forms_and_strengths'
    arguments = {
        "dosage_forms_and_strengths": "tablet 500 mg" # Combined info as one string
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_dosage_forms_and_strengths_by_drug_name.py
from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_dosage_forms_and_strengths_by_drug_name"
    arguments = {
        "drug_name": "ibuprofen"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_abuse_dependence_info.py
from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_abuse_dependence_info"
    # CORRECTED: Parameter name is 'abuse_info'
    arguments = {
        "abuse_info": "opioid abuse"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_abuse_dependence_info_by_drug_name.py
from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_abuse_dependence_info_by_drug_name"
    arguments = {
        "drug_name": "oxycodone"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_lab_test_interference.py
from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_lab_test_interference"
    # CORRECTED: Parameter name is 'lab_test_interference'
    arguments = {
        "lab_test_interference": "glucose"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_lab_test_interference_info_by_drug_name.py
from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_lab_test_interference_info_by_drug_name"
    arguments = {
        "drug_name": "acetaminophen"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()



"""#here"""

# test_tool_FDA_get_drug_names_by_drug_interactions.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_drug_interactions"

    # CORRECTED: Parameter name is 'interaction_term'
    arguments = {
        "interaction_term": "warfarin"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_interactions_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_interactions_by_drug_name"

    # Example: A common antibiotic
    arguments = {
        "drug_name": "amoxicillin"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_effective_time.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_effective_time"

    # Example: A specific effective date (YYYYMMDD format is common for FDA API dates)
    arguments = {
        "effective_time": "20240101"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_effective_time_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_effective_time_by_drug_name"

    # Example: Trying 'ibuprofen' as another common drug.
    # The 'No matches found!' error for 'paracetamol' indicates potential data sparsity
    # or indexing issues in the FDA API for the 'effective_time' field.
    arguments = {
        "drug_name": "ibuprofen"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)
    print("Note: 'No matches found!' might indicate data sparsity for 'effective_time' in the FDA API, not a parameter error.")

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_name_by_environmental_warning.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_name_by_environmental_warning"

    # Trying a very general term like 'environmental'
    arguments = {
        "environmental_warning": "environmental"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)
    print("Note: Persistent 'No matches found!' for environmental warnings indicates likely data sparsity in the FDA API for this field.")

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_environmental_warning_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_environmental_warning_by_drug_name"

    # Example: A drug sometimes associated with environmental concerns
    arguments = {
        "drug_name": "diclofenac"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_food_safety_warnings.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_food_safety_warnings"

    # Trying a common phrase related to food warnings
    arguments = {
        "field_info": "food interaction"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)
    print("Note: Persistent 'No matches found!' for food safety warnings indicates likely data sparsity in the FDA API for this field.")

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_general_precautions.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_general_precautions"

    # CORRECTED: Parameter name is 'precaution_info'
    arguments = {
        "precaution_info": "driving"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_general_precautions_by_drug_name.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_general_precautions_by_drug_name"

    # Example: A drug known for precautions like drowsiness
    arguments = {
        "drug_name": "diphenhydramine"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

# test_tool_FDA_get_drug_names_by_geriatric_use.py

from tooluniverse.execute_function import ToolUniverse
import json

def run_tool_demo():
    tooluni = ToolUniverse()
    tooluni.load_tools()

    tool_name = "FDA_get_drug_names_by_geriatric_use"

    # CORRECTED: Parameter name is 'geriatric_use'
    arguments = {
        "geriatric_use": "renal impairment"
    }

    print(f"--- Running Demo for Tool: {tool_name} ---")
    print(f"Arguments: {arguments}")
    print("-" * 60)

    query = {
        "name": tool_name,
        "arguments": arguments
    }
    try:
        result = tooluni.run(query)
        print("Response:")
        if result:
            print(json.dumps(result, indent=2))
        else:
            print("No data returned or empty response.")
    except Exception as e:
        print(f"Error during tool execution for '{tool_name}' with arguments {arguments}: {e}")
        print("Please ensure 'tooluniverse' is installed and configured correctly.")

    print("-" * 60)

if __name__ == "__main__":
    run_tool_demo()

