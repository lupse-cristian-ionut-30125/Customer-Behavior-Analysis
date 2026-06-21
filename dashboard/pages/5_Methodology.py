"""Methodology page."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

import components as C

st.title("Methodology")

st.markdown(
    f"""
This dashboard summarizes a customer-behavior analysis of the
**UCI Online Retail II** dataset (a UK online retailer, Dec 2009 – Dec 2011).

### Data pipeline (medallion architecture)
- **Bronze** — raw Excel, concatenated across both sheets.
- **Silver** — cleaned transactions: missing customers dropped, positive prices
  only, utility stock codes excluded, **UK-only**, deduplicated
  ({len(C.load_transactions()):,} rows).
- **Gold** — business-ready tables: RFM, K-Means segments, basket rules.

### RFM scoring
- **Recency** — days since last purchase relative to the snapshot
  ({C.SETTINGS['snapshot_date']}).
- **Frequency** — number of distinct purchase invoices (returns excluded).
- **Monetary** — total signed revenue (returns reduce the total).
- Each dimension is scored into quintiles (1–5); a rule-based baseline
  assigns Champions / Loyal / At Risk / Hibernating / Lost.

### K-Means segmentation
- Features: RFM after a signed-log transform and standardization.
- **k = {C.SETTINGS['kmeans']['chosen_k']}**, selected by triangulating the
  elbow with the silhouette, Davies-Bouldin, and Calinski-Harabasz indices,
  weighting business interpretability.
- Clusters are labeled by ranking their RFM centroids on a composite value score.

### Market basket analysis
- **Spark MLlib FP-Growth** (parallel FP-Growth, Li et al., 2008) over UK
  purchase baskets, with min support {C.SETTINGS['basket']['min_support']},
  min confidence {C.SETTINGS['basket']['min_confidence']}.
- *Lift* > 1 marks products co-purchased more than chance.

### Reproducibility
- Fixed random seed ({C.SETTINGS['seed']}); deterministic preprocessing.
- One-command rebuild: `python scripts/run_pipeline.py all`.

### Key references
- Hughes, A. M. (1994). *Strategic Database Marketing.*
- Chen, D., Sain, S. L., & Guo, K. (2012). Data mining for the online retail
  industry (RFM + K-Means).
- Agrawal, R., & Srikant, R. (1994). Fast algorithms for mining association rules.
- Han, J., Pei, J., & Yin, Y. (2000). Mining frequent patterns without candidate
  generation (FP-Growth).
- Li, H., et al. (2008). PFP: Parallel FP-Growth for query recommendation.
"""
)
