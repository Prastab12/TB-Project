"""
Generate 13 FHIR R4 Measure definition files and the measures bundle.

Scoring:
  - 7 monthly notification indicators → ratio  (numerator + denominator)
  - 6 annual cohort indicators        → cohort (initial-population)

Output:
  fhir/measures/measures/nepal-tb-{id}.json   (13 files)
  fhir/measures/measures/nepal-tb-measures-bundle.json
  fhir/measure_reports/bundles/bundle-all-measures.json
"""

import json, os
from datetime import datetime, timezone

BASE         = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEASURES_DIR = os.path.join(BASE, "fhir/measures/measures")
BUNDLES_DIR  = os.path.join(BASE, "fhir/measure_reports/bundles")
FHIR_BASE    = "https://iihms.gov.np/fhir"
DATE         = "2026-05-22"
PUBLISHER    = "Integrated Health Information Management System (IIHMS), Nepal"

# (measure-id, title, num-csv-col, description, improvement, scoring)
# scoring: "ratio" | "cohort"
MEASURES = [
    # ── 7 ratio indicators (numerator = TB count, denominator = district population) ──
    ("new-cases-total",   "New TB Cases (Total)",
     "new_cases_total",
     "Monthly count of newly registered TB cases (male + female) in Kathmandu district. "
     "Denominator is the CBS mid-year district population.",
     None, "ratio"),
    ("new-cases-female",  "New TB Cases (Female)",
     "new_cases_female",
     "Monthly count of newly registered TB cases among female patients in Kathmandu district. "
     "Denominator is the CBS mid-year district population.",
     None, "ratio"),
    ("new-cases-male",    "New TB Cases (Male)",
     "new_cases_male",
     "Monthly count of newly registered TB cases among male patients in Kathmandu district. "
     "Denominator is the CBS mid-year district population.",
     None, "ratio"),
    ("relapse-total",     "TB Relapse Cases (Total)",
     "relapse_total",
     "Monthly count of TB relapse (re-treatment) cases in Kathmandu district. "
     "Denominator is the CBS mid-year district population.",
     None, "ratio"),
    ("relapse-female",    "TB Relapse Cases (Female)",
     "relapse_female",
     "Monthly count of TB relapse cases among female patients in Kathmandu district. "
     "Denominator is the CBS mid-year district population.",
     None, "ratio"),
    ("relapse-male",      "TB Relapse Cases (Male)",
     "relapse_male",
     "Monthly count of TB relapse cases among male patients in Kathmandu district. "
     "Denominator is the CBS mid-year district population.",
     None, "ratio"),
    ("total-tb-notified", "Total TB Cases Notified",
     "total_tb_m+f",
     "Monthly total TB cases notified (new + relapse, male + female) in Kathmandu district. "
     "Denominator is the CBS mid-year district population.",
     None, "ratio"),

    # ── 6 cohort indicators (initial-population = annual treatment cohort count) ──
    ("pbc-reg",   "Pulmonary Bacteriologically Confirmed Registered Cohort",
     "pbc_reg",
     "Annual count of pulmonary bacteriologically confirmed TB patients registered "
     "in the treatment cohort for a given BS fiscal year.",
     None, "cohort"),
    ("cured",     "TB Patients Cured",
     "cured",
     "Annual count of TB patients who completed treatment and were bacteriologically "
     "confirmed cured (sputum-negative at end of treatment).",
     "increase", "cohort"),
    ("failed",    "TB Treatment Failures",
     "failed",
     "Annual count of TB patients whose treatment failed "
     "(sputum-positive at month 5 or later during treatment).",
     "decrease", "cohort"),
    ("died",      "TB Patients Died",
     "died",
     "Annual count of TB patients who died from any cause during the treatment period.",
     "decrease", "cohort"),
    ("ltfu",      "TB Patients Lost to Follow-up",
     "ltfu",
     "Annual count of TB patients whose treatment was interrupted "
     "for two or more consecutive months.",
     "decrease", "cohort"),
    ("not-eval",  "TB Treatment Outcomes Not Evaluated",
     "not_eval",
     "Annual count of TB patients for whom no treatment outcome was assigned.",
     "decrease", "cohort"),
]

SCORING_SYS   = "http://terminology.hl7.org/CodeSystem/measure-scoring"
POP_CODE_SYS  = "http://terminology.hl7.org/CodeSystem/measure-population"
IMP_NOTE_SYS  = "http://terminology.hl7.org/CodeSystem/measure-improvement-notation"

IMP_INCREASE = {"coding": [{"system": IMP_NOTE_SYS, "code": "increase",
                             "display": "Increased score indicates improvement"}]}
IMP_DECREASE = {"coding": [{"system": IMP_NOTE_SYS, "code": "decrease",
                             "display": "Decreased score indicates improvement"}]}


def make_measure(measure_id, title, num_col, description, improvement, scoring):
    full_id  = f"nepal-tb-{measure_id}"
    name_up  = full_id.upper().replace("-", "_")
    group_id = f"group-{full_id}"

    if scoring == "ratio":
        populations = [
            {
                "id": f"pop-numer-{full_id}",
                "code": {"coding": [{"system": POP_CODE_SYS,
                                     "code": "numerator", "display": "Numerator"}]},
                "criteria": {
                    "language": "text/plain",
                    "expression": f"Monthly count of {num_col} from NTP reporting data for Kathmandu district.",
                },
            },
            {
                "id": f"pop-denom-{full_id}",
                "code": {"coding": [{"system": POP_CODE_SYS,
                                     "code": "denominator", "display": "Denominator"}]},
                "criteria": {
                    "language": "text/plain",
                    "expression": "Kathmandu district mid-year population from CBS (district_pop_mid_year_cbs).",
                },
            },
        ]
    else:
        populations = [
            {
                "id": f"pop-init-{full_id}",
                "code": {"coding": [{"system": POP_CODE_SYS,
                                     "code": "initial-population",
                                     "display": "Initial Population"}]},
                "criteria": {
                    "language": "text/plain",
                    "expression": f"Count of {num_col} from NTP monthly reporting data for Kathmandu district.",
                },
            }
        ]

    m = {
        "resourceType": "Measure",
        "id": full_id,
        "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Measure"]},
        "url": f"{FHIR_BASE}/Measure/{full_id}",
        "identifier": [{
            "use": "official",
            "system": f"{FHIR_BASE}/NamingSystem/measure-identifiers",
            "value": full_id,
        }],
        "version": "1.0.0",
        "name": name_up,
        "title": title,
        "status": "active",
        "experimental": False,
        "date": DATE,
        "publisher": PUBLISHER,
        "contact": [{"telecom": [{"system": "url", "value": "https://iihms.gov.np"}]}],
        "description": description,
        "scoring": {
            "coding": [{
                "system": SCORING_SYS,
                "code": scoring,
                "display": "Ratio" if scoring == "ratio" else "Cohort",
            }]
        },
        "group": [{"id": group_id, "population": populations}],
    }

    if improvement == "increase":
        m["improvementNotation"] = IMP_INCREASE
    elif improvement == "decrease":
        m["improvementNotation"] = IMP_DECREASE

    return m


def main():
    os.makedirs(MEASURES_DIR, exist_ok=True)
    os.makedirs(BUNDLES_DIR,  exist_ok=True)

    all_measures = []
    for measure_id, title, num_col, description, improvement, scoring in MEASURES:
        m    = make_measure(measure_id, title, num_col, description, improvement, scoring)
        all_measures.append(m)
        path = os.path.join(MEASURES_DIR, f"nepal-tb-{measure_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(m, f, indent=2)
        print(f"  [{scoring:6}] {os.path.basename(path)}")

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = [{"fullUrl": f"{FHIR_BASE}/Measure/{m['id']}", "resource": m}
               for m in all_measures]
    bundle = {
        "resourceType": "Bundle",
        "id": "bundle-all-measures",
        "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Bundle"]},
        "type": "collection",
        "timestamp": now_str,
        "entry": entries,
    }

    measures_bundle = os.path.join(MEASURES_DIR, "nepal-tb-measures-bundle.json")
    bundles_copy    = os.path.join(BUNDLES_DIR,  "bundle-all-measures.json")
    for path in (measures_bundle, bundles_copy):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(bundle, f, indent=2)

    print(f"\nMeasures bundle → {measures_bundle}  ({len(entries)} entries)")
    print(f"Measures bundle → {bundles_copy}  ({len(entries)} entries)")
    print("Done.")


if __name__ == "__main__":
    main()
