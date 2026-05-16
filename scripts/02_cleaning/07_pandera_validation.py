import pandas as pd
import pandera.pandas as pa
import os
from datetime import date

def validate_schema():
    input_file = "data/cleaned/cleaned_data.csv"
    output_report = "outputs/reports/03_Data_Quality_Assessment_Report.txt"
    failed_rows_csv = "outputs/reports/05_Pandera_Failed_Rows.csv"
    validation_log_csv = "outputs/reports/05_Pandera_Validation_Log.csv"

    df = pd.read_csv(input_file)

    # -----------------------------------------------------------------------
    # PRE-PROCESSING: coerce count columns to Int64 (nullable integer)
    # so we can properly validate them as integers (CSV reads all as float).
    # Columns that should be whole-number counts per WHO / Rule 13.
    # -----------------------------------------------------------------------
    integer_count_cols = [
        "new_cases_total", "new_cases_female", "new_cases_male",
        "relapse_total", "relapse_female", "relapse_male",
        "total_tb_m+f", "total_tb_female", "total_tb_male",
        "pbc_reg", "cured", "failed", "died", "ltfu", "not_eval"
    ]

    for col in integer_count_cols:
        if col in df.columns:
            # Flag non-integer values before coercing
            mask = df[col].notna() & (df[col] % 1 != 0)
            if mask.any():
                print(f"WARNING: Column '{col}' has {mask.sum()} non-integer values.")
            df[col] = df[col].astype("Int64")

    # -----------------------------------------------------------------------
    # SCHEMA DEFINITION
    # -----------------------------------------------------------------------
    schema = pa.DataFrameSchema(
        columns={
            # --- Identifiers (required, non-null) ---
            "district":    pa.Column(str, required=True, nullable=False),
            "bs_month":    pa.Column(str, required=True, nullable=False),
            "bs_year":     pa.Column(
                               int,
                               pa.Check(lambda x: x.isin([2078, 2079, 2080, 2081, 2082]),
                                        element_wise=False,
                                        error="bs_year must be in {2078-2082}"),
                               required=True, nullable=False
                           ),

            # --- Integer count columns (required=True, non-negative) ---
            "new_cases_total": pa.Column(
                                   pd.Int64Dtype(),
                                   pa.Check(lambda x: x >= 0, element_wise=True,
                                            error="new_cases_total must be >= 0"),
                                   required=True, nullable=True
                               ),
            "relapse_total":   pa.Column(
                                   pd.Int64Dtype(),
                                   pa.Check(lambda x: x >= 0, element_wise=True,
                                            error="relapse_total must be >= 0"),
                                   required=True, nullable=True
                               ),
            "total_tb_m+f":    pa.Column(
                                   pd.Int64Dtype(),
                                   pa.Check(lambda x: x >= 0, element_wise=True,
                                            error="total_tb_m+f must be >= 0"),
                                   required=True, nullable=True
                               ),
            "pbc_reg":         pa.Column(
                                   pd.Int64Dtype(),
                                   pa.Check(lambda x: x >= 0, element_wise=True,
                                            error="pbc_reg must be >= 0"),
                                   required=True, nullable=True
                               ),
            "cured":           pa.Column(
                                   pd.Int64Dtype(),
                                   pa.Check(lambda x: x >= 0, element_wise=True,
                                            error="cured must be >= 0"),
                                   required=True, nullable=True
                               ),
            "failed":          pa.Column(
                                   pd.Int64Dtype(),
                                   pa.Check(lambda x: x >= 0, element_wise=True,
                                            error="failed must be >= 0"),
                                   required=True, nullable=True
                               ),
            "died":            pa.Column(
                                   pd.Int64Dtype(),
                                   pa.Check(lambda x: x >= 0, element_wise=True,
                                            error="died must be >= 0"),
                                   required=True, nullable=True
                               ),
            "ltfu":            pa.Column(
                                   pd.Int64Dtype(),
                                   pa.Check(lambda x: x >= 0, element_wise=True,
                                            error="ltfu must be >= 0"),
                                   required=True, nullable=True
                               ),
            "not_eval":        pa.Column(
                                   pd.Int64Dtype(),
                                   pa.Check(lambda x: x >= 0, element_wise=True,
                                            error="not_eval must be >= 0"),
                                   required=True, nullable=True
                               ),

            # --- Float / rate columns ---
            "district_pop_mid_year_cbs": pa.Column(
                                             float,
                                             pa.Check(lambda x: x >= 0, element_wise=True,
                                                      error="population must be >= 0"),
                                             required=True, nullable=True
                                         ),
            "tb_hiv_pct":    pa.Column(
                                 float,
                                 pa.Check(lambda x: (x >= 0) & (x <= 1), element_wise=True,
                                          error="tb_hiv_pct must be in [0, 1]"),
                                 required=True, nullable=True
                             ),
            "xpert_cov_pct": pa.Column(
                                 float,
                                 pa.Check(lambda x: (x >= 0) & (x <= 1), element_wise=True,
                                          error="xpert_cov_pct must be in [0, 1]"),
                                 required=True, nullable=True
                             ),
        },
        coerce=False,
        strict=False    # allow extra columns not defined in schema
    )

    # -----------------------------------------------------------------------
    # RUN VALIDATION
    # -----------------------------------------------------------------------
    report_lines = [
        "\n--------------------------------------------------------------------------------",
        f"B. PANDERA SCHEMA VALIDATION",
        f"   Validation Date : {date.today().isoformat()}",
        f"   Rows Evaluated  : {len(df)}",
        "--------------------------------------------------------------------------------"
    ]

    try:
        schema.validate(df, lazy=True)

        report_lines += [
            "Status : PASSED",
            "",
            "Checks Performed:",
            "  [✓] Integer columns  — pbc_reg, cured, failed, died, ltfu, not_eval,",
            "                         new_cases_total, relapse_total, total_tb_m+f",
            "  [✓] Non-negative counts — all integer & float count fields",
            "  [✓] Required columns — all mandatory columns present and non-null",
            "  [✓] Proportion bounds — tb_hiv_pct, xpert_cov_pct within [0, 1]",
            "  [✓] Fiscal year range — bs_year in {2078, 2079, 2080, 2081, 2082}",
            "",
            "Conclusion: Data complies with all Pandera schema constraints.",
            "No failed rows."
        ]

        # Empty failed rows file
        pd.DataFrame().to_csv(failed_rows_csv, index=False)
        pd.DataFrame().to_csv(validation_log_csv, index=False)

        print("Pandera schema validation: PASSED")

    except pa.errors.SchemaErrors as err:
        fc = err.failure_cases.copy()
        total_violations = len(fc)

        report_lines += [
            "Status : FAILED",
            f"Total violations : {total_violations}",
            "",
            "Checks Performed:",
            "  [✓] Integer columns  — pbc_reg, cured, failed, died, ltfu, not_eval,",
            "                         new_cases_total, relapse_total, total_tb_m+f",
            "  [✓] Non-negative counts — all integer & float count fields",
            "  [✓] Required columns — all mandatory columns present",
            "  [✓] Proportion bounds — tb_hiv_pct, xpert_cov_pct within [0, 1]",
            "  [✓] Fiscal year range — bs_year in {2078, 2079, 2080, 2081, 2082}",
            "",
            "Failure Summary by Column & Constraint:",
            "---------------------------------------"
        ]

        summary = (
            fc.groupby(['schema_context', 'column', 'check'])
              .size()
              .reset_index(name='violation_count')
        )
        for _, row in summary.iterrows():
            report_lines.append(
                f"  - [{row['schema_context']}] Column '{row['column']}' "
                f"| Constraint: {row['check']} "
                f"| Violations: {row['violation_count']}"
            )

        report_lines += [
            "",
            f"Detailed failure cases saved to : {failed_rows_csv}",
            f"Full validation log saved to    : {validation_log_csv}"
        ]

        # Save outputs
        fc.to_csv(failed_rows_csv, index=False)
        fc.to_csv(validation_log_csv, index=False)

        print(f"Pandera schema validation: FAILED — {total_violations} violations")
        print(f"Failed rows  → {failed_rows_csv}")
        print(f"Validation log → {validation_log_csv}")

    # -----------------------------------------------------------------------
    # WRITE TO REPORT (strip old Pandera section first, then append)
    # -----------------------------------------------------------------------
    with open(output_report, "r") as f:
        existing = f.read()

    marker = "\n--------------------------------------------------------------------------------\nB. PANDERA SCHEMA VALIDATION"
    if marker in existing:
        existing = existing[:existing.index(marker)]

    with open(output_report, "w") as f:
        f.write(existing.rstrip() + "\n")
        f.write("\n".join(report_lines) + "\n")

    print(f"Report updated → {output_report}")


if __name__ == "__main__":
    validate_schema()
