# Customer Behavior Analysis

Master's dissertation — customer behavior analysis on the UCI Online Retail II dataset (UK, 2009–2011).

## RO

Proiect de disertație: analiza comportamentală a clienților unui magazin online — segmentare RFM + K-Means și market basket analysis (FP-Growth). Livrabile: notebook-uri Jupyter, pipeline reproductibil, dashboard Streamlit.

## EN

Dissertation project: customer behavior analysis for an online retailer — RFM scoring, K-Means segmentation, and market basket analysis (FP-Growth). Deliverables: Jupyter notebooks, reproducible pipeline, Streamlit dashboard.

## Dataset

UCI Online Retail II — download `online_retail_II.xlsx` and place it at `data/bronze/online_retail_II.xlsx`.

Data layers follow the medallion architecture:

- **`data/bronze/`** — raw source (`online_retail_II.xlsx`, raw concat parquet).
- **`data/silver/`** — cleaned and validated transactions.
- **`data/gold/`** — business-ready tables (RFM, segments, basket rules).

Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii

## Setup

```bash
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Conda alternative:

```bash
conda env create -f environment.yml
conda activate customer-behavior-analysis
```

> Notebook 06 (market basket) uses Spark MLlib FP-Growth via PySpark, which
> requires a **Java 17** runtime with `JAVA_HOME` set.

## Run

```bash
python scripts/run_pipeline.py all
streamlit run dashboard/app.py
```

## Conventions

- Code + comments: English.
- Thesis text + dashboard UI: Romanian.
- Currency: GBP throughout.
- Scope: UK transactions only.
- Snapshot date: 2011-12-10 (fixed).
- Random seed: 42.

## Implementation status

| Stage | Module | Notebook | Output | Done |
|---|---|---|---|---|
| Ingestion | `src/data.py` | `01_data_ingestion.ipynb` | `bronze/transactions_concat.parquet`, `silver/transactions_clean.parquet` | ✓ |
| EDA | — | `02_eda.ipynb` | `reports/figures/02_*.png`, `reports/tables/02_*.csv` | ✓ |
| RFM | `src/rfm.py` | `03_rfm_analysis.ipynb` | `gold/rfm_table.parquet` | ✓ |
| K-Means | `src/segmentation.py` | `04_kmeans_segmentation.ipynb` | `gold/customer_segments.parquet` | ✓ |
| Profiling | — | `05_segment_profiling.ipynb` | `gold/segment_summary.parquet`, `reports/figures/05_*.png`, `reports/tables/05_*.csv` | ✓ |
| Basket | `src/basket.py` | `06_market_basket.ipynb` | `gold/basket_rules.parquet` | ✓ |
| Dashboard | `dashboard/app.py` + pages | — | Streamlit app | — |
| Pipeline CLI | `scripts/run_pipeline.py` | — | — | — |
| Tests | `tests/` | — | — | — |

### Current data shape (post-cleaning)

- **5,336 UK customers** after the 9-step cleaning pipeline.
- **Snapshot date**: 2011-12-10.
- **RFM ranges**: Recency 0–738 days; Frequency 1–323 invoices; Monetary −£1,343 to £578,408 (median £814).
- **Traditional baseline segments**: Champions / Loyal / At Risk / Hibernating / Lost (assigned via R+F quintile rules).

## License

MIT — see [LICENSE](LICENSE).
