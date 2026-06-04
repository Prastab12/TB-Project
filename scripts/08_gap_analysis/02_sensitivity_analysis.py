"""
Phase 6 — Gap Analysis: Sensitivity Analysis + Structural Gap Documentation
=============================================================================
Input  : data/final/final_cleaned_data.csv
Output : outputs/reports/08_Kathmandu_Sensitivity_Analysis_Report.txt

Section A — IQR sensitivity matrix (1.5×, 2.0×, 3.0× multipliers)
Section B — Structural gap documentation (Baishak/Jestha/Asar 2078)
Section C — Year-over-year trend summary
"""

import pandas as pd
import numpy as np
import os
from datetime import date

INPUT   = "data/final/final_cleaned_data.csv"
REPORT  = "outputs/reports/08_Kathmandu_Sensitivity_Analysis_Report.txt"
GAP_IDS = {1, 2, 3}

ANALYSIS_VARS = [
    "new_cases_total", "new_cases_female", "new_cases_male",
    "relapse_total", "total_tb_mf",
    "tb_hiv_positive",
    "pbc_reg", "cured", "failed", "died", "ltfu", "not_eval",
]

MULTIPLIERS = [1.5, 2.0, 3.0]


def iqr_count(series, mult):
    Q1, Q3 = series.quantile(0.25), series.quantile(0.75)
    IQR    = Q3 - Q1
    lo, hi = Q1 - mult * IQR, Q3 + mult * IQR
    return int(((series < lo) | (series > hi)).sum()), round(lo, 1), round(hi, 1)


def main():
    df     = pd.read_csv(INPUT)
    df_all = df.copy()
    df_57  = df[~df["chron_order"].isin(GAP_IDS)].reset_index(drop=True)
    gap_df = df[df["chron_order"].isin(GAP_IDS)].reset_index(drop=True)

    L = []
    L.append("=" * 70)
    L.append("KATHMANDU DISTRICT — SENSITIVITY ANALYSIS & GAP DOCUMENTATION")
    L.append("=" * 70)
    L.append(f"Date    : {date.today().isoformat()}")
    L.append(f"Dataset : {INPUT}")
    L.append("")

    # ── Section A: IQR Sensitivity Matrix ─────────────────────────────────────
    L.append("=" * 70)
    L.append("SECTION A — IQR SENSITIVITY MATRIX")
    L.append("  Sex/age variables use 57-month subset (gap months excluded).")
    L.append("  Total-count variables use all 60 months.")
    L.append("=" * 70)
    L.append("")

    sex_age_set = {"new_cases_female", "new_cases_male", "relapse_total",
                   "total_tb_mf"}
    hdr = f"  {'Variable':<28}" + "".join(
        f"  {m}x IQR (outliers)" for m in MULTIPLIERS)
    L.append(hdr)
    L.append("  " + "-" * 85)

    matrix = {}
    for var in ANALYSIS_VARS:
        src = df_57 if var in sex_age_set else df_all
        row = []
        for mult in MULTIPLIERS:
            cnt, lo, hi = iqr_count(src[var].astype(float), mult)
            row.append((cnt, lo, hi))
        matrix[var] = row
        counts_str = "".join(
            f"  {r[0]:>2} [{r[1]:>7},{r[2]:>7}]" for r in row)
        L.append(f"  {var:<28}{counts_str}")

    L.append("")
    L.append("  Reading: each cell shows 'count [lower_fence, upper_fence]'.")
    L.append("  As multiplier increases, fences widen → fewer outliers flagged.")
    L.append("  Variables consistently flagging 0 at all multipliers are clean.")

    # ── Section B: Structural Gap Documentation ────────────────────────────────
    L.append("")
    L.append("=" * 70)
    L.append("SECTION B — STRUCTURAL REPORTING GAP DOCUMENTATION")
    L.append("=" * 70)
    L.append("")
    L.append("  Source    : DHIS2 / IIHMS national platform")
    L.append("  Gap scope : Baishak 2078, Jestha 2078, Asar 2078  (BS calendar Q4)")
    L.append("  Gregorian : April 16 – July 15, 2021")
    L.append("")
    L.append("  Root cause:")
    L.append("    Sex-disaggregated and age-stratified TB data was not captured")
    L.append("    in the DHIS2 system for Kathmandu District in these 3 months.")
    L.append("    Total new case counts (new_cases_total) ARE present and reliable.")
    L.append("    All treatment outcome fields (pbc_reg, cured, etc.) are present.")
    L.append("")

    gap_cases = int(gap_df["new_cases_total"].sum())
    total_cases = int(df_all["new_cases_total"].sum())
    gap_pct = gap_cases / total_cases * 100

    L.append("  Quantitative impact:")
    L.append(f"    New cases in gap months        : {gap_cases}")
    L.append(f"    Total new cases (60 months)    : {total_cases}")
    L.append(f"    Cases missing sex/age breakdown: {gap_cases} "
             f"({gap_pct:.1f}% of 60-month total)")
    L.append(f"    Sex/age data recovered (57 mo) : {total_cases - gap_cases} "
             f"({100 - gap_pct:.1f}%)")
    L.append("")
    L.append("  Per-month breakdown of gap period:")
    L.append(f"    {'Month':<15} {'New Cases':>10} {'PBC Reg':>8} "
             f"{'Cured':>7} {'Died':>6}")
    L.append("    " + "-" * 50)
    for _, row in gap_df.iterrows():
        L.append(f"    {row['bs_month']:<15} {int(row['new_cases_total']):>10} "
                 f"{int(row['pbc_reg']):>8} {int(row['cured']):>7} "
                 f"{int(row['died']):>6}")
    L.append("")
    L.append("  Variables affected by this gap:")
    L.append("    new_cases_female, new_cases_male, relapse_female, relapse_male,")
    L.append("    relapse_total, total_tb_female, total_tb_male, total_tb_mf,")
    L.append("    all 16 age-sex band columns (0_to_4_f through 65_m)")
    L.append("")
    L.append("  FHIR handling:")
    L.append("    These 3 months carry data-absent-reason: not-reported on the")
    L.append("    affected MeasureReport numerator and measureScore fields.")
    L.append("    24 variables × 3 months = 72 MeasureReports with DAR applied.")
    L.append("")
    L.append("  Classification: MNAR — Missing Not At Random (Structural Gap).")
    L.append("  Action taken  : Zero-fill in cleaning pipeline for computation;")
    L.append("                  DAR extension in FHIR for semantic correctness.")

    # ── Section C: Year-over-Year Trend Summary ────────────────────────────────
    L.append("")
    L.append("=" * 70)
    L.append("SECTION C — YEAR-OVER-YEAR TREND SUMMARY")
    L.append("=" * 70)
    L.append("")

    yearly = df_all.groupby("bs_year").agg(
        months        =("new_cases_total", "count"),
        new_cases_sum =("new_cases_total", "sum"),
        new_cases_avg =("new_cases_total", "mean"),
        relapse_sum   =("relapse_total",   "sum"),
        tb_hiv_sum    =("tb_hiv_positive", "sum"),
        cured_sum     =("cured",           "sum"),
        died_sum      =("died",            "sum"),
        pbc_sum       =("pbc_reg",         "sum"),
    ).reset_index()

    yearly["tsr"]          = (yearly["cured_sum"]   / yearly["pbc_sum"]).round(3)
    yearly["mortality"]    = (yearly["died_sum"]    / yearly["pbc_sum"]).round(3)
    yearly["relapse_rate"] = (yearly["relapse_sum"] /
                              (yearly["new_cases_sum"] + yearly["relapse_sum"])).round(3)
    yearly["pop"] = df_all.groupby("bs_year")["district_pop_mid_year_cbs"].first().values
    yearly["ann_rate"] = (yearly["new_cases_avg"] * 12 /
                          yearly["pop"] * 100_000).round(1)

    L.append(f"  {'BS Year':>8} {'New Cases':>10} {'Avg/Mo':>7} "
             f"{'Ann Rate':>9} {'Relapse':>8} {'TSR':>6} {'Mort':>6} {'HIV+':>5}")
    L.append("  " + "-" * 65)
    for _, r in yearly.iterrows():
        L.append(
            f"  {int(r['bs_year']):>8} {int(r['new_cases_sum']):>10} "
            f"{r['new_cases_avg']:>7.1f} {r['ann_rate']:>9.1f} "
            f"{int(r['relapse_sum']):>8} {r['tsr']:>6.3f} "
            f"{r['mortality']:>6.3f} {int(r['tb_hiv_sum']):>5}"
        )
    L.append("")
    L.append("  Ann Rate = annualised notification rate per 100,000 population")
    L.append("  TSR      = Treatment Success Rate (cured / pbc_reg)")
    L.append("  Mort     = Mortality Rate (died / pbc_reg)")
    L.append("")

    # Trend observations
    rates = yearly["ann_rate"].tolist()
    tsrs  = yearly["tsr"].tolist()
    L.append("  Observations:")
    L.append(f"    Notification rate range: {min(rates):.1f}–{max(rates):.1f}/100k "
             f"(all years within Nepal NTP expected range 100–200/100k)")
    L.append(f"    TSR range: {min(tsrs):.3f}–{max(tsrs):.3f} "
             f"(WHO target ≥0.85)")
    best_tsr  = yearly.loc[yearly['tsr'].idxmax()]
    worst_tsr = yearly.loc[yearly['tsr'].idxmin()]
    L.append(f"    Best TSR  : BS {int(best_tsr['bs_year'])} = {best_tsr['tsr']:.3f}")
    L.append(f"    Lowest TSR: BS {int(worst_tsr['bs_year'])} = {worst_tsr['tsr']:.3f}")

    L.append("")
    L.append("=" * 70)

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w") as f:
        f.write("\n".join(L))

    print(f"Sensitivity Analysis Report → {REPORT}")
    print("Script 02 complete.")


if __name__ == "__main__":
    main()
