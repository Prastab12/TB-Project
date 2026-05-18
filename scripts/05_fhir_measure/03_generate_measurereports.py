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
        "Baishak": 4, "Asar": 6  # Adding spelling variants found in dataset
    }
    
    # Strip any trailing year if present (e.g., "Shrawan 2078" -> "Shrawan")
    clean_month = bs_month.split()[0].strip()
    m = month_map.get(clean_month, 1)
    
    # Standard translation mapping: BS Year - 57 = AD Year
    g_year = bs_year - 57 if m >= 4 else bs_year - 56
    
    start_date = f"{g_year}-{m:02d}-16"
    
    # Calculate end date
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
    # Baishakh to Ashad are in the second half of the fiscal year
    if m <= 3:
        return f"{bs_year-1}/{str(bs_year)[-2:]}"
    else:
        return f"{bs_year}/{str(bs_year+1)[-2:]}"

def main():
    BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_file = os.path.join(BASE, "data/final/final_cleaned_data.csv")
    output_dir = os.path.join(BASE, "fhir/district_monthly_measure_report")
    ref_dir = os.path.join(output_dir, "reference_resources")
    os.makedirs(ref_dir, exist_ok=True)

    df = pd.read_csv(input_file)
    print(f"Loaded {len(df)} rows of cleaned data.")

    # ------------------------------------------------------------------ #
    # 6.1 Create Reference Resources
    # ------------------------------------------------------------------ #
    org_mohp = {
        "resourceType": "Organization",
        "id": "org-mohp",
        "name": "Ministry of Health and Population, Nepal",
        "alias": ["MoHP"]
    }
    org_ntp = {
        "resourceType": "Organization",
        "id": "org-ntp",
        "name": "National Tuberculosis Programme",
        "alias": ["NTP"],
        "partOf": {"reference": "Organization/org-mohp"}
    }
    
    loc_bagmati = {
        "resourceType": "Location",
        "id": "loc-bagmati",
        "name": "Bagmati Province",
        "physicalType": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                "code": "jdn",
                "display": "Jurisdiction"
            }]
        }
    }
    
    with open(os.path.join(ref_dir, "org_mohp.json"), "w") as f:
        json.dump(org_mohp, f, indent=2)
    with open(os.path.join(ref_dir, "org_ntp.json"), "w") as f:
        json.dump(org_ntp, f, indent=2)
    with open(os.path.join(ref_dir, "loc_bagmati.json"), "w") as f:
        json.dump(loc_bagmati, f, indent=2)

    districts = df['district'].unique()
    district_locations = {}
    for d in districts:
        loc_id = f"loc-{d.lower()}"
        loc_res = {
            "resourceType": "Location",
            "id": loc_id,
            "name": d,
            "physicalType": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                    "code": "jdn",
                    "display": "Jurisdiction"
                }]
            },
            "partOf": {"reference": "Location/loc-bagmati"}
        }
        with open(os.path.join(ref_dir, f"{loc_id}.json"), "w") as f:
            json.dump(loc_res, f, indent=2)
        district_locations[d] = loc_id

    # ------------------------------------------------------------------ #
    # 6.2 Build Calendar Mapping Appendix CSV
    # ------------------------------------------------------------------ #
    mapping_rows = []
    for idx, row in df[["bs_year", "bs_month"]].drop_duplicates().iterrows():
        start, end = get_iso_period(int(row["bs_year"]), row["bs_month"])
        fy = get_fiscal_year(int(row["bs_year"]), row["bs_month"])
        mapping_rows.append({
            "BS Year": row["bs_year"],
            "BS Month": row["bs_month"],
            "Gregorian Start": start,
            "Gregorian End": end,
            "Fiscal Year": fy
        })
    mapping_df = pd.DataFrame(mapping_rows)
    mapping_df.to_csv(os.path.join(output_dir, "nepali_fiscal_period_mapping.csv"), index=False)
    print("Generated calendar period mapping appendix.")

    # ------------------------------------------------------------------ #
    # 6.4/6.7 Generate MeasureReport Resources
    # ------------------------------------------------------------------ #
    # 11 Indicators definitions mapping directly to cleaned columns
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

    # Group records by Year and Month to evaluate provincial totals and district stratifiers
    grouped = df.groupby(["bs_year", "bs_month"])
    
    print(f"Generating MeasureReports for {len(grouped)} monthly periods...")
    
    for (bs_yr, bs_mnth), group_df in grouped:
        start_date, end_date = get_iso_period(int(bs_yr), bs_mnth)
        fy = get_fiscal_year(int(bs_yr), bs_mnth)
        
        # Clean month name for compliant FHIR ID strings (no spaces allowed)
        clean_month = bs_mnth.split()[0].strip().lower()
        
        # Build MeasureReports for each configured indicator
        for meas_id, spec in indicators_spec.items():
            suffix = meas_id.replace("nepal-tb-", "")
            report_id = f"tb-{suffix}-bagmati-{bs_yr}-{clean_month}"
            
            # 6.7 Numerator and Denominator totals
            total_num = 0
            total_denom = 0
            
            stratifiers = []
            
            for idx, row in group_df.iterrows():
                dist_name = row["district"]
                
                # Retrieve denominator
                if spec["is_cohort_lag"]:
                    lag_yr = int(bs_yr) - 1
                    clean_mnth = bs_mnth.split()[0].strip()
                    lag_row = df[(df["district"] == dist_name) &
                                 (df["bs_year"] == lag_yr) &
                                 (df["bs_month"].str.split().str[0] == clean_mnth)]
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
                
                # Retrieve numerator
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
                    
                total_num += num_val
                total_denom += denom_val
                
                # Stratum for this district
                stratum = {
                    "value": {
                        "text": dist_name
                    },
                    "population": [
                        {
                            "code": {
                                "coding": [{
                                    "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                                    "code": "numerator"
                                }]
                            },
                            "count": num_val
                        },
                        {
                            "code": {
                                "coding": [{
                                    "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                                    "code": "denominator"
                                }]
                            },
                            "count": denom_val
                        }
                    ]
                }
                
                stratifiers.append(stratum)
                
            # Calculate measureScore
            score = (total_num / total_denom) if total_denom > 0 else 0.0
            
            measure_report = {
                "resourceType": "MeasureReport",
                "id": report_id,
                "contained": [
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
                        "id": "loc-bagmati",
                        "name": "Bagmati Province",
                        "physicalType": {
                            "coding": [{
                                "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                                "code": "jdn",
                                "display": "Jurisdiction"
                            }]
                        }
                    }
                ],
                "status": "complete",
                "type": "summary",
                "measure": f"https://iihms.gov.np/fhir/Measure/{meas_id}",
                "subject": {
                    "reference": "#loc-bagmati",
                    "display": "Bagmati Province"
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
                                {"url": "bs-year", "valueInteger": int(bs_yr)},
                                {"url": "bs-month", "valueString": bs_mnth.split()[0].strip()},
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
                        "population": [
                            {
                                "code": {
                                    "coding": [{
                                        "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                                        "code": "denominator"
                                    }]
                                },
                                "count": total_denom
                            },
                            {
                                "code": {
                                    "coding": [{
                                        "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                                        "code": "numerator"
                                    }]
                                },
                                "count": total_num
                            }
                        ],
                        "measureScore": {
                            "value": float(round(score, 4)),
                            "unit": "{ratio}" if meas_id in ["nepal-tb-notification-rate", "nepal-tb-gender-ratio"] else "{proportion}",
                            "system": "http://unitsofmeasure.org",
                            "code": "{ratio}" if meas_id in ["nepal-tb-notification-rate", "nepal-tb-gender-ratio"] else "{proportion}"
                        },
                        "stratifier": [
                            {
                                "id": "stratifier-district",
                                "code": [
                                    {"text": "District-level Disaggregation"}
                                ],
                                "stratum": stratifiers
                            }
                        ]
                    }
                ]
            }
            
            # Save MeasureReport
            report_file = os.path.join(output_dir, f"{report_id}.json")
            with open(report_file, "w") as f:
                json.dump(measure_report, f, indent=2)

    print("Successfully generated all district-wise monthly MeasureReport resources.")


if __name__ == "__main__":
    main()
