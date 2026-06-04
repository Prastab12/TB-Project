import pandas as pd
import numpy as np
import os
from datetime import date

INPUT_FILE   = "data/final/final_cleaned_data.csv"
OUTPUT_FILE  = "data/harmonized/harmonized_tb_data.csv"
MAPPING_CSV  = "outputs/reports/11_DHIS2_FHIR_Mapping_Table.csv"
REPORT_FILE  = "outputs/reports/06_FHIR_Measure_Standardisation_Report.txt"

# Rows 1-3 (chron_order 1, 2, 3) are Baishak/Jestha/Asar 2078 —
# sex and age columns were zero-filled from NaN. Indicators that depend
# on those columns must be set to NaN so FHIR MeasureReports can apply
# data-absent-reason: not-reported instead of a false zero.
GAP_ORDERS = {1, 2, 3}


def calculate_indicators(df):
    gap = df["chron_order"].isin(GAP_ORDERS)

    # ── Indicators valid for all 60 months ──────────────────────────────────

    # 1. Treatment Success Rate
    df["tsr_cure_rate"] = np.where(
        df["pbc_reg"] > 0, df["cured"] / df["pbc_reg"], np.nan)

    # 2. Annualised TB Notification Rate (per 100,000 population)
    df["notification_rate_100k"] = np.where(
        df["district_pop_mid_year_cbs"] > 0,
        df["new_cases_total"] * 12 / df["district_pop_mid_year_cbs"] * 100_000,
        np.nan)

    # 3. Mortality Rate
    df["mortality_rate"] = np.where(
        df["pbc_reg"] > 0, df["died"] / df["pbc_reg"], np.nan)

    # 4. LTFU Rate
    df["ltfu_rate"] = np.where(
        df["pbc_reg"] > 0, df["ltfu"] / df["pbc_reg"], np.nan)

    # 5. Treatment Failure Rate
    df["failure_rate"] = np.where(
        df["pbc_reg"] > 0, df["failed"] / df["pbc_reg"], np.nan)

    # 6. Not Evaluated Rate
    df["not_eval_rate"] = np.where(
        df["pbc_reg"] > 0, df["not_eval"] / df["pbc_reg"], np.nan)

    # 7. Bacteriological Confirmation Proportion
    df["bacteriological_confirmation_pct"] = np.where(
        df["new_cases_total"] > 0, df["pbc_reg"] / df["new_cases_total"], np.nan)

    # 8. TB-HIV Co-infection Proportion
    df["tb_hiv_proportion"] = np.where(
        df["new_cases_total"] > 0,
        df["tb_hiv_positive"] / df["new_cases_total"],
        np.nan)

    # ── Indicators requiring sex/age data — NaN for 3 gap months ───────────

    # 9. M:F Notification Ratio
    df["mf_ratio"] = np.where(
        (~gap) & (df["new_cases_female"] > 0),
        df["new_cases_male"] / df["new_cases_female"],
        np.nan)

    # 10. Relapse Proportion
    total_cases = df["new_cases_total"] + df["relapse_total"]
    df["relapse_proportion"] = np.where(
        (~gap) & (total_cases > 0),
        df["relapse_total"] / total_cases,
        np.nan)

    # 11–18. Age Group Proportions (all 8 bands)
    age_bands = [
        ("age_group_0to4_proportion",   df["0_to_4_f"]   + df["0_to_4_m"]),
        ("age_group_5to14_proportion",  df["5_to_14_f"]  + df["5_to_14_m"]),
        ("age_group_15to24_proportion", df["15_to_24_f"] + df["15_to_24_m"]),
        ("age_group_25to34_proportion", df["25_to_34_f"] + df["25_to_34_m"]),
        ("age_group_35to44_proportion", df["35_to_44_f"] + df["35_to_44_m"]),
        ("age_group_45to54_proportion", df["45_to_54_f"] + df["45_to_54_m"]),
        ("age_group_55to64_proportion", df["55_to_64_f"] + df["55_to_64_m"]),
        ("age_group_65plus_proportion", df["65_f"]       + df["65_m"]),
    ]
    for col_name, band_sum in age_bands:
        df[col_name] = np.where(
            (~gap) & (df["new_cases_total"] > 0),
            band_sum / df["new_cases_total"],
            np.nan)

    # Round all indicator columns to 4 decimal places
    indicator_cols = [
        "tsr_cure_rate", "notification_rate_100k", "mortality_rate",
        "ltfu_rate", "failure_rate", "not_eval_rate",
        "bacteriological_confirmation_pct", "tb_hiv_proportion",
        "mf_ratio", "relapse_proportion",
        "age_group_0to4_proportion",   "age_group_5to14_proportion",
        "age_group_15to24_proportion", "age_group_25to34_proportion",
        "age_group_35to44_proportion", "age_group_45to54_proportion",
        "age_group_55to64_proportion", "age_group_65plus_proportion",
    ]
    df[indicator_cols] = df[indicator_cols].round(4)

    return df, indicator_cols


def write_mapping_table():
    rows = [
        ("Treatment Success Rate (TSR)",
         "nepal-tb-tsr-cure", "cured", "pbc_reg",
         "proportion", "increase", "cured, pbc_reg", "All 60 months"),
        ("Annualised TB Notification Rate",
         "nepal-tb-notification-rate",
         "new_cases_total × 12 × 100,000", "district_pop_mid_year_cbs",
         "ratio", "—", "new_cases_total, district_pop_mid_year_cbs", "All 60 months"),
        ("Mortality Rate",
         "nepal-tb-mortality-rate", "died", "pbc_reg",
         "proportion", "decrease", "died, pbc_reg", "All 60 months"),
        ("Lost to Follow-Up (LTFU) Rate",
         "nepal-tb-ltfu-rate", "ltfu", "pbc_reg",
         "proportion", "decrease", "ltfu, pbc_reg", "All 60 months"),
        ("Treatment Failure Rate",
         "nepal-tb-failure-rate", "failed", "pbc_reg",
         "proportion", "decrease", "failed, pbc_reg", "All 60 months"),
        ("Not Evaluated Rate",
         "nepal-tb-not-eval-rate", "not_eval", "pbc_reg",
         "proportion", "decrease", "not_eval, pbc_reg", "All 60 months"),
        ("Bacteriological Confirmation Proportion",
         "nepal-tb-bacteriological-confirmation", "pbc_reg", "new_cases_total",
         "proportion", "increase", "pbc_reg, new_cases_total", "All 60 months"),
        ("TB-HIV Co-infection Proportion",
         "nepal-tb-hiv-coinfection", "tb_hiv_positive", "new_cases_total",
         "proportion", "—", "tb_hiv_positive, new_cases_total", "All 60 months"),
        ("Male-to-Female Notification Ratio",
         "nepal-tb-gender-ratio", "new_cases_male", "new_cases_female",
         "ratio", "—", "new_cases_male, new_cases_female",
         "57 months (NaN for Baishak/Jestha/Asar 2078)"),
        ("Relapse Proportion",
         "nepal-tb-relapse-proportion", "relapse_total",
         "new_cases_total + relapse_total",
         "proportion", "—", "relapse_total, new_cases_total",
         "57 months (NaN for Baishak/Jestha/Asar 2078)"),
        ("Age Group 0–4 Proportion",   "nepal-tb-age-group-0to4",
         "0_to_4_f + 0_to_4_m", "new_cases_total", "proportion", "—",
         "0_to_4_f, 0_to_4_m, new_cases_total",
         "57 months (NaN for Baishak/Jestha/Asar 2078)"),
        ("Age Group 5–14 Proportion",  "nepal-tb-age-group-5to14",
         "5_to_14_f + 5_to_14_m", "new_cases_total", "proportion", "—",
         "5_to_14_f, 5_to_14_m, new_cases_total",
         "57 months (NaN for Baishak/Jestha/Asar 2078)"),
        ("Age Group 15–24 Proportion", "nepal-tb-age-group-15to24",
         "15_to_24_f + 15_to_24_m", "new_cases_total", "proportion", "—",
         "15_to_24_f, 15_to_24_m, new_cases_total",
         "57 months (NaN for Baishak/Jestha/Asar 2078)"),
        ("Age Group 25–34 Proportion", "nepal-tb-age-group-25to34",
         "25_to_34_f + 25_to_34_m", "new_cases_total", "proportion", "—",
         "25_to_34_f, 25_to_34_m, new_cases_total",
         "57 months (NaN for Baishak/Jestha/Asar 2078)"),
        ("Age Group 35–44 Proportion", "nepal-tb-age-group-35to44",
         "35_to_44_f + 35_to_44_m", "new_cases_total", "proportion", "—",
         "35_to_44_f, 35_to_44_m, new_cases_total",
         "57 months (NaN for Baishak/Jestha/Asar 2078)"),
        ("Age Group 45–54 Proportion", "nepal-tb-age-group-45to54",
         "45_to_54_f + 45_to_54_m", "new_cases_total", "proportion", "—",
         "45_to_54_f, 45_to_54_m, new_cases_total",
         "57 months (NaN for Baishak/Jestha/Asar 2078)"),
        ("Age Group 55–64 Proportion", "nepal-tb-age-group-55to64",
         "55_to_64_f + 55_to_64_m", "new_cases_total", "proportion", "—",
         "55_to_64_f, 55_to_64_m, new_cases_total",
         "57 months (NaN for Baishak/Jestha/Asar 2078)"),
        ("Age Group 65+ Proportion",   "nepal-tb-age-group-65plus",
         "65_f + 65_m", "new_cases_total", "proportion", "—",
         "65_f, 65_m, new_cases_total",
         "57 months (NaN for Baishak/Jestha/Asar 2078)"),
    ]
    cols = ["DHIS2 Indicator", "FHIR Measure ID", "Numerator", "Denominator",
            "Scoring Type", "Improvement Notation", "Source Columns", "Data Availability"]
    mapping_df = pd.DataFrame(rows, columns=cols)
    os.makedirs(os.path.dirname(MAPPING_CSV), exist_ok=True)
    mapping_df.to_csv(MAPPING_CSV, index=False)
    print(f"  Mapping table → {MAPPING_CSV}")
    return mapping_df


def write_report(df, indicator_cols, mapping_df):
    today    = date.today().isoformat()
    gap_mask = df["chron_order"].isin(GAP_ORDERS)

    L = []
    L.append("=" * 80)
    L.append("PHASE 3: FHIR MEASURE STANDARDISATION REPORT")
    L.append("=" * 80)
    L.append("Integrated Health Information Management System (IIHMS) | Nepal")
    L.append(f"Date Generated : {today}")
    L.append(f"District       : Kathmandu")
    L.append(f"Reporting Period: BS 2078 Baishak – BS 2082 Chaitra (60 months)")
    L.append("Status         : COMPLETE")
    L.append("")

    L.append("-" * 80)
    L.append("SECTION A: FHIR ARCHITECTURAL STRATEGY")
    L.append("-" * 80)
    L.append("")
    L.append("Structural Strategy:")
    L.append("  Measure (Definitional) : Defines the indicator — groups, scoring,")
    L.append("                           populations, and CQL expressions.")
    L.append("  MeasureReport (Instance): Holds computed results (numerator, denominator,")
    L.append("                           measureScore) for one district, one month.")
    L.append("")
    L.append("Scoring Types:")
    L.append("  proportion : Numerator is a strict subset of denominator. Score in [0, 1].")
    L.append("  ratio      : Numerator is NOT a subset of denominator (e.g., rates, ratios).")
    L.append("")
    L.append("Data-Absent Handling:")
    L.append("  Months Baishak / Jestha / Asar 2078 have no sex or age data in the source.")
    L.append("  Indicator columns that depend on sex/age are set to NaN in harmonized_tb_data.csv.")
    L.append("  In Phase 4 MeasureReports these NaN values will be encoded as:")
    L.append('  data-absent-reason: "not-reported" per HL7 FHIR R4 specification.')
    L.append("")

    L.append("-" * 80)
    L.append("SECTION B: DHIS2 → FHIR MAPPING TABLE")
    L.append("-" * 80)
    L.append("")
    hdr = f"{'DHIS2 Indicator':<42} {'FHIR Measure ID':<38} {'Scoring':<12} {'Availability'}"
    L.append(hdr)
    L.append("-" * len(hdr))
    for _, row in mapping_df.iterrows():
        L.append(f"{row['DHIS2 Indicator']:<42} {row['FHIR Measure ID']:<38} "
                 f"{row['Scoring Type']:<12} {row['Data Availability']}")
    L.append("")
    L.append(f"Full mapping table saved → {MAPPING_CSV}")
    L.append("")

    L.append("-" * 80)
    L.append("SECTION C: INDICATOR CALCULATION SUMMARY")
    L.append("-" * 80)
    L.append("")
    L.append(f"  Input  : {INPUT_FILE}")
    L.append(f"  Output : {OUTPUT_FILE}")
    L.append(f"  Total months        : {len(df)}")
    L.append(f"  Fully computed rows : {(~gap_mask).sum()} (Shrawan 2078 → Chaitra 2082)")
    L.append(f"  Gap months (NaN)    : {gap_mask.sum()} (Baishak/Jestha/Asar 2078)")
    L.append("")
    L.append(f"  {'Indicator':<38} {'Min':>8} {'Mean':>8} {'Max':>8} {'NaN count':>10}")
    L.append("  " + "-" * 76)
    for col in indicator_cols:
        s = df[col].dropna()
        nan_n = df[col].isna().sum()
        if len(s) > 0:
            L.append(f"  {col:<38} {s.min():>8.4f} {s.mean():>8.4f} {s.max():>8.4f} {nan_n:>10}")
        else:
            L.append(f"  {col:<38} {'—':>8} {'—':>8} {'—':>8} {nan_n:>10}")
    L.append("")

    L.append("-" * 80)
    L.append("SECTION D: FHIR MEASURE RESOURCE GENERATION")
    L.append("-" * 80)
    L.append("")
    L.append("  11 FHIR R4 Measure definition JSON files generated in fhir/measures/")
    for _, row in mapping_df.iterrows():
        L.append(f"    [{row['Scoring Type']:<10}] {row['FHIR Measure ID']}.json")
    L.append("")
    L.append("  1 Master Bundle: nepal-tb-measures-bundle.json (type: collection)")
    L.append("")
    L.append("  Two indicators from the previous project are replaced:")
    L.append("    REMOVED: nepal-tb-xpert-coverage  (xpert_cov_pct not in new dataset)")
    L.append("    REMOVED: nepal-tb-art-coverage     (art_cov_pct not in new dataset)")
    L.append("    ADDED  : nepal-tb-relapse-proportion       (now computable from new data)")
    L.append("    ADDED  : nepal-tb-age-group-0to4 through nepal-tb-age-group-65plus")
    L.append("             (all 8 age group proportions — full age distribution coverage)")
    L.append("")
    L.append("=" * 80)

    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    with open(REPORT_FILE, "w") as f:
        f.write("\n".join(L))
    print(f"  Report → {REPORT_FILE}")


def main():
    os.makedirs("data/harmonized", exist_ok=True)

    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded: {df.shape[0]} rows × {df.shape[1]} columns")

    # Mark gap months explicitly
    df["gap_month"] = df["chron_order"].isin(GAP_ORDERS)

    print("Calculating indicators...")
    df, indicator_cols = calculate_indicators(df)

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Harmonized data → {OUTPUT_FILE}  ({df.shape[0]} rows × {df.shape[1]} cols)")

    print("Writing mapping table...")
    mapping_df = write_mapping_table()

    print("Writing Phase 3 report...")
    write_report(df, indicator_cols, mapping_df)

    print("\n--- Indicator Summary ---")
    for col in indicator_cols:
        s     = df[col].dropna()
        nan_n = df[col].isna().sum()
        print(f"  {col:<40} mean={s.mean():.4f}  NaN={nan_n}")

    print("\nPhase 3 — Part A complete.")


if __name__ == "__main__":
    main()
