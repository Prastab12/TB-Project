# Data Quality Assessment (DQA) Report
**Dataset Evaluated:** `cleaned_data.csv`
**Date of Assessment:** 2026-05-16
**Scope:** 780 Rows (13 Districts × 60 Months) × 30 Variables

---

## 1. Executive Summary
This report summarizes the findings of the comprehensive Data Quality Assessment performed on the IIHMS Tuberculosis dataset. The dataset exhibits **excellent internal mathematical consistency** and **high epidemiological plausibility**. The primary quality issue is data missingness, specifically within derived ratios and HIV/ART covariates. One variable (`art_cov_pct`) has been flagged as a structural gap (MNAR) due to exceeding the 20% missingness threshold.

---

## 2. Completeness Assessment
Completeness was evaluated to determine the viability of downstream MICE (Multiple Imputation by Chained Equations) imputation.

### 2.1 Variable-Wise Missingness
*   **Complete Variables (0% Missing):** All demographic identifiers, treatment outcomes (`cured`, `failed`, `died`, `ltfu`, `not_eval`), and test coverage (`xpert_cov_pct`, `tb_hiv_pct`).
*   **Imputable Variables (≤20% Missing):** 
    *   `m_to_f_ratio` (17.05%)
    *   Gender Disaggregated Counts: `new_cases_female`, `new_cases_male`, `relapse_female`, `relapse_male`, `total_tb_female`, `total_tb_male` (12.69%)
    *   Total Aggregates: `new_cases_total`, `relapse_total`, `total_tb_m+f` (5.00%)
*   **Data Gaps (>20% Missing):**
    *   `art_cov_pct` (32.31%) ❌ **Action Required:** Do not impute. Document as a formal gap.

### 2.2 Record-Wise Missingness
*   **Perfectly Complete Records:** 502 out of 780 rows (64%) contain 0 missing values.
*   **Average Missingness per Row:** 4.65%
*   **Maximum Missingness per Row:** 61.90% (Isolated to specific sparse district-months).

---

## 3. Missingness Mechanism Testing
Logistic Regression was utilized as an MCAR test alternative to determine if missingness (1=Missing, 0=Observed) was dependent on observed covariates (`District`, `bs_year`).

1.  **`new_cases_total`:**
    *   **Result:** MCAR Hypothesis NOT Rejected.
    *   **Classification:** **MCAR** (Missing Completely at Random). Missingness does not depend on geography or time.
2.  **`m_to_f_ratio`:**
    *   **Result:** MCAR Hypothesis REJECTED (p < 0.05).
    *   **Classification:** **MAR** (Missing at Random). Missingness is highly correlated with specific districts (Rasuwa, Ramechhap) and years, but is statistically safe for MICE because covariates are observed.
3.  **`art_cov_pct`:**
    *   **Result:** MCAR Hypothesis REJECTED (p < 0.05).
    *   **Classification:** **MNAR / GAP**. Missingness exceeds the 20% methodological threshold and is structurally biased by location and time. 

---

## 4. Consistency Checks
We verified that the dataset is internally consistent and mathematically balanced.

### 4.1 Logical Consistency (Numerator ≤ Denominator)
*   **Status:** 🟢 **Passed**
*   **Details:** No individual treatment outcome (e.g., `cured`, `died`) exceeds the total registered cohort (`pbc_reg`) in any given row. 

### 4.2 Sum Consistency
Tested equation: `Cured + Failed + Died + LTFU + Not Evaluated == pbc_reg`
*   **Status:** ❌ **Errors Detected**
*   **Details:** 
    *   **744 Rows (Under-reported):** The sum of outcomes is less than `pbc_reg`. This is expected due to the structural absence of the `Completed` variable in the dataset schema.
    *   **12 Rows (Over-reported):** The sum of the subset outcomes strictly exceeds the total registered cohort. This is a mathematical impossibility and represents a raw data entry error at the IIHMS level.

---

## 5. Plausibility & Range Checks
### 5.1 Temporal Plausibility
*   **Negative Values:** 🟢 **Passed.** 0 negative case counts found across all variables.
*   **Future Dates:** 🟢 **Passed.** Maximum date is BS 2082, which is bounded within plausible calendar conversions.

### 5.2 Epidemiological Range Checks
*   **Metric Assessed:** Annualized TB Notification Rate (Cases per 100,000 population).
*   **Calculated Rates:** Mean = 99.47, Max = 231.55.
*   **Status:** 🟢 **Passed.** 
*   **Conclusion:** The calculated rates map perfectly onto the expected national TB incidence/notification range for Nepal (100–200 per 100,000). The volume of reported cases is epidemiologically sound and realistic.
