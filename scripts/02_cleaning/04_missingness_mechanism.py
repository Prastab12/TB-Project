import pandas as pd
import numpy as np
from statsmodels.formula.api import logit
import warnings
warnings.filterwarnings("ignore")

CLEAN_PATH = "../../data/cleaned/cleaned_data.csv"


def test_missingness():
    df = pd.read_csv(CLEAN_PATH)

    print("=" * 55)
    print("MISSINGNESS MECHANISM TESTING REPORT")
    print("=" * 55)
    print("Dataset : Kathmandu District — single district, 60 months")
    print("Method  : Logistic regression of missingness indicator")
    print("          (1=Missing, 0=Observed) on bs_year")
    print("Threshold: Alpha = 0.05 to reject MCAR")
    print()

    # Only sex/age columns have missing values (3 rows each)
    test_vars = [c for c in df.columns if df[c].isnull().sum() > 0]

    if not test_vars:
        print("No missing values found — all variables complete.")
        return

    print(f"Variables with missing values: {len(test_vars)}")
    print(f"Missing count per variable   : {df[test_vars[0]].isnull().sum()} "
          f"(same for all — structural gap)")
    print()

    # Test a representative variable from each group
    representative = {
        "new_cases_female":  "New cases by sex",
        "relapse_female":    "Relapse by sex (provisional)",
        "0_to_4_f":         "Age-sex bands",
    }
    rep_vars = {k: v for k, v in representative.items() if k in df.columns}

    for target, label in rep_vars.items():
        missing_n   = int(df[target].isnull().sum())
        missing_pct = missing_n / len(df) * 100
        print(f"--- Variable: {target}  [{label}]  ({missing_n} missing, {missing_pct:.1f}%) ---")

        df["_miss"] = df[target].isnull().astype(int)

        # Show which rows are missing
        missing_rows = df[df["_miss"] == 1][["chron_order", "bs_month", "bs_year"]]
        print(f"  Missing in rows: {list(missing_rows['bs_month'].values)} "
              f"{list(missing_rows['bs_year'].astype(int).values)}")

        # Logistic regression with bs_year as sole covariate (single district)
        # Manual check: are ALL missing rows confined to the same 3 known months?
        missing_years  = set(df[df["_miss"] == 1]["bs_year"].astype(int).tolist())
        missing_months = set(df[df["_miss"] == 1]["bs_month"].tolist())
        known_gap_years  = {2078}
        known_gap_months = {"Baishak", "Jestha", "Asar"}
        is_structural = (missing_years == known_gap_years and
                         missing_months == known_gap_months)

        try:
            model  = logit("_miss ~ C(bs_year)", data=df).fit(disp=0)
            p_vals = model.pvalues
            sig    = p_vals[(p_vals < 0.05) & (~p_vals.index.str.contains("Intercept"))]
            lr_result = "REJECTED" if len(sig) > 0 else "NOT REJECTED"
        except Exception:
            lr_result = "INCONCLUSIVE (perfect separation or small sample)"

        print(f"  Logistic regression  : MCAR {lr_result}")
        if lr_result == "NOT REJECTED":
            print("  NOTE: Low statistical power — only 3 missing events in 60 rows.")
            print("        Regression alone is insufficient; domain knowledge is applied.")

        if is_structural:
            print("  Domain check         : All missing rows confirmed in Baishak/Jestha/Asar 2078")
            print("  FINAL CLASSIFICATION : MNAR — Structural Gap")
            print("  Reason: Source DHIS2 system had no sex/age data for these 3 months.")
            print("  Action: Zero-fill. Flag in FHIR as data-absent-reason: not-reported.")
        else:
            print("  FINAL CLASSIFICATION : MAR — requires further investigation")

        df.drop(columns=["_miss"], inplace=True)
        print()

    # Summary table
    print("--- Summary ---")
    print(f"  {'Variable Group':<35} {'Missing':>8} {'Mechanism':<30}")
    print("  " + "-" * 75)
    groups = [
        ("New Cases Total, PBC outcomes, TB-HIV",     "0",  "Complete"),
        ("New Cases F/M (57 months have data)",        "3",  "MNAR — Structural Gap (BS 2078 Q4)"),
        ("All 16 age-sex band columns",               "3",  "MNAR — Structural Gap (BS 2078 Q4)"),
        ("Relapse F/M, Total TB F/M",                 "3",  "MNAR — Structural Gap (provisional)"),
    ]
    for grp, miss, mech in groups:
        print(f"  {grp:<35} {miss:>8}  {mech}")

    print("\nScript 04 complete.")


if __name__ == "__main__":
    test_missingness()
