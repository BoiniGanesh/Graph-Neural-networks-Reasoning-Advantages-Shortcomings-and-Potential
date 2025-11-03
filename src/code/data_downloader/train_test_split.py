# -*- coding: utf-8 -*-


# %% [Cell 1: Setup & Imports]
import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.nn import RGCNConv
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from collections import defaultdict
import networkx as nx
import numpy as np
import random

# Reproducibility
seed = 42
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
torch.cuda.manual_seed_all(seed)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print("Using device:", device)

# %% [Cell 2: Mount Drive & Load GraphML]


graph_path = "hetionet.graphml"
print("Loading graph ...")
G = nx.read_graphml(graph_path)
print(f"Loaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges.")

# %% [Cell 3: Build Node and Edge Mappings]
node_type_map = defaultdict(list)
node_id_map = {}
node_idx_by_type = defaultdict(dict)
for nid, data in G.nodes(data=True):
    if 'kind' not in data:
        continue
    ntype = data['kind']
    idx = len(node_type_map[ntype])
    node_type_map[ntype].append(nid)
    node_id_map[nid] = (ntype, idx)
    node_idx_by_type[ntype][nid] = idx

edge_type_map = defaultdict(list)
for src, dst, attr in G.edges(data=True):
    rel = attr.get('metaedge', attr.get('relation', None))
    if not rel or src not in node_id_map or dst not in node_id_map:
        continue
    src_t, src_i = node_id_map[src]
    dst_t, dst_i = node_id_map[dst]
    edge_type_map[(src_t, rel, dst_t)].append((src_i, dst_i))

print(f"✅ Node types: {list(node_type_map.keys())}")
print(f"✅ Total edge types: {len(edge_type_map)}")

# %% [Cell 4: Homogeneous Graph]
type_offsets = {}
global_id_map = {}
offset = 0
for ntype, nodes in node_type_map.items():
    type_offsets[ntype] = offset
    for local_idx in range(len(nodes)):
        global_id_map[(ntype, local_idx)] = offset + local_idx
    offset += len(nodes)

num_nodes = offset
edge_type_keys = list(edge_type_map.keys())
rel2id = {etype: i for i, etype in enumerate(edge_type_keys)}
num_relations = len(edge_type_keys)

all_src, all_dst, all_rel = [], [], []
for etype, edges in edge_type_map.items():
    rel_id = rel2id[etype]
    src_type, _, dst_type = etype
    for (s_local, d_local) in edges:
        all_src.append(type_offsets[src_type] + s_local)
        all_dst.append(type_offsets[dst_type] + d_local)
        all_rel.append(rel_id)

edge_index = torch.tensor([all_src, all_dst], dtype=torch.long)
edge_type = torch.tensor(all_rel, dtype=torch.long)

print(f"Homogeneous nodes: {num_nodes}, edges: {edge_index.size(1)}")

# %% [Cell: Global 80/20 split + save in chosen format (single cell)]
import os, json, torch, numpy as np

# ========= CONFIG =========
out_dir = "hetionet_splits_newlatest_80_20"
save_format = "csv"   # choose from: "pt", "npz", "csv", "jsonl", "parquet"
seed_for_split = 42
# =========================

os.makedirs(out_dir, exist_ok=True)

# ---- sanity checks ----
assert isinstance(edge_index, torch.Tensor) and edge_index.ndim == 2 and edge_index.size(0) == 2, \
    "edge_index must be a LongTensor of shape [2, E]"
assert isinstance(edge_type, torch.Tensor) and edge_type.ndim == 1 and edge_type.size(0) == edge_index.size(1), \
    "edge_type must be a LongTensor of shape [E]"
E = edge_index.size(1)

# ---- Build a single global 80/20 split over ALL edges ----
gen = torch.Generator().manual_seed(seed_for_split)
perm = torch.randperm(E, generator=gen)
n_train = int(0.8 * E)
train_cols = perm[:n_train]
test_cols  = perm[n_train:]

train_edge_index = edge_index[:, train_cols].cpu()
test_edge_index  = edge_index[:, test_cols].cpu()
train_edge_type  = edge_type[train_cols].cpu()
test_edge_type   = edge_type[test_cols].cpu()

manifest = {
    "num_nodes": int(num_nodes),
    "num_edges_total": int(E),
    "num_edges_train": int(train_edge_index.size(1)),
    "num_edges_test":  int(test_edge_index.size(1)),
    "format": save_format,
    "dir": out_dir,
    "seed": seed_for_split,
}

# ---- Save helpers for each format ----
def save_pt():
    torch.save(
        {"edge_index": train_edge_index, "edge_type": train_edge_type},
        os.path.join(out_dir, "train.pt"),
    )
    torch.save(
        {"edge_index": test_edge_index, "edge_type": test_edge_type},
        os.path.join(out_dir, "test.pt"),
    )

def save_npz():
    np.savez_compressed(
        os.path.join(out_dir, "train.npz"),
        src=train_edge_index[0].numpy(),
        dst=train_edge_index[1].numpy(),
        rel=train_edge_type.numpy(),
    )
    np.savez_compressed(
        os.path.join(out_dir, "test.npz"),
        src=test_edge_index[0].numpy(),
        dst=test_edge_index[1].numpy(),
        rel=test_edge_type.numpy(),
    )

def _to_df(src_t, dst_t, rel_t):
    import pandas as pd
    return pd.DataFrame({"src": src_t.numpy(), "dst": dst_t.numpy(), "rel": rel_t.numpy()})

def save_csv():
    import pandas as pd
    _to_df(train_edge_index[0], train_edge_index[1], train_edge_type) \
        .to_csv(os.path.join(out_dir, "train.csv"), index=False)
    _to_df(test_edge_index[0], test_edge_index[1], test_edge_type) \
        .to_csv(os.path.join(out_dir, "test.csv"), index=False)

def save_jsonl():
    def _dump(path, src, dst, rel):
        with open(path, "w") as f:
            for s, d, r in zip(src.tolist(), dst.tolist(), rel.tolist()):
                f.write(json.dumps({"src": s, "dst": d, "rel": r}) + "\n")
    _dump(os.path.join(out_dir, "train.jsonl"),
          train_edge_index[0], train_edge_index[1], train_edge_type)
    _dump(os.path.join(out_dir, "test.jsonl"),
          test_edge_index[0], test_edge_index[1], test_edge_type)

def save_parquet():
    # Try parquet; if unavailable, fall back to CSV (with a notice).
    try:
        import pandas as pd
        df_tr = _to_df(train_edge_index[0], train_edge_index[1], train_edge_type)
        df_te = _to_df(test_edge_index[0], test_edge_index[1], test_edge_type)
        df_tr.to_parquet(os.path.join(out_dir, "train.parquet"), index=False)
        df_te.to_parquet(os.path.join(out_dir, "test.parquet"), index=False)
    except Exception as e:
        print(f"[parquet unavailable → falling back to CSV] {e}")
        save_csv()

# ---- Dispatch on format ----
fmt = save_format.lower()
if fmt == "pt":
    save_pt()
elif fmt == "npz":
    save_npz()
elif fmt == "csv":
    save_csv()
elif fmt == "jsonl":
    save_jsonl()
elif fmt == "parquet":
    save_parquet()
else:
    raise ValueError(f"Unknown save_format: {save_format}")

# ---- Save a manifest for convenience ----
with open(os.path.join(out_dir, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)

print(f"✅ Saved global 80/20 split ({manifest['num_edges_train']} train / {manifest['num_edges_test']} test) as {save_format} to: {out_dir}")

# ---- primekg ----
import pickle
import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.nn import RGCNConv
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from collections import defaultdict
import numpy as np
import random

# --- Load Pickled PrimeKG Graph ---
pkl_path = "primekg_graph.pkl"
with open(pkl_path, "rb") as f:
    G = pickle.load(f)
print(f"✅ Loaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges.")

# --- Map Nodes and Edges Using PrimeKG Naming Conventions ---
node_type_map = defaultdict(list)
node_id_map = {}
node_idx_by_type = defaultdict(dict)

for nid, data in G.nodes(data=True):
    ntype = data.get("node_type", "unknown")
    idx = len(node_type_map[ntype])
    node_type_map[ntype].append(nid)
    node_id_map[nid] = (ntype, idx)
    node_idx_by_type[ntype][nid] = idx

edge_type_map = defaultdict(list)
for src, dst, attr in G.edges(data=True):
    rel = attr.get("relation", "unknown")
    if src not in node_id_map or dst not in node_id_map:
        continue
    src_t, src_i = node_id_map[src]
    dst_t, dst_i = node_id_map[dst]
    edge_type_map[(src_t, rel, dst_t)].append((src_i, dst_i))

print(f"✅ Node types: {list(node_type_map.keys())}")
print(f"✅ Total edge types: {len(edge_type_map)}")

# --- Build Homogeneous Graph ---
type_offsets = {}
global_id_map = {}
offset = 0
for ntype, nodes in node_type_map.items():
    type_offsets[ntype] = offset
    for local_idx in range(len(nodes)):
        global_id_map[(ntype, local_idx)] = offset + local_idx
    offset += len(nodes)

num_nodes = offset
edge_type_keys = list(edge_type_map.keys())
rel2id = {etype: i for i, etype in enumerate(edge_type_keys)}
num_relations = len(edge_type_keys)

all_src, all_dst, all_rel = [], [], []
edge_type_splits = {}

for etype, edges in edge_type_map.items():
    rel_id = rel2id[etype]
    src_type, _, dst_type = etype
    if len(edges) < 5:
        continue
    perm = torch.randperm(len(edges))
    num_train = int(0.8 * len(edges))
    num_val = int(0.1 * len(edges))
    train_edges = [edges[i] for i in perm[:num_train]]
    val_edges = [edges[i] for i in perm[num_train:num_train+num_val]]
    test_edges = [edges[i] for i in perm[num_train+num_val:]]

    for (s_local, d_local) in train_edges:
        all_src.append(type_offsets[src_type] + s_local)
        all_dst.append(type_offsets[dst_type] + d_local)
        all_rel.append(rel_id)

    edge_type_splits[etype] = {
        "val": torch.tensor([
            [type_offsets[src_type] + s for s, d in val_edges],
            [type_offsets[dst_type] + d for s, d in val_edges]
        ], dtype=torch.long),
        "test": torch.tensor([
            [type_offsets[src_type] + s for s, d in test_edges],
            [type_offsets[dst_type] + d for s, d in test_edges]
        ], dtype=torch.long)
    }

edge_index = torch.tensor([all_src, all_dst], dtype=torch.long)
edge_type = torch.tensor(all_rel, dtype=torch.long)

print(f"Homogeneous nodes: {num_nodes}, edges used for training: {edge_index.size(1)}")

# %% [Cell: Global 80/20 split + save in chosen format (single cell)]
import os, json, torch, numpy as np

# ========= CONFIG =========
out_dir = "primekg_splits_newlatest_80_20"
save_format = "csv"   # choose from: "pt", "npz", "csv", "jsonl", "parquet"
seed_for_split = 42
# =========================

os.makedirs(out_dir, exist_ok=True)

# ---- sanity checks ----
assert isinstance(edge_index, torch.Tensor) and edge_index.ndim == 2 and edge_index.size(0) == 2, \
    "edge_index must be a LongTensor of shape [2, E]"
assert isinstance(edge_type, torch.Tensor) and edge_type.ndim == 1 and edge_type.size(0) == edge_index.size(1), \
    "edge_type must be a LongTensor of shape [E]"
E = edge_index.size(1)

# ---- Build a single global 80/20 split over ALL edges ----
gen = torch.Generator().manual_seed(seed_for_split)
perm = torch.randperm(E, generator=gen)
n_train = int(0.8 * E)
train_cols = perm[:n_train]
test_cols  = perm[n_train:]

train_edge_index = edge_index[:, train_cols].cpu()
test_edge_index  = edge_index[:, test_cols].cpu()
train_edge_type  = edge_type[train_cols].cpu()
test_edge_type   = edge_type[test_cols].cpu()

manifest = {
    "num_nodes": int(num_nodes),
    "num_edges_total": int(E),
    "num_edges_train": int(train_edge_index.size(1)),
    "num_edges_test":  int(test_edge_index.size(1)),
    "format": save_format,
    "dir": out_dir,
    "seed": seed_for_split,
}

# ---- Save helpers for each format ----
def save_pt():
    torch.save(
        {"edge_index": train_edge_index, "edge_type": train_edge_type},
        os.path.join(out_dir, "train.pt"),
    )
    torch.save(
        {"edge_index": test_edge_index, "edge_type": test_edge_type},
        os.path.join(out_dir, "test.pt"),
    )

def save_npz():
    np.savez_compressed(
        os.path.join(out_dir, "train.npz"),
        src=train_edge_index[0].numpy(),
        dst=train_edge_index[1].numpy(),
        rel=train_edge_type.numpy(),
    )
    np.savez_compressed(
        os.path.join(out_dir, "test.npz"),
        src=test_edge_index[0].numpy(),
        dst=test_edge_index[1].numpy(),
        rel=test_edge_type.numpy(),
    )

def _to_df(src_t, dst_t, rel_t):
    import pandas as pd
    return pd.DataFrame({"src": src_t.numpy(), "dst": dst_t.numpy(), "rel": rel_t.numpy()})

def save_csv():
    import pandas as pd
    _to_df(train_edge_index[0], train_edge_index[1], train_edge_type) \
        .to_csv(os.path.join(out_dir, "train.csv"), index=False)
    _to_df(test_edge_index[0], test_edge_index[1], test_edge_type) \
        .to_csv(os.path.join(out_dir, "test.csv"), index=False)

def save_jsonl():
    def _dump(path, src, dst, rel):
        with open(path, "w") as f:
            for s, d, r in zip(src.tolist(), dst.tolist(), rel.tolist()):
                f.write(json.dumps({"src": s, "dst": d, "rel": r}) + "\n")
    _dump(os.path.join(out_dir, "train.jsonl"),
          train_edge_index[0], train_edge_index[1], train_edge_type)
    _dump(os.path.join(out_dir, "test.jsonl"),
          test_edge_index[0], test_edge_index[1], test_edge_type)

def save_parquet():
    # Try parquet; if unavailable, fall back to CSV (with a notice).
    try:
        import pandas as pd
        df_tr = _to_df(train_edge_index[0], train_edge_index[1], train_edge_type)
        df_te = _to_df(test_edge_index[0], test_edge_index[1], test_edge_type)
        df_tr.to_parquet(os.path.join(out_dir, "train.parquet"), index=False)
        df_te.to_parquet(os.path.join(out_dir, "test.parquet"), index=False)
    except Exception as e:
        print(f"[parquet unavailable → falling back to CSV] {e}")
        save_csv()

# ---- Dispatch on format ----
fmt = save_format.lower()
if fmt == "pt":
    save_pt()
elif fmt == "npz":
    save_npz()
elif fmt == "csv":
    save_csv()
elif fmt == "jsonl":
    save_jsonl()
elif fmt == "parquet":
    save_parquet()
else:
    raise ValueError(f"Unknown save_format: {save_format}")

# ---- Save a manifest for convenience ----
with open(os.path.join(out_dir, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)

print(f"✅ Saved global 80/20 split ({manifest['num_edges_train']} train / {manifest['num_edges_test']} test) as {save_format} to: {out_dir}")

# ✅ OpenFDA (GraphML) + sections — R-GCN with Type-Aware, Filtered Negatives
#     Single-Cell Script: Load → Normalize → Split (80/20) → Save → Train → Eval

# =========================
# 0) Imports & Repro / Device
# =========================
import os, random, pickle, json, re
from collections import defaultdict

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.nn import RGCNConv
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
import networkx as nx

SEED = 42
random.seed(SEED); np.random.seed(SEED)
torch.manual_seed(SEED); torch.cuda.manual_seed_all(SEED)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# =========================
# 1) Config
# =========================
# 👉 Point this to your data:
# graph_path = "/Users/ganeshkumarboini/Downloads/drug_data_kg_rebuilt_normalized.graphml"
graph_path = "drug_data_kg_rebuilt.graphml"
assert os.path.exists(graph_path), f"Path does not exist: {graph_path}"

# Where to write the 80/20 split:
out_dir = "openfda_another_split_80_20"
save_format = "csv"  # choose: "pt", "npz", "csv", "jsonl", "parquet"
os.makedirs(out_dir, exist_ok=True)

# Training hyperparams
EPOCHS = 20
LR = 1e-2
NEG_K = 1  # negatives per positive for loss (train & eval)
EMB_DIM = 64
HID_DIM = 64
OUT_DIM = 64

# =========================
# 2) Load graph & normalize attributes
# =========================
def load_graph(path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".graphml":
        print(f"📥 Loading GraphML from: {path}")
        G0 = nx.read_graphml(path)
        H = nx.MultiDiGraph()
        H.add_nodes_from(G0.nodes(data=True))
        if G0.is_multigraph():
            for u, v, k, data in G0.edges(keys=True, data=True):
                H.add_edge(u, v, key=k, **(data or {}))
        else:
            for u, v, data in G0.edges(data=True):
                H.add_edge(u, v, **(data or {}))
        return H
    elif ext in [".pkl", ".pickle"]:
        print(f"📥 Loading pickle from: {path}")
        with open(path, "rb") as f:
            return pickle.load(f)
    else:
        raise ValueError(f"Unsupported file extension: {ext}")

G = load_graph(graph_path)

# Prefer 'node_type' on nodes; fallback chain
for n, data in G.nodes(data=True):
    if "node_type" not in data:
        data["node_type"] = data.get("type", data.get("category", data.get("kind", "unknown")))

# Prefer 'relation' on edges; fallback chain
for u, v, attr in G.edges(data=True):
    if "relation" not in attr:
        attr["relation"] = attr.get("type", attr.get("label", "unknown"))

print(f"✅ Loaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges.")
ex_node = next(iter(G.nodes(data=True)))[1] if len(G) else {}
ex_edge = next(iter(G.edges(data=True)))[2] if G.number_of_edges() else {}
print("🔎 Example node keys:", list(ex_node.keys()))
print("🔎 Example edge keys:", list(ex_edge.keys()))

# =========================
# 3) Build type maps & edge maps
# =========================
node_type_map = defaultdict(list)      # {node_type: [original node ids]}
node_id_map = {}                       # {original node id: (node_type, local_idx)}
node_idx_by_type = defaultdict(dict)   # {node_type: {original id: local_idx}}

for nid, data in G.nodes(data=True):
    ntype = data.get("node_type", "unknown")
    idx = len(node_type_map[ntype])
    node_type_map[ntype].append(nid)
    node_id_map[nid] = (ntype, idx)
    node_idx_by_type[ntype][nid] = idx

edge_type_map = defaultdict(list)      # {(src_type, relation, dst_type): [(src_local, dst_local), ...]}
for src, dst, attr in G.edges(data=True):
    if src not in node_id_map or dst not in node_id_map:
        continue
    rel = attr.get("relation", "unknown")
    src_t, src_i = node_id_map[src]
    dst_t, dst_i = node_id_map[dst]
    edge_type_map[(src_t, rel, dst_t)].append((src_i, dst_i))

print(f"✅ Node types ({len(node_type_map)}): {list(node_type_map.keys())[:10]}{'...' if len(node_type_map)>10 else ''}")
print(f"✅ Total edge types: {len(edge_type_map)}")

# =========================
# 4) Homogeneous remap + Global 80/20 split + Save
# =========================
# 4.1) Node remap
type_offsets = {}
global_id_map = {}
offset = 0
for ntype, nodes in node_type_map.items():
    type_offsets[ntype] = offset
    for local_idx in range(len(nodes)):
        global_id_map[(ntype, local_idx)] = offset + local_idx
    offset += len(nodes)
num_nodes = offset

# 4.2) All edges + relation dictionary
edge_type_keys = list(edge_type_map.keys())     # index -> (src_type, rel, dst_type)
rel2id = {etype: i for i, etype in enumerate(edge_type_keys)}
num_relations = len(edge_type_keys)

all_src, all_dst, all_rel = [], [], []
existing_edges_triples = set()  # (s_g, d_g, rel_id) for filtered negatives

for etype, pairs in edge_type_map.items():
    src_type, _, dst_type = etype
    r = rel2id[etype]
    for (s_l, d_l) in pairs:
        s_g = type_offsets[src_type] + s_l
        d_g = type_offsets[dst_type] + d_l
        all_src.append(s_g)
        all_dst.append(d_g)
        all_rel.append(r)
        existing_edges_triples.add((s_g, d_g, r))

edge_index_full = torch.tensor([all_src, all_dst], dtype=torch.long)
edge_type_full  = torch.tensor(all_rel, dtype=torch.long)
E = edge_index_full.size(1)
print(f"Homogeneous nodes: {num_nodes}, total edges: {E}")

# 4.3) Global 80/20 split (deterministic)
SPLIT_SEED = 42
gen = torch.Generator().manual_seed(SPLIT_SEED)
perm = torch.randperm(E, generator=gen)
n_train = int(0.8 * E)
train_cols = perm[:n_train]
test_cols  = perm[n_train:]

train_edge_index = edge_index_full[:, train_cols].contiguous()
test_edge_index  = edge_index_full[:, test_cols].contiguous()
train_edge_type  = edge_type_full[train_cols].contiguous()
test_edge_type   = edge_type_full[test_cols].contiguous()

print(f"Split → train: {train_edge_index.size(1)}, test: {test_edge_index.size(1)}")

# 4.4) Save split in desired format
manifest = {
    "num_nodes": int(num_nodes),
    "num_relations": int(num_relations),
    "edges_total": int(E),
    "edges_train": int(train_edge_index.size(1)),
    "edges_test":  int(test_edge_index.size(1)),
    "seed": SPLIT_SEED,
    "format": save_format,
    "dir": out_dir
}

def _to_df(src_t, dst_t, rel_t):
    import pandas as pd
    return pd.DataFrame({
        "src": src_t.detach().cpu().numpy(),
        "dst": dst_t.detach().cpu().numpy(),
        "rel": rel_t.detach().cpu().numpy()
    })

def save_split(fmt="pt"):
    fmt = fmt.lower()
    if fmt == "pt":
        torch.save(
            {"edge_index": train_edge_index.cpu(), "edge_type": train_edge_type.cpu()},
            os.path.join(out_dir, "train.pt"),
        )
        torch.save(
            {"edge_index": test_edge_index.cpu(), "edge_type": test_edge_type.cpu()},
            os.path.join(out_dir, "test.pt"),
        )
    elif fmt == "npz":
        np.savez_compressed(
            os.path.join(out_dir, "train.npz"),
            src=train_edge_index[0].cpu().numpy(),
            dst=train_edge_index[1].cpu().numpy(),
            rel=train_edge_type.cpu().numpy(),
        )
        np.savez_compressed(
            os.path.join(out_dir, "test.npz"),
            src=test_edge_index[0].cpu().numpy(),
            dst=test_edge_index[1].cpu().numpy(),
            rel=test_edge_type.cpu().numpy(),
        )
    elif fmt == "csv":
        _to_df(train_edge_index[0], train_edge_index[1], train_edge_type) \
            .to_csv(os.path.join(out_dir, "train.csv"), index=False)
        _to_df(test_edge_index[0], test_edge_index[1], test_edge_type) \
            .to_csv(os.path.join(out_dir, "test.csv"), index=False)
    elif fmt == "jsonl":
        def _dump(path, src, dst, rel):
            with open(path, "w") as f:
                for s, d, r in zip(src.cpu().tolist(), dst.cpu().tolist(), rel.cpu().tolist()):
                    f.write(json.dumps({"src": s, "dst": d, "rel": r}) + "\n")
        _dump(os.path.join(out_dir, "train.jsonl"),
              train_edge_index[0], train_edge_index[1], train_edge_type)
        _dump(os.path.join(out_dir, "test.jsonl"),
              test_edge_index[0], test_edge_index[1], test_edge_type)
    elif fmt == "parquet":
        try:
            _to_df(train_edge_index[0], train_edge_index[1], train_edge_type) \
                .to_parquet(os.path.join(out_dir, "train.parquet"), index=False)
            _to_df(test_edge_index[0], test_edge_index[1], test_edge_type) \
                .to_parquet(os.path.join(out_dir, "test.parquet"), index=False)
        except Exception as e:
            print(f"[parquet unavailable → falling back to CSV] {e}")
            _to_df(train_edge_index[0], train_edge_index[1], train_edge_type) \
                .to_csv(os.path.join(out_dir, "train.csv"), index=False)
            _to_df(test_edge_index[0], test_edge_index[1], test_edge_type) \
                .to_csv(os.path.join(out_dir, "test.csv"), index=False)
    else:
        raise ValueError(f"Unknown save_format: {fmt}")

save_split(save_format)
with open(os.path.join(out_dir, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)
print(f"✅ Saved global 80/20 split ({manifest['edges_train']} train / {manifest['edges_test']} test) as {save_format} to: {out_dir}")

# ---- combined primekg hetionet kg ----
import pickle
import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.nn import RGCNConv
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from collections import defaultdict
import numpy as np
import random

# --- Load Pickled PrimeKG Graph ---
pkl_path = "primekg_hetionet_combined.pkl"
with open(pkl_path, "rb") as f:
    G = pickle.load(f)
print(f"✅ Loaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges.")

# --- Map Nodes and Edges Using PrimeKG Naming Conventions ---
node_type_map = defaultdict(list)
node_id_map = {}
node_idx_by_type = defaultdict(dict)

for nid, data in G.nodes(data=True):
    ntype = data.get("node_type", "unknown")
    idx = len(node_type_map[ntype])
    node_type_map[ntype].append(nid)
    node_id_map[nid] = (ntype, idx)
    node_idx_by_type[ntype][nid] = idx

edge_type_map = defaultdict(list)
for src, dst, attr in G.edges(data=True):
    rel = attr.get("relation", "unknown")
    if src not in node_id_map or dst not in node_id_map:
        continue
    src_t, src_i = node_id_map[src]
    dst_t, dst_i = node_id_map[dst]
    edge_type_map[(src_t, rel, dst_t)].append((src_i, dst_i))

print(f"✅ Node types: {list(node_type_map.keys())}")
print(f"✅ Total edge types: {len(edge_type_map)}")

# --- Build Homogeneous Graph ---
type_offsets = {}
global_id_map = {}
offset = 0
for ntype, nodes in node_type_map.items():
    type_offsets[ntype] = offset
    for local_idx in range(len(nodes)):
        global_id_map[(ntype, local_idx)] = offset + local_idx
    offset += len(nodes)

num_nodes = offset
edge_type_keys = list(edge_type_map.keys())
rel2id = {etype: i for i, etype in enumerate(edge_type_keys)}
num_relations = len(edge_type_keys)

all_src, all_dst, all_rel = [], [], []
edge_type_splits = {}

for etype, edges in edge_type_map.items():
    rel_id = rel2id[etype]
    src_type, _, dst_type = etype
    if len(edges) < 5:
        continue
    perm = torch.randperm(len(edges))
    num_train = int(0.8 * len(edges))
    num_val = int(0.1 * len(edges))
    train_edges = [edges[i] for i in perm[:num_train]]
    val_edges = [edges[i] for i in perm[num_train:num_train+num_val]]
    test_edges = [edges[i] for i in perm[num_train+num_val:]]

    for (s_local, d_local) in train_edges:
        all_src.append(type_offsets[src_type] + s_local)
        all_dst.append(type_offsets[dst_type] + d_local)
        all_rel.append(rel_id)

    edge_type_splits[etype] = {
        "val": torch.tensor([
            [type_offsets[src_type] + s for s, d in val_edges],
            [type_offsets[dst_type] + d for s, d in val_edges]
        ], dtype=torch.long),
        "test": torch.tensor([
            [type_offsets[src_type] + s for s, d in test_edges],
            [type_offsets[dst_type] + d for s, d in test_edges]
        ], dtype=torch.long)
    }

edge_index = torch.tensor([all_src, all_dst], dtype=torch.long)
edge_type = torch.tensor(all_rel, dtype=torch.long)

print(f"Homogeneous nodes: {num_nodes}, edges used for training: {edge_index.size(1)}")

# %% [Cell: Global 80/20 split + save in chosen format (single cell)]
import os, json, torch, numpy as np

# ========= CONFIG =========
out_dir = "combined_splits_newlatest_80_20"
save_format = "csv"   # choose from: "pt", "npz", "csv", "jsonl", "parquet"
seed_for_split = 42
# =========================

os.makedirs(out_dir, exist_ok=True)

# ---- sanity checks ----
assert isinstance(edge_index, torch.Tensor) and edge_index.ndim == 2 and edge_index.size(0) == 2, \
    "edge_index must be a LongTensor of shape [2, E]"
assert isinstance(edge_type, torch.Tensor) and edge_type.ndim == 1 and edge_type.size(0) == edge_index.size(1), \
    "edge_type must be a LongTensor of shape [E]"
E = edge_index.size(1)

# ---- Build a single global 80/20 split over ALL edges ----
gen = torch.Generator().manual_seed(seed_for_split)
perm = torch.randperm(E, generator=gen)
n_train = int(0.8 * E)
train_cols = perm[:n_train]
test_cols  = perm[n_train:]

train_edge_index = edge_index[:, train_cols].cpu()
test_edge_index  = edge_index[:, test_cols].cpu()
train_edge_type  = edge_type[train_cols].cpu()
test_edge_type   = edge_type[test_cols].cpu()

manifest = {
    "num_nodes": int(num_nodes),
    "num_edges_total": int(E),
    "num_edges_train": int(train_edge_index.size(1)),
    "num_edges_test":  int(test_edge_index.size(1)),
    "format": save_format,
    "dir": out_dir,
    "seed": seed_for_split,
}

# ---- Save helpers for each format ----
def save_pt():
    torch.save(
        {"edge_index": train_edge_index, "edge_type": train_edge_type},
        os.path.join(out_dir, "train.pt"),
    )
    torch.save(
        {"edge_index": test_edge_index, "edge_type": test_edge_type},
        os.path.join(out_dir, "test.pt"),
    )

def save_npz():
    np.savez_compressed(
        os.path.join(out_dir, "train.npz"),
        src=train_edge_index[0].numpy(),
        dst=train_edge_index[1].numpy(),
        rel=train_edge_type.numpy(),
    )
    np.savez_compressed(
        os.path.join(out_dir, "test.npz"),
        src=test_edge_index[0].numpy(),
        dst=test_edge_index[1].numpy(),
        rel=test_edge_type.numpy(),
    )

def _to_df(src_t, dst_t, rel_t):
    import pandas as pd
    return pd.DataFrame({"src": src_t.numpy(), "dst": dst_t.numpy(), "rel": rel_t.numpy()})

def save_csv():
    import pandas as pd
    _to_df(train_edge_index[0], train_edge_index[1], train_edge_type) \
        .to_csv(os.path.join(out_dir, "train.csv"), index=False)
    _to_df(test_edge_index[0], test_edge_index[1], test_edge_type) \
        .to_csv(os.path.join(out_dir, "test.csv"), index=False)

def save_jsonl():
    def _dump(path, src, dst, rel):
        with open(path, "w") as f:
            for s, d, r in zip(src.tolist(), dst.tolist(), rel.tolist()):
                f.write(json.dumps({"src": s, "dst": d, "rel": r}) + "\n")
    _dump(os.path.join(out_dir, "train.jsonl"),
          train_edge_index[0], train_edge_index[1], train_edge_type)
    _dump(os.path.join(out_dir, "test.jsonl"),
          test_edge_index[0], test_edge_index[1], test_edge_type)

def save_parquet():
    # Try parquet; if unavailable, fall back to CSV (with a notice).
    try:
        import pandas as pd
        df_tr = _to_df(train_edge_index[0], train_edge_index[1], train_edge_type)
        df_te = _to_df(test_edge_index[0], test_edge_index[1], test_edge_type)
        df_tr.to_parquet(os.path.join(out_dir, "train.parquet"), index=False)
        df_te.to_parquet(os.path.join(out_dir, "test.parquet"), index=False)
    except Exception as e:
        print(f"[parquet unavailable → falling back to CSV] {e}")
        save_csv()

# ---- Dispatch on format ----
fmt = save_format.lower()
if fmt == "pt":
    save_pt()
elif fmt == "npz":
    save_npz()
elif fmt == "csv":
    save_csv()
elif fmt == "jsonl":
    save_jsonl()
elif fmt == "parquet":
    save_parquet()
else:
    raise ValueError(f"Unknown save_format: {save_format}")

# ---- Save a manifest for convenience ----
with open(os.path.join(out_dir, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)

print(f"✅ Saved global 80/20 split ({manifest['num_edges_train']} train / {manifest['num_edges_test']} test) as {save_format} to: {out_dir}")

# ---- combined primekg hetionet kg ----
import pickle
import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.nn import RGCNConv
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from collections import defaultdict
import numpy as np
import random

# --- Load Pickled PrimeKG Graph ---
pkl_path = "primekg_hetionet_combined.pkl"
with open(pkl_path, "rb") as f:
    G = pickle.load(f)
print(f"✅ Loaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges.")

# --- Map Nodes and Edges Using PrimeKG Naming Conventions ---
node_type_map = defaultdict(list)
node_id_map = {}
node_idx_by_type = defaultdict(dict)

for nid, data in G.nodes(data=True):
    ntype = data.get("node_type", "unknown")
    idx = len(node_type_map[ntype])
    node_type_map[ntype].append(nid)
    node_id_map[nid] = (ntype, idx)
    node_idx_by_type[ntype][nid] = idx

edge_type_map = defaultdict(list)
for src, dst, attr in G.edges(data=True):
    rel = attr.get("relation", "unknown")
    if src not in node_id_map or dst not in node_id_map:
        continue
    src_t, src_i = node_id_map[src]
    dst_t, dst_i = node_id_map[dst]
    edge_type_map[(src_t, rel, dst_t)].append((src_i, dst_i))

print(f"✅ Node types: {list(node_type_map.keys())}")
print(f"✅ Total edge types: {len(edge_type_map)}")

# --- Build Homogeneous Graph ---
type_offsets = {}
global_id_map = {}
offset = 0
for ntype, nodes in node_type_map.items():
    type_offsets[ntype] = offset
    for local_idx in range(len(nodes)):
        global_id_map[(ntype, local_idx)] = offset + local_idx
    offset += len(nodes)

num_nodes = offset
edge_type_keys = list(edge_type_map.keys())
rel2id = {etype: i for i, etype in enumerate(edge_type_keys)}
num_relations = len(edge_type_keys)

all_src, all_dst, all_rel = [], [], []
edge_type_splits = {}

for etype, edges in edge_type_map.items():
    rel_id = rel2id[etype]
    src_type, _, dst_type = etype
    if len(edges) < 5:
        continue
    perm = torch.randperm(len(edges))
    num_train = int(0.8 * len(edges))
    num_val = int(0.1 * len(edges))
    train_edges = [edges[i] for i in perm[:num_train]]
    val_edges = [edges[i] for i in perm[num_train:num_train+num_val]]
    test_edges = [edges[i] for i in perm[num_train+num_val:]]

    for (s_local, d_local) in train_edges:
        all_src.append(type_offsets[src_type] + s_local)
        all_dst.append(type_offsets[dst_type] + d_local)
        all_rel.append(rel_id)

    edge_type_splits[etype] = {
        "val": torch.tensor([
            [type_offsets[src_type] + s for s, d in val_edges],
            [type_offsets[dst_type] + d for s, d in val_edges]
        ], dtype=torch.long),
        "test": torch.tensor([
            [type_offsets[src_type] + s for s, d in test_edges],
            [type_offsets[dst_type] + d for s, d in test_edges]
        ], dtype=torch.long)
    }

edge_index = torch.tensor([all_src, all_dst], dtype=torch.long)
edge_type = torch.tensor(all_rel, dtype=torch.long)

print(f"Homogeneous nodes: {num_nodes}, edges used for training: {edge_index.size(1)}")
# Add this debug code before the save_csv_with_names() function to see what node attributes exist
print("🔍 Debug: Checking node attributes for a few nodes...")
sample_nodes = list(G.nodes(data=True))[:5]  # Check first 5 nodes
for i, (node_id, attrs) in enumerate(sample_nodes):
    print(f"Node {i}: ID={node_id}, Attributes={attrs}")

# Also check what edge attributes look like
print("\n🔍 Debug: Checking edge attributes for a few edges...")
sample_edges = list(G.edges(data=True))[:3]
for i, (src, dst, attrs) in enumerate(sample_edges):
    print(f"Edge {i}: {src} -> {dst}, Attributes={attrs}")

import os, json, torch, numpy as np

# ========= CONFIG =========
out_dir = "combined_splits_withnames_80_20"
save_format = "csv"   # choose from: "pt", "npz", "csv", "jsonl", "parquet"
seed_for_split = 42
# =========================

os.makedirs(out_dir, exist_ok=True)

# ---- sanity checks ----
assert isinstance(edge_index, torch.Tensor) and edge_index.ndim == 2 and edge_index.size(0) == 2, \
    "edge_index must be a LongTensor of shape [2, E]"
assert isinstance(edge_type, torch.Tensor) and edge_type.ndim == 1 and edge_type.size(0) == edge_index.size(1), \
    "edge_type must be a LongTensor of shape [E]"
E = edge_index.size(1)

# ---- Build a single global 80/20 split over ALL edges ----
gen = torch.Generator().manual_seed(seed_for_split)
perm = torch.randperm(E, generator=gen)
n_train = int(0.8 * E)
train_cols = perm[:n_train]
test_cols  = perm[n_train:]

train_edge_index = edge_index[:, train_cols].cpu()
test_edge_index  = edge_index[:, test_cols].cpu()
train_edge_type  = edge_type[train_cols].cpu()
test_edge_type   = edge_type[test_cols].cpu()

manifest = {
    "num_nodes": int(num_nodes),
    "num_edges_total": int(E),
    "num_edges_train": int(train_edge_index.size(1)),
    "num_edges_test":  int(test_edge_index.size(1)),
    "format": save_format,
    "dir": out_dir,
    "seed": seed_for_split,
}

# ---- Modified CSV saving with names ----
def save_csv_with_names():
    import pandas as pd

    # Create reverse mappings for node names and relation types
    print("Building reverse mappings for node names and relations...")

    # Build node ID to name mapping
    node_id_to_name = {}
    for nid, data in G.nodes(data=True):
        # Try multiple possible name fields
        name = data.get('node_name')
        node_id_to_name[nid] = name

    # Build global ID to original node ID mapping
    global_id_to_original = {}
    for (ntype, local_idx), global_id in global_id_map.items():
        if local_idx < len(node_type_map[ntype]):  # Safety check
            original_node_id = node_type_map[ntype][local_idx]
            global_id_to_original[global_id] = original_node_id

    # Build relation ID to relation name mapping
    rel_id_to_name = {}
    for (src_type, rel_name, dst_type), rel_id in rel2id.items():
        rel_id_to_name[rel_id] = rel_name

    # Build node ID to type mapping
    global_id_to_type = {}
    for (ntype, local_idx), global_id in global_id_map.items():
        global_id_to_type[global_id] = ntype

    print(f"✅ Built mappings: {len(node_id_to_name)} node names, {len(rel_id_to_name)} relation names")
    print(f"✅ Global to original mapping: {len(global_id_to_original)} entries")

    def create_enhanced_dataframe(edge_index, edge_type, split_name):
        src_global = edge_index[0].numpy()
        dst_global = edge_index[1].numpy()
        rel_ids = edge_type.numpy()

        data = []
        for i in range(len(src_global)):
            src_gid = src_global[i]
            dst_gid = dst_global[i]
            rel_id = rel_ids[i]

            # Get original node IDs
            src_original = global_id_to_original.get(src_gid, 'Unknown')
            dst_original = global_id_to_original.get(dst_gid, 'Unknown')

            # Get node names and types
            src_name = node_id_to_name.get(src_original, 'Unknown')
            dst_name = node_id_to_name.get(dst_original, 'Unknown')
            src_type = global_id_to_type.get(src_gid, 'Unknown')
            dst_type = global_id_to_type.get(dst_gid, 'Unknown')

            # Get relation name
            rel_name = rel_id_to_name.get(rel_id, 'Unknown')

            data.append({
                'src_global_id': src_gid,
                'dst_global_id': dst_gid,
                'src_original_id': src_original,
                'dst_original_id': dst_original,
                'src_name': src_name,
                'dst_name': dst_name,
                'src_type': src_type,
                'dst_type': dst_type,
                'rel_id': rel_id,
                'rel_name': rel_name
            })

            # Progress indicator for large datasets
            if i % 10000 == 0 and i > 0:
                print(f"  Processed {i}/{len(src_global)} edges for {split_name}...")

        return pd.DataFrame(data)

    # Create enhanced DataFrames
    print("Creating training set DataFrame with names...")
    train_df = create_enhanced_dataframe(train_edge_index, train_edge_type, "train")

    print("Creating test set DataFrame with names...")
    test_df = create_enhanced_dataframe(test_edge_index, test_edge_type, "test")

    # Save to CSV
    train_csv_path = os.path.join(out_dir, "combined_train_with_names.csv")
    test_csv_path = os.path.join(out_dir, "combined_test_with_names.csv")

    train_df.to_csv(train_csv_path, index=False)
    test_df.to_csv(test_csv_path, index=False)

    print(f"✅ Saved training set with {len(train_df)} edges to {train_csv_path}")
    print(f"✅ Saved test set with {len(test_df)} edges to {test_csv_path}")

    # Also save node and relation mappings for reference
    node_mapping_df = pd.DataFrame([
        {
            'global_id': global_id,
            'original_id': original_id,
            'node_type': global_id_to_type[global_id],
            'node_name': node_id_to_name.get(original_id, 'Unknown')
        }
        for global_id, original_id in global_id_to_original.items()
    ])
    node_mapping_df.to_csv(os.path.join(out_dir, "node_mapping.csv"), index=False)

    relation_mapping_df = pd.DataFrame([
        {
            'rel_id': rel_id,
            'rel_name': rel_name,
            'src_type': src_type,
            'dst_type': dst_type
        }
        for (src_type, rel_name, dst_type), rel_id in rel2id.items()
    ])
    relation_mapping_df.to_csv(os.path.join(out_dir, "relation_mapping.csv"), index=False)

    print("✅ Saved additional mapping files: node_mapping.csv, relation_mapping.csv")

    # Print some sample data for verification
    print("\n📊 Sample training edges:")
    print(train_df.head(3).to_string(index=False))

    return train_df, test_df

# ---- Dispatch on format ----
fmt = save_format.lower()
if fmt == "pt":
    save_pt()
elif fmt == "npz":
    save_npz()
elif fmt == "csv":
    save_csv_with_names()  # Use the enhanced version directly
elif fmt == "jsonl":
    save_jsonl()
elif fmt == "parquet":
    save_parquet()
else:
    raise ValueError(f"Unknown save_format: {save_format}")

# ---- Save a manifest for convenience ----
with open(os.path.join(out_dir, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)

print(f"✅ Saved global 80/20 split ({manifest['num_edges_train']} train / {manifest['num_edges_test']} test) as {save_format} to: {out_dir}")

# ---- primekg ----
import pickle
import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.nn import RGCNConv
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from collections import defaultdict
import numpy as np
import random

# --- Load Pickled PrimeKG Graph ---
pkl_path = "primekg_graph.pkl"
with open(pkl_path, "rb") as f:
    G = pickle.load(f)
print(f"✅ Loaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges.")

# --- Map Nodes and Edges Using PrimeKG Naming Conventions ---
node_type_map = defaultdict(list)
node_id_map = {}
node_idx_by_type = defaultdict(dict)

for nid, data in G.nodes(data=True):
    ntype = data.get("node_type", "unknown")
    idx = len(node_type_map[ntype])
    node_type_map[ntype].append(nid)
    node_id_map[nid] = (ntype, idx)
    node_idx_by_type[ntype][nid] = idx

edge_type_map = defaultdict(list)
for src, dst, attr in G.edges(data=True):
    rel = attr.get("relation", "unknown")
    if src not in node_id_map or dst not in node_id_map:
        continue
    src_t, src_i = node_id_map[src]
    dst_t, dst_i = node_id_map[dst]
    edge_type_map[(src_t, rel, dst_t)].append((src_i, dst_i))

print(f"✅ Node types: {list(node_type_map.keys())}")
print(f"✅ Total edge types: {len(edge_type_map)}")

# --- Build Homogeneous Graph ---
type_offsets = {}
global_id_map = {}
offset = 0
for ntype, nodes in node_type_map.items():
    type_offsets[ntype] = offset
    for local_idx in range(len(nodes)):
        global_id_map[(ntype, local_idx)] = offset + local_idx
    offset += len(nodes)

num_nodes = offset
edge_type_keys = list(edge_type_map.keys())
rel2id = {etype: i for i, etype in enumerate(edge_type_keys)}
num_relations = len(edge_type_keys)

all_src, all_dst, all_rel = [], [], []
edge_type_splits = {}

for etype, edges in edge_type_map.items():
    rel_id = rel2id[etype]
    src_type, _, dst_type = etype
    if len(edges) < 5:
        continue
    perm = torch.randperm(len(edges))
    num_train = int(0.8 * len(edges))
    num_val = int(0.1 * len(edges))
    train_edges = [edges[i] for i in perm[:num_train]]
    val_edges = [edges[i] for i in perm[num_train:num_train+num_val]]
    test_edges = [edges[i] for i in perm[num_train+num_val:]]

    for (s_local, d_local) in train_edges:
        all_src.append(type_offsets[src_type] + s_local)
        all_dst.append(type_offsets[dst_type] + d_local)
        all_rel.append(rel_id)

    edge_type_splits[etype] = {
        "val": torch.tensor([
            [type_offsets[src_type] + s for s, d in val_edges],
            [type_offsets[dst_type] + d for s, d in val_edges]
        ], dtype=torch.long),
        "test": torch.tensor([
            [type_offsets[src_type] + s for s, d in test_edges],
            [type_offsets[dst_type] + d for s, d in test_edges]
        ], dtype=torch.long)
    }

edge_index = torch.tensor([all_src, all_dst], dtype=torch.long)
edge_type = torch.tensor(all_rel, dtype=torch.long)

print(f"Homogeneous nodes: {num_nodes}, edges used for training: {edge_index.size(1)}")
# Add this debug code before the save_csv_with_names() function to see what node attributes exist
print("🔍 Debug: Checking node attributes for a few nodes...")
sample_nodes = list(G.nodes(data=True))[:5]  # Check first 5 nodes
for i, (node_id, attrs) in enumerate(sample_nodes):
    print(f"Node {i}: ID={node_id}, Attributes={attrs}")

# Also check what edge attributes look like
print("\n🔍 Debug: Checking edge attributes for a few edges...")
sample_edges = list(G.edges(data=True))[:3]
for i, (src, dst, attrs) in enumerate(sample_edges):
    print(f"Edge {i}: {src} -> {dst}, Attributes={attrs}")

import os, json, torch, numpy as np

# ========= CONFIG =========
out_dir = "primekg_splits_withnames_80_20"
save_format = "csv"   # choose from: "pt", "npz", "csv", "jsonl", "parquet"
seed_for_split = 42
# =========================

os.makedirs(out_dir, exist_ok=True)

# ---- sanity checks ----
assert isinstance(edge_index, torch.Tensor) and edge_index.ndim == 2 and edge_index.size(0) == 2, \
    "edge_index must be a LongTensor of shape [2, E]"
assert isinstance(edge_type, torch.Tensor) and edge_type.ndim == 1 and edge_type.size(0) == edge_index.size(1), \
    "edge_type must be a LongTensor of shape [E]"
E = edge_index.size(1)

# ---- Build a single global 80/20 split over ALL edges ----
gen = torch.Generator().manual_seed(seed_for_split)
perm = torch.randperm(E, generator=gen)
n_train = int(0.8 * E)
train_cols = perm[:n_train]
test_cols  = perm[n_train:]

train_edge_index = edge_index[:, train_cols].cpu()
test_edge_index  = edge_index[:, test_cols].cpu()
train_edge_type  = edge_type[train_cols].cpu()
test_edge_type   = edge_type[test_cols].cpu()

manifest = {
    "num_nodes": int(num_nodes),
    "num_edges_total": int(E),
    "num_edges_train": int(train_edge_index.size(1)),
    "num_edges_test":  int(test_edge_index.size(1)),
    "format": save_format,
    "dir": out_dir,
    "seed": seed_for_split,
}

# ---- Modified CSV saving with names ----
def save_csv_with_names():
    import pandas as pd

    # Create reverse mappings for node names and relation types
    print("Building reverse mappings for node names and relations...")

    # Build node ID to name mapping
    node_id_to_name = {}
    for nid, data in G.nodes(data=True):
        # Try multiple possible name fields
        name = data.get('node_name')
        node_id_to_name[nid] = name

    # Build global ID to original node ID mapping
    global_id_to_original = {}
    for (ntype, local_idx), global_id in global_id_map.items():
        if local_idx < len(node_type_map[ntype]):  # Safety check
            original_node_id = node_type_map[ntype][local_idx]
            global_id_to_original[global_id] = original_node_id

    # Build relation ID to relation name mapping
    rel_id_to_name = {}
    for (src_type, rel_name, dst_type), rel_id in rel2id.items():
        rel_id_to_name[rel_id] = rel_name

    # Build node ID to type mapping
    global_id_to_type = {}
    for (ntype, local_idx), global_id in global_id_map.items():
        global_id_to_type[global_id] = ntype

    print(f"✅ Built mappings: {len(node_id_to_name)} node names, {len(rel_id_to_name)} relation names")
    print(f"✅ Global to original mapping: {len(global_id_to_original)} entries")

    def create_enhanced_dataframe(edge_index, edge_type, split_name):
        src_global = edge_index[0].numpy()
        dst_global = edge_index[1].numpy()
        rel_ids = edge_type.numpy()

        data = []
        for i in range(len(src_global)):
            src_gid = src_global[i]
            dst_gid = dst_global[i]
            rel_id = rel_ids[i]

            # Get original node IDs
            src_original = global_id_to_original.get(src_gid, 'Unknown')
            dst_original = global_id_to_original.get(dst_gid, 'Unknown')

            # Get node names and types
            src_name = node_id_to_name.get(src_original, 'Unknown')
            dst_name = node_id_to_name.get(dst_original, 'Unknown')
            src_type = global_id_to_type.get(src_gid, 'Unknown')
            dst_type = global_id_to_type.get(dst_gid, 'Unknown')

            # Get relation name
            rel_name = rel_id_to_name.get(rel_id, 'Unknown')

            data.append({
                'src_global_id': src_gid,
                'dst_global_id': dst_gid,
                'src_original_id': src_original,
                'dst_original_id': dst_original,
                'src_name': src_name,
                'dst_name': dst_name,
                'src_type': src_type,
                'dst_type': dst_type,
                'rel_id': rel_id,
                'rel_name': rel_name
            })

            # Progress indicator for large datasets
            if i % 10000 == 0 and i > 0:
                print(f"  Processed {i}/{len(src_global)} edges for {split_name}...")

        return pd.DataFrame(data)

    # Create enhanced DataFrames
    print("Creating training set DataFrame with names...")
    train_df = create_enhanced_dataframe(train_edge_index, train_edge_type, "train")

    print("Creating test set DataFrame with names...")
    test_df = create_enhanced_dataframe(test_edge_index, test_edge_type, "test")

    # Save to CSV
    train_csv_path = os.path.join(out_dir, "primekg_train_with_names.csv")
    test_csv_path = os.path.join(out_dir, "primekg_test_with_names.csv")

    train_df.to_csv(train_csv_path, index=False)
    test_df.to_csv(test_csv_path, index=False)

    print(f"✅ Saved training set with {len(train_df)} edges to {train_csv_path}")
    print(f"✅ Saved test set with {len(test_df)} edges to {test_csv_path}")

    # Also save node and relation mappings for reference
    node_mapping_df = pd.DataFrame([
        {
            'global_id': global_id,
            'original_id': original_id,
            'node_type': global_id_to_type[global_id],
            'node_name': node_id_to_name.get(original_id, 'Unknown')
        }
        for global_id, original_id in global_id_to_original.items()
    ])
    node_mapping_df.to_csv(os.path.join(out_dir, "node_mapping.csv"), index=False)

    relation_mapping_df = pd.DataFrame([
        {
            'rel_id': rel_id,
            'rel_name': rel_name,
            'src_type': src_type,
            'dst_type': dst_type
        }
        for (src_type, rel_name, dst_type), rel_id in rel2id.items()
    ])
    relation_mapping_df.to_csv(os.path.join(out_dir, "relation_mapping.csv"), index=False)

    print("✅ Saved additional mapping files: node_mapping.csv, relation_mapping.csv")

    # Print some sample data for verification
    print("\n📊 Sample training edges:")
    print(train_df.head(3).to_string(index=False))

    return train_df, test_df

# ---- Dispatch on format ----
fmt = save_format.lower()
if fmt == "pt":
    save_pt()
elif fmt == "npz":
    save_npz()
elif fmt == "csv":
    save_csv_with_names()  # Use the enhanced version directly
elif fmt == "jsonl":
    save_jsonl()
elif fmt == "parquet":
    save_parquet()
else:
    raise ValueError(f"Unknown save_format: {save_format}")

# ---- Save a manifest for convenience ----
with open(os.path.join(out_dir, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)

print(f"✅ Saved global 80/20 split ({manifest['num_edges_train']} train / {manifest['num_edges_test']} test) as {save_format} to: {out_dir}")

primekg='primekg_splits_withnames_80_20/primekg_train_with_names.csv'
combined='compare_train_test/combined_splits_withnames_80_20/combined_train_with_names.csv'

import pandas as pd
primekg= pd.read_csv(primekg)
combined= pd.read_csv(combined)

combined.head(10)

primekg.head(10)

import pandas as pd


# Extract unique (src_type, dst_type) pairs from each
prime_pairs = set(primekg[['src_type', 'dst_type']].apply(tuple, axis=1).unique())
combined_pairs = set(combined[['src_type', 'dst_type']].apply(tuple, axis=1).unique())

# Common pairs
common_pairs = prime_pairs & combined_pairs

# Unique to each
prime_only = prime_pairs - combined_pairs
combined_only = combined_pairs - prime_pairs

print("✅ Common edge type pairs between both files:")
print(common_pairs)

print("\n📌 Edge type pairs only in PrimeKG:")
print(prime_only)

print("\n📌 Edge type pairs only in Combined:")
print(combined_only)

# Value counts for PrimeKG
prime_counts = primekg.groupby(['src_type', 'dst_type']).size().reset_index(name='count')
print("📊 PrimeKG edge type counts:")
print(prime_counts.sort_values('count', ascending=False))

# Value counts for Combined
combined_counts = combined.groupby(['src_type', 'dst_type']).size().reset_index(name='count')
print("\n📊 Combined edge type counts:")
print(combined_counts.sort_values('count', ascending=False))

import pandas as pd

# Define edges as unordered sets to ignore direction
primekg_edges = set(frozenset([s, d]) for s, d in zip(primekg.src_name, primekg.dst_name))
combined_edges  = set(frozenset([s, d]) for s, d in zip(combined.src_name, combined.dst_name))

# Overlaps
common = primekg_edges & combined_edges
missing_in_comb = primekg_edges - combined_edges
extra_in_comb   = combined_edges - primekg_edges

# Percentages
pct_preserved = len(common) / len(primekg_edges) * 100 if primekg_edges else 0
pct_missing   = len(missing_in_comb) / len(primekg_edges) * 100 if primekg_edges else 0
pct_extra     = len(extra_in_comb) / len(combined_edges) * 100 if combined_edges else 0

print(f"PrimeKG edges preserved in Combined (direction-agnostic): {pct_preserved:.2f}%")
print(f"PrimeKG edges missing in Combined (direction-agnostic): {pct_missing:.2f}%")
print(f"Extra edges only in Combined (direction-agnostic): {pct_extra:.2f}%")

import pandas as pd

# Optional: normalize names first (lowercase, remove spaces/underscores)
def normalize_name(name):
    return str(name).lower().replace("_", "").replace(" ", "")

primekg['src_name_norm'] = primekg['src_name'].apply(normalize_name)
primekg['dst_name_norm'] = primekg['dst_name'].apply(normalize_name)
combined['src_name_norm'] = combined['src_name'].apply(normalize_name)
combined['dst_name_norm'] = combined['dst_name'].apply(normalize_name)

# Drop duplicate edges in PrimeKG and Combined
primekg_unique = primekg.drop_duplicates(subset=['src_name_norm', 'dst_name_norm'])
combined_unique = combined.drop_duplicates(subset=['src_name_norm', 'dst_name_norm'])

# Define edges as unordered sets to ignore direction
primekg_edges = set(frozenset([s, d]) for s, d in zip(primekg_unique.src_name_norm, primekg_unique.dst_name_norm))
combined_edges  = set(frozenset([s, d]) for s, d in zip(combined_unique.src_name_norm, combined_unique.dst_name_norm))

# Overlaps
common = primekg_edges & combined_edges
missing_in_comb = primekg_edges - combined_edges
extra_in_comb   = combined_edges - primekg_edges

# Percentages
pct_preserved = len(common) / len(primekg_edges) * 100 if primekg_edges else 0
pct_missing   = len(missing_in_comb) / len(primekg_edges) * 100 if primekg_edges else 0
pct_extra     = len(extra_in_comb) / len(combined_edges) * 100 if combined_edges else 0

print(f"PrimeKG edges preserved in Combined (normalized, direction-agnostic, duplicates removed): {pct_preserved:.2f}%")
print(f"PrimeKG edges missing in Combined (normalized, direction-agnostic, duplicates removed): {pct_missing:.2f}%")
print(f"Extra edges only in Combined (normalized, direction-agnostic, duplicates removed): {pct_extra:.2f}%")

import pandas as pd

# Optional: normalize names first (lowercase, remove spaces/underscores)
def normalize_name(name):
    return str(name).lower().replace("_", "").replace(" ", "")

primekg['src_name_norm'] = primekg['src_name'].apply(normalize_name)
primekg['dst_name_norm'] = primekg['dst_name'].apply(normalize_name)
combined['src_name_norm'] = combined['src_name'].apply(normalize_name)
combined['dst_name_norm'] = combined['dst_name'].apply(normalize_name)

# -----------------------------
# 3️⃣ Check for duplicates within PrimeKG
# If PrimeKG has duplicate (src_name, dst_name) edges with different relations,
# it might artificially inflate “missing” if Combined merged them.
# We remove duplicates to see the unique overlap
# -----------------------------
primekg_unique = primekg.drop_duplicates(subset=['src_name_norm', 'dst_name_norm'])
combined_unique = combined.drop_duplicates(subset=['src_name_norm', 'dst_name_norm'])

# Define edges as unordered sets to ignore direction
primekg_edges = set(frozenset([s, d]) for s, d in zip(primekg_unique.src_name_norm, primekg_unique.dst_name_norm))
combined_edges  = set(frozenset([s, d]) for s, d in zip(combined_unique.src_name_norm, combined_unique.dst_name_norm))

# Overlaps
common = primekg_edges & combined_edges
missing_in_comb = primekg_edges - combined_edges
extra_in_comb   = combined_edges - primekg_edges

# Percentages
pct_preserved = len(common) / len(primekg_edges) * 100 if primekg_edges else 0
pct_missing   = len(missing_in_comb) / len(primekg_edges) * 100 if primekg_edges else 0
pct_extra     = len(extra_in_comb) / len(combined_edges) * 100 if combined_edges else 0

print(f"PrimeKG edges preserved in Combined (normalized, direction-agnostic, duplicates removed): {pct_preserved:.2f}%")
print(f"PrimeKG edges missing in Combined (normalized, direction-agnostic, duplicates removed): {pct_missing:.2f}%")
print(f"Extra edges only in Combined (normalized, direction-agnostic, duplicates removed): {pct_extra:.2f}%")

fusionhpo='hetionet_openfda_primekg_withnames_80_20/combined_hpo_train_with_names.csv'

combined= pd.read_csv(fusionhpo)

import pandas as pd

# Optional: normalize names first (lowercase, remove spaces/underscores)
def normalize_name(name):
    return str(name).lower().replace("_", "").replace(" ", "")

primekg['src_name_norm'] = primekg['src_name'].apply(normalize_name)
primekg['dst_name_norm'] = primekg['dst_name'].apply(normalize_name)
combined['src_name_norm'] = combined['src_name'].apply(normalize_name)
combined['dst_name_norm'] = combined['dst_name'].apply(normalize_name)

# Drop duplicate edges in PrimeKG and Combined
primekg_unique = primekg.drop_duplicates(subset=['src_name_norm', 'dst_name_norm'])
combined_unique = combined.drop_duplicates(subset=['src_name_norm', 'dst_name_norm'])

# Define edges as unordered sets to ignore direction
primekg_edges = set(frozenset([s, d]) for s, d in zip(primekg_unique.src_name_norm, primekg_unique.dst_name_norm))
combined_edges  = set(frozenset([s, d]) for s, d in zip(combined_unique.src_name_norm, combined_unique.dst_name_norm))

# Overlaps
common = primekg_edges & combined_edges
missing_in_comb = primekg_edges - combined_edges
extra_in_comb   = combined_edges - primekg_edges

# Percentages
pct_preserved = len(common) / len(primekg_edges) * 100 if primekg_edges else 0
pct_missing   = len(missing_in_comb) / len(primekg_edges) * 100 if primekg_edges else 0
pct_extra     = len(extra_in_comb) / len(combined_edges) * 100 if combined_edges else 0

print(f"PrimeKG edges preserved in Combined (normalized, direction-agnostic, duplicates removed): {pct_preserved:.2f}%")
print(f"PrimeKG edges missing in Combined (normalized, direction-agnostic, duplicates removed): {pct_missing:.2f}%")
print(f"Extra edges only in Combined (normalized, direction-agnostic, duplicates removed): {pct_extra:.2f}%")

fusionho='compare_train_test/hetionet_openfda_withnames_80_20/combined_hetionet_openfda_train_with_names.csv'

hetionetkg='compare_train_test/hetionet_withnames_80_20/hetionet_train_with_names.csv'

import pandas as pd
combined= pd.read_csv(fusionho)
hetionetkg= pd.read_csv(hetionetkg)

import pandas as pd

# Optional: normalize names first (lowercase, remove spaces/underscores)
def normalize_name(name):
    return str(name).lower().replace("_", "").replace(" ", "")

hetionetkg['src_name_norm'] = hetionetkg['src_name'].apply(normalize_name)
hetionetkg['dst_name_norm'] = hetionetkg['dst_name'].apply(normalize_name)
combined['src_name_norm'] = combined['src_name'].apply(normalize_name)
combined['dst_name_norm'] = combined['dst_name'].apply(normalize_name)

# Drop duplicate edges in PrimeKG and Combined
hetionetkg_unique = hetionetkg.drop_duplicates(subset=['src_name_norm', 'dst_name_norm'])
combined_unique = combined.drop_duplicates(subset=['src_name_norm', 'dst_name_norm'])

# Define edges as unordered sets to ignore direction
hetionetkg_edges = set(frozenset([s, d]) for s, d in zip(hetionetkg_unique.src_name_norm, hetionetkg_unique.dst_name_norm))
combined_edges  = set(frozenset([s, d]) for s, d in zip(combined_unique.src_name_norm, combined_unique.dst_name_norm))

# Overlaps
common = hetionetkg_edges & combined_edges
missing_in_comb = hetionetkg_edges - combined_edges
extra_in_comb   = combined_edges - hetionetkg_edges

# Percentages
pct_preserved = len(common) / len(hetionetkg_edges) * 100 if hetionetkg_edges else 0
pct_missing   = len(missing_in_comb) / len(hetionetkg_edges) * 100 if hetionetkg_edges else 0
pct_extra     = len(extra_in_comb) / len(combined_edges) * 100 if combined_edges else 0

print(f"hetionetkg edges preserved in Combined (normalized, direction-agnostic, duplicates removed): {pct_preserved:.2f}%")
print(f"hetionetkg edges missing in Combined (normalized, direction-agnostic, duplicates removed): {pct_missing:.2f}%")
print(f"Extra edges only in Combined (normalized, direction-agnostic, duplicates removed): {pct_extra:.2f}%")

fusionho='compare_train_test/hetionet_openfda_withnames_80_20/combined_hetionet_openfda_train_with_names.csv'

openfdakg='compare_train_test/openfda_split_80_20_withnames/train_with_names.csv'

import pandas as pd
combined= pd.read_csv(fusionho)
openfdakg= pd.read_csv(openfdakg)

import pandas as pd

# Optional: normalize names first (lowercase, remove spaces/underscores)
def normalize_name(name):
    return str(name).lower().replace("_", "").replace(" ", "")

openfdakg['src_name_norm'] = openfdakg['src_name'].apply(normalize_name)
openfdakg['dst_name_norm'] = openfdakg['dst_name'].apply(normalize_name)
combined['src_name_norm'] = combined['src_name'].apply(normalize_name)
combined['dst_name_norm'] = combined['dst_name'].apply(normalize_name)

# Drop duplicate edges in PrimeKG and Combined
openfdakg_unique = openfdakg.drop_duplicates(subset=['src_name_norm', 'dst_name_norm'])
combined_unique = combined.drop_duplicates(subset=['src_name_norm', 'dst_name_norm'])

# Define edges as unordered sets to ignore direction
openfdakg_edges = set(frozenset([s, d]) for s, d in zip(openfdakg_unique.src_name_norm, openfdakg_unique.dst_name_norm))
combined_edges  = set(frozenset([s, d]) for s, d in zip(combined_unique.src_name_norm, combined_unique.dst_name_norm))

# Overlaps
common = openfdakg_edges & combined_edges
missing_in_comb = openfdakg_edges - combined_edges
extra_in_comb   = combined_edges - openfdakg_edges

# Percentages
pct_preserved = len(common) / len(openfdakg_edges) * 100 if openfdakg_edges else 0
pct_missing   = len(missing_in_comb) / len(openfdakg_edges) * 100 if openfdakg_edges else 0
pct_extra     = len(extra_in_comb) / len(combined_edges) * 100 if combined_edges else 0

print(f"openfdakg edges preserved in Combined (normalized, direction-agnostic, duplicates removed): {pct_preserved:.2f}%")
print(f"openfdakg edges missing in Combined (normalized, direction-agnostic, duplicates removed): {pct_missing:.2f}%")
print(f"Extra edges only in Combined (normalized, direction-agnostic, duplicates removed): {pct_extra:.2f}%")