# ===============================
# 1) Imports
# ===============================
import pickle
import torch
import torch.nn.functional as F
from torch import nn
from torch_geometric.nn import RGCNConv
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score
from collections import defaultdict
import random
import numpy as np

import os, random, numpy as np, torch

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)
torch.backends.cudnn.deterministic = True   # ✅ make ops deterministic
torch.backends.cudnn.benchmark = False      # ✅ disable autotuning
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

# ===============================
# 2) Load Hetionet + PrimeKG Graph
# ===============================
pkl_path = "primekg_hetionet_combined.pkl"
with open(pkl_path, "rb") as f:
    G = pickle.load(f)
print(f"✅ Loaded graph with {len(G.nodes)} nodes and {len(G.edges)} edges.")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

# ===============================
# 3) Build Node & Edge Type Maps
# ===============================
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

# ===============================
# 4) Build Homogeneous Graph (Train-only edges)
# ===============================
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

    # Add train edges to global train graph
    for (s_local, d_local) in train_edges:
        all_src.append(type_offsets[src_type] + s_local)
        all_dst.append(type_offsets[dst_type] + d_local)
        all_rel.append(rel_id)

    edge_type_splits[etype] = {
        "train": torch.tensor([
            [type_offsets[src_type] + s for s, d in train_edges],
            [type_offsets[dst_type] + d for s, d in train_edges]
        ], dtype=torch.long),
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
print(f"Homogeneous train graph -> nodes: {num_nodes}, train edges: {edge_index.size(1)}")

# ===============================
# 5) Type-consistent Negative Sampling Setup
# ===============================
def build_pools_and_forbidden(edge_type_splits, node_type_map, type_offsets):
    rel_resources = {}
    for rel_key, splits in edge_type_splits.items():
        src_t, _, dst_t = rel_key
        src_pool = list(range(type_offsets[src_t], type_offsets[src_t] + len(node_type_map[src_t])))
        dst_pool = list(range(type_offsets[dst_t], type_offsets[dst_t] + len(node_type_map[dst_t])))
        all_edges = torch.cat([splits["train"], splits["val"], splits["test"]], dim=1)
        forbidden = set((int(s), int(d)) for s, d in zip(all_edges[0].tolist(), all_edges[1].tolist()))
        rel_resources[rel_key] = {"src_pool": src_pool, "dst_pool": dst_pool, "forbidden": forbidden}
    return rel_resources

def sample_type_consistent_negs(num_samples, src_pool, dst_pool, forbidden_set, device):
    src_pool_t = torch.tensor(src_pool, device=device)
    dst_pool_t = torch.tensor(dst_pool, device=device)
    neg_src, neg_dst = [], []
    while len(neg_src) < num_samples:
        s = src_pool_t[torch.randint(0, len(src_pool_t), (num_samples * 2,))]
        d = dst_pool_t[torch.randint(0, len(dst_pool_t), (num_samples * 2,))]
        pairs = [(int(si), int(di)) for si, di in zip(s, d)]
        filtered = [p for p in pairs if p not in forbidden_set]
        if len(filtered) > 0:
            ns = [p[0] for p in filtered][:num_samples - len(neg_src)]
            nd = [p[1] for p in filtered][:num_samples - len(neg_dst)]
            neg_src.extend(ns)
            neg_dst.extend(nd)
    return torch.tensor([neg_src, neg_dst], device=device)

rel_resources = build_pools_and_forbidden(edge_type_splits, node_type_map, type_offsets)

# ===============================
# 6) R-GCN Model Definition
# ===============================
class RGCN(nn.Module):
    def __init__(self, num_nodes, num_relations, emb_dim=64, hidden_dim=64, out_dim=64):
        super().__init__()
        self.emb = nn.Embedding(num_nodes, emb_dim)
        self.conv1 = RGCNConv(emb_dim, hidden_dim, num_relations=num_relations)
        self.conv2 = RGCNConv(hidden_dim, out_dim, num_relations=num_relations)

    def forward(self, node_ids, edge_index, edge_type):
        x = self.emb(node_ids)
        x = F.relu(self.conv1(x, edge_index, edge_type))
        x = self.conv2(x, edge_index, edge_type)
        return x

def edge_scores(z, eidx):
    return torch.sigmoid((z[eidx[0]] * z[eidx[1]]).sum(dim=-1))

# ===============================
# 7) Train R-GCN (Type-consistent negatives)
# ===============================
node_ids = torch.arange(num_nodes, device=device)
model = RGCN(num_nodes, num_relations).to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=0.005)
EPOCHS = 20

for epoch in range(1, EPOCHS + 1):
    model.train()
    optimizer.zero_grad()
    z = model(node_ids, edge_index.to(device), edge_type.to(device))
    pos_edges_all, neg_edges_all = [], []

    for rel_key, splits in edge_type_splits.items():
        pos_e = splits["train"].to(device)
        if pos_e.size(1) == 0:
            continue
        N = pos_e.size(1)
        neg_e = sample_type_consistent_negs(
            N,
            rel_resources[rel_key]["src_pool"],
            rel_resources[rel_key]["dst_pool"],
            rel_resources[rel_key]["forbidden"],
            device
        )
        pos_edges_all.append(pos_e)
        neg_edges_all.append(neg_e)

    pos_edges_all = torch.cat(pos_edges_all, dim=1)
    neg_edges_all = torch.cat(neg_edges_all, dim=1)
    pos_scores = edge_scores(z, pos_edges_all)
    neg_scores = edge_scores(z, neg_edges_all)
    loss = -(pos_scores + 1e-15).log().mean() - (1 - neg_scores + 1e-15).log().mean()
    loss.backward()
    optimizer.step()

    if epoch % 5 == 0 or epoch == 1:
        print(f"Epoch {epoch:02d} | Loss: {loss.item():.4f}")

# ===============================
# 8) Evaluation per Relation
# ===============================
model.eval()
results = []
with torch.no_grad():
    z = model(node_ids, edge_index.to(device), edge_type.to(device))
    for rel_key, splits in edge_type_splits.items():
        test_e = splits["test"].to(device)
        if test_e.size(1) == 0:
            continue
        N = test_e.size(1)
        neg_e = sample_type_consistent_negs(
            N,
            rel_resources[rel_key]["src_pool"],
            rel_resources[rel_key]["dst_pool"],
            rel_resources[rel_key]["forbidden"],
            device
        )
        y_true = torch.cat([torch.ones(N, device=device), torch.zeros(N, device=device)])
        scores = torch.cat([edge_scores(z, test_e), edge_scores(z, neg_e)])
        y = y_true.cpu().numpy()
        s = scores.cpu().numpy()
        auc = roc_auc_score(y, s)
        preds = (s > 0.5).astype(int)
        p = precision_score(y, preds, zero_division=0)
        r = recall_score(y, preds, zero_division=0)
        f1 = f1_score(y, preds, zero_division=0)
        results.append((rel_key, auc, p, r, f1))
        print(f"{rel_key}: AUC={auc:.4f}, P={p:.3f}, R={r:.3f}, F1={f1:.3f}")

# ===============================
# 9) Overall Evaluation
# ===============================
all_pos, all_neg = [], []
with torch.no_grad():
    for rel_key, splits in edge_type_splits.items():
        test_e = splits["test"].to(device)
        if test_e.size(1) == 0:
            continue
        N = test_e.size(1)
        neg_e = sample_type_consistent_negs(
            N,
            rel_resources[rel_key]["src_pool"],
            rel_resources[rel_key]["dst_pool"],
            rel_resources[rel_key]["forbidden"],
            device
        )
        all_pos.append(test_e)
        all_neg.append(neg_e)

all_pos = torch.cat(all_pos, dim=1)
all_neg = torch.cat(all_neg, dim=1)
with torch.no_grad():
    scores_pos = edge_scores(z, all_pos)
    scores_neg = edge_scores(z, all_neg)

y_true = torch.cat([
    torch.ones(scores_pos.numel(), device=device),
    torch.zeros(scores_neg.numel(), device=device)
])
scores_all = torch.cat([scores_pos, scores_neg], dim=0)
preds = (scores_all > 0.5).int()

auc_overall = roc_auc_score(y_true.cpu().numpy(), scores_all.cpu().numpy())
p_overall = precision_score(y_true.cpu().numpy(), preds.cpu().numpy(), zero_division=0)
r_overall = recall_score(y_true.cpu().numpy(), preds.cpu().numpy(), zero_division=0)
f1_overall = f1_score(y_true.cpu().numpy(), preds.cpu().numpy(), zero_division=0)

print("\n🌍 Overall performance across all relations:")
print(f"AUC={auc_overall:.4f}, Precision={p_overall:.3f}, Recall={r_overall:.3f}, F1={f1_overall:.3f}")
