# Plan: Disertație — Analiza comportamentală a clienților unui magazin online

## Context

Proiect de disertație (Master) — analiză comportamentală a clienților unui magazin online: identificarea tiparelor, segmentarea clienților și evidențierea factorilor care influențează decizia de cumpărare. Directorul de lucru este gol — totul se construiește de la zero.

**Decizii confirmate:**
- **Dataset**: UCI Online Retail II (~1M tranzacții reale, UK retailer 2009–2011) — standard academic, citat în literatură.
- **Scop geografic**: doar UK (91% din tranzacții; eliminăm zgomotul, justificare metodologică simplă).
- **Tehnici**: RFM scoring + segmentare K-Means + **market basket analysis** (Apriori/FP-Growth). Basket-ul răspunde direct cerinței "factori care influențează decizia de cumpărare".
- **Stack**: Python (pandas, scikit-learn, mlxtend, plotly, seaborn).
- **Livrabile**: notebook-uri Jupyter (pipeline de analiză) + dashboard Streamlit (demo de susținere) + figuri/tabele exportate pentru lucrarea scrisă.
- **Limbă**: lucrare + dashboard în română; cod + commenturi în engleză (standard de facto).
- **Monedă**: GBP păstrat în toate cifrele; eventuala conversie EUR/RON menționată ca footnote.

**Rezultat așteptat**: pipeline reproductibil + dashboard demonstrabil + 5–6 figuri și tabele cheie pentru capitolele de metodologie și rezultate.

---

## Structura proiectului

```
comportamental-behavior-clients/
├── .gitignore                         # data/raw/*.xlsx, data/processed/*, .ipynb_checkpoints, __pycache__, .venv
├── README.md                          # ro + en, instrucțiuni reproducere
├── LICENSE                            # MIT
├── requirements.txt
├── environment.yml                    # alternativă conda
├── pyproject.toml                     # black, ruff, pytest config
├── config/
│   └── settings.yaml                  # snapshot_date, k_range, seed, paths, country_filter
├── data/
│   ├── raw/online_retail_II.xlsx      # gitignored; descărcat manual din UCI
│   ├── interim/transactions_concat.parquet
│   └── processed/
│       ├── transactions_clean.parquet
│       ├── rfm_table.parquet
│       └── customer_segments.parquet
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_rfm_analysis.ipynb
│   ├── 04_kmeans_segmentation.ipynb
│   ├── 05_segment_profiling.ipynb
│   └── 06_market_basket.ipynb
├── src/
│   ├── __init__.py
│   ├── config.py                      # încarcă settings.yaml
│   ├── data.py                        # ingestion + curățare
│   ├── rfm.py                         # R/F/M + quintile scoring
│   ├── segmentation.py                # K-Means + evaluare k
│   ├── basket.py                      # Apriori / FP-Growth
│   ├── viz.py                         # helpers de plotting (stil unitar)
│   └── io_utils.py                    # parquet, export LaTeX
├── scripts/
│   └── run_pipeline.py                # CLI: ingest → rfm → segment → basket
├── tests/
│   ├── test_data.py
│   ├── test_rfm.py
│   └── test_segmentation.py
├── dashboard/
│   ├── app.py                         # pagină Overview + sidebar
│   ├── pages/
│   │   ├── 1_RFM_Distribution.py
│   │   ├── 2_Segment_Profiling.py
│   │   ├── 3_Segment_Drilldown.py
│   │   └── 4_Methodology.py
│   └── components.py
├── reports/
│   ├── figures/                       # 300 dpi PNG + PDF vectorial
│   └── tables/                        # CSV + LaTeX booktabs
└── docs/
    └── data_dictionary.md
```

---

## Pipeline de analiză (notebook-uri)

| # | Notebook | Conținut | Output |
|---|---|---|---|
| 01 | `01_data_ingestion.ipynb` | Încărcare 2 sheets (`Year 2009-2010`, `Year 2010-2011`), concat, inspecție schemă, salvare parquet | `transactions_concat.parquet` |
| 02 | `02_eda.ipynb` | Trenduri temporale, top 20 produse, distribuție pe țări, rata returnărilor, sezonalitate (lună / zi din săptămână) | 8–10 figuri |
| 03 | `03_rfm_analysis.ipynb` | Calcul R/F/M, distribuții raw + log, scoring quintile, segmente tradiționale ca baseline | `rfm_table.parquet` + 4–5 figuri |
| 04 | `04_kmeans_segmentation.ipynb` | Preprocesare (log + StandardScaler), elbow + silhouette + Davies-Bouldin + Calinski-Harabasz pentru k∈[2..10], fit final, scatter 3D + proiecție PCA | `customer_segments.parquet` + 5–6 figuri |
| 05 | `05_segment_profiling.ipynb` | Denumire clustere (Champions, Loyal, At Risk, Hibernating, Lost), stats descriptive, comparare K-Means vs quintile, top produse / țări per segment | Tabel CSV + LaTeX, 6–8 figuri |
| 06 | `06_market_basket.ipynb` | Encoding coș, FP-Growth (`min_support=0.02`, `min_confidence=0.3`, `lift > 1`), top 20 reguli, network graph | Reguli CSV + LaTeX, 2–3 figuri |

---

## Module Python — semnături cheie

### `src/data.py`
Ordine curățare (documentată în docstring + EDA notebook):
1. concat două sheets
2. strip whitespace + uppercase pe `StockCode` și `Description`
3. drop unde `Customer ID` e null (doar pentru RFM)
4. drop unde `Price <= 0`
5. exclude StockCode-uri non-produs: `POST`, `M`, `BANK CHARGES`, `D`, `DOT`, `CRUK`, `AMAZONFEE`, `S`, `TEST001`, `TEST002`, `B`, `PADS`, `gift_*`
6. filtru țară: `Country == "United Kingdom"`
7. drop duplicates
8. adaugă coloana `Revenue = Quantity * Price` (păstrează semnul pentru returnări)
9. log row counts înainte/după fiecare pas

```python
def load_raw(xlsx_path: Path) -> pd.DataFrame: ...
def clean_transactions(df, *, drop_missing_customer=True, excluded_stockcodes=(), country_filter="United Kingdom") -> pd.DataFrame: ...
def split_purchases_returns(df) -> tuple[pd.DataFrame, pd.DataFrame]: ...
def add_revenue(df) -> pd.DataFrame: ...
```

### `src/rfm.py`
- **Snapshot date**: `max(InvoiceDate) + timedelta(days=1) = 2011-12-10` (fix; nu folosim `today()`).
- **Recency**: zile (int) între snapshot și ultima cumpărare.
- **Frequency**: număr de invoice-uri unice (NU linii de comandă).
- **Monetary**: sumă `Revenue` (cumpărări − returnări).

```python
def compute_rfm(df, snapshot_date) -> pd.DataFrame: ...
def score_rfm_quintiles(rfm) -> pd.DataFrame:  # adaugă R_score, F_score, M_score (1..5) + RFM_score
def assign_traditional_segments(rfm_scored) -> pd.DataFrame: ...
```

### `src/segmentation.py`
```python
def preprocess_for_kmeans(rfm, log_transform=True, scaler="standard") -> tuple[np.ndarray, BaseEstimator]: ...
def evaluate_k(X, k_range, seed) -> pd.DataFrame:  # inertia, silhouette, davies_bouldin, calinski_harabasz
def fit_kmeans(X, k, seed) -> KMeans: ...
def assign_clusters(rfm, model, X) -> pd.DataFrame: ...
def label_clusters(rfm_with_clusters, centroids_unscaled) -> dict[int, str]: ...
```

### `src/basket.py`
```python
def build_basket_matrix(df, invoice_col="Invoice", item_col="Description") -> pd.DataFrame: ...
def mine_rules(basket, min_support=0.02, min_confidence=0.3, min_lift=1.0, algorithm="fpgrowth") -> pd.DataFrame: ...
def top_rules(rules, by="lift", n=20) -> pd.DataFrame: ...
```

### `src/viz.py`
Stil unitar setat o singură dată: `seaborn.set_theme(style="whitegrid", context="paper", font_scale=1.1)`, paletă `viridis` (colorblind-safe), export 300 dpi PNG + PDF vectorial.

---

## Pitfalls cheie pentru UCI Online Retail II (de tratat explicit)

1. **Două sheets** — concat obligatoriu.
2. **~25% null `Customer ID`** — drop pentru RFM, păstrare pentru EDA produs/basket dacă e relevant.
3. **Returnări** (`Invoice` începe cu `C`, `Quantity < 0`): scădere din Monetary, NU contează la Frequency; filtrate la basket.
4. **`Price <= 0`**, **StockCode-uri non-produs**, **duplicate exacte** — toate eliminate, listate.
5. **GBP** — declarat explicit în README + thesis.
6. **Snapshot date fix** la 2011-12-10 — nu `today()`.
7. **Outlieri Monetary**: log-transform pentru K-Means; pentru vizualizare se poate winsoriza la P99, dar fără să fie scoși din model.

---

## Dashboard Streamlit (5 pagini, ≤5 min walk-through)

1. **Overview** — KPI tiles + revenue over time (`app.py`).
2. **RFM Distribution** — histograme R/F/M (log pentru M) + scatter 3D colorat pe cluster.
3. **Segment Profiling** — bar chart mărimi clustere + heatmap z-scores + tabel etichetat (pagina-vedetă).
4. **Segment Drill-down** — dropdown segment → top clienți + top produse + distribuție țări.
5. **Methodology** — pagină statică cu snapshot date, k ales, silhouette, pași preprocesare.

Dashboard-ul citește **doar** `data/processed/*.parquet` (nu recalculează). Lipsește un parquet? `st.error("Rulează `python scripts/run_pipeline.py all` mai întâi.")`.

Anti-features (NU se construiesc): autentificare, scoring în timp real, backend DB, hartă (UK domină oricum).

---

## Bibliografie cheie

- **Chen, D., Sain, S. L., & Guo, K. (2012).** "Data mining for the online retail industry: A case study of RFM model-based customer segmentation." *Journal of Database Marketing & Customer Strategy Management*, 19(3), 197–208. — **Must-cite** (folosește exact predecessor-ul acestui dataset).
- **Hughes, A. M. (1994).** *Strategic Database Marketing*. Probus Publishing. — Origine RFM.
- **Christy, A. J. et al. (2021).** "RFM ranking — An effective approach to customer segmentation." *J. King Saud University CIS*, 33(10), 1251–1257.
- **Bult & Wansbeek (1995).** "Optimal Selection for Direct Mail." *Marketing Science*, 14(4).
- **Arthur & Vassilvitskii (2007).** "k-means++". SODA '07. — Justifică `init='k-means++'`.
- **Rousseeuw (1987).** "Silhouettes." *J. Comp. Appl. Math*, 20, 53–65.
- **Agrawal & Srikant (1994).** "Fast algorithms for mining association rules." VLDB. — Pentru basket.
- Cel puțin **3 surse în română** din ASE / UBB / FEAA / Revista Română de Statistică pe segmentare sau retail analytics.

---

## Fișiere critice (ordine de implementare)

1. `src/data.py` — fundație; orice greșeală aici se propagă peste tot.
2. `src/rfm.py` — miezul metodologic; corectitudinea definițiilor R/F/M e non-negociabilă.
3. `src/segmentation.py` — al doilea miez metodologic.
4. `notebooks/04_kmeans_segmentation.ipynb` — narativa care devine Capitolul 4 al lucrării.
5. `dashboard/app.py` — artefactul vizibil la susținere.

Secvențiere ~3–4 săptămâni part-time:
- **Z1**: scaffold (config, requirements, .gitignore, README, descărcat dataset).
- **Z2–3**: `data.py` + nb 01–02 + `test_data.py`.
- **Z4–5**: `rfm.py` + nb 03 + `test_rfm.py`.
- **Z6–8**: `segmentation.py` + nb 04 + `test_segmentation.py`.
- **Z9–10**: nb 05 (profiling) + export figuri/tabele.
- **Z11–12**: `basket.py` + nb 06.
- **Z13–15**: dashboard Streamlit.
- **Z16–17**: `scripts/run_pipeline.py`, smoke test complet de la zero.

---

## Verificare end-to-end

**Pipeline**:
```bash
python scripts/run_pipeline.py all
streamlit run dashboard/app.py
```
Trebuie să regenereze toate artefactele din `data/raw/online_retail_II.xlsx` și să pornească dashboard-ul.

**Calitate date**:
- Row counts logate la fiecare pas de curățare, totaluri reconciliate.
- Snapshot date = 2011-12-10 documentat în config + README + thesis §3.2.
- Country = UK declarat explicit; GBP declarat explicit.

**RFM**:
- Distribuții R/F/M plotate raw + log.
- Quintile cu `pd.qcut(..., duplicates='drop')` (gestionează tie-uri).

**K-Means**:
- 4 metrici de validitate raportate (inertia, silhouette, DB, CH).
- k ales pe baza combinației elbow + silhouette (nu pe un singur criteriu).
- Seed fix declarat (42).
- Nume clustere justificate din valorile centroidelor.

**Basket**:
- `min_support`, `min_confidence`, `min_lift` declarate și justificate.
- Top 20 reguli prezentate ca tabel în lucrare.

**Engineering**:
- `pytest` trece (6–10 teste).
- `ruff check` + `black --check` trec.
- Streamlit pornește pe o mașină curată doar cu `requirements.txt`.
- Toate figurile exportate la 300 dpi PNG + PDF vectorial.
- Toate tabelele exportate ca CSV + LaTeX booktabs.

**Academic**:
- ≥15 referințe, mix EN + RO (cel puțin 3 RO).
- Chen et al. (2012) și Hughes (1994) citate obligatoriu.
- Capitol de limitări: date UK-centric, fără features demografice, snapshot bias, asumpții K-Means (clustere sferice, varianță egală).
