"""
Phase 4 — FHIR R4 MeasureReport generation.

Generates one MeasureReport per variable per month:
  32 variables × 60 months = 1,920 MeasureReport JSON files

Output:
  fhir/measure_reports/by_indicator/{var_id}/tb-{var_id}-kathmandu-{year}-{month}.json
  fhir/measure_reports/bundles/bundle-{var_id}.json   (63 entries each)
  fhir/measure_reports/bundles/bundle-all.json         (1,923 entries)
  outputs/reports/07_FHIR_MeasureReport_Generation_Report.txt
"""

import csv, json, os, shutil
from datetime import datetime, timezone, date

BASE        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_CSV   = os.path.join(BASE, "data", "final", "final_cleaned_data.csv")
OUTPUT_BASE = os.path.join(BASE, "fhir", "measure_reports")
BY_VAR_DIR  = os.path.join(OUTPUT_BASE, "by_indicator")
BUNDLES_DIR = os.path.join(OUTPUT_BASE, "bundles")
REPORT_OUT  = os.path.join(BASE, "outputs", "reports",
                            "07_FHIR_MeasureReport_Generation_Report.txt")

FHIR_BASE   = "https://iihms.gov.np/fhir"
DENOM_COL   = "district_pop_mid_year_cbs"

# ── Variable catalogue ────────────────────────────────────────────────────────
# (measure-id-suffix, csv_column, gap_affected)
# gap_affected=True  → apply data-absent-reason for Baishak/Jestha/Asar 2078
RATIO_VARIABLES = [
    ("new-cases-total",   "new_cases_total",  False),
    ("new-cases-female",  "new_cases_female", True),
    ("new-cases-male",    "new_cases_male",   True),
    ("relapse-total",     "relapse_total",    True),
    ("relapse-female",    "relapse_female",   True),
    ("relapse-male",      "relapse_male",     True),
    ("total-tb-notified", "total_tb_mf",      True),
    ("total-tb-female",   "total_tb_female",  True),
    ("total-tb-male",     "total_tb_male",    True),
    ("hiv-positive",      "tb_hiv_positive",  False),
    ("age-0to4-f",        "0_to_4_f",         True),
    ("age-0to4-m",        "0_to_4_m",         True),
    ("age-5to14-f",       "5_to_14_f",        True),
    ("age-5to14-m",       "5_to_14_m",        True),
    ("age-15to24-f",      "15_to_24_f",       True),
    ("age-15to24-m",      "15_to_24_m",       True),
    ("age-25to34-f",      "25_to_34_f",       True),
    ("age-25to34-m",      "25_to_34_m",       True),
    ("age-35to44-f",      "35_to_44_f",       True),
    ("age-35to44-m",      "35_to_44_m",       True),
    ("age-45to54-f",      "45_to_54_f",       True),
    ("age-45to54-m",      "45_to_54_m",       True),
    ("age-55to64-f",      "55_to_64_f",       True),
    ("age-55to64-m",      "55_to_64_m",       True),
    ("age-65plus-f",      "65_f",             True),
    ("age-65plus-m",      "65_m",             True),
]

COHORT_VARIABLES = [
    ("pbc-reg",  "pbc_reg"),
    ("cured",    "cured"),
    ("failed",   "failed"),
    ("died",     "died"),
    ("ltfu",     "ltfu"),
    ("not-eval", "not_eval"),
]

GAP_MONTHS = {("2078", "Baishak"), ("2078", "Jestha"), ("2078", "Asar")}

# ── FHIR constants ────────────────────────────────────────────────────────────
DAR_EXT     = [{"url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
                "valueCode": "not-reported"}]
POP_SYS     = "http://terminology.hl7.org/CodeSystem/measure-population"
UCUM_SYS    = "http://unitsofmeasure.org"
NCP_EXT_URL = f"{FHIR_BASE}/StructureDefinition/nepali-fiscal-period"

# ── Shared canonical resources ────────────────────────────────────────────────
ORG_MOHP = {
    "resourceType": "Organization", "id": "org-mohp",
    "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Organization"]},
    "identifier": [{"system": f"{FHIR_BASE}/NamingSystem/organization-id",
                    "value": "org-mohp"}],
    "name": "Ministry of Health and Population, Nepal", "alias": ["MoHP"],
}
ORG_NTP = {
    "resourceType": "Organization", "id": "org-ntp",
    "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Organization"]},
    "identifier": [{"system": f"{FHIR_BASE}/NamingSystem/organization-id",
                    "value": "org-ntp"}],
    "name": "National Tuberculosis Programme", "alias": ["NTP"],
    "partOf": {"reference": f"{FHIR_BASE}/Organization/org-mohp",
               "display": "Ministry of Health and Population, Nepal"},
}
LOC_KTM = {
    "resourceType": "Location", "id": "loc-kathmandu",
    "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Location"]},
    "identifier": [{"system": f"{FHIR_BASE}/NamingSystem/location-id",
                    "value": "loc-kathmandu"}],
    "name": "Kathmandu District, Nepal",
    "physicalType": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                                  "code": "jdn", "display": "Jurisdiction"}]},
}
CONTAINED = [
    {"resourceType": "Organization", "id": "org-mohp",
     "name": "Ministry of Health and Population, Nepal", "alias": ["MoHP"]},
    {"resourceType": "Organization", "id": "org-ntp",
     "name": "National Tuberculosis Programme", "alias": ["NTP"],
     "partOf": {"reference": "#org-mohp"}},
    {"resourceType": "Location", "id": "loc-kathmandu",
     "name": "Kathmandu District, Nepal",
     "physicalType": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                                   "code": "jdn", "display": "Jurisdiction"}]}},
]
SHARED_ENTRIES = [
    {"fullUrl": f"{FHIR_BASE}/Organization/org-mohp", "resource": ORG_MOHP},
    {"fullUrl": f"{FHIR_BASE}/Organization/org-ntp",  "resource": ORG_NTP},
    {"fullUrl": f"{FHIR_BASE}/Location/loc-kathmandu","resource": LOC_KTM},
]

# ── Calendar helpers ──────────────────────────────────────────────────────────
MONTH_TO_GM = {
    "Baishak": 4,  "Jestha": 5,  "Asar": 6,    "Shrawan": 7,
    "Bhadra":  8,  "Ashwin": 9,  "Kartik": 10, "Mangsir": 11,
    "Poush":  12,  "Magh":   1,  "Falgun":  2, "Chaitra":  3,
}
FY_ORDER = ["Shrawan", "Bhadra", "Ashwin", "Kartik", "Mangsir", "Poush",
            "Magh", "Falgun", "Chaitra", "Baishak", "Jestha", "Asar"]


def iso_period(bs_year, bs_month):
    m      = MONTH_TO_GM[bs_month]
    g_year = bs_year - 57 if m >= 4 else bs_year - 56
    nm, ny = (m + 1, g_year) if m < 12 else (1, g_year + 1)
    return f"{g_year}-{m:02d}-16", f"{ny}-{nm:02d}-15"


def fiscal_year(bs_year, bs_month):
    pos = FY_ORDER.index(bs_month) + 1
    if pos <= 9:
        return f"{bs_year}/{str(bs_year + 1)[-2:]}"
    return f"{bs_year - 1}/{str(bs_year)[-2:]}"


# ── Population entry helpers ──────────────────────────────────────────────────
def pop_entry(code, count, absent=False):
    p = {"code": {"coding": [{"system": POP_SYS, "code": code,
                               "display": code.replace("-", " ").title()}]}}
    if absent:
        p["_count"] = {"extension": DAR_EXT}
    else:
        p["count"] = count
    return p


def period_block(bs_year, bs_month, start, end, fy):
    return {
        "extension": [{"url": NCP_EXT_URL, "extension": [
            {"url": "bs-year",     "valueInteger": int(bs_year)},
            {"url": "bs-month",    "valueString":  bs_month},
            {"url": "fiscal-year", "valueString":  fy},
        ]}],
        "start": start, "end": end,
    }


def measure_score_block(value=None, absent=False):
    if absent:
        return {"unit": "1", "system": UCUM_SYS, "code": "1",
                "_value": {"extension": DAR_EXT}}
    return {"value": value, "unit": "1", "system": UCUM_SYS, "code": "1"}


# ── MeasureReport builders ────────────────────────────────────────────────────
def build_ratio_report(row, var_id, csv_col, gap_affected,
                        report_id, start, end, fy, standalone, now_str):
    bs_year  = row["bs_year"]
    bs_month = row["bs_month"].strip()

    absent = gap_affected and (bs_year, bs_month) in GAP_MONTHS

    num_count = int(float(row[csv_col]))
    den_count = int(float(row[DENOM_COL]))

    if absent:
        numer_pop  = pop_entry("numerator",   0,         absent=True)
        ms_block   = measure_score_block(absent=True)
    else:
        numer_pop  = pop_entry("numerator",   num_count, absent=False)
        ratio      = round(num_count / den_count, 8) if den_count > 0 else 0.0
        ms_block   = measure_score_block(value=ratio)

    denom_pop    = pop_entry("denominator", den_count, absent=False)
    subject_ref  = "#loc-kathmandu"  if standalone else f"{FHIR_BASE}/Location/loc-kathmandu"
    reporter_ref = "#org-ntp"        if standalone else f"{FHIR_BASE}/Organization/org-ntp"

    report = {
        "resourceType": "MeasureReport",
        "id": report_id,
        "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/MeasureReport"]},
        "status": "complete",
        "type":   "summary",
        "measure": f"{FHIR_BASE}/Measure/nepal-tb-{var_id}",
        "subject":  {"reference": subject_ref,  "display": "Kathmandu District, Nepal"},
        "date":     now_str,
        "reporter": {"reference": reporter_ref, "display": "National Tuberculosis Programme"},
        "period":   period_block(bs_year, bs_month, start, end, fy),
        "group": [{"id":         f"group-nepal-tb-{var_id}",
                   "population": [numer_pop, denom_pop],
                   "measureScore": ms_block}],
    }
    if standalone:
        report["contained"] = CONTAINED
    return report


def build_cohort_report(row, var_id, csv_col,
                         report_id, start, end, fy, standalone, now_str):
    bs_year  = row["bs_year"]
    bs_month = row["bs_month"].strip()
    count    = int(float(row[csv_col]))

    pop_block = pop_entry("initial-population", count)
    ms_block  = {"value": count, "unit": "count", "system": UCUM_SYS, "code": "1"}

    subject_ref  = "#loc-kathmandu"  if standalone else f"{FHIR_BASE}/Location/loc-kathmandu"
    reporter_ref = "#org-ntp"        if standalone else f"{FHIR_BASE}/Organization/org-ntp"

    report = {
        "resourceType": "MeasureReport",
        "id": report_id,
        "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/MeasureReport"]},
        "status": "complete",
        "type":   "summary",
        "measure": f"{FHIR_BASE}/Measure/nepal-tb-{var_id}",
        "subject":  {"reference": subject_ref,  "display": "Kathmandu District, Nepal"},
        "date":     now_str,
        "reporter": {"reference": reporter_ref, "display": "National Tuberculosis Programme"},
        "period":   period_block(bs_year, bs_month, start, end, fy),
        "group": [{"id":         f"group-nepal-tb-{var_id}",
                   "population": [pop_block],
                   "measureScore": ms_block}],
    }
    if standalone:
        report["contained"] = CONTAINED
    return report


def make_bundle(bundle_id, mr_entries, now_str):
    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Bundle"]},
        "type": "collection",
        "timestamp": now_str,
        "entry": SHARED_ENTRIES + mr_entries,
    }


# ── Report writer ─────────────────────────────────────────────────────────────
def write_report(stats, now_str):
    today = date.today().isoformat()
    L = []
    L.append("=" * 80)
    L.append("PHASE 4: FHIR R4 MEASUREREPORT GENERATION REPORT")
    L.append("=" * 80)
    L.append("Project    : IIHMS TB Data Standardization | Kathmandu District, Nepal")
    L.append(f"Generated  : {today}")
    L.append(f"FHIR Ver   : R4 (4.0.1)")
    L.append("Status     : COMPLETE")
    L.append("")
    L.append("-" * 80)
    L.append("GENERATION SUMMARY")
    L.append("-" * 80)
    L.append(f"  Input CSV               : data/final/final_cleaned_data.csv")
    L.append(f"  Total months            : {stats['months']}")
    L.append(f"  Total variables         : {stats['variables']} (26 ratio + 6 cohort)")
    L.append(f"  MeasureReport files     : {stats['total_reports']}  (by_indicator/)")
    L.append(f"  Per-variable bundles    : {stats['var_bundles']}  (bundles/)")
    L.append(f"  Master bundle           : 1  (bundle-all.json)")
    L.append(f"  DAR entries (not-reported): {stats['dar_count']}  "
             f"(24 gap-affected variables × 3 months)")
    L.append("")
    L.append("-" * 80)
    L.append("VARIABLE CATALOGUE")
    L.append("-" * 80)
    L.append(f"  {'Variable ID':<30} {'CSV Column':<22} {'Type':<8} {'DAR?'}")
    L.append("  " + "-" * 72)
    for var_id, csv_col, gap in RATIO_VARIABLES:
        L.append(f"  {'nepal-tb-'+var_id:<30} {csv_col:<22} {'ratio':<8} "
                 f"{'Yes (3 months)' if gap else 'No'}")
    for var_id, csv_col in COHORT_VARIABLES:
        L.append(f"  {'nepal-tb-'+var_id:<30} {csv_col:<22} {'cohort':<8} No")
    L.append("")
    L.append("-" * 80)
    L.append("DATA-ABSENT-REASON SCOPE")
    L.append("-" * 80)
    L.append("  Gap months: Baishak 2078, Jestha 2078, Asar 2078")
    L.append("  Reason: Source DHIS2 system had no sex/age data for these 3 months.")
    L.append("  Variables NOT affected (data valid for all 60 months):")
    L.append("    nepal-tb-new-cases-total, nepal-tb-hiv-positive,")
    L.append("    nepal-tb-pbc-reg, nepal-tb-cured, nepal-tb-failed,")
    L.append("    nepal-tb-died, nepal-tb-ltfu, nepal-tb-not-eval")
    L.append("  Variables WITH data-absent-reason for gap months (24 variables):")
    L.append("    All sex-disaggregated counts and all 16 age-sex band variables.")
    L.append("")
    L.append("-" * 80)
    L.append("FILE STRUCTURE")
    L.append("-" * 80)
    L.append("  fhir/measure_reports/")
    L.append("    by_indicator/")
    for var_id, _, _ in RATIO_VARIABLES:
        L.append(f"      {var_id}/   (60 standalone JSON files)")
    for var_id, _ in COHORT_VARIABLES:
        L.append(f"      {var_id}/   (60 standalone JSON files)")
    L.append("    bundles/")
    L.append(f"      bundle-{{variable}}.json  (32 files — 3 shared + 60 MRs each)")
    L.append(f"      bundle-all.json           (3 shared + {stats['total_reports']} MRs)")
    L.append("")
    L.append("=" * 80)

    os.makedirs(os.path.dirname(REPORT_OUT), exist_ok=True)
    with open(REPORT_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"  Report → {REPORT_OUT}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if os.path.exists(OUTPUT_BASE):
        shutil.rmtree(OUTPUT_BASE)
    os.makedirs(BY_VAR_DIR, exist_ok=True)
    os.makedirs(BUNDLES_DIR, exist_ok=True)

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows)} rows from {INPUT_CSV}")

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_mr_entries = []
    var_mr_entries = {}
    for var_id, _, _ in RATIO_VARIABLES:
        var_mr_entries[var_id] = []
    for var_id, _ in COHORT_VARIABLES:
        var_mr_entries[var_id] = []

    total_reports = 0
    dar_count     = 0

    for row in rows:
        bs_year  = row["bs_year"]
        bs_month = row["bs_month"].strip()
        month_lc = bs_month.lower()
        start, end = iso_period(int(bs_year), bs_month)
        fy         = fiscal_year(int(bs_year), bs_month)

        # ── Ratio variables
        for var_id, csv_col, gap_affected in RATIO_VARIABLES:
            report_id = f"tb-{var_id}-kathmandu-{bs_year}-{month_lc}"
            is_absent = gap_affected and (bs_year, bs_month) in GAP_MONTHS

            standalone = build_ratio_report(
                row, var_id, csv_col, gap_affected,
                report_id, start, end, fy, standalone=True, now_str=now_str)
            var_dir = os.path.join(BY_VAR_DIR, var_id)
            os.makedirs(var_dir, exist_ok=True)
            with open(os.path.join(var_dir, f"{report_id}.json"), "w") as f:
                json.dump(standalone, f, indent=2)

            bundle_ver = build_ratio_report(
                row, var_id, csv_col, gap_affected,
                report_id, start, end, fy, standalone=False, now_str=now_str)
            entry = {"fullUrl": f"{FHIR_BASE}/MeasureReport/{report_id}",
                     "resource": bundle_ver}
            all_mr_entries.append(entry)
            var_mr_entries[var_id].append(entry)
            total_reports += 1
            if is_absent:
                dar_count += 1

        # ── Cohort variables
        for var_id, csv_col in COHORT_VARIABLES:
            report_id = f"tb-{var_id}-kathmandu-{bs_year}-{month_lc}"

            standalone = build_cohort_report(
                row, var_id, csv_col,
                report_id, start, end, fy, standalone=True, now_str=now_str)
            var_dir = os.path.join(BY_VAR_DIR, var_id)
            os.makedirs(var_dir, exist_ok=True)
            with open(os.path.join(var_dir, f"{report_id}.json"), "w") as f:
                json.dump(standalone, f, indent=2)

            bundle_ver = build_cohort_report(
                row, var_id, csv_col,
                report_id, start, end, fy, standalone=False, now_str=now_str)
            entry = {"fullUrl": f"{FHIR_BASE}/MeasureReport/{report_id}",
                     "resource": bundle_ver}
            all_mr_entries.append(entry)
            var_mr_entries[var_id].append(entry)
            total_reports += 1

    print(f"Generated {total_reports} MeasureReport files  "
          f"(DAR entries: {dar_count})")

    # ── Per-variable bundles
    for var_id, entries in var_mr_entries.items():
        bundle = make_bundle(f"bundle-kathmandu-{var_id}", entries, now_str)
        with open(os.path.join(BUNDLES_DIR, f"bundle-{var_id}.json"), "w") as f:
            json.dump(bundle, f, indent=2)
    print(f"Generated {len(var_mr_entries)} per-variable bundles")

    # ── Master bundle
    master = make_bundle("bundle-kathmandu-all-measurereports",
                          all_mr_entries, now_str)
    with open(os.path.join(BUNDLES_DIR, "bundle-all.json"), "w") as f:
        json.dump(master, f, indent=2)
    print(f"Generated master bundle  "
          f"({len(master['entry'])} entries = 3 shared + {total_reports} MRs)")

    # ── Report
    write_report({
        "months":        len(rows),
        "variables":     len(RATIO_VARIABLES) + len(COHORT_VARIABLES),
        "total_reports": total_reports,
        "var_bundles":   len(var_mr_entries),
        "dar_count":     dar_count,
    }, now_str)

    print("\nPhase 4 — MeasureReport generation complete.")


if __name__ == "__main__":
    main()
