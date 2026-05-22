"""
Fresh MeasureReport generation — reads final_cleaned_data.csv directly.
FHIR R4 compliant output. Cohort scoring (raw counts).

Individual files  (standalone, with contained):
  fhir/measure_reports/by_indicator/{indicator-id}/tb-{id}-kathmandu-{year}-{month}.json

Bundles (R4 collection, shared resources as bundle entries, absolute fullUrl):
  fhir/measure_reports/bundles/bundle-all.json            (3 shared + 780 reports)
  fhir/measure_reports/bundles/bundle-{indicator}.json    (3 shared + 60 reports each)
"""

import csv
import json
import os
import shutil
from datetime import datetime, timezone

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE        = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_CSV   = os.path.join(BASE, "data/final/final_cleaned_data.csv")
OUTPUT_BASE = os.path.join(BASE, "fhir/measure_reports")
BY_IND_DIR  = os.path.join(OUTPUT_BASE, "by_indicator")
BUNDLES_DIR = os.path.join(OUTPUT_BASE, "bundles")

OLD_DIRS = [
    os.path.join(BASE, "fhir/kathmandu_monthly_measure_report"),
    os.path.join(BASE, "fhir/measures/measure_report"),
]

# ── Canonical base URL ────────────────────────────────────────────────────────
FHIR_BASE = "https://iihms.gov.np/fhir"

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


# ── 13 indicator specs ─────────────────────────────────────────────────────────
# (indicator-id, title, csv-column)
INDICATORS = [
    ("new-cases-total",      "New TB Cases (Total)",                          "new_cases_total"),
    ("new-cases-female",     "New TB Cases (Female)",                         "new_cases_female"),
    ("new-cases-male",       "New TB Cases (Male)",                           "new_cases_male"),
    ("relapse-total",        "TB Relapse Cases (Total)",                      "relapse_total"),
    ("relapse-female",       "TB Relapse Cases (Female)",                     "relapse_female"),
    ("relapse-male",         "TB Relapse Cases (Male)",                       "relapse_male"),
    ("total-tb-notified",    "Total TB Cases Notified",                       "total_tb_m+f"),
    ("pbc-reg",              "PBC Registered Cohort",                         "pbc_reg"),
    ("cured",                "TB Patients Cured",                             "cured"),
    ("failed",               "TB Treatment Failures",                         "failed"),
    ("died",                 "TB Patients Died",                              "died"),
    ("ltfu",                 "TB Patients Lost to Follow-up",                 "ltfu"),
    ("not-eval",             "TB Treatment Outcomes Not Evaluated",           "not_eval"),
]

# Under-reported months: total_tb_m+f = 0 (BS 2078 Baishak/Jestha/Asar)
UNDER_REPORTED = {("2078", "Baishak"), ("2078", "Jestha"), ("2078", "Asar")}

# Monthly notification-based columns affected by under-reporting
MONTHLY_COLS = {
    "new_cases_total", "new_cases_female", "new_cases_male",
    "relapse_total", "relapse_female", "relapse_male", "total_tb_m+f",
}

DAR_EXT = [{"url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
             "valueCode": "not-reported"}]

# ── Shared canonical resources ────────────────────────────────────────────────
ORG_MOHP = {
    "resourceType": "Organization",
    "id": "org-mohp",
    "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Organization"]},
    "identifier": [{"system": f"{FHIR_BASE}/NamingSystem/organization-id",
                    "value": "org-mohp"}],
    "name": "Ministry of Health and Population, Nepal",
    "alias": ["MoHP"],
}

ORG_NTP = {
    "resourceType": "Organization",
    "id": "org-ntp",
    "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Organization"]},
    "identifier": [{"system": f"{FHIR_BASE}/NamingSystem/organization-id",
                    "value": "org-ntp"}],
    "name": "National Tuberculosis Programme",
    "alias": ["NTP"],
    "partOf": {"reference": f"{FHIR_BASE}/Organization/org-mohp",
               "display": "Ministry of Health and Population, Nepal"},
}

LOC_KTM = {
    "resourceType": "Location",
    "id": "loc-kathmandu",
    "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Location"]},
    "identifier": [{"system": f"{FHIR_BASE}/NamingSystem/location-id",
                    "value": "loc-kathmandu"}],
    "name": "Kathmandu District, Nepal",
    "physicalType": {
        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                    "code": "jdn", "display": "Jurisdiction"}]
    },
}

CONTAINED_FOR_STANDALONE = [
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


# ── Helpers ───────────────────────────────────────────────────────────────────
def build_report(row, ind_id, csv_col, report_id, start, end, fy,
                 standalone=True, now_str=""):
    bs_year  = row["bs_year"]
    bs_month = row["bs_month"].strip()

    raw     = row[csv_col].strip()
    # Data absent: under-reported months (monthly notification cols) or genuinely missing cell
    no_data = ((bs_year, bs_month) in UNDER_REPORTED and csv_col in MONTHLY_COLS) or raw == ""
    count   = int(float(raw)) if raw != "" else 0

    if no_data:
        population = {
            "code": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/measure-population",
                                  "code": "initial-population",
                                  "display": "Initial Population"}]},
            "_count": {"extension": DAR_EXT},
        }
        measure_score = {
            "unit": "count",
            "system": "http://unitsofmeasure.org",
            "code": "1",
            "_value": {"extension": DAR_EXT},
        }
    else:
        population = {
            "code": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/measure-population",
                                  "code": "initial-population",
                                  "display": "Initial Population"}]},
            "count": count,
        }
        measure_score = {
            "value": count,
            "unit": "count",
            "system": "http://unitsofmeasure.org",
            "code": "1",
        }

    if standalone:
        subject_ref  = "#loc-kathmandu"
        reporter_ref = "#org-ntp"
    else:
        subject_ref  = f"{FHIR_BASE}/Location/loc-kathmandu"
        reporter_ref = f"{FHIR_BASE}/Organization/org-ntp"

    report = {
        "resourceType": "MeasureReport",
        "id": report_id,
        "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/MeasureReport"]},
        "status": "complete",
        "type": "summary",
        "measure": f"{FHIR_BASE}/Measure/nepal-tb-{ind_id}",
        "subject": {"reference": subject_ref,
                    "display": "Kathmandu District, Nepal"},
        "date": now_str,
        "reporter": {"reference": reporter_ref,
                     "display": "National Tuberculosis Programme"},
        "period": {
            "extension": [{
                "url": f"{FHIR_BASE}/StructureDefinition/nepali-fiscal-period",
                "extension": [
                    {"url": "bs-year",     "valueInteger": int(bs_year)},
                    {"url": "bs-month",    "valueString":  bs_month},
                    {"url": "fiscal-year", "valueString":  fy},
                ]
            }],
            "start": start,
            "end":   end,
        },
        "group": [{
            "id": f"group-nepal-tb-{ind_id}",
            "population": [population],
            "measureScore": measure_score,
        }],
    }

    if standalone:
        report["contained"] = CONTAINED_FOR_STANDALONE

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
    # 1. Delete old trees
    for d in OLD_DIRS:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"Deleted: {d}")

    # 2. Wipe and recreate output dirs
    if os.path.exists(OUTPUT_BASE):
        shutil.rmtree(OUTPUT_BASE)
    os.makedirs(BY_IND_DIR, exist_ok=True)
    os.makedirs(BUNDLES_DIR, exist_ok=True)

    # 3. Read CSV
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"Loaded {len(rows)} rows from CSV")

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    shared_entries = [
        {"fullUrl": f"{FHIR_BASE}/Organization/org-mohp", "resource": ORG_MOHP},
        {"fullUrl": f"{FHIR_BASE}/Organization/org-ntp",  "resource": ORG_NTP},
        {"fullUrl": f"{FHIR_BASE}/Location/loc-kathmandu","resource": LOC_KTM},
    ]

    # 4. Generate individual files + collect bundle entries
    all_bundle_entries = []
    ind_bundle_entries = {s[0]: [] for s in INDICATORS}

    for row in rows:
        bs_year  = row["bs_year"]
        bs_month = row["bs_month"].strip()
        month_lc = bs_month.lower()
        start, end = iso_period(int(bs_year), bs_month)
        fy         = fiscal_year(int(bs_year), bs_month)

        for ind_id, _, csv_col in INDICATORS:
            report_id = f"tb-{ind_id}-kathmandu-{bs_year}-{month_lc}"

            standalone = build_report(row, ind_id, csv_col, report_id,
                                      start, end, fy, standalone=True, now_str=now_str)
            ind_dir = os.path.join(BY_IND_DIR, ind_id)
            os.makedirs(ind_dir, exist_ok=True)
            with open(os.path.join(ind_dir, f"{report_id}.json"), "w", encoding="utf-8") as f:
                json.dump(standalone, f, indent=2)

            bundle_ver = build_report(row, ind_id, csv_col, report_id,
                                      start, end, fy, standalone=False, now_str=now_str)
            entry = {"fullUrl": f"{FHIR_BASE}/MeasureReport/{report_id}",
                     "resource": bundle_ver}
            all_bundle_entries.append(entry)
            ind_bundle_entries[ind_id].append(entry)

    print(f"Generated {len(all_bundle_entries)} individual MeasureReport files")

    # 5. Per-indicator bundles (3 shared + 60 reports = 63 entries each)
    for ind_id, entries in ind_bundle_entries.items():
        bundle = make_bundle(f"bundle-kathmandu-{ind_id}", entries, now_str, shared_entries)
        with open(os.path.join(BUNDLES_DIR, f"bundle-{ind_id}.json"), "w", encoding="utf-8") as f:
            json.dump(bundle, f, indent=2)
    print(f"Generated {len(INDICATORS)} per-indicator bundles")

    # 6. Master bundle (3 shared + 780 reports = 783 entries)
    master = make_bundle("bundle-kathmandu-all-measurereports",
                         all_bundle_entries, now_str, shared_entries)
    master_path = os.path.join(BUNDLES_DIR, "bundle-all.json")
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2)
    print(f"Generated master bundle ({len(master['entry'])} entries) → {master_path}")


if __name__ == "__main__":
    main()
