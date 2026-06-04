"""
Generate 32 FHIR R4 Measure definition resources — one per raw data variable.

Scoring:
  ratio  : notification / count variables (numerator=count, denominator=population)
  cohort : treatment outcome variables    (initial-population=count)

Output:
  fhir/measures/<id>.json   (32 files)
"""

import json
import os
from datetime import date

BASE       = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR    = os.path.join(BASE, "fhir", "measures")
FHIR_BASE  = "https://iihms.gov.np/fhir"
PUBLISHER  = "Integrated Health Information Management System (IIHMS), Nepal"
DATE       = date.today().isoformat()

SCORING_SYS = "http://terminology.hl7.org/CodeSystem/measure-scoring"
POP_SYS     = "http://terminology.hl7.org/CodeSystem/measure-population"
IMP_SYS     = "http://terminology.hl7.org/CodeSystem/measure-improvement-notation"

# (measure-id, title, csv-column, description, improvement, scoring)
MEASURES = [

    # ── Notification counts — ratio (count vs CBS population) ──────────────
    ("new-cases-total",
     "New TB Cases (Total)",
     "new_cases_total",
     "Monthly count of all newly registered TB cases (male + female) in Kathmandu district.",
     None, "ratio"),

    ("new-cases-female",
     "New TB Cases (Female)",
     "new_cases_female",
     "Monthly count of newly registered TB cases among female patients in Kathmandu district. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("new-cases-male",
     "New TB Cases (Male)",
     "new_cases_male",
     "Monthly count of newly registered TB cases among male patients in Kathmandu district. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("relapse-total",
     "TB Relapse Cases (Total)",
     "relapse_total",
     "Monthly count of TB relapse (re-treatment) cases (male + female) in Kathmandu district. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("relapse-female",
     "TB Relapse Cases (Female)",
     "relapse_female",
     "Monthly count of TB relapse cases among female patients in Kathmandu district. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("relapse-male",
     "TB Relapse Cases (Male)",
     "relapse_male",
     "Monthly count of TB relapse cases among male patients in Kathmandu district. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("total-tb-notified",
     "Total TB Cases Notified (M+F)",
     "total_tb_mf",
     "Monthly total TB cases notified (new + relapse, male + female) in Kathmandu district.",
     None, "ratio"),

    ("total-tb-female",
     "Total TB Cases Notified (Female)",
     "total_tb_female",
     "Monthly total TB cases notified among female patients (new + relapse female). "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("total-tb-male",
     "Total TB Cases Notified (Male)",
     "total_tb_male",
     "Monthly total TB cases notified among male patients (new + relapse male). "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("hiv-positive",
     "TB Patients with HIV Co-infection",
     "tb_hiv_positive",
     "Monthly count of TB patients with confirmed HIV co-infection in Kathmandu district.",
     None, "ratio"),

    # ── Age-sex band counts — ratio (16 individual variables) ──────────────
    ("age-0to4-f",   "New TB Cases — Female, Age 0–4",   "0_to_4_f",
     "Monthly new TB cases among female patients aged 0–4 years. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("age-0to4-m",   "New TB Cases — Male, Age 0–4",     "0_to_4_m",
     "Monthly new TB cases among male patients aged 0–4 years. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("age-5to14-f",  "New TB Cases — Female, Age 5–14",  "5_to_14_f",
     "Monthly new TB cases among female patients aged 5–14 years. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("age-5to14-m",  "New TB Cases — Male, Age 5–14",    "5_to_14_m",
     "Monthly new TB cases among male patients aged 5–14 years. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("age-15to24-f", "New TB Cases — Female, Age 15–24", "15_to_24_f",
     "Monthly new TB cases among female patients aged 15–24 years. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("age-15to24-m", "New TB Cases — Male, Age 15–24",   "15_to_24_m",
     "Monthly new TB cases among male patients aged 15–24 years. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("age-25to34-f", "New TB Cases — Female, Age 25–34", "25_to_34_f",
     "Monthly new TB cases among female patients aged 25–34 years. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("age-25to34-m", "New TB Cases — Male, Age 25–34",   "25_to_34_m",
     "Monthly new TB cases among male patients aged 25–34 years. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("age-35to44-f", "New TB Cases — Female, Age 35–44", "35_to_44_f",
     "Monthly new TB cases among female patients aged 35–44 years. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("age-35to44-m", "New TB Cases — Male, Age 35–44",   "35_to_44_m",
     "Monthly new TB cases among male patients aged 35–44 years. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("age-45to54-f", "New TB Cases — Female, Age 45–54", "45_to_54_f",
     "Monthly new TB cases among female patients aged 45–54 years. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("age-45to54-m", "New TB Cases — Male, Age 45–54",   "45_to_54_m",
     "Monthly new TB cases among male patients aged 45–54 years. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("age-55to64-f", "New TB Cases — Female, Age 55–64", "55_to_64_f",
     "Monthly new TB cases among female patients aged 55–64 years. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("age-55to64-m", "New TB Cases — Male, Age 55–64",   "55_to_64_m",
     "Monthly new TB cases among male patients aged 55–64 years. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("age-65plus-f", "New TB Cases — Female, Age 65+",   "65_f",
     "Monthly new TB cases among female patients aged 65 years and above. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    ("age-65plus-m", "New TB Cases — Male, Age 65+",     "65_m",
     "Monthly new TB cases among male patients aged 65 years and above. "
     "Data-absent-reason: not-reported for Baishak/Jestha/Asar 2078.",
     None, "ratio"),

    # ── Treatment outcome counts — cohort (initial-population only) ────────
    ("pbc-reg",
     "Pulmonary Bacteriologically Confirmed Registered Cohort",
     "pbc_reg",
     "Count of pulmonary bacteriologically confirmed TB patients registered "
     "in the treatment cohort for the reporting period.",
     None, "cohort"),

    ("cured",
     "TB Patients Cured",
     "cured",
     "Count of TB patients who completed treatment and were bacteriologically confirmed cured.",
     "increase", "cohort"),

    ("failed",
     "TB Treatment Failures",
     "failed",
     "Count of TB patients whose treatment failed "
     "(sputum-positive at month 5 or later during treatment).",
     "decrease", "cohort"),

    ("died",
     "TB Patients Died During Treatment",
     "died",
     "Count of TB patients who died from any cause during the treatment period.",
     "decrease", "cohort"),

    ("ltfu",
     "TB Patients Lost to Follow-Up",
     "ltfu",
     "Count of TB patients whose treatment was interrupted for two or more consecutive months.",
     "decrease", "cohort"),

    ("not-eval",
     "TB Treatment Outcomes Not Evaluated",
     "not_eval",
     "Count of TB patients for whom no treatment outcome was assigned.",
     "decrease", "cohort"),
]


def build_measure(measure_id, title, csv_col, description, improvement, scoring):
    full_id = f"nepal-tb-{measure_id}"

    if scoring == "ratio":
        populations = [
            {
                "id":   f"pop-numer-{full_id}",
                "code": {"coding": [{"system": POP_SYS,
                                      "code": "numerator", "display": "Numerator"}]},
                "criteria": {
                    "language":   "text/plain",
                    "expression": f"Monthly count of {csv_col} from NTP reporting data "
                                  "for Kathmandu district.",
                },
            },
            {
                "id":   f"pop-denom-{full_id}",
                "code": {"coding": [{"system": POP_SYS,
                                      "code": "denominator", "display": "Denominator"}]},
                "criteria": {
                    "language":   "text/plain",
                    "expression": "Kathmandu district mid-year population from CBS "
                                  "(district_pop_mid_year_cbs).",
                },
            },
        ]
    else:  # cohort
        populations = [
            {
                "id":   f"pop-init-{full_id}",
                "code": {"coding": [{"system": POP_SYS,
                                      "code": "initial-population",
                                      "display": "Initial Population"}]},
                "criteria": {
                    "language":   "text/plain",
                    "expression": f"Count of {csv_col} from NTP monthly reporting data "
                                  "for Kathmandu district.",
                },
            },
        ]

    resource = {
        "resourceType": "Measure",
        "id":           full_id,
        "url":          f"{FHIR_BASE}/Measure/{full_id}",
        "identifier": [{
            "use":    "official",
            "system": f"{FHIR_BASE}/NamingSystem/measure-identifiers",
            "value":  full_id,
        }],
        "version":      "1.0.0",
        "name":         full_id.upper().replace("-", "_"),
        "title":        title,
        "status":       "active",
        "experimental": False,
        "date":         DATE,
        "publisher":    PUBLISHER,
        "contact":      [{"telecom": [{"system": "url",
                                        "value": "https://iihms.gov.np"}]}],
        "description":  description,
        "scoring": {"coding": [{
            "system":  SCORING_SYS,
            "code":    scoring,
            "display": "Ratio" if scoring == "ratio" else "Cohort",
        }]},
        "group": [{"id": f"group-{full_id}", "population": populations}],
    }

    if improvement:
        resource["improvementNotation"] = {"coding": [{
            "system":  IMP_SYS,
            "code":    improvement,
            "display": ("Increased score indicates improvement"
                        if improvement == "increase"
                        else "Decreased score indicates improvement"),
        }]}

    return resource


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    generated = []

    for measure_id, title, csv_col, description, improvement, scoring in MEASURES:
        resource  = build_measure(measure_id, title, csv_col,
                                  description, improvement, scoring)
        file_path = os.path.join(OUT_DIR, f"nepal-tb-{measure_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(resource, f, indent=2)
        generated.append(file_path)
        print(f"  [{scoring:6}] nepal-tb-{measure_id}.json")

    print(f"\nGenerated {len(generated)} FHIR Measure resources → {OUT_DIR}/")
    print("Phase 3 — Part B (Measure definitions) complete.")


if __name__ == "__main__":
    main()
