import pandas as pd
import numpy as np
from datetime import datetime
import os

LOG = []

def log_change(row_idx, column, original, cleaned, fix_type, rule):
    LOG.append({
        "timestamp":      datetime.now().isoformat(),
        "row_index":      row_idx,
        "column":         column,
        "original_value": original,
        "cleaned_value":  cleaned,
        "fix_type":       fix_type,
        "rule_triggered": rule,
    })


def main():
    input_file  = "data/cleaned/cleaned_data.csv"
    output_file = "data/final/final_cleaned_data.csv"
    audit_log   = "outputs/reports/05_Cleaning_Audit_Log.csv"
    os.makedirs("data/final", exist_ok=True)

    df = pd.read_csv(input_file)
    print(f"Loaded: {df.shape[0]} rows × {df.shape[1]} columns")

    # ------------------------------------------------------------------ #
    # STEP 1 — Zero-fill all missing numeric values
    # ------------------------------------------------------------------ #
    numeric_cols = df.select_dtypes(include=[np.number, "float64", "int64"]).columns.tolist()
    for col in numeric_cols:
        mask = df[col].isna()
        if mask.any():
            for idx in df[mask].index:
                log_change(idx, col, "NaN", 0, "MISSING_VALUE", "Zero_Filling")
            df[col] = df[col].fillna(0)
    print(f"Step 1 done: zero-filled missing numeric values.")

    # ------------------------------------------------------------------ #
    # STEP 2 — Convert all numeric columns to int64
    # ------------------------------------------------------------------ #
    for col in numeric_cols:
        old_dtype = str(df[col].dtype)
        df[col]   = df[col].round(0).astype(np.int64)
        log_change("ALL", col, old_dtype, "int64", "TYPE_CONVERSION", "Int64_Enforcement")
    print(f"Step 2 done: all numeric columns cast to int64.")

    # ------------------------------------------------------------------ #
    # STEP 3 — Derive relapse_total and total_tb_mf
    # ------------------------------------------------------------------ #
    df["relapse_total"] = df["relapse_female"] + df["relapse_male"]
    df["total_tb_mf"]   = df["total_tb_female"] + df["total_tb_male"]
    log_change("ALL", "relapse_total", "absent", "relapse_female + relapse_male",
               "DERIVED_COLUMN", "Relapse_Total_Derivation")
    log_change("ALL", "total_tb_mf", "absent", "total_tb_female + total_tb_male",
               "DERIVED_COLUMN", "Total_TB_MF_Derivation")
    print("Step 3 done: derived relapse_total and total_tb_mf columns.")

    # ------------------------------------------------------------------ #
    # SAVE
    # ------------------------------------------------------------------ #
    df.to_csv(output_file, index=False)
    pd.DataFrame(LOG).to_csv(audit_log, index=False)

    print(f"\nFinal dataset → {output_file}  ({df.shape[0]} rows × {df.shape[1]} cols)")
    print(f"Audit log     → {audit_log}  ({len(LOG)} entries)")
    print("Script 08 complete.")


if __name__ == "__main__":
    main()
