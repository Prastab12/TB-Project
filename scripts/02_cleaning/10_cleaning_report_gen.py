import pandas as pd
from datetime import date
import os

def generate_cleaning_report():
    input_file  = "data/cleaned/cleaned_data.csv"
    final_file  = "data/final/final_cleaned_data.csv"
    audit_file  = "outputs/reports/05_Cleaning_Audit_Log.csv"
    report_file = "outputs/reports/05_Data_Cleaning_Pipeline_Report.txt"

    df_orig  = pd.read_csv(input_file)
    df_final = pd.read_csv(final_file)
    audit_df = pd.read_csv(audit_file)

    zero_fills  = audit_df[audit_df["fix_type"] == "MISSING_VALUE"].shape[0]
    type_casts  = audit_df[audit_df["fix_type"] == "TYPE_CONVERSION"].shape[0]
    derived     = audit_df[audit_df["fix_type"] == "DERIVED_COLUMN"].shape[0]
    final_nulls = df_final.isna().sum().sum()
    float_cols  = df_final.select_dtypes(include=["float"]).columns.tolist()

    L = []
    L.append("=" * 80)
    L.append("DATA CLEANING PIPELINE REPORT")
    L.append("TB Data Quality Standardization | Kathmandu District, Nepal")
    L.append("=" * 80)
    L.append(f"Date Generated  : {date.today().isoformat()}")
    L.append(f"Source Dataset  : {input_file}")
    L.append(f"Cleaned Dataset : {final_file}")
    L.append("")

    L.append("1. PIPELINE OBJECTIVES")
    L.append("-" * 30)
    L.append("  - Eliminate data missingness in numeric columns (Zero-filling).")
    L.append("  - Enforce strict structural types (Int64) across all count columns.")
    L.append("  - Derive relapse_total and total_tb_mf summary columns.")
    L.append("  - Flag cohort outcome completeness (BALANCED / UNDER_REPORTED / OVER_REPORTED).")
    L.append("  - Ensure mathematical consistency for downstream FHIR MeasureReport generation.")
    L.append("")

    L.append("2. CLEANING STRATEGIES APPLIED")
    L.append("-" * 30)
    L.append("  [STRATEGY A] Zero-Filling Missing Values")
    L.append("    - All NaN cells in numeric columns replaced with integer 0.")
    L.append("    - Applies to the 3-month structural gap: Baishak/Jestha/Asar 2078.")
    L.append(f"    - Total cells zero-filled: {zero_fills}")
    L.append("")
    L.append("  [STRATEGY B] Int64 Type Enforcement")
    L.append("    - All numeric columns cast to int64 via round(0).astype(int64).")
    L.append(f"    - Columns converted: {type_casts}")
    L.append("")
    L.append("  [STRATEGY C] Derived Column Addition")
    L.append("    - relapse_total  = relapse_female + relapse_male")
    L.append("    - total_tb_mf    = total_tb_female + total_tb_male")
    L.append(f"    - Columns added : {derived}")
    L.append("    - cohort_sum_flag: NOT added — structural under-reporting on all rows")
    L.append("      makes this flag uninformative for a single-district dataset.")
    L.append("")

    L.append("3. EXECUTION SUMMARY")
    L.append("-" * 30)
    L.append(f"  Total Rows Processed    : {len(df_final)}")
    L.append(f"  Total Columns (final)   : {df_final.shape[1]}")
    L.append(f"  Missing Values Filled   : {zero_fills} cells")
    L.append(f"  Type Conversions        : {type_casts} columns")
    L.append(f"  Derived Columns Added   : {derived}")
    L.append(f"  Total Audit Log Entries : {len(audit_df)}")
    L.append("")

    L.append("4. COHORT SUM FLAG")
    L.append("-" * 30)
    L.append("  cohort_sum_flag was intentionally excluded from the final dataset.")
    L.append("  Reason: PBC outcome under-reporting is structural (the 'Completed'")
    L.append("  category is absent from the schema), so the flag would read")
    L.append("  UNDER_REPORTED for 58/60 rows — carrying no discriminatory value.")
    L.append("")

    L.append("5. FINAL DATA INTEGRITY STATUS")
    L.append("-" * 30)
    L.append(f"  Remaining Null Values   : {final_nulls} (Target: 0)")
    L.append(f"  Float64 Columns Left    : {len(float_cols)} (Target: 0)")
    status = "VERIFIED — CLEAN AND INTEGER-STRICT" if final_nulls == 0 and len(float_cols) == 0 else "ISSUES DETECTED"
    L.append(f"  STATUS: {status}")
    L.append("")

    L.append("6. FILE REFERENCES")
    L.append("-" * 30)
    L.append(f"  Full Audit Log        : {audit_file}")
    L.append(f"  Final Cleaned CSV     : {final_file}")
    L.append(f"  Pandera Validation    : outputs/reports/04_Pandera_Validation_Report.txt")
    L.append(f"  Failed Rows (if any)  : outputs/reports/05_Pandera_Failed_Rows.csv")
    L.append("")
    L.append("=" * 80)

    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    with open(report_file, "w") as f:
        f.write("\n".join(L))

    print(f"Pipeline report → {report_file}")
    print("Script 10 complete.")


if __name__ == "__main__":
    generate_cleaning_report()
