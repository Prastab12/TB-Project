# Data Inspection Report & Dataset Catalog

## 1. File Inventory Table

| File Name | Format | Size (MB) | Sheet Name(s) | Encoding | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Data.xlsx` | Excel (.xlsx) | 0.14 | `Data Set` | Standard Excel | Source Raw |
| `cleaned_data.csv` | CSV (.csv) | ~0.15 | N/A | UTF-8 | Cleaned |

---

## 2. Dataset Catalog & Structural Inspection

### 2.1 General Schema & Structure
*   **Total Rows:** 780 (After removing 60 'BAGMATI PROVINCE' aggregate rows)
*   **Total Columns:** 30
*   **Duplicate Rows:** 0 (Clean!)
*   **Schema Consistency:** Because all data from all years is unified into a single flat file, there are no missing, extra, or renamed columns between years. The schema is 100% consistent across the timeline.
*   **Malformed Rows:** The raw file contained 2 header/metadata rows. This was resolved during ingestion.

### 2.2 Coverage Profile
*   **Fiscal Year Coverage:** 5 Years (BS 2078, 2079, 2080, 2081, 2082)
*   **District Coverage:** 13 distinct true districts are covered.
*   **Monthly Completeness:** All 12 months for each of the 5 years are represented (60 unique months total).

### 2.3 Specific Task Checks
*   **Vaccine Columns:** None detected. There are no columns indicating vaccine doses or coverage in this specific dataset.
*   **Data Types:** Strong consistency.
    *   15 `float64` (Metrics, percentages)
    *   10 `int64` (Outcomes, total counts)
    *   5 `object` (Strings: District names, quarters, months)

### 2.4 Missing Values Profile

| Column | Missing Count | Actions / Notes |
| :--- | :--- | :--- |
| `art_cov_pct` | 312 | Significant absence. May affect downstream HIV/TB correlation metrics. |
| `m_to_f_ratio` | 133 | Derived field; can potentially be recalculated if raw M/F counts exist. |
| `male_pct_new`, `female_pct_new` | 103 | Derived fields. |
| `new_cases_female`, `new_cases_male` | 99 | Gender disaggregation missing for ~12% of data. |
| `relapse_female`, `relapse_male` | 99 | Gender disaggregation missing. |
| `total_tb_female`, `total_tb_male` | 99 | Gender disaggregation missing. |
| `tb_hiv_pct`, `xpert_cov_pct` | 60 | Lab testing / comorbidity coverage missing. |
| `new_cases_total`, `relapse_total`, `total_tb_m+f` | 39 | Primary outcome counts missing in ~5% of rows. |
