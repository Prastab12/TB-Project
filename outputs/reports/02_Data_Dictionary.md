# TB Project: Data Dictionary
**Dataset:** `cleaned_data.csv` (780 Rows, 30 Columns)

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `chron_order` | `int64` | Chronological sort order identifier. |
| `bs_month` | `object` | Month of reporting in Bikram Sambat (e.g., Shrawan, Bhadra). |
| `bs_year` | `int64` | Fiscal year in Bikram Sambat (e.g., 2078). |
| `ad_year` | `int64` | Corresponding Gregorian calendar year (e.g., 2021). |
| `quarter` | `object` | Reporting quarter (e.g., Q1, Q2). |
| `district` | `object` | Name of the specific district in Bagmati Province. |
| `code` | `object` | Standardized health facility / district code. |
| `eco_zone` | `object` | Ecological zone classification (e.g., Mountain/Hill). |
| `district_pop_mid_year_cbs` | `int64` | Mid-year population estimate for the district based on CBS data. |
| `new_cases_total` | `float64` | Total count of incident (new) Tuberculosis cases. |
| `new_cases_female` | `float64` | Count of incident Tuberculosis cases (Female). |
| `new_cases_male` | `float64` | Count of incident Tuberculosis cases (Male). |
| `relapse_total` | `float64` | Total count of relapse Tuberculosis cases. |
| `relapse_female` | `float64` | Count of relapse Tuberculosis cases (Female). |
| `relapse_male` | `float64` | Count of relapse Tuberculosis cases (Male). |
| `total_tb_m+f` | `float64` | Total combined Tuberculosis cases (New + Relapse, Male + Female). |
| `total_tb_female` | `float64` | Total combined Tuberculosis cases (Female). |
| `total_tb_male` | `float64` | Total combined Tuberculosis cases (Male). |
| `m_to_f_ratio` | `float64` | Ratio of male TB cases to female TB cases. |
| `male_pct_new` | `float64` | Proportion/Percentage of new cases that are Male. |
| `female_pct_new` | `float64` | Proportion/Percentage of new cases that are Female. |
| `pbc_reg` | `int64` | Pulmonary Bacteriologically Confirmed registered cases. |
| `cured` | `int64` | Treatment Outcome: Number of patients successfully cured. |
| `failed` | `int64` | Treatment Outcome: Number of patients whose treatment failed. |
| `died` | `int64` | Treatment Outcome: Number of patients who died during treatment. |
| `ltfu` | `int64` | Treatment Outcome: Number of patients Lost To Follow-Up. |
| `not_eval` | `int64` | Treatment Outcome: Number of patients Not Evaluated. |
| `tb_hiv_pct` | `float64` | Percentage of TB patients co-infected with HIV. |
| `art_cov_pct` | `float64` | Antiretroviral Therapy (ART) coverage percentage among TB-HIV positive cases. |
| `xpert_cov_pct` | `float64` | GeneXpert rapid molecular diagnostic test coverage percentage. |
