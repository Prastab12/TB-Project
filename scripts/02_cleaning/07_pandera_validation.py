import pandas as pd
import pandera.pandas as pa
import os
from datetime import date

def validate_schema():
    input_file      = "data/final/final_cleaned_data.csv"
    standalone_txt  = "outputs/reports/04_Pandera_Validation_Report.txt"
    failed_rows_csv = "outputs/reports/05_Pandera_Failed_Rows.csv"
    validation_log  = "outputs/reports/05_Pandera_Validation_Log.csv"
    dqa_report      = "outputs/reports/03_Data_Quality_Assessment_Report.txt"

    df = pd.read_csv(input_file)

    age_band_cols = [
        "0_to_4_f", "0_to_4_m", "5_to_14_f", "5_to_14_m",
        "15_to_24_f", "15_to_24_m", "25_to_34_f", "25_to_34_m",
        "35_to_44_f", "35_to_44_m", "45_to_54_f", "45_to_54_m",
        "55_to_64_f", "55_to_64_m", "65_f", "65_m",
    ]

    schema_cols = {
        "chron_order":               pa.Column(int, pa.Check(lambda x: x >= 1), nullable=False),
        "bs_year":                   pa.Column(int, pa.Check(lambda x: x >= 2078), nullable=False),
        "ad_year":                   pa.Column(int, nullable=False),
        "district_pop_mid_year_cbs": pa.Column(int, pa.Check(lambda x: x > 0), nullable=False),
        "new_cases_total":           pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
        "new_cases_female":          pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
        "new_cases_male":            pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
        "relapse_female":            pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
        "relapse_male":              pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
        "relapse_total":             pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
        "total_tb_female":           pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
        "total_tb_male":             pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
        "total_tb_mf":               pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
        "pbc_reg":                   pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
        "cured":                     pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
        "failed":                    pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
        "died":                      pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
        "ltfu":                      pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
        "not_eval":                  pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
        "tb_hiv_positive":           pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False),
    }
    for col in age_band_cols:
        schema_cols[col] = pa.Column(int, pa.Check(lambda x: x >= 0), nullable=False)

    schema = pa.DataFrameSchema(columns=schema_cols, coerce=True, strict=False)

    try:
        schema.validate(df, lazy=True)
        status          = "PASSED"
        violation_count = 0
        pd.DataFrame().to_csv(failed_rows_csv, index=False)
        pd.DataFrame().to_csv(validation_log,  index=False)
    except pa.errors.SchemaErrors as err:
        status          = "FAILED"
        fc              = err.failure_cases
        violation_count = len(fc)
        fc.to_csv(failed_rows_csv, index=False)
        fc.to_csv(validation_log,  index=False)

    report_lines = [
        "",
        "-" * 80,
        "B. PANDERA SCHEMA VALIDATION (Zero-Fill & Int64)",
        f"   Validation Date : {date.today().isoformat()}",
        f"   Status          : {status} ({violation_count} violations)",
        "-" * 80,
        "Configuration:",
        "  - Missing Values  : Replaced with 0 (Zero-fill strategy)",
        "  - Numeric Type    : Enforced as int64",
        "  - Non-negative    : Checked for all count and population columns",
        "",
        f"Standalone report  : {standalone_txt}",
    ]

    os.makedirs(os.path.dirname(standalone_txt), exist_ok=True)
    with open(standalone_txt, "w") as f:
        f.write("\n".join(report_lines))

    # Append to existing DQA report
    if os.path.exists(dqa_report):
        with open(dqa_report, "r") as f:
            existing = f.read()
        marker = "\n--------------------------------------------------------------------------------\nB. PANDERA"
        if marker in existing:
            existing = existing[:existing.index(marker)]
        with open(dqa_report, "w") as f:
            f.write(existing.rstrip() + "\n")
            f.write("\n".join(report_lines) + "\n")

    print(f"Pandera validation : {status}  ({violation_count} violations)")
    print(f"Report → {standalone_txt}")
    print("Script 07 complete.")


if __name__ == "__main__":
    validate_schema()
