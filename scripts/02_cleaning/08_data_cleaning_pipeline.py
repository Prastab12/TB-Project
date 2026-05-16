import pandas as pd
import numpy as np
from datetime import datetime
import os

LOG = []

def log_change(row_idx, column, original, cleaned, fix_type, rule):
    LOG.append({
        "timestamp": datetime.now().isoformat(),
        "row_index": row_idx,
        "column": column,
        "original_value": original,
        "cleaned_value": cleaned,
        "fix_type": fix_type,
        "rule_triggered": rule
    })

def main():
    input_file  = "data/cleaned/cleaned_data.csv"
    output_file = "data/final/final_cleaned_data.csv"
    audit_log   = "outputs/reports/05_Cleaning_Audit_Log.csv"
    os.makedirs("data/final", exist_ok=True)

    df = pd.read_csv(input_file)
    print(f"Loaded: {df.shape[0]} rows x {df.shape[1]} columns")

    # ------------------------------------------------------------------ #
    # FIX 1 — District Name Standardization
    # ------------------------------------------------------------------ #
    spelling_map = {"MAKWANPUR": "MAKAWANPUR", "CHITWAN": "CHITAWAN"}
    for wrong, correct in spelling_map.items():
        mask = df["district"] == wrong
        for idx in df[mask].index:
            log_change(idx, "district", wrong, correct, "STANDARDIZATION", "Rule_06")
        df.loc[mask, "district"] = correct

    # ------------------------------------------------------------------ #
    # STEP 1: Replace all empty values with 0
    # ------------------------------------------------------------------ #
    # Only for numeric columns? Or all? User said "all empty values to 0".
    # Typically this applies to numeric fields in this context.
    numeric_cols = df.select_dtypes(include=[np.number, "float64", "int64"]).columns.tolist()
    
    for col in numeric_cols:
        mask = df[col].isna()
        if mask.any():
            for idx in df[mask].index:
                log_change(idx, col, "NaN", 0, "MISSING_VALUE", "Zero_Filling")
            df[col] = df[col].fillna(0)
    
    print(f"Step 1 Done: All empty numeric values replaced with 0.")

    # ------------------------------------------------------------------ #
    # STEP 2: Convert all numeric columns from float64 to int64
    # ------------------------------------------------------------------ #
    # Note: This will round/truncate decimals for rates (e.g. 0.05 -> 0).
    for col in numeric_cols:
        old_dtype = str(df[col].dtype)
        # We use rounded conversion to avoid 1.99999 -> 1 issues if any exist
        df[col] = df[col].round(0).astype(np.int64)
        new_dtype = str(df[col].dtype)
        log_change("ALL", col, old_dtype, new_dtype, "TYPE_CONVERSION", "Int64_Enforcement")

    print(f"Step 2 Done: All numeric columns converted to int64.")

    # ------------------------------------------------------------------ #
    # FIX 3 — Cohort Sum Flagging
    # ------------------------------------------------------------------ #
    outcome_cols = ["cured", "failed", "died", "ltfu", "not_eval"]
    df["_cohort_sum"] = df[outcome_cols].sum(axis=1) # Already filled with 0s
    def cohort_flag(row):
        enrolled = row["pbc_reg"]
        s = row["_cohort_sum"]
        if s > enrolled and enrolled > 0:
            return "OVER_REPORTED"
        elif s < enrolled:
            return "UNDER_REPORTED"
        elif s == enrolled and enrolled > 0:
            return "BALANCED"
        return "UNKNOWN"
    df["cohort_sum_flag"] = df.apply(cohort_flag, axis=1)
    df.drop(columns=["_cohort_sum"], inplace=True)

    # ------------------------------------------------------------------ #
    # SAVE RESULTS
    # ------------------------------------------------------------------ #
    df.to_csv(output_file, index=False)
    audit_df = pd.DataFrame(LOG)
    audit_df.to_csv(audit_log, index=False)
    
    print(f"Pipeline Completed (Simple Zero-Filling & Int64 conversion).")
    print(f"Final Data → {output_file}")
    print(f"Audit Log  → {audit_log}")

if __name__ == "__main__":
    main()
