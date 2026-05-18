import pandas as pd
import os
import json
from datetime import datetime, timezone

def get_iso_period(bs_year, bs_month):
    """
    Deterministic BS to AD Gregorian period mapper.
    """
    month_map = {
        "Baishakh": 4, "Jestha": 5, "Ashad": 6, "Shrawan": 7,
        "Bhadra": 8, "Ashwin": 9, "Kartik": 10, "Mangsir": 11,
        "Poush": 12, "Magh": 1, "Falgun": 2, "Chaitra": 3,
        "Baishak": 4, "Asar": 6
    }

    clean_month = bs_month.split()[0].strip()
    m = month_map.get(clean_month, 1)

    g_year = bs_year - 57 if m >= 4 else bs_year - 56
    start_date = f"{g_year}-{m:02d}-16"

    next_m = m + 1
    next_yr = g_year
    if next_m > 12:
        next_m = 1
        next_yr += 1

    end_date = f"{next_yr}-{next_m:02d}-15"
    return start_date, end_date

def get_fiscal_year(bs_year, bs_month):
    """
    Returns localized fiscal year string.
    """
    month_map = {
        "Baishakh": 1, "Jestha": 2, "Ashad": 3, "Shrawan": 4,
        "Bhadra": 5, "Ashwin": 6, "Kartik": 7, "Mangsir": 8,
        "Poush": 9, "Magh": 10, "Falgun": 11, "Chaitra": 12,
        "Baishak": 1, "Asar": 3
    }
    clean_month = bs_month.split()[0].strip()
    m = month_map.get(clean_month, 1)
    if m <= 3:
        return f"{bs_year-1}/{str(bs_year)[-2:]}"
    else:
        return f"{bs_year}/{str(bs_year+1)[-2:]}"

CONTAINED_RESOURCES = [
    {
        "resourceType": "Organization",
        "id": "org-mohp",
        "name": "Ministry of Health and Population, Nepal",
        "alias": ["MoHP"]
    },
    {
        "resourceType": "Organization",
        "id": "org-ntp",
        "name": "National Tuberculosis Programme",
        "alias": ["NTP"],
        "partOf": {"reference": "#org-mohp"}
    },
    {
        "resourceType": "Location",
        "id": "loc-kathmandu",
        "name": "Kathmandu District, Nepal",
        "physicalType": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                "code": "jdn",
                "display": "Jurisdiction"
            }]
        }
    }
]

def main():
    BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_file = os.path.join(BASE, "data/final/final_cleaned_data.csv")
    base_dir = os.path.join(BASE, "fhir/measures/measure_report/monthwise_measure_report")
    os.makedirs(base_dir, exist_ok=True)

    df = pd.read_csv(input_file)

    df_ktm = df[df["district"].str.upper() == "KATHMANDU"].copy()
    print(f"Loaded {len(df_ktm)} Kathmandu-specific monthly records.")

    indicators_spec = {
        "nepal-tb-tsr-cure": {
            "title": "Treatment Success Rate (TSR)",
            "numerator_field": "cured",
            "denominator_field": "pbc_reg",
            "is_cohort_lag": True,
            "is_derived": False
        },
        "nepal-tb-notification-rate": {
            "title": "Annualized TB Notification Rate",
            "numerator_field": "total_tb_m+f",
            "denominator_field": "district_pop_mid_year_cbs",
            "is_cohort_lag": False,
            "is_derived": False
        },
        "nepal-tb-mortality-rate": {
            "title": "Mortality Rate (Cohort)",
            "numerator_field": "died",
            "denominator_field": "pbc_reg",
            "is_cohort_lag": True,
            "is_derived": False
        },
        "nepal-tb-ltfu-rate": {
            "title": "Lost to Follow-up (LTFU) Rate",
            "numerator_field": "ltfu",
            "denominator_field": "pbc_reg",
            "is_cohort_lag": True,
            "is_derived": False
        },
        "nepal-tb-failure-rate": {
            "title": "Treatment Failure Rate",
            "numerator_field": "failed",
            "denominator_field": "pbc_reg",
            "is_cohort_lag": True,
            "is_derived": False
        },
        "nepal-tb-not-eval-rate": {
            "title": "Not Evaluated Rate",
            "numerator_field": "not_eval",
            "denominator_field": "pbc_reg",
            "is_cohort_lag": True,
            "is_derived": False
        },
        "nepal-tb-bacteriological-confirmation": {
            "title": "Bacteriological Confirmation Proportion",
            "numerator_field": "pbc_reg",
            "denominator_field": "total_tb_m+f",
            "is_cohort_lag": False,
            "is_derived": False
        },
        "nepal-tb-xpert-coverage": {
            "title": "Xpert MTB/RIF Coverage Rate",
            "numerator_field": "xpert_cov_pct",
            "denominator_field": "district_pop_mid_year_cbs",
            "is_cohort_lag": False,
            "is_derived": True,
            "derived_type": "rate_of_pop"
        },
        "nepal-tb-hiv-coinfection": {
            "title": "Tuberculosis/HIV Co-infection Proportion",
            "numerator_field": "tb_hiv_pct",
            "denominator_field": "district_pop_mid_year_cbs",
            "is_cohort_lag": False,
            "is_derived": True,
            "derived_type": "rate_of_pop"
        },
        "nepal-tb-art-coverage": {
            "title": "HIV/ART Coverage Percentage",
            "numerator_field": "art_cov_pct",
            "denominator_field": "tb_hiv_pct",
            "is_cohort_lag": False,
            "is_derived": True,
            "derived_type": "rate_of_hiv"
        },
        "nepal-tb-gender-ratio": {
            "title": "Male-to-Female TB Notification Ratio",
            "numerator_field": "total_tb_male",
            "denominator_field": "total_tb_female",
            "is_cohort_lag": False,
            "is_derived": False
        }
    }

    folders_created = 0
    total_files_generated = 0
    total_bundles_generated = 0

    for idx, row in df_ktm.iterrows():
        bs_yr = int(row["bs_year"])
        bs_mnth = row["bs_month"]
        clean_month = bs_mnth.split()[0].strip().lower()
        clean_mnth = bs_mnth.split()[0].strip()

        start_date, end_date = get_iso_period(bs_yr, bs_mnth)
        fy = get_fiscal_year(bs_yr, bs_mnth)

        month_folder_name = f"{bs_yr}-{clean_month}"
        month_dir = os.path.join(base_dir, month_folder_name)
        os.makedirs(month_dir, exist_ok=True)
        folders_created += 1

        measure_reports = []

        for meas_id, spec in indicators_spec.items():
            report_id = f"tb-{meas_id.replace('nepal-tb-', '')}-kathmandu-{bs_yr}-{clean_month}"

            # Retrieve Denominator
            if spec["is_cohort_lag"]:
                lag_yr = bs_yr - 1
                lag_row = df_ktm[(df_ktm["bs_year"] == lag_yr) &
                                 (df_ktm["bs_month"].str.split().str[0] == clean_mnth)]
                if len(lag_row) > 0:
                    raw = lag_row.iloc[0][spec["denominator_field"]]
                    denom_val = int(raw) if pd.notna(raw) else 0
                else:
                    denom_val = 0
            elif spec["is_derived"] and spec["derived_type"] == "rate_of_hiv":
                pop_val = int(row["district_pop_mid_year_cbs"]) if pd.notna(row["district_pop_mid_year_cbs"]) else 0
                hiv_rate = int(row["tb_hiv_pct"]) if pd.notna(row["tb_hiv_pct"]) else 0
                denom_val = hiv_rate * pop_val
            else:
                raw = row[spec["denominator_field"]]
                denom_val = int(raw) if pd.notna(raw) else 0

            # Retrieve Numerator
            if spec["is_derived"]:
                if spec["derived_type"] == "rate_of_pop":
                    pop_val = int(row["district_pop_mid_year_cbs"]) if pd.notna(row["district_pop_mid_year_cbs"]) else 0
                    raw = row[spec["numerator_field"]]
                    rate_val = int(raw) if pd.notna(raw) else 0
                    num_val = rate_val * pop_val
                elif spec["derived_type"] == "rate_of_hiv":
                    raw = row[spec["numerator_field"]]
                    art_rate = int(raw) if pd.notna(raw) else 0
                    num_val = art_rate * denom_val
                else:
                    num_val = 0
            else:
                raw = row[spec["numerator_field"]]
                num_val = int(raw) if pd.notna(raw) else 0

            is_data_absent_month = (bs_yr == 2078) and (clean_month in ["baishak", "baishakh", "jestha", "asar", "ashad"])

            is_absent_numerator = False
            is_absent_denominator = False
            if is_data_absent_month:
                if meas_id == "nepal-tb-notification-rate":
                    is_absent_numerator = True
                elif meas_id == "nepal-tb-gender-ratio":
                    is_absent_numerator = True
                    is_absent_denominator = True
                elif meas_id == "nepal-tb-bacteriological-confirmation":
                    is_absent_denominator = True

            score = (num_val / denom_val) if (denom_val > 0 and not is_absent_numerator and not is_absent_denominator) else 0.0
            ucum_code = "{ratio}" if meas_id in ["nepal-tb-notification-rate", "nepal-tb-gender-ratio"] else "{proportion}"

            # Build populations with DataAbsentReason extensions where appropriate
            denom_pop = {
                "code": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                        "code": "denominator"
                    }]
                }
            }
            if is_absent_denominator:
                denom_pop["_count"] = {
                    "extension": [{
                        "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
                        "valueCode": "not-reported"
                    }]
                }
            else:
                denom_pop["count"] = denom_val

            num_pop = {
                "code": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                        "code": "numerator"
                    }]
                }
            }
            if is_absent_numerator:
                num_pop["_count"] = {
                    "extension": [{
                        "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
                        "valueCode": "not-reported"
                    }]
                }
            else:
                num_pop["count"] = num_val

            # R4: measureScore (Quantity) — not measureScoreQuantity which is R5
            measure_score_obj = {
                "unit": ucum_code,
                "system": "http://unitsofmeasure.org",
                "code": ucum_code
            }
            if is_absent_numerator or is_absent_denominator:
                measure_score_obj["_value"] = {
                    "extension": [{
                        "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
                        "valueCode": "not-reported"
                    }]
                }
            else:
                measure_score_obj["value"] = float(round(score, 4))

            measure_report = {
                "resourceType": "MeasureReport",
                "id": report_id,
                "contained": CONTAINED_RESOURCES,
                "status": "complete",
                "type": "summary",
                "measure": f"https://iihms.gov.np/fhir/Measure/{meas_id}",
                "subject": {
                    "reference": "#loc-kathmandu",
                    "display": "Kathmandu District, Nepal"
                },
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "reporter": {
                    "reference": "#org-ntp",
                    "display": "National Tuberculosis Programme"
                },
                "period": {
                    "extension": [
                        {
                            "url": "https://iihms.gov.np/fhir/StructureDefinition/nepali-fiscal-period",
                            "extension": [
                                {"url": "bs-year", "valueInteger": bs_yr},
                                {"url": "bs-month", "valueString": clean_mnth},
                                {"url": "fiscal-year", "valueString": fy}
                            ]
                        }
                    ],
                    "start": start_date,
                    "end": end_date
                },
                "group": [
                    {
                        "id": f"group-{meas_id}",
                        "population": [denom_pop, num_pop],
                        "measureScore": measure_score_obj
                    }
                ]
            }

            report_file = os.path.join(month_dir, f"{report_id}.json")
            with open(report_file, "w") as f:
                json.dump(measure_report, f, indent=2)

            measure_reports.append(measure_report)
            total_files_generated += 1

        bundle_id = f"bundle-kathmandu-{month_folder_name}"
        bundle_res = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "type": "collection",
            "entry": [
                {
                    "fullUrl": f"https://iihms.gov.np/fhir/MeasureReport/{mr['id']}",
                    "resource": mr
                } for mr in measure_reports
            ]
        }

        bundle_file = os.path.join(month_dir, f"{bundle_id}.json")
        with open(bundle_file, "w") as f:
            json.dump(bundle_res, f, indent=2)
        total_bundles_generated += 1

    print(f"Successfully processed Kathmandu data:")
    print(f"  → Created month-wise folders: {folders_created}")
    print(f"  → Generated individual reports: {total_files_generated}")
    print(f"  → Generated specific Bundles: {total_bundles_generated}")

if __name__ == "__main__":
    main()
