import pandas as pd
import pandera.pandas as pa
import os
from datetime import date

# ============================================================
# Pandera Schema Validation — Schema Definitions Catalogue
# ============================================================
SCHEMA_CATALOGUE = [
    {
        "column": "district",
        "dtype": "str",
        "required": True,
        "nullable": False,
        "constraints": ["Must be non-null string"],
        "rationale": "Primary geographic identifier — mandatory for all FHIR Location resources"
    },
    {
        "column": "bs_month",
        "dtype": "str",
        "required": True,
        "nullable": False,
        "constraints": ["Must be non-null string"],
        "rationale": "Bikram Sambat month label required for temporal period mapping"
    },
    {
        "column": "bs_year",
        "dtype": "int",
        "required": True,
        "nullable": False,
        "constraints": ["Must be integer", "Must be in {2078, 2079, 2080, 2081, 2082}"],
        "rationale": "Fiscal year range bounded to project scope — guards against stale or future data"
    },
    {
        "column": "new_cases_total",
        "dtype": "Int64 (nullable integer)",
        "required": True,
        "nullable": True,
        "constraints": ["Must be integer (no decimals)", "Must be >= 0"],
        "rationale": "Case count — fractional values indicate data entry error (Rule 13)"
    },
    {
        "column": "relapse_total",
        "dtype": "Int64 (nullable integer)",
        "required": True,
        "nullable": True,
        "constraints": ["Must be integer (no decimals)", "Must be >= 0"],
        "rationale": "Relapse count — must be whole number per WHO TB data standards"
    },
    {
        "column": "total_tb_m+f",
        "dtype": "Int64 (nullable integer)",
        "required": True,
        "nullable": True,
        "constraints": ["Must be integer (no decimals)", "Must be >= 0"],
        "rationale": "Total TB notifications — denominator for notification rate (Rule 4)"
    },
    {
        "column": "pbc_reg",
        "dtype": "Int64 (nullable integer)",
        "required": True,
        "nullable": True,
        "constraints": ["Must be integer (no decimals)", "Must be >= 0"],
        "rationale": "Bacteriologically confirmed / cohort registered — denominator for TSR calculation"
    },
    {
        "column": "cured",
        "dtype": "Int64 (nullable integer)",
        "required": True,
        "nullable": True,
        "constraints": ["Must be integer (no decimals)", "Must be >= 0"],
        "rationale": "Treatment outcome count — used in TSR numerator"
    },
    {
        "column": "failed",
        "dtype": "Int64 (nullable integer)",
        "required": True,
        "nullable": True,
        "constraints": ["Must be integer (no decimals)", "Must be >= 0"],
        "rationale": "Treatment failure count — WHO cohort outcome component"
    },
    {
        "column": "died",
        "dtype": "Int64 (nullable integer)",
        "required": True,
        "nullable": True,
        "constraints": ["Must be integer (no decimals)", "Must be >= 0"],
        "rationale": "Mortality count — WHO cohort outcome component; mortality rate numerator"
    },
    {
        "column": "ltfu",
        "dtype": "Int64 (nullable integer)",
        "required": True,
        "nullable": True,
        "constraints": ["Must be integer (no decimals)", "Must be >= 0"],
        "rationale": "Lost to follow-up count — WHO cohort outcome component"
    },
    {
        "column": "not_eval",
        "dtype": "Int64 (nullable integer)",
        "required": True,
        "nullable": True,
        "constraints": ["Must be integer (no decimals)", "Must be >= 0"],
        "rationale": "Not evaluated count — WHO cohort outcome component"
    },
    {
        "column": "district_pop_mid_year_cbs",
        "dtype": "float",
        "required": True,
        "nullable": True,
        "constraints": ["Must be float", "Must be >= 0"],
        "rationale": "CBS mid-year population estimate — denominator for all per-100,000 rate calculations (Rule 4, Rule 11)"
    },
    {
        "column": "tb_hiv_pct",
        "dtype": "float",
        "required": True,
        "nullable": True,
        "constraints": ["Must be float", "Must be in [0.0, 1.0]"],
        "rationale": "TB/HIV co-infection proportion — encoded as FHIR Observation; must be valid proportion (Rule 3)"
    },
    {
        "column": "xpert_cov_pct",
        "dtype": "float",
        "required": True,
        "nullable": True,
        "constraints": ["Must be float", "Must be in [0.0, 1.0]"],
        "rationale": "Xpert MTB/RIF test coverage proportion — must be valid proportion (Rule 3)"
    },
]


def validate_schema():
    input_file       = "data/cleaned/cleaned_data.csv"
    dqa_report       = "outputs/reports/03_Data_Quality_Assessment_Report.txt"
    standalone_txt   = "outputs/reports/04_Pandera_Validation_Report.txt"
    failed_rows_csv  = "outputs/reports/05_Pandera_Failed_Rows.csv"
    validation_log   = "outputs/reports/05_Pandera_Validation_Log.csv"

    df = pd.read_csv(input_file)

    # ------------------------------------------------------------------
    # PRE-PROCESSING — coerce count columns to nullable Int64
    # ------------------------------------------------------------------
    integer_count_cols = [
        "new_cases_total", "new_cases_female", "new_cases_male",
        "relapse_total", "relapse_female", "relapse_male",
        "total_tb_m+f", "total_tb_female", "total_tb_male",
        "pbc_reg", "cured", "failed", "died", "ltfu", "not_eval"
    ]
    non_integer_warnings = []
    for col in integer_count_cols:
        if col in df.columns:
            mask = df[col].notna() & (df[col] % 1 != 0)
            if mask.any():
                non_integer_warnings.append(f"  Column '{col}': {mask.sum()} non-integer value(s) detected before coercion")
            df[col] = df[col].astype("Int64")

    # ------------------------------------------------------------------
    # SCHEMA DEFINITION
    # ------------------------------------------------------------------
    schema = pa.DataFrameSchema(
        columns={
            "district":    pa.Column(str, required=True, nullable=False),
            "bs_month":    pa.Column(str, required=True, nullable=False),
            "bs_year":     pa.Column(
                               int,
                               pa.Check(lambda x: x.isin([2078, 2079, 2080, 2081, 2082]),
                                        element_wise=False,
                                        error="bs_year must be in {2078-2082}"),
                               required=True, nullable=False
                           ),
            "new_cases_total": pa.Column(pd.Int64Dtype(),
                                         pa.Check(lambda x: x >= 0, element_wise=True,
                                                  error="new_cases_total must be >= 0"),
                                         required=True, nullable=True),
            "relapse_total":   pa.Column(pd.Int64Dtype(),
                                         pa.Check(lambda x: x >= 0, element_wise=True,
                                                  error="relapse_total must be >= 0"),
                                         required=True, nullable=True),
            "total_tb_m+f":    pa.Column(pd.Int64Dtype(),
                                         pa.Check(lambda x: x >= 0, element_wise=True,
                                                  error="total_tb_m+f must be >= 0"),
                                         required=True, nullable=True),
            "pbc_reg":         pa.Column(pd.Int64Dtype(),
                                         pa.Check(lambda x: x >= 0, element_wise=True,
                                                  error="pbc_reg must be >= 0"),
                                         required=True, nullable=True),
            "cured":           pa.Column(pd.Int64Dtype(),
                                         pa.Check(lambda x: x >= 0, element_wise=True,
                                                  error="cured must be >= 0"),
                                         required=True, nullable=True),
            "failed":          pa.Column(pd.Int64Dtype(),
                                         pa.Check(lambda x: x >= 0, element_wise=True,
                                                  error="failed must be >= 0"),
                                         required=True, nullable=True),
            "died":            pa.Column(pd.Int64Dtype(),
                                         pa.Check(lambda x: x >= 0, element_wise=True,
                                                  error="died must be >= 0"),
                                         required=True, nullable=True),
            "ltfu":            pa.Column(pd.Int64Dtype(),
                                         pa.Check(lambda x: x >= 0, element_wise=True,
                                                  error="ltfu must be >= 0"),
                                         required=True, nullable=True),
            "not_eval":        pa.Column(pd.Int64Dtype(),
                                         pa.Check(lambda x: x >= 0, element_wise=True,
                                                  error="not_eval must be >= 0"),
                                         required=True, nullable=True),
            "district_pop_mid_year_cbs": pa.Column(float,
                                                    pa.Check(lambda x: x >= 0, element_wise=True,
                                                             error="population must be >= 0"),
                                                    required=True, nullable=True),
            "tb_hiv_pct":    pa.Column(float,
                                       pa.Check(lambda x: (x >= 0) & (x <= 1), element_wise=True,
                                                error="tb_hiv_pct must be in [0, 1]"),
                                       required=True, nullable=True),
            "xpert_cov_pct": pa.Column(float,
                                       pa.Check(lambda x: (x >= 0) & (x <= 1), element_wise=True,
                                                error="xpert_cov_pct must be in [0, 1]"),
                                       required=True, nullable=True),
        },
        coerce=False,
        strict=False
    )

    # ------------------------------------------------------------------
    # RUN VALIDATION
    # ------------------------------------------------------------------
    passed = False
    fc = pd.DataFrame()
    try:
        schema.validate(df, lazy=True)
        passed = True
        pd.DataFrame().to_csv(failed_rows_csv, index=False)
        pd.DataFrame().to_csv(validation_log, index=False)
        print("Pandera schema validation: PASSED")
    except pa.errors.SchemaErrors as err:
        fc = err.failure_cases.copy()
        fc.to_csv(failed_rows_csv, index=False)
        fc.to_csv(validation_log, index=False)
        print(f"Pandera schema validation: FAILED — {len(fc)} violation(s)")

    # ------------------------------------------------------------------
    # BUILD STANDALONE TXT REPORT
    # ------------------------------------------------------------------
    L = []
    L.append("=" * 80)
    L.append("PANDERA SCHEMA VALIDATION REPORT")
    L.append("TB Data Quality Pipeline | Bagmati Province, Nepal")
    L.append("=" * 80)
    L.append(f"Generated On      : {date.today().isoformat()}")
    L.append(f"Dataset           : data/cleaned/cleaned_data.csv")
    L.append(f"Total Rows        : {len(df)}")
    L.append(f"Total Districts   : {df['district'].nunique()}")
    L.append(f"Fiscal Years      : {sorted(df['bs_year'].dropna().unique().astype(int).tolist())}")
    L.append(f"Schema Columns    : {len(SCHEMA_CATALOGUE)}")
    L.append(f"Total Violations  : {len(fc)}")
    L.append("")

    # Executive Summary
    L.append("=" * 80)
    L.append("EXECUTIVE SUMMARY")
    L.append("=" * 80)
    if passed:
        L.append("STATUS : PASSED")
        L.append("All 780 rows comply with the defined Pandera schema.")
        L.append("No failed rows. No violations detected.")
    else:
        L.append("STATUS : FAILED")
        L.append(f"  Total violations : {len(fc)}")
        L.append(f"  Failed rows CSV  : {failed_rows_csv}")
        L.append(f"  Validation log   : {validation_log}")
    L.append("")

    if non_integer_warnings:
        L.append("Pre-Processing Warnings (non-integer values coerced to Int64):")
        L.extend(non_integer_warnings)
        L.append("")

    # Schema Catalogue
    L.append("=" * 80)
    L.append("SCHEMA DEFINITION — ALL VALIDATED COLUMNS")
    L.append("=" * 80)

    for entry in SCHEMA_CATALOGUE:
        col = entry["column"]
        L.append("")
        L.append("-" * 80)
        L.append(f"Column     : {col}")
        L.append(f"Data Type  : {entry['dtype']}")
        L.append(f"Required   : {entry['required']}")
        L.append(f"Nullable   : {entry['nullable']}")
        L.append(f"Constraints:")
        for c in entry["constraints"]:
            L.append(f"  - {c}")
        L.append(f"Rationale  : {entry['rationale']}")

        if not fc.empty and col in fc['column'].values:
            col_fc = fc[fc['column'] == col]
            L.append(f"Result     : FAILED — {len(col_fc)} violation(s)")
            L.append("  Violation detail:")
            L.append(f"  {'Check':<40} {'Failure Case':<20} {'Row Index'}")
            L.append("  " + "-" * 75)
            for _, r in col_fc.head(10).iterrows():
                L.append(f"  {str(r.get('check','')):<40} {str(r.get('failure_case','')):<20} {str(r.get('index',''))}")
        else:
            L.append(f"Result     : PASSED — No violations")

    # Violation Summary
    L.append("")
    L.append("=" * 80)
    L.append("VIOLATION SUMMARY")
    L.append("=" * 80)
    if not fc.empty:
        L.append("")
        L.append("By Column & Constraint:")
        summary = fc.groupby(['column', 'check']).size().reset_index(name='count')
        for _, r in summary.iterrows():
            L.append(f"  {str(r['column']):<35} | {str(r['check']):<40} | {r['count']} violation(s)")

        L.append("")
        L.append("By Schema Context:")
        for ctx, cnt in fc['schema_context'].value_counts().items():
            L.append(f"  {ctx:<25} {cnt:>6} violation(s)")
    else:
        L.append("No violations to summarize.")

    # Checks performed summary
    L.append("")
    L.append("=" * 80)
    L.append("CHECKS PERFORMED")
    L.append("=" * 80)
    checks = [
        ("[✓] Integer columns",       "pbc_reg, cured, failed, died, ltfu, not_eval, new_cases_total, relapse_total, total_tb_m+f validated as Int64"),
        ("[✓] Non-negative counts",   "All integer and float count fields checked >= 0"),
        ("[✓] Required columns",      "All 15 schema columns verified as required=True (present in dataframe)"),
        ("[✓] Proportion bounds",     "tb_hiv_pct and xpert_cov_pct validated within [0.0, 1.0]"),
        ("[✓] Fiscal year range",     "bs_year validated against {2078, 2079, 2080, 2081, 2082}"),
        ("[✓] Non-null identifiers",  "district, bs_month, bs_year enforced as nullable=False"),
        ("[✓] Float types",           "district_pop_mid_year_cbs, tb_hiv_pct, xpert_cov_pct validated as float"),
    ]
    for tag, desc in checks:
        L.append(f"  {tag:<30} {desc}")

    # Output files
    L.append("")
    L.append("=" * 80)
    L.append("OUTPUT FILES")
    L.append("=" * 80)
    L.append(f"  Standalone Report (TXT) : {standalone_txt}")
    L.append(f"  Failed Rows (CSV)       : {failed_rows_csv}")
    L.append(f"  Validation Log (CSV)    : {validation_log}")
    L.append(f"  DQA Report (appended)   : {dqa_report}")
    L.append("")

    # Write standalone report
    with open(standalone_txt, "w") as f:
        f.write("\n".join(L))
    print(f"Standalone report → {standalone_txt}")

    # ------------------------------------------------------------------
    # APPEND SUMMARY TO DQA REPORT (03_...)
    # ------------------------------------------------------------------
    dqa_lines = [
        "\n--------------------------------------------------------------------------------",
        f"B. PANDERA SCHEMA VALIDATION",
        f"   Validation Date : {date.today().isoformat()}",
        f"   Rows Evaluated  : {len(df)}",
        "--------------------------------------------------------------------------------",
        "Status : PASSED" if passed else f"Status : FAILED — {len(fc)} violation(s)",
        "",
        "Checks Performed:",
        "  [✓] Integer columns  — pbc_reg, cured, failed, died, ltfu, not_eval,",
        "                         new_cases_total, relapse_total, total_tb_m+f",
        "  [✓] Non-negative counts — all integer & float count fields",
        "  [✓] Required columns — all 15 mandatory columns present",
        "  [✓] Proportion bounds — tb_hiv_pct, xpert_cov_pct within [0, 1]",
        "  [✓] Fiscal year range — bs_year in {2078, 2079, 2080, 2081, 2082}",
        "  [✓] Non-null identifiers — district, bs_month, bs_year",
        "",
    ]

    if not fc.empty:
        dqa_lines.append("Failure Summary by Column & Constraint:")
        dqa_lines.append("---------------------------------------")
        summary = fc.groupby(['schema_context', 'column', 'check']).size().reset_index(name='count')
        for _, row in summary.iterrows():
            dqa_lines.append(
                f"  - [{row['schema_context']}] Column '{row['column']}' "
                f"| Constraint: {row['check']} "
                f"| Violations: {row['count']}"
            )
        dqa_lines.append("")

    dqa_lines += [
        f"Full report       : {standalone_txt}",
        f"Failed rows CSV   : {failed_rows_csv}",
        f"Validation log    : {validation_log}",
    ]

    with open(dqa_report, "r") as f:
        existing = f.read()

    marker = "\n--------------------------------------------------------------------------------\nB. PANDERA SCHEMA VALIDATION"
    if marker in existing:
        existing = existing[:existing.index(marker)]

    with open(dqa_report, "w") as f:
        f.write(existing.rstrip() + "\n")
        f.write("\n".join(dqa_lines) + "\n")

    print(f"DQA report updated → {dqa_report}")


if __name__ == "__main__":
    validate_schema()
