import json
import os

def create_measure_resource(measure_id, title, description, scoring_code, scoring_display, numerator_desc, denominator_desc, improvement_code=None, has_gender_stratifier=False):
    """
    Constructs a valid HL7 FHIR R4 Measure Resource.
    """
    canonical_url = f"https://iihms.gov.np/fhir/Measure/{measure_id}"
    
    measure = {
        "resourceType": "Measure",
        "id": measure_id,
        "url": canonical_url,
        "identifier": [
            {
                "use": "official",
                "system": "https://iihms.gov.np/fhir/NamingSystem/measure-identifiers",
                "value": measure_id
            }
        ],
        "version": "1.0.0",
        "name": measure_id.replace("-", "_").upper(),
        "title": title,
        "status": "active",
        "experimental": False,
        "date": "2026-05-17",
        "publisher": "Integrated Health Information Management System (IIHMS), Nepal",
        "contact": [
            {
                "telecom": [
                    {
                        "system": "url",
                        "value": "https://iihms.gov.np"
                    }
                ]
            }
        ],
        "description": description,
        "scoring": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/measure-scoring",
                    "code": scoring_code,
                    "display": scoring_display
                }
            ]
        }
    }
    
    if improvement_code:
        measure["improvementNotation"] = {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/measure-improvement-notation",
                    "code": improvement_code,
                    "display": "Increased score indicates improvement" if improvement_code == "increase" else "Decreased score indicates improvement"
                }
            ]
        }
        
    # Group Definition (numerator and denominator)
    group = {
        "id": f"group-{measure_id}",
        "population": [
            {
                "id": f"pop-denom-{measure_id}",
                "code": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                            "code": "denominator",
                            "display": "Denominator"
                        }
                    ]
                },
                "criteria": {
                    "language": "text/cql",
                    "expression": denominator_desc
                }
            },
            {
                "id": f"pop-numer-{measure_id}",
                "code": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                            "code": "numerator",
                            "display": "Numerator"
                        }
                    ]
                },
                "criteria": {
                    "language": "text/cql",
                    "expression": numerator_desc
                }
            }
        ]
    }
    
    # Optional Gender Stratifier
    if has_gender_stratifier:
        group["stratifier"] = [
            {
                "id": "stratifier-gender",
                "code": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "263495000",
                            "display": "Gender"
                        }
                    ],
                    "text": "Stratification by patient gender"
                },
                "criteria": {
                    "language": "text/cql",
                    "expression": "Patient.gender"
                }
            }
        ]
        
    measure["group"] = [group]
    return measure

def main():
    output_dir = "fhir/measures"
    os.makedirs(output_dir, exist_ok=True)
    
    # 11 Standardized Indicators mapped from the verified Mapping Table
    measures_to_generate = [
        {
            "id": "nepal-tb-tsr-cure",
            "title": "Tuberculosis Treatment Success Rate (Cure Rate)",
            "description": "The proportion of registered bacteriologically confirmed TB cases that completed treatment and were cured.",
            "scoring_code": "proportion",
            "scoring_display": "Proportion",
            "numerator_desc": "Successfully cured TB cases (cured)",
            "denominator_desc": "Registered bacteriologically confirmed cases (pbc_reg)",
            "improvement_code": "increase",
            "has_gender_stratifier": True
        },
        {
            "id": "nepal-tb-notification-rate",
            "title": "Annualized Tuberculosis Notification Rate",
            "description": "The rate of newly notified and relapse TB cases per 100,000 population.",
            "scoring_code": "ratio",
            "scoring_display": "Ratio",
            "numerator_desc": "Total notified TB cases (total_tb_m+f)",
            "denominator_desc": "CBS Mid-year district population (district_pop_mid_year_cbs)",
            "improvement_code": None,
            "has_gender_stratifier": True
        },
        {
            "id": "nepal-tb-mortality-rate",
            "title": "Tuberculosis Mortality Rate",
            "description": "The proportion of registered TB patients who died during treatment.",
            "scoring_code": "proportion",
            "scoring_display": "Proportion",
            "numerator_desc": "Registered TB cases who died (died)",
            "denominator_desc": "Registered bacteriologically confirmed cases (pbc_reg)",
            "improvement_code": "decrease",
            "has_gender_stratifier": True
        },
        {
            "id": "nepal-tb-ltfu-rate",
            "title": "Tuberculosis Lost to Follow-Up (LTFU) Rate",
            "description": "The proportion of registered TB patients who were lost to follow-up.",
            "scoring_code": "proportion",
            "scoring_display": "Proportion",
            "numerator_desc": "TB cases lost to follow-up (ltfu)",
            "denominator_desc": "Registered bacteriologically confirmed cases (pbc_reg)",
            "improvement_code": "decrease",
            "has_gender_stratifier": True
        },
        {
            "id": "nepal-tb-failure-rate",
            "title": "Tuberculosis Treatment Failure Rate",
            "description": "The proportion of registered TB patients whose treatment failed.",
            "scoring_code": "proportion",
            "scoring_display": "Proportion",
            "numerator_desc": "TB cases whose treatment failed (failed)",
            "denominator_desc": "Registered bacteriologically confirmed cases (pbc_reg)",
            "improvement_code": "decrease",
            "has_gender_stratifier": True
        },
        {
            "id": "nepal-tb-not-eval-rate",
            "title": "Tuberculosis Not Evaluated Rate",
            "description": "The proportion of registered TB patients whose treatment outcome was not evaluated.",
            "scoring_code": "proportion",
            "scoring_display": "Proportion",
            "numerator_desc": "TB cases not evaluated (not_eval)",
            "denominator_desc": "Registered bacteriologically confirmed cases (pbc_reg)",
            "improvement_code": "decrease",
            "has_gender_stratifier": True
        },
        {
            "id": "nepal-tb-bacteriological-confirmation",
            "title": "Tuberculosis Bacteriological Confirmation Proportion",
            "description": "The proportion of notified TB cases that were bacteriologically confirmed.",
            "scoring_code": "proportion",
            "scoring_display": "Proportion",
            "numerator_desc": "Bacteriologically confirmed registered cases (pbc_reg)",
            "denominator_desc": "Total notified TB cases (total_tb_m+f)",
            "improvement_code": "increase",
            "has_gender_stratifier": False
        },
        {
            "id": "nepal-tb-xpert-coverage",
            "title": "Xpert MTB/RIF Coverage Rate",
            "description": "The proportion of the population covered or tested using Xpert MTB/RIF assays.",
            "scoring_code": "proportion",
            "scoring_display": "Proportion",
            "numerator_desc": "Xpert coverage percent * population",
            "denominator_desc": "CBS Mid-year district population (district_pop_mid_year_cbs)",
            "improvement_code": "increase",
            "has_gender_stratifier": False
        },
        {
            "id": "nepal-tb-hiv-coinfection",
            "title": "Tuberculosis/HIV Co-infection Proportion",
            "description": "The proportion of the population evaluated who are co-infected with TB and HIV.",
            "scoring_code": "proportion",
            "scoring_display": "Proportion",
            "numerator_desc": "TB-HIV percentage * population",
            "denominator_desc": "CBS Mid-year district population (district_pop_mid_year_cbs)",
            "improvement_code": None,
            "has_gender_stratifier": False
        },
        {
            "id": "nepal-tb-art-coverage",
            "title": "HIV/ART Coverage Percentage",
            "description": "The proportion of TB/HIV co-infected patients receiving antiretroviral therapy (ART).",
            "scoring_code": "proportion",
            "scoring_display": "Proportion",
            "numerator_desc": "ART coverage percentage * TB-HIV positive cases",
            "denominator_desc": "TB-HIV co-infected cases (tb_hiv_pct * population)",
            "improvement_code": "increase",
            "has_gender_stratifier": False
        },
        {
            "id": "nepal-tb-gender-ratio",
            "title": "Male-to-Female TB Notification Ratio",
            "description": "The ratio of notified male TB cases to female TB cases to track skewness in case detection.",
            "scoring_code": "ratio",
            "scoring_display": "Ratio",
            "numerator_desc": "Total male TB cases notified (total_tb_male)",
            "denominator_desc": "Total female TB cases notified (total_tb_female)",
            "improvement_code": None,
            "has_gender_stratifier": False
        }
    ]
    
    generated_files = []
    
    # Loop and generate standard FHIR JSON files
    for spec in measures_to_generate:
        resource = create_measure_resource(
            measure_id=spec["id"],
            title=spec["title"],
            description=spec["description"],
            scoring_code=spec["scoring_code"],
            scoring_display=spec["scoring_display"],
            numerator_desc=spec["numerator_desc"],
            denominator_desc=spec["denominator_desc"],
            improvement_code=spec.get("improvement_code"),
            has_gender_stratifier=spec["has_gender_stratifier"]
        )
        
        file_path = os.path.join(output_dir, f"{spec['id']}.json")
        with open(file_path, "w") as f:
            json.dump(resource, f, indent=2)
        generated_files.append(file_path)
        print(f"Generated FHIR Measure → {file_path}")
        
    print(f"\nSuccessfully generated {len(generated_files)} FHIR Measure resources in '{output_dir}/'")

if __name__ == "__main__":
    main()
