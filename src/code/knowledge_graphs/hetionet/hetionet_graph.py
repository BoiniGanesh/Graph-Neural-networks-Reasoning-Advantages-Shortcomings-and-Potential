#%%
import pandas as pd

# === Convert nodes.tsv to CSV ===
nodes = pd.read_csv("hetionet-v1.0-nodes.tsv", sep="\t")
nodes.to_csv("hetionet_nodes.csv", index=False)

# %%

import pandas as pd
import gzip

path = "hetionet-v1.0-edges.sif.gz"

edges_data = []
with gzip.open(path, 'rt') as f:
    for line in f:
        parts = line.strip().split()
        if len(parts) == 3:
            edges_data.append(parts)

edges_df = pd.DataFrame(edges_data, columns=['source', 'relation', 'target'])
edges_df.to_csv("hetionet_edges.csv", index=False)
print("✅ Saved edges to hetionet_edges.csv")
print(edges_df.head())

# %%
import pandas as pd
import networkx as nx

# Load the node and edge CSVs
nodes_df = pd.read_csv("hetionet_nodes.csv")
edges_df = pd.read_csv("hetionet_edges.csv")

# Create a directed multigraph
G = nx.MultiDiGraph()

# Add nodes with attributes
for _, row in nodes_df.iterrows():
    G.add_node(
        row['id'],
        name=row.get('name', ''),
        kind=row.get('kind', ''),
        description=row.get('description', '')
    )

# Add edges with relation labels
for _, row in edges_df.iterrows():
    G.add_edge(
        row['source'],
        row['target'],
        relation=row['relation']
    )

print(f"Graph built with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

# %%
nx.write_graphml(G, "hetionet.graphml")


#testing and querying the graph
# %%
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
from collections import Counter
import random

# === Load Hetionet Graph ===
G = nx.read_graphml("hetionet.graphml")
print(f"✅ Hetionet loaded with {G.number_of_nodes():,} nodes and {G.number_of_edges():,} edges.")

# === Health Checks ===
node_types = [data.get("kind", "unknown") for _, data in G.nodes(data=True)]
edge_types = [data.get("relation", "unknown") for _, _, data in G.edges(data=True)]
print("\n🧬 Node Type Counts:")
for k, v in Counter(node_types).items():
    print(f"  - {k}: {v:,}")
print("\n🔗 Edge Type Counts:")
for k, v in Counter(edge_types).items():
    print(f"  - {k}: {v:,}")

# Connectivity
if isinstance(G, nx.DiGraph):
    print("\n🔗 Directed Graph Connectivity:")
    print(f"  - Weakly Connected Components: {nx.number_weakly_connected_components(G)}")
    print(f"  - Strongly Connected Components: {nx.number_strongly_connected_components(G)}")
else:
    print("\n🔗 Undirected Graph Connectivity:")
    print(f"  - Connected Components: {nx.number_connected_components(G)}")

# Degree Distribution
degrees = [deg for _, deg in G.degree()]
print("\n📈 Degree Distribution:")
print(f"  - Min: {min(degrees)}, Max: {max(degrees)}, Avg: {sum(degrees)/len(degrees):.2f}")

# === Helper Functions ===
def get_node(name):
    return next((n for n, d in G.nodes(data=True) if d.get("name", "").lower() == name.lower()), None)

def draw_interactive_subgraph(node_names, title="Subgraph"):
    name_to_index = {data.get("name"): n for n, data in G.nodes(data=True) if "name" in data}
    indices = [name_to_index[name] for name in node_names if name in name_to_index]
    subgraph = G.subgraph(indices)

    if not subgraph.nodes:
        print("⚠️ No valid nodes to draw.")
        return

    pos = nx.spring_layout(subgraph, seed=1)
    node_x, node_y, hovertext = [], [], []

    for n in subgraph.nodes():
        x, y = pos[n]
        node_x.append(x)
        node_y.append(y)
        d = G.nodes[n]
        hovertext.append(f"{d.get('name', n)}<br>({d.get('kind', 'unknown')})")

    edge_x, edge_y = [], []
    for u, v in subgraph.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=1, color='gray'), hoverinfo='none')
    node_trace = go.Scatter(x=node_x, y=node_y, mode='markers+text',
                            text=[G.nodes[n].get('name', str(n)) for n in subgraph.nodes()],
                            hovertext=hovertext,
                            hoverinfo='text',
                            textposition="top center",
                            marker=dict(color='skyblue', size=20, line=dict(width=2, color='darkblue')))

    fig = go.Figure(data=[edge_trace, node_trace], layout=go.Layout(
        title=dict(text=title, font=dict(size=22)),
        showlegend=False,
        hovermode='closest',
        margin=dict(b=40, l=40, r=40, t=60),
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(showgrid=False, zeroline=False),
        height=800))
    fig.show()

def get_drugs_for_disease(disease_name):
    disease_node = get_node(disease_name)
    return [G.nodes[n]['name'] for n in G.neighbors(disease_node)
            if G.nodes[n]['kind'] == 'Compound'] if disease_node else []

def get_genes_for_disease(disease_name):
    disease_node = get_node(disease_name)
    return [G.nodes[n]['name'] for n in G.neighbors(disease_node)
            if G.nodes[n]['kind'] == 'Gene'] if disease_node else []
#%%
def draw_shortest_path(entity1, entity2):
    name_to_node = {data.get("name"): n for n, data in G.nodes(data=True) if "name" in data}
    src = name_to_node.get(entity1)
    tgt = name_to_node.get(entity2)

    if not src or not tgt:
        print(f"❌ One or both entities not found: '{entity1}', '{entity2}'")
        return

    if not nx.has_path(G, src, tgt):
        print(f"❌ No path found between '{entity1}' and '{entity2}'")
        return

    path = nx.shortest_path(G, source=src, target=tgt)
    readable_path = [G.nodes[n].get("name", str(n)) for n in path]
    print(f"✅ Shortest path ({len(path)} steps): {' → '.join(readable_path)}")
    draw_interactive_subgraph(readable_path, title=f"Shortest Path: {entity1} → {entity2}")

# === Queries for "asthma" and "albuterol" ===
entity = "asthma"
drug_query = "albuterol"

print(f"\n💊 Drugs for '{entity}':")
drugs = get_drugs_for_disease(entity)
print(drugs[:10])
draw_interactive_subgraph([entity] + drugs[:10], title="Drugs for Disease")

print(f"\n🧬 Genes for '{entity}':")
genes = get_genes_for_disease(entity)
print(genes[:10])
draw_interactive_subgraph([entity] + genes[:10], title="Genes for Disease")

print(f"\n🔗 Shortest path from 'TP53' to '{entity}':")
draw_shortest_path("TP53", entity)

# %%
def draw_neighbors_interactive(entity_name):
    # Map node names to IDs, using .get to avoid KeyErrors
    node_map = {data.get("name"): n for n, data in G.nodes(data=True) if "name" in data}
    node = node_map.get(entity_name)

    if node is None:
        print(f"❌ Entity '{entity_name}' not found.")
        return

    neighbors = list(G.neighbors(node))
    sub_nodes = [node] + neighbors
    subgraph = G.subgraph(sub_nodes)

    pos = nx.spring_layout(subgraph, seed=42)
    node_x, node_y, hovertext = [], [], []

    for n in subgraph.nodes():
        x, y = pos[n]
        node_x.append(x)
        node_y.append(y)
        d = G.nodes[n]
        hovertext.append(f"{d.get('name', str(n))}<br>({d.get('kind', 'N/A')})")

    edge_x, edge_y = [], []
    for u, v in subgraph.edges():
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color='gray'),
        hoverinfo='none',
        mode='lines'
    )

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[G.nodes[n].get("name", str(n)) for n in subgraph.nodes()],
        hovertext=hovertext,
        hoverinfo='text',
        textposition="top center",
        marker=dict(
            color='lightgreen',
            size=20,
            line=dict(width=2, color='darkgreen')
        )
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=dict(
                text=f"🌐 Neighbors of '{entity_name}' in Hetionet",
                font=dict(size=22)
            ),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=40, l=40, r=40, t=60),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
            height=800
        )
    )

    fig.show()
draw_neighbors_interactive("asthma")
draw_neighbors_interactive("albuterol")

# %%
