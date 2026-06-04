# TB Project: Data Dictionary

**Dataset:** `Original Final_KTM_data_set.xlsx`  
**Date:** 2026-06-04  
**Sheet:** Monthly Summary — 60 rows, 34 columns  

---

## Columns

| # | Column Name | Dtype | Description |
| :--- | :--- | :--- | :--- |
| 0 | `BS_Month` | `object` | Month of reporting in Bikram Sambat (e.g., Baishak, Shrawan) |
| 1 | `BS_Year` | `float64` | Bikram Sambat year (e.g., 2078, 2079) |
| 2 | `AD_Year` | `float64` | Corresponding Gregorian calendar year (e.g., 2021, 2022). Rule: Baishak–Poush = BS_Year − 57; Magh–Chaitra = BS_Year − 56. |
| 3 | `District Pop (Mid-Year CBS)` | `float64` | Annual mid-year population estimate from Central Bureau of Statistics. Constant within each BS year. Used as denominator for notification rates. |
| 4 | `New Cases (Total)` | `int64` | Total incident (new) TB cases — source: TB-Age group-All New |
| 5 | `New Cases Female` | `float64` | New TB cases — Female; sum of 8 age bands. NaN for Baishak/Jestha/Asar 2078. |
| 6 | `New Cases Male` | `float64` | New TB cases — Male; sum of 8 age bands. NaN for Baishak/Jestha/Asar 2078. |
| 7 | `Relapse Female` | `float64` | Relapse TB cases — Female. PROVISIONAL — verify against source before use. |
| 8 | `Relapse Male` | `float64` | Relapse TB cases — Male. PROVISIONAL — verify against source before use. |
| 9 | `Total TB Female` | `float64` | Total TB cases Female (New + Relapse Female). PROVISIONAL. |
| 10 | `Total TB Male` | `float64` | Total TB cases Male (New + Relapse Male). PROVISIONAL. |
| 11 | `PBC Reg *` | `int64` | PBC New cohort registered cases — denominator for treatment outcome rates. |
| 12 | `Cured *` | `int64` | Treatment outcome: successfully cured (PBC New cohort). |
| 13 | `Failed *` | `int64` | Treatment outcome: treatment failed (PBC New cohort). |
| 14 | `Died *` | `int64` | Treatment outcome: died during treatment (PBC New cohort). |
| 15 | `LTFU *` | `int64` | Treatment outcome: Lost to Follow-Up (PBC New cohort). |
| 16 | `Not Eval *` | `int64` | Treatment outcome: not evaluated (PBC New cohort). |
| 17 | `TB-HIV +ve` | `int64` | Count of TB patients with confirmed HIV co-infection. |
| 18 | `0 to 4 F` | `float64` | New TB cases — Female, age group 0 to 4. NaN for Baishak/Jestha/Asar 2078. |
| 19 | `0 to 4 M` | `float64` | New TB cases — Male, age group 0 to 4. NaN for Baishak/Jestha/Asar 2078. |
| 20 | `5 to 14 F` | `float64` | New TB cases — Female, age group 5 to 14. NaN for Baishak/Jestha/Asar 2078. |
| 21 | `5 to 14 M` | `float64` | New TB cases — Male, age group 5 to 14. NaN for Baishak/Jestha/Asar 2078. |
| 22 | `15 to 24 F` | `float64` | New TB cases — Female, age group 15 to 24. NaN for Baishak/Jestha/Asar 2078. |
| 23 | `15 to 24 M` | `float64` | New TB cases — Male, age group 15 to 24. NaN for Baishak/Jestha/Asar 2078. |
| 24 | `25 to 34 F` | `float64` | New TB cases — Female, age group 25 to 34. NaN for Baishak/Jestha/Asar 2078. |
| 25 | `25 to 34 M` | `float64` | New TB cases — Male, age group 25 to 34. NaN for Baishak/Jestha/Asar 2078. |
| 26 | `35 to 44 F` | `float64` | New TB cases — Female, age group 35 to 44. NaN for Baishak/Jestha/Asar 2078. |
| 27 | `35 to 44 M` | `float64` | New TB cases — Male, age group 35 to 44. NaN for Baishak/Jestha/Asar 2078. |
| 28 | `45 to 54 F` | `float64` | New TB cases — Female, age group 45 to 54. NaN for Baishak/Jestha/Asar 2078. |
| 29 | `45 to 54 M` | `float64` | New TB cases — Male, age group 45 to 54. NaN for Baishak/Jestha/Asar 2078. |
| 30 | `55 to 64 F` | `float64` | New TB cases — Female, age group 55 to 64. NaN for Baishak/Jestha/Asar 2078. |
| 31 | `55 to 64 M` | `float64` | New TB cases — Male, age group 55 to 64. NaN for Baishak/Jestha/Asar 2078. |
| 32 | `65+ F` | `float64` | New TB cases — Female, age group 65+. NaN for Baishak/Jestha/Asar 2078. |
| 33 | `65+ M` | `float64` | New TB cases — Male, age group 65+. NaN for Baishak/Jestha/Asar 2078. |

---

## Column Group Summary

| Group | Columns | Notes |
| :--- | :--- | :--- |
| Time identifiers | BS_Month, BS_Year, AD_Year | Quarter absent — derived in Phase 2 |
| Population | District Pop (Mid-Year CBS) | Annual CBS figure; constant within each BS year |
| New TB cases | New Cases (Total/Female/Male) | Female/Male validated against 16 age bands |
| Relapse | Relapse Female, Relapse Male | PROVISIONAL — ±1–4 errors in ~25 months |
| Total TB | Total TB Female, Total TB Male | PROVISIONAL — New + Relapse by sex |
| Treatment outcomes | PBC Reg *, Cured *, Failed *, Died *, LTFU *, Not Eval * | PBC New cohort; recent months may be incomplete |
| TB-HIV | TB-HIV +ve | Raw count of HIV co-infected TB patients |
| Age-sex bands | 0 to 4 F/M through 65+ F/M (16 cols) | New cases only; NaN for first 3 months |

---

## Notes

- `*` suffix = PBC (Pulmonary Bacteriologically Confirmed) New cohort.
- **PROVISIONAL** columns: Relapse Female, Relapse Male, Total TB Female, Total TB Male.
- Age-sex bands apply to **new cases only** — not relapse.
- First 3 months (Baishak, Jestha, Asar 2078): NaN in all sex and age columns — structural source gap.
- **Quarter** is not present in the raw file. It will be added in Phase 2 using: Q1 = Shrawan/Bhadra/Ashwin, Q2 = Kartik/Mangsir/Poush, Q3 = Magh/Falgun/Chaitra, Q4 = Baishak/Jestha/Asar.
- **District** is not present in the raw file. Fixed as Kathmandu throughout.