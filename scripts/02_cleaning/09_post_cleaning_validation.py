import pandas as pd
import numpy as np

def run_post_validation():
    df = pd.read_csv("data/final/final_cleaned_data.csv")

    checks = []

    # 1. No missing values anywhere
    total_missing = df.isna().sum().sum()
    checks.append(("No missing values in entire dataset", total_missing == 0))

    # 2. All numeric columns are int64
    numeric_vars = [
        "bs_year", "ad_year", "district_pop_mid_year_cbs",
        "new_cases_total", "new_cases_female", "new_cases_male",
        "relapse_female", "relapse_male", "relapse_total",
        "total_tb_female", "total_tb_male", "total_tb_mf",
        "pbc_reg", "cured", "failed", "died", "ltfu", "not_eval",
        "tb_hiv_positive",
    ]
    age_cols = [c for c in df.columns if "_to_" in c or c in ("65_f", "65_m")]
    numeric_vars += age_cols

    all_int = True
    for var in numeric_vars:
        if var not in df.columns:
            print(f"  MISSING COLUMN: {var}")
            all_int = False
            continue
        if "int64" not in str(df[var].dtype):
            print(f"  WRONG DTYPE: {var} is {df[var].dtype} (expected int64)")
            all_int = False
    checks.append(("All numeric columns are int64", all_int))

    # 3. No negative values
    num_cols  = df.select_dtypes(include=[np.number]).columns
    neg_count = (df[num_cols] < 0).sum().sum()
    checks.append(("No negative values in numeric columns", neg_count == 0))

    # 4. Derived columns correct
    relapse_ok = (df["relapse_total"] == df["relapse_female"] + df["relapse_male"]).all()
    checks.append(("relapse_total = relapse_female + relapse_male", relapse_ok))

    ttb_ok = (df["total_tb_mf"] == df["total_tb_female"] + df["total_tb_male"]).all()
    checks.append(("total_tb_mf = total_tb_female + total_tb_male", ttb_ok))

    # 5. Row count
    checks.append(("Dataset has exactly 60 rows", len(df) == 60))

    # 6. BS months stripped (no trailing whitespace)
    stripped_ok = (df["bs_month"] == df["bs_month"].str.strip()).all()
    checks.append(("bs_month values have no leading/trailing whitespace", stripped_ok))

    # 7. chron_order is sequential 1-60
    chron_ok = list(df["chron_order"]) == list(range(1, 61))
    checks.append(("chron_order is sequential 1–60", chron_ok))

    # 8. cohort_sum_flag intentionally removed (structural under-reporting on all rows)
    checks.append(("cohort_sum_flag column absent", "cohort_sum_flag" not in df.columns))

    print("\n" + "=" * 55)
    print("POST-CLEANING VALIDATION RESULTS")
    print("=" * 55)
    all_passed = True
    for label, status in checks:
        icon = "PASS" if status else "FAIL"
        print(f"  [{icon}] {label}")
        if not status:
            all_passed = False
    print("=" * 55)
    print(f"STATUS: {'ALL CHECKS PASSED' if all_passed else 'ERRORS DETECTED'}")
    print("=" * 55 + "\n")
    print("Script 09 complete.")


if __name__ == "__main__":
    run_post_validation()
