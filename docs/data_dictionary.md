# Data Dictionary — UCI Online Retail II

Source: https://archive.ics.uci.edu/dataset/502/online+retail+ii

Two sheets — `Year 2009-2010` and `Year 2010-2011` — share the same schema.

| Column | Type | Description |
|---|---|---|
| `Invoice` | string | Invoice number. Prefix `C` marks a cancellation/return. |
| `StockCode` | string | Product (item) code. |
| `Description` | string | Product name. |
| `Quantity` | int | Units per transaction. Negative for returns. |
| `InvoiceDate` | datetime | Invoice timestamp. |
| `Price` | float | Unit price in GBP. |
| `Customer ID` | float | Customer identifier (~25% null). |
| `Country` | string | Customer country. Project keeps only `United Kingdom`. |

Derived columns:

| Column | Source | Definition |
|---|---|---|
| `Revenue` | `Quantity * Price` | Signed: positive for purchases, negative for returns. |
