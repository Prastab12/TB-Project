import os
import json
import glob
from pydantic import ValidationError
from fhir.resources.measurereport import MeasureReport
from fhir.resources.bundle import Bundle
from fhir.resources.measure import Measure


def get_expected_dates(bs_year, bs_month):
    """
    Deterministic BS to AD Gregorian period mapper for assertion validation.
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

def validate_measure_report(file_path):
    """
    Tier 2 (fhir.resources) & Tier 3 (semantic logic) validation for MeasureReport.
    """
    errors = []
    
    # 1. Tier 2: FHIR R4 Specification Check
    try:
        report = MeasureReport.parse_file(file_path)
    except ValidationError as e:
        errors.append(f"Tier 2 Spec Error: Pydantic validation failed: {str(e)}")
        return errors
    
    # Load raw JSON for Tier 3 checks (to inspect physical presence/absence of properties)
    with open(file_path, "r") as f:
        raw = json.load(f)
        
    # 2. Tier 3: Subject Integrity Check
    subject = raw.get("subject", {})
    if subject.get("reference") != "Location/loc-kathmandu":
        errors.append(f"Tier 3 Error: Reference must be 'Location/loc-kathmandu', got '{subject.get('reference')}'")
    if subject.get("display") != "Kathmandu District, Nepal":
        errors.append(f"Tier 3 Error: Reference display must be 'Kathmandu District, Nepal', got '{subject.get('display')}'")
        
    # 3. Tier 3: Date & Calendar Mapping Check
    period = raw.get("period", {})
    extensions = period.get("extension", [])
    fiscal_ext = None
    for ext in extensions:
        if ext.get("url") == "https://iihms.gov.np/fhir/StructureDefinition/nepali-fiscal-period":
            fiscal_ext = ext
            break
            
    if not fiscal_ext:
        errors.append("Tier 3 Error: Missing custom 'nepali-fiscal-period' extension under period.")
    else:
        sub_exts = fiscal_ext.get("extension", [])
        bs_yr, bs_month, fy = None, None, None
        for sub in sub_exts:
            if sub.get("url") == "bs-year":
                bs_yr = sub.get("valueInteger")
            elif sub.get("url") == "bs-month":
                bs_month = sub.get("valueString")
            elif sub.get("url") == "fiscal-year":
                fy = sub.get("valueString")
                
        if not bs_yr or not bs_month or not fy:
            errors.append(f"Tier 3 Error: Malformed nepali-fiscal-period extension sub-fields (bs_year={bs_yr}, bs_month={bs_month}, fy={fy})")
        else:
            # Deterministic date mapping audit
            expected_start, expected_end = get_expected_dates(bs_yr, bs_month)
            if period.get("start") != expected_start or period.get("end") != expected_end:
                errors.append(f"Tier 3 Error: Period bounds mismatch for {bs_month} {bs_yr} (Expected {expected_start} to {expected_end}, got {period.get('start')} to {period.get('end')})")
                
    # 4. Tier 3: DataAbsentReason Extension & Score Audit
    groups = raw.get("group", [])
    for g_idx, group in enumerate(groups):
        score_obj = group.get("measureScoreQuantity", {})
        has_absent_reason = False
        
        # Check populations
        populations = group.get("population", [])
        for p_idx, pop in enumerate(populations):
            absent_ext = None
            if "_count" in pop:
                count_exts = pop["_count"].get("extension", [])
                for ext in count_exts:
                    if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/data-absent-reason":
                        absent_ext = ext
                        break
                        
            if absent_ext:
                has_absent_reason = True
                if absent_ext.get("valueCode") != "not-reported":
                    errors.append(f"Tier 3 Error: DataAbsentReason valueCode must be 'not-reported', got '{absent_ext.get('valueCode')}'")
                if "count" in pop:
                    errors.append(f"Tier 3 Error: Property 'count' must be omitted when data absent reason extension is present under group[{g_idx}] population[{p_idx}].")
            else:
                if "count" not in pop:
                    errors.append(f"Tier 3 Error: Missing required 'count' property under group[{g_idx}] population[{p_idx}].")
                    
        # Check measureScoreQuantity
        if has_absent_reason:
            if "value" in score_obj:
                errors.append(f"Tier 3 Error: measureScoreQuantity.value must be omitted when either population is absent.")
            if "_value" not in score_obj:
                errors.append(f"Tier 3 Error: Missing '_value' with data-absent-reason extension under measureScoreQuantity.")
            else:
                val_exts = score_obj["_value"].get("extension", [])
                score_absent = False
                for ext in val_exts:
                    if ext.get("url") == "http://hl7.org/fhir/StructureDefinition/data-absent-reason" and ext.get("valueCode") == "not-reported":
                        score_absent = True
                        break
                if not score_absent:
                    errors.append(f"Tier 3 Error: Missing 'not-reported' data-absent-reason extension in measureScoreQuantity._value.")
        else:
            if "value" not in score_obj:
                errors.append(f"Tier 3 Error: Missing measureScoreQuantity.value property for valid count calculations.")
            if "_value" in score_obj:
                errors.append(f"Tier 3 Error: Property '_value' must be omitted when numerical score value exists.")

                
    return errors

def validate_bundle(file_path):
    """
    Tier 2 validation for FHIR Bundle.
    """
    errors = []
    try:
        Bundle.parse_file(file_path)
    except ValidationError as e:
        errors.append(f"Tier 2 Spec Error: Bundle validation failed: {str(e)}")
    return errors

def validate_measure(file_path):
    """
    Tier 2 validation for FHIR definitional Measure.
    """
    errors = []
    try:
        Measure.parse_file(file_path)
    except ValidationError as e:
        errors.append(f"Tier 2 Spec Error: Measure validation failed: {str(e)}")
    return errors

def main():
    # 1. Audit definitional Measures
    meas_dir = "fhir/measures/measures"
    failures = {}
    total_measures_audited = 0
    total_def_bundles_audited = 0
    
    if os.path.exists(meas_dir):
        print("🔍 Auditing definitional Measures and Bundle in fhir/measures/measures/...")
        meas_files = glob.glob(os.path.join(meas_dir, "nepal-tb-*.json"))
        for f in meas_files:
            fname = os.path.basename(f)
            if "bundle" in fname:
                total_def_bundles_audited += 1
                errors = validate_bundle(f)
            else:
                total_measures_audited += 1
                errors = validate_measure(f)
                
            if errors:
                failures[f"Definitional/{fname}"] = errors
                
    # 2. Audit monthly reports and bundles
    base_dir = "fhir/measures/measure_report/monthwise_measure_report"
    total_reports_audited = 0
    total_bundles_audited = 0
    
    if os.path.exists(base_dir):
        monthly_folders = sorted(glob.glob(os.path.join(base_dir, "*")))
        print(f"🔍 Auditing {len(monthly_folders)} monthly directories in {base_dir}...\n")
        
        for folder in monthly_folders:
            folder_name = os.path.basename(folder)
            reports = glob.glob(os.path.join(folder, "tb-*.json"))
            bundles = glob.glob(os.path.join(folder, "bundle-*.json"))
            
            # Audit Reports
            for rep in reports:
                rep_name = os.path.basename(rep)
                rep_errors = validate_measure_report(rep)
                total_reports_audited += 1
                if rep_errors:
                    failures[f"{folder_name}/{rep_name}"] = rep_errors
                    
            # Audit Bundles
            for bun in bundles:
                bun_name = os.path.basename(bun)
                bun_errors = validate_bundle(bun)
                total_bundles_audited += 1
                if bun_errors:
                    failures[f"{folder_name}/{bun_name}"] = bun_errors
                    
    print("================================================================================")
    print("📋 PHASE 7 AUDIT RESULTS SUMMARY")
    print("================================================================================")
    print(f"Total Definitional Measures Audited : {total_measures_audited}")
    print(f"Total Definitional Bundles Audited  : {total_def_bundles_audited}")
    print(f"Total MeasureReports Audited        : {total_reports_audited}")
    print(f"Total Monthly Bundles Audited       : {total_bundles_audited}")
    print(f"Total Failed Resources              : {len(failures)}")
    
    if failures:
        print("\n❌ FAILED CHECKS ENCOUNTERED:")
        for res_path, errs in failures.items():
            print(f"\n  [!] Resource: {res_path}")
            for err in errs:
                print(f"      → {err}")
        print("\n================================================================================")
        print("❌ STATUS: AUDIT FAILED.")
        exit(1)
    else:
        print("\n✅ STATUS: AUDIT PASSED successfully! 100% structural and logical integrity.")
        print("================================================================================")
        exit(0)


if __name__ == "__main__":
    main()
