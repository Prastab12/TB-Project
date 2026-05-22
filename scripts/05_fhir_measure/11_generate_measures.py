"""
Generate 13 FHIR R4 Measure definition files (cohort scoring, raw counts)
and the measures bundle.

Output:
  fhir/measures/measures/nepal-tb-{id}.json   (13 files)
  fhir/measures/measures/nepal-tb-measures-bundle.json
"""

import json
import os

BASE         = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEASURES_DIR = os.path.join(BASE, "fhir/measures/measures")
BUNDLES_DIR  = os.path.join(BASE, "fhir/measure_reports/bundles")
FHIR_BASE   = "https://iihms.gov.np/fhir"
DATE        = "2026-05-21"
PUBLISHER   = "Integrated Health Information Management System (IIHMS), Nepal"

# (measure-id, title, csv-column, description, improvement-direction)
# improvement-direction: "increase" | "decrease" | None (no improvementNotation)
MEASURES = [
    (
        "new-cases-total",
        "New TB Cases (Total)",
        "new_cases_total",
        "Total number of newly registered TB cases (male + female) in a given BS month.",
        None,
    ),
    (
        "new-cases-female",
        "New TB Cases (Female)",
        "new_cases_female",
        "Number of newly registered TB cases among female patients in a given BS month.",
        None,
    ),
    (
        "new-cases-male",
        "New TB Cases (Male)",
        "new_cases_male",
        "Number of newly registered TB cases among male patients in a given BS month.",
        None,
    ),
    (
        "relapse-total",
        "TB Relapse Cases (Total)",
        "relapse_total",
        "Total number of TB relapse cases (re-treatment) registered in a given BS month.",
        None,
    ),
    (
        "relapse-female",
        "TB Relapse Cases (Female)",
        "relapse_female",
        "Number of TB relapse cases among female patients in a given BS month.",
        None,
    ),
    (
        "relapse-male",
        "TB Relapse Cases (Male)",
        "relapse_male",
        "Number of TB relapse cases among male patients in a given BS month.",
        None,
    ),
    (
        "total-tb-notified",
        "Total TB Cases Notified",
        "total_tb_m+f",
        "Total TB cases notified (new + relapse, male + female) in a given BS month, "
        "as reported to the National Tuberculosis Programme.",
        None,
    ),
    (
        "pbc-reg",
        "Pulmonary Bacteriologically Confirmed Registered Cohort",
        "pbc_reg",
        "Annual count of pulmonary bacteriologically confirmed TB patients registered "
        "in the treatment cohort for a given BS fiscal year.",
        None,
    ),
    (
        "cured",
        "TB Patients Cured",
        "cured",
        "Annual count of TB patients who completed treatment and were bacteriologically "
        "confirmed cured (sputum-negative at end of treatment).",
        "increase",
    ),
    (
        "failed",
        "TB Treatment Failures",
        "failed",
        "Annual count of TB patients whose treatment failed "
        "(sputum-positive at month 5 or later during treatment).",
        "decrease",
    ),
    (
        "died",
        "TB Patients Died",
        "died",
        "Annual count of TB patients who died from any cause during the treatment period.",
        "decrease",
    ),
    (
        "ltfu",
        "TB Patients Lost to Follow-up",
        "ltfu",
        "Annual count of TB patients whose treatment was interrupted "
        "for two or more consecutive months.",
        "decrease",
    ),
    (
        "not-eval",
        "TB Treatment Outcomes Not Evaluated",
        "not_eval",
        "Annual count of TB patients for whom no treatment outcome was assigned.",
        "decrease",
    ),
]

IMPROVEMENT_NOTATION_INCREASE = {
    "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/measure-improvement-notation",
        "code": "increase",
        "display": "Increased score indicates improvement",
    }]
}
IMPROVEMENT_NOTATION_DECREASE = {
    "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/measure-improvement-notation",
        "code": "decrease",
        "display": "Decreased score indicates improvement",
    }]
}


def make_measure(measure_id, title, csv_col, description, improvement):
    full_id  = f"nepal-tb-{measure_id}"
    name_up  = full_id.upper().replace("-", "_")
    group_id = f"group-{full_id}"
    pop_id   = f"pop-init-{full_id}"

    m = {
        "resourceType": "Measure",
        "id": full_id,
        "meta": {
            "profile": ["http://hl7.org/fhir/StructureDefinition/Measure"]
        },
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
                "system": "http://terminology.hl7.org/CodeSystem/measure-scoring",
                "code": "cohort",
                "display": "Cohort",
            }]
        },
        "group": [{
            "id": group_id,
            "population": [{
                "id": pop_id,
                "code": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                        "code": "initial-population",
                        "display": "Initial Population",
                    }]
                },
                "criteria": {
                    "language": "text/plain",
                    "expression": f"Count of {csv_col} from the NTP monthly reporting data for Kathmandu district.",
                },
            }],
        }],
    }

    if improvement == "increase":
        m["improvementNotation"] = IMPROVEMENT_NOTATION_INCREASE
    elif improvement == "decrease":
        m["improvementNotation"] = IMPROVEMENT_NOTATION_DECREASE

    return m


def main():
    os.makedirs(MEASURES_DIR, exist_ok=True)

    all_measures = []
    for measure_id, title, csv_col, description, improvement in MEASURES:
        m = make_measure(measure_id, title, csv_col, description, improvement)
        all_measures.append(m)
        path = os.path.join(MEASURES_DIR, f"nepal-tb-{measure_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(m, f, indent=2)
        print(f"  Written: {os.path.basename(path)}")

    # Build master measures bundle — 13 Measure definitions only
    entries = [
        {"fullUrl": f"{FHIR_BASE}/Measure/{m['id']}", "resource": m}
        for m in all_measures
    ]
    bundle = {
        "resourceType": "Bundle",
        "id": "bundle-all-measures",
        "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/Bundle"]},
        "type": "collection",
        "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "entry": entries,
    }

    # Save alongside individual Measure files
    measures_bundle_path = os.path.join(MEASURES_DIR, "nepal-tb-measures-bundle.json")
    with open(measures_bundle_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)
    print(f"\nMeasures bundle → {measures_bundle_path}  ({len(entries)} entries)")

    # Also save in the shared bundles dir alongside bundle-all.json
    os.makedirs(BUNDLES_DIR, exist_ok=True)
    bundles_copy_path = os.path.join(BUNDLES_DIR, "bundle-all-measures.json")
    with open(bundles_copy_path, "w", encoding="utf-8") as f:
        json.dump(bundle, f, indent=2)
    print(f"Measures bundle → {bundles_copy_path}  ({len(entries)} entries)")
    print("Done.")


if __name__ == "__main__":
    main()
