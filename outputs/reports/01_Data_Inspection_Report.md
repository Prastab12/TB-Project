# Data Inspection Report & Dataset Catalog

**Assessment Date:** 2026-06-04  
**Dataset:** `Original Final_KTM_data_set.xlsx`  
**Scope:** Kathmandu District, Bagmati Province, Nepal  

---

## 1. File Inventory

| File Name | Format | Size (MB) | Sheet(s) | Status |
| :--- | :--- | :--- | :--- | :--- |
| `Original Final_KTM_data_set.xlsx` | Excel (.xlsx) | 0.02 | Monthly Summary | Source Raw |

---

## 2. Dataset Structure

- **Rows:** 60  (data rows; TOTAL summary row excluded during ingestion)
- **Columns:** 34
- **Duplicate Rows:** 0
- **Schema Consistency:** Single flat file — column schema is 100% consistent across all 60 months.
- **Note:** `Quarter` and `District` columns are not present in this dataset. `Quarter` will be derived from `BS_Month` during Phase 2 cleaning. `District` is fixed as Kathmandu throughout.

**Column Schema:**

| # | Column | Dtype |
| :--- | :--- | :--- |
| 0 | `BS_Month` | `object` |
| 1 | `BS_Year` | `float64` |
| 2 | `AD_Year` | `float64` |
| 3 | `District Pop (Mid-Year CBS)` | `float64` |
| 4 | `New Cases (Total)` | `int64` |
| 5 | `New Cases Female` | `float64` |
| 6 | `New Cases Male` | `float64` |
| 7 | `Relapse Female` | `float64` |
| 8 | `Relapse Male` | `float64` |
| 9 | `Total TB Female` | `float64` |
| 10 | `Total TB Male` | `float64` |
| 11 | `PBC Reg *` | `int64` |
| 12 | `Cured *` | `int64` |
| 13 | `Failed *` | `int64` |
| 14 | `Died *` | `int64` |
| 15 | `LTFU *` | `int64` |
| 16 | `Not Eval *` | `int64` |
| 17 | `TB-HIV +ve` | `int64` |
| 18 | `0 to 4 F` | `float64` |
| 19 | `0 to 4 M` | `float64` |
| 20 | `5 to 14 F` | `float64` |
| 21 | `5 to 14 M` | `float64` |
| 22 | `15 to 24 F` | `float64` |
| 23 | `15 to 24 M` | `float64` |
| 24 | `25 to 34 F` | `float64` |
| 25 | `25 to 34 M` | `float64` |
| 26 | `35 to 44 F` | `float64` |
| 27 | `35 to 44 M` | `float64` |
| 28 | `45 to 54 F` | `float64` |
| 29 | `45 to 54 M` | `float64` |
| 30 | `55 to 64 F` | `float64` |
| 31 | `55 to 64 M` | `float64` |
| 32 | `65+ F` | `float64` |
| 33 | `65+ M` | `float64` |

---

## 3. Coverage Profile

| Attribute | Value |
| :--- | :--- |
| District | Kathmandu |
| BS Years | [2078, 2079, 2080, 2081, 2082] |
| Total Months | 60 |
| Months with Sex / Age Data | 57 |
| Months without Sex / Age Data | 3 (Baishak, Jestha, Asar 2078) |

**Monthly Coverage by BS Year:**

| BS Year | Month Count |
| :--- | :--- |
| 2078 | 12 |
| 2079 | 12 |
| 2080 | 12 |
| 2081 | 12 |
| 2082 | 12 |

**Population Denominator (Annual CBS Mid-Year):**

| BS Year | Population |
| :--- | :--- |
| 2078 | 2,049,618 |
| 2079 | 2,087,199 |
| 2080 | 2,122,517 |
| 2081 | 2,156,070 |
| 2082 | 2,188,035 |

---

## 4. Missing Values Profile

| Column | Missing | % Missing | Cause |
| :--- | :--- | :--- | :--- |
| `New Cases Female` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `New Cases Male` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `Relapse Female` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `Relapse Male` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `Total TB Female` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `Total TB Male` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `0 to 4 F` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `0 to 4 M` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `5 to 14 F` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `5 to 14 M` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `15 to 24 F` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `15 to 24 M` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `25 to 34 F` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `25 to 34 M` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `35 to 44 F` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `35 to 44 M` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `45 to 54 F` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `45 to 54 M` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `55 to 64 F` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `55 to 64 M` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `65+ F` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |
| `65+ M` | 3 | 5.0% | Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source |

---

## 5. Data Source Notes

- **Validated columns:** New Cases (Total), New Cases Female/Male, all 16 age-sex band columns — the 16 bands sum exactly to New Cases (Total) in all 57 months.
- **Provisional columns:** Relapse Female, Relapse Male, Total TB Female, Total TB Male — may carry ±1–4 errors in ~25 months. Confirm against source file before sex-disaggregated relapse analysis.
- **Outcome columns (*):** PBC New cohort data — recent months may be incomplete as cohorts need ~12 months to mature.
- **Quarter:** Not present in raw file — will be derived in Phase 2 from BS_Month (Q1=Shrawan-Ashwin, Q2=Kartik-Poush, Q3=Magh-Chaitra, Q4=Baishak-Asar).