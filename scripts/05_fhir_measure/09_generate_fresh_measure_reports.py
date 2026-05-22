"""
Fresh MeasureReport generation — reads final_cleaned_data.csv directly.
FHIR R4 compliant output.

Scoring:
  - 7 ratio indicators   → numerator (TB count) + denominator (district_pop_mid_year_cbs)
  - 6 cohort indicators  → initial-population (annual count)

Output:
  fhir/measure_reports/by_indicator/{id}/tb-{id}-kathmandu-{year}-{month}.json
  fhir/measure_reports/bundles/bundle-all.json
  fhir/measure_reports/bundles/bundle-{indicator}.json
"""

import csv, json, os, shutil
from datetime import datetime, timezone

BASE        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_CSV   = os.path.join(BASE, "data/final/final_cleaned_data.csv")
OUTPUT_BASE = os.path.join(BASE, "fhir/measure_reports")
BY_IND_DIR  = os.path.join(OUTPUT_BASE, "by_indicator")
BUNDLES_DIR = os.path.join(OUTPUT_BASE, "bundles")

OLD_DIRS = [
    os.path.join(BASE, "fhir/kathmandu_monthly_measure_report"),
    os.path.join(BASE, "fhir/measures/measure_report"),
]

FHIR_BASE      = "https://iihms.gov.np/fhir"
DENOMINATOR_COL = "district_pop_mid_year_cbs"

# ── Calendar helpers ──────────────────────────────────────────────────────────
MONTH_TO_GM = {
    "Baishak": 4,  "Jestha": 5,  "Asar": 6,    "Shrawan": 7,
    "Bhadra":  8,  "Ashwin": 9,  "Kartik": 10, "Mangsir": 11,
    "Poush":  12,  "Magh":   1,  "Falgun":  2, "Chaitra":  3,
}
FY_ORDER = ["Shrawan","Bhadra","Ashwin","Kartik","Mangsir","Poush",
            "Magh","Falgun","Chaitra","Baishak","Jestha","Asar"]


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


# ── Indicator specs ───────────────────────────────────────────────────────────
# Ratio: (id, title, num_csv_col)
RATIO_INDICATORS = [
    ("new-cases-total",   "New TB Cases (Total)",        "new_cases_total"),
    ("new-cases-female",  "New TB Cases (Female)",       "new_cases_female"),
    ("new-cases-male",    "New TB Cases (Male)",         "new_cases_male"),
    ("relapse-total",     "TB Relapse Cases (Total)",    "relapse_total"),
    ("relapse-female",    "TB Relapse Cases (Female)",   "relapse_female"),
    ("relapse-male",      "TB Relapse Cases (Male)",     "relapse_male"),
    ("total-tb-notified", "Total TB Cases Notified",     "total_tb_m+f"),
]

# Cohort: (id, title, csv_col)
COHORT_INDICATORS = [
    ("pbc-reg",  "PBC Registered Cohort",               "pbc_reg"),
    ("cured",    "TB Patients Cured",                   "cured"),
    ("failed",   "TB Treatment Failures",               "failed"),
    ("died",     "TB Patients Died",                    "died"),
    ("ltfu",     "TB Patients Lost to Follow-up",       "ltfu"),
    ("not-eval", "TB Treatment Outcomes Not Evaluated", "not_eval"),
]

ALL_INDICATORS = [(i[0], i[1]) for i in RATIO_INDICATORS + COHORT_INDICATORS]

# Under-reported: numerator absent for these months on all ratio indicators
UNDER_REPORTED = {("2078", "Baishak"), ("2078", "Jestha"), ("2078", "Asar")}

DAR_EXT = [{"url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
             "valueCode": "not-reported"}]

POP_CODE_SYS = "http://terminology.hl7.org/CodeSystem/measure-population"

# ── Shared canonical resources ────────────────────────────────────────────────
ORG_MOHP = {
    "resourceType": "Organization", "id": "org-mohp",
    "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Organization"]},
    "identifier": [{"system": f"{FHIR_BASE}/NamingSystem/organization-id", "value": "org-mohp"}],
    "name": "Ministry of Health and Population, Nepal", "alias": ["MoHP"],
}
ORG_NTP = {
    "resourceType": "Organization", "id": "org-ntp",
    "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Organization"]},
    "identifier": [{"system": f"{FHIR_BASE}/NamingSystem/organization-id", "value": "org-ntp"}],
    "name": "National Tuberculosis Programme", "alias": ["NTP"],
    "partOf": {"reference": f"{FHIR_BASE}/Organization/org-mohp",
               "display": "Ministry of Health and Population, Nepal"},
}
LOC_KTM = {
    "resourceType": "Location", "id": "loc-kathmandu",
    "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Location"]},
    "identifier": [{"system": f"{FHIR_BASE}/NamingSystem/location-id", "value": "loc-kathmandu"}],
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


def pop_entry(code, count, absent=False):
    p = {"code": {"coding": [{"system": POP_CODE_SYS, "code": code,
                               "display": code.replace("-", " ").title()}]}}
    if absent:
        p["_count"] = {"extension": DAR_EXT}
    else:
        p["count"] = count
    return p


def period_block(bs_year, bs_month, start, end, fy):
    return {
        "extension": [{"url": f"{FHIR_BASE}/StructureDefinition/nepali-fiscal-period",
                        "extension": [
                            {"url": "bs-year",     "valueInteger": int(bs_year)},
                            {"url": "bs-month",    "valueString":  bs_month},
                            {"url": "fiscal-year", "valueString":  fy},
                        ]}],
        "start": start, "end": end,
    }


# ── Ratio MeasureReport ───────────────────────────────────────────────────────
def build_ratio_report(row, ind_id, num_col, report_id, start, end, fy,
                        standalone=True, now_str=""):
    bs_year  = row["bs_year"]
    bs_month = row["bs_month"].strip()

    num_raw  = row[num_col].strip()
    den_raw  = row[DENOMINATOR_COL].strip()

    numer_absent = (bs_year, bs_month) in UNDER_REPORTED or num_raw == ""
    num_count    = int(float(num_raw)) if num_raw != "" else 0
    den_count    = int(float(den_raw))

    numer_pop = pop_entry("numerator",   num_count, absent=numer_absent)
    denom_pop = pop_entry("denominator", den_count, absent=False)

    if numer_absent:
        measure_score = {"unit": "1", "system": "http://unitsofmeasure.org", "code": "1",
                         "_value": {"extension": DAR_EXT}}
    else:
        ratio = round(num_count / den_count, 8) if den_count > 0 else 0.0
        measure_score = {"value": ratio, "unit": "1",
                         "system": "http://unitsofmeasure.org", "code": "1"}

    subject_ref  = "#loc-kathmandu"            if standalone else f"{FHIR_BASE}/Location/loc-kathmandu"
    reporter_ref = "#org-ntp"                  if standalone else f"{FHIR_BASE}/Organization/org-ntp"

    report = {
        "resourceType": "MeasureReport",
        "id": report_id,
        "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/MeasureReport"]},
        "status": "complete",
        "type": "summary",
        "measure": f"{FHIR_BASE}/Measure/nepal-tb-{ind_id}",
        "subject":  {"reference": subject_ref,  "display": "Kathmandu District, Nepal"},
        "date":     now_str,
        "reporter": {"reference": reporter_ref, "display": "National Tuberculosis Programme"},
        "period":   period_block(bs_year, bs_month, start, end, fy),
        "group": [{"id": f"group-nepal-tb-{ind_id}",
                   "population": [numer_pop, denom_pop],
                   "measureScore": measure_score}],
    }
    if standalone:
        report["contained"] = CONTAINED
    return report


# ── Cohort MeasureReport ──────────────────────────────────────────────────────
def build_cohort_report(row, ind_id, csv_col, report_id, start, end, fy,
                         standalone=True, now_str=""):
    bs_year  = row["bs_year"]
    bs_month = row["bs_month"].strip()

    raw     = row[csv_col].strip()
    missing = raw == ""
    count   = int(float(raw)) if not missing else 0

    if missing:
        population    = pop_entry("initial-population", 0, absent=True)
        measure_score = {"unit": "count", "system": "http://unitsofmeasure.org", "code": "1",
                         "_value": {"extension": DAR_EXT}}
    else:
        population    = pop_entry("initial-population", count)
        measure_score = {"value": count, "unit": "count",
                         "system": "http://unitsofmeasure.org", "code": "1"}

    subject_ref  = "#loc-kathmandu"  if standalone else f"{FHIR_BASE}/Location/loc-kathmandu"
    reporter_ref = "#org-ntp"        if standalone else f"{FHIR_BASE}/Organization/org-ntp"

    report = {
        "resourceType": "MeasureReport",
        "id": report_id,
        "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/MeasureReport"]},
        "status": "complete",
        "type": "summary",
        "measure": f"{FHIR_BASE}/Measure/nepal-tb-{ind_id}",
        "subject":  {"reference": subject_ref,  "display": "Kathmandu District, Nepal"},
        "date":     now_str,
        "reporter": {"reference": reporter_ref, "display": "National Tuberculosis Programme"},
        "period":   period_block(bs_year, bs_month, start, end, fy),
        "group": [{"id": f"group-nepal-tb-{ind_id}",
                   "population": [population],
                   "measureScore": measure_score}],
    }
    if standalone:
        report["contained"] = CONTAINED
    return report


def make_bundle(bundle_id, entries, now_str, shared_entries):
    return {
        "resourceType": "Bundle",
        "id": bundle_id,
        "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Bundle"]},
        "type": "collection",
        "timestamp": now_str,
        "entry": shared_entries + entries,
    }


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    for d in OLD_DIRS:
        if os.path.exists(d):
            shutil.rmtree(d); print(f"Deleted: {d}")

    if os.path.exists(OUTPUT_BASE):
        shutil.rmtree(OUTPUT_BASE)
    os.makedirs(BY_IND_DIR, exist_ok=True)
    os.makedirs(BUNDLES_DIR, exist_ok=True)

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows)} rows from CSV")

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    shared_entries = [
        {"fullUrl": f"{FHIR_BASE}/Organization/org-mohp", "resource": ORG_MOHP},
        {"fullUrl": f"{FHIR_BASE}/Organization/org-ntp",  "resource": ORG_NTP},
        {"fullUrl": f"{FHIR_BASE}/Location/loc-kathmandu","resource": LOC_KTM},
    ]

    all_bundle_entries = []
    ind_bundle_entries = {ind_id: [] for ind_id, _ in ALL_INDICATORS}

    for row in rows:
        bs_year  = row["bs_year"]
        bs_month = row["bs_month"].strip()
        month_lc = bs_month.lower()
        start, end = iso_period(int(bs_year), bs_month)
        fy         = fiscal_year(int(bs_year), bs_month)

        # Ratio indicators
        for ind_id, _, num_col in RATIO_INDICATORS:
            report_id  = f"tb-{ind_id}-kathmandu-{bs_year}-{month_lc}"
            standalone = build_ratio_report(row, ind_id, num_col, report_id,
                                            start, end, fy, standalone=True, now_str=now_str)
            ind_dir = os.path.join(BY_IND_DIR, ind_id)
            os.makedirs(ind_dir, exist_ok=True)
            with open(os.path.join(ind_dir, f"{report_id}.json"), "w") as f:
                json.dump(standalone, f, indent=2)

            bundle_ver = build_ratio_report(row, ind_id, num_col, report_id,
                                             start, end, fy, standalone=False, now_str=now_str)
            entry = {"fullUrl": f"{FHIR_BASE}/MeasureReport/{report_id}", "resource": bundle_ver}
            all_bundle_entries.append(entry)
            ind_bundle_entries[ind_id].append(entry)

        # Cohort indicators
        for ind_id, _, csv_col in COHORT_INDICATORS:
            report_id  = f"tb-{ind_id}-kathmandu-{bs_year}-{month_lc}"
            standalone = build_cohort_report(row, ind_id, csv_col, report_id,
                                              start, end, fy, standalone=True, now_str=now_str)
            ind_dir = os.path.join(BY_IND_DIR, ind_id)
            os.makedirs(ind_dir, exist_ok=True)
            with open(os.path.join(ind_dir, f"{report_id}.json"), "w") as f:
                json.dump(standalone, f, indent=2)

            bundle_ver = build_cohort_report(row, ind_id, csv_col, report_id,
                                              start, end, fy, standalone=False, now_str=now_str)
            entry = {"fullUrl": f"{FHIR_BASE}/MeasureReport/{report_id}", "resource": bundle_ver}
            all_bundle_entries.append(entry)
            ind_bundle_entries[ind_id].append(entry)

    print(f"Generated {len(all_bundle_entries)} MeasureReport files")

    for ind_id, entries in ind_bundle_entries.items():
        bundle = make_bundle(f"bundle-kathmandu-{ind_id}", entries, now_str, shared_entries)
        with open(os.path.join(BUNDLES_DIR, f"bundle-{ind_id}.json"), "w") as f:
            json.dump(bundle, f, indent=2)
    print(f"Generated {len(ALL_INDICATORS)} per-indicator bundles")

    master = make_bundle("bundle-kathmandu-all-measurereports",
                         all_bundle_entries, now_str, shared_entries)
    master_path = os.path.join(BUNDLES_DIR, "bundle-all.json")
    with open(master_path, "w") as f:
        json.dump(master, f, indent=2)
    print(f"Generated master bundle ({len(master['entry'])} entries) → {master_path}")


if __name__ == "__main__":
    main()
