import pandas as pd
import pandera.pandas as pa
import os
from datetime import date

def validate_schema():
    # Validating the FINAL cleaned dataset
    input_file       = "data/final/final_cleaned_data.csv"
    dqa_report       = "outputs/reports/03_Data_Quality_Assessment_Report.txt"
    standalone_txt   = "outputs/reports/04_Pandera_Validation_Report.txt"
    failed_rows_csv  = "outputs/reports/05_Pandera_Failed_Rows.csv"
    validation_log   = "outputs/reports/05_Pandera_Validation_Log.csv"

    df = pd.read_csv(input_file)

    # -----------------------------------------------------------------------
    # SCHEMA DEFINITION (Adjusted for Int64 strategy)
    # -----------------------------------------------------------------------
    schema = pa.DataFrameSchema(
        columns={
            "district":    pa.Column(str, required=True, nullable=False),
            "bs_month":    pa.Column(str, required=True, nullable=False),
            "bs_year":     pa.Column(int, required=True, nullable=False),
            
            # All these columns were converted to int64 by the pipeline
            "new_cases_total": pa.Column(int, pa.Check(lambda x: x >= 0), required=True, nullable=False),
            "relapse_total":   pa.Column(int, pa.Check(lambda x: x >= 0), required=True, nullable=False),
            "total_tb_m+f":    pa.Column(int, pa.Check(lambda x: x >= 0), required=True, nullable=False),
            "pbc_reg":         pa.Column(int, pa.Check(lambda x: x >= 0), required=True, nullable=False),
            "cured":           pa.Column(int, pa.Check(lambda x: x >= 0), required=True, nullable=False),
            "failed":          pa.Column(int, pa.Check(lambda x: x >= 0), required=True, nullable=False),
            "died":            pa.Column(int, pa.Check(lambda x: x >= 0), required=True, nullable=False),
            "ltfu":            pa.Column(int, pa.Check(lambda x: x >= 0), required=True, nullable=False),
            "not_eval":        pa.Column(int, pa.Check(lambda x: x >= 0), required=True, nullable=False),
            
            "district_pop_mid_year_cbs": pa.Column(int, pa.Check(lambda x: x >= 0), required=True, nullable=False),
            
            # Rates are now integers (0 or 1 usually, since they were 0.0x)
            "tb_hiv_pct":    pa.Column(int, required=True, nullable=False),
            "xpert_cov_pct": pa.Column(int, required=True, nullable=False),
            "m_to_f_ratio":  pa.Column(int, required=True, nullable=False),
        },
        coerce=True, # Allow coercion from int64 to int
        strict=False 
    )

    # -----------------------------------------------------------------------
    # RUN VALIDATION
    # -----------------------------------------------------------------------
    try:
        schema.validate(df, lazy=True)
        status = "PASSED"
        violation_count = 0
        pd.DataFrame().to_csv(failed_rows_csv, index=False)
        pd.DataFrame().to_csv(validation_log, index=False)
    except pa.errors.SchemaErrors as err:
        status = "FAILED"
        fc = err.failure_cases
        violation_count = len(fc)
        fc.to_csv(failed_rows_csv, index=False)
        fc.to_csv(validation_log, index=False)

    # Update Reports
    report_lines = [
        "\n" + "-"*80,
        "B. PANDERA SCHEMA VALIDATION (Zero-Fill & Int64)",
        f"   Validation Date : {date.today().isoformat()}",
        f"   Status          : {status} ({violation_count} violations)",
        "-"*80,
        "Configuration:",
        "  - Missing Values: Replaced with 0",
        "  - Numeric Type  : Enforced as Int64",
        "  - District Names: Standardized",
        "",
        f"Standalone report: {standalone_txt}"
    ]

    # Append/Update main report
    with open(dqa_report, "r") as f:
        existing = f.read()
    
    marker = "\n--------------------------------------------------------------------------------\nB. PANDERA SCHEMA VALIDATION"
    if marker in existing:
        existing = existing[:existing.index(marker)]
    
    with open(dqa_report, "w") as f:
        f.write(existing.rstrip() + "\n")
        f.write("\n".join(report_lines) + "\n")

    # Simple standalone txt
    with open(standalone_txt, "w") as f:
        f.write("\n".join(report_lines))

    print(f"Pandera validation: {status}")

if __name__ == "__main__":
    validate_schema()
