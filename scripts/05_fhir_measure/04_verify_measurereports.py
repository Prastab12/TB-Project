import json
import glob
import os

def main():
    reports_dir = "fhir/district_monthly_measure_report"
    files = glob.glob(os.path.join(reports_dir, "*.json"))
    
    print(f"Auditing {len(files)} generated FHIR MeasureReports...")
    
    passed = 0
    failed = 0
    
    for f_path in files:
        try:
            with open(f_path, "r") as f:
                data = json.load(f)
                
            # Verify basic structure
            assert data["resourceType"] == "MeasureReport", "Missing resourceType"
            assert "id" in data, "Missing ID"
            assert data["status"] == "complete", "Incorrect status"
            
            # Verify sum of stratifiers matches group totals
            group = data["group"][0]
            group_denom = [p["count"] for p in group["population"] if p["code"]["coding"][0]["code"] == "denominator"][0]
            group_numer = [p["count"] for p in group["population"] if p["code"]["coding"][0]["code"] == "numerator"][0]
            
            strat_denom_sum = 0
            strat_numer_sum = 0
            
            strata = group["stratifier"][0]["stratum"]
            assert len(strata) == 13, f"Expected 13 districts, found {len(strata)}"
            
            for s in strata:
                s_denom = [p["count"] for p in s["population"] if p["code"]["coding"][0]["code"] == "denominator"][0]
                s_numer = [p["count"] for p in s["population"] if p["code"]["coding"][0]["code"] == "numerator"][0]
                strat_denom_sum += s_denom
                strat_numer_sum += s_numer
                
            assert group_denom == strat_denom_sum, f"Denominator mismatch: Group={group_denom}, StratSum={strat_denom_sum}"
            assert group_numer == strat_numer_sum, f"Numerator mismatch: Group={group_numer}, StratSum={strat_numer_sum}"
            
            passed += 1
        except Exception as e:
            print(f"Verification failed for {os.path.basename(f_path)}: {str(e)}")
            failed += 1
            
    print(f"\nAudit complete: {passed} passed, {failed} failed.")

if __name__ == "__main__":
    main()
