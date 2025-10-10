# 🧬 Biomedical Knowledge Graph Integration and Link Prediction

## 📘 Abstract

Biomedical knowledge graphs (KGs) are essential for representing complex relationships in drug discovery and precision medicine. Yet, individual KGs often suffer from sparsity and limited relational scope, reducing their effectiveness in link prediction tasks.

To overcome these limitations, a **unified biomedical KG** was constructed by integrating **Hetionet**, **PrimeKG**, and a newly created **OpenFDA KG**. The integrated graph was benchmarked against its individual components using both **classical models**—including **XGBoost**—and **graph neural networks (GNNs)** such as **Relational Graph Convolutional Networks (R-GCN)** and **Graph Attention Networks (GAT)**.

The results yield three key insights:

1. **GNNs benefit from denser graphs**, as relational information increases—but excessive complexity leads to diminishing returns due to structural overload.
2. **Classical models** (XGBoost, Feedforward Neural Networks) excel in binary link prediction but struggle with relational semantics. **GNNs**, conversely, better distinguish link types, though their margin of improvement is moderate.
3. **Model accuracy saturates** beyond a certain data scale, after which more information can reduce performance.

These findings indicate that **schema-aligned KG integration** not only enhances biomedical link prediction but also clarifies the conditions under which GNNs outperform alternative models.

---

## 🗷️ Repository Structure

```
GRAPH-NEURAL-NETWORKS-REASONING-ADVANTAGES-SHORTCOMINGS-AND-POTENTIAL/
│
└── src/
    ├── code/
    │   └── data_downloader/           # Scripts to fetch and preprocess KG data
    │
    └── knowledge_graphs/
        ├── Combined_Graphs/           # Unified Hetionet + PrimeKG + OpenFDA graph
        │                ├── Hetionet+openfda/
        │                ├── hetionet+openfda+primekg/
        │                ├── primekg+hetionet/
        ├── hetionet/                  # Original Hetionet dataset
        ├── openfda/                   # Newly created OpenFDA KG
        └── primekg/                   # PrimeKG biomedical knowledge graph
│
├── .gitignore
├── .gitkeep
└── README.md                          
```


---

## ⚙️ Installation

### Requirements

Python ≥ 3.9

Install dependencies:

```bash
pip install torch torch-geometric xgboost scikit-learn pandas numpy matplotlib networkx tqdm ollama
```


---

## 🧠 Key Insights

* **Integration** of Hetionet, PrimeKG, and OpenFDA improves predictive coverage and cross-domain reasoning.
* **GNNs** are effective when graph richness is high; **XGBoost** dominates  binary setups.
* **Graph fusion** amplifies interpretability and exposes limits of model scalability.

---

## 📚 Citation

If you use this repository or the unified biomedical KG, please cite:


> - [PrimeKG Paper](https://www.nature.com/articles/s41597-023-01960-3)


---

## 📧 Contact

**Dinesh Chandra Gaddam**
📩 [dineshchandra.gaddam@gwu.edu](mailto:dineshchandra.gaddam@gwu.edu)
📩 [g.boini@gwu.edu](mailto:g.boini@gwu.edu)
Department of CCAS, George Washington University

---

## 🧾 License

Released under the **MIT License**.




