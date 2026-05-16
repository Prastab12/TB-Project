import pandas as pd
import numpy as np

def run_post_validation():
    input_file  = "data/final/final_cleaned_data.csv"
    df = pd.read_csv(input_file)
    
    checks = []
    
    # 1. Total Missingness
    total_missing = df.isna().sum().sum()
    checks.append(("No empty values in entire dataset", total_missing == 0))
    
    # 2. Column Types (Numeric columns should be int64)
    # We'll check the columns we expected to be numeric
    numeric_vars = [
        'bs_year', 'district_pop_mid_year_cbs', 'new_cases_total', 'pbc_reg',
        'tb_hiv_pct', 'art_cov_pct', 'xpert_cov_pct', 'm_to_f_ratio'
    ]
    all_int = True
    for var in numeric_vars:
        dtype = str(df[var].dtype)
        if 'int64' not in dtype:
            all_int = False
            print(f"DEBUG: {var} is {dtype} (expected int64)")
    checks.append(("Numeric columns converted to Int64", all_int))
    
    # 3. Specific value check (0 replacement)
    # Checking a column that previously had high missingness (art_cov_pct)
    # It should have no NaNs and many 0s.
    art_nulls = df['art_cov_pct'].isna().sum()
    checks.append(("art_cov_pct has 0 nulls", art_nulls == 0))

    # 4. District Spelling
    valid_districts = ['BHAKTAPUR','CHITAWAN','DHADING','DOLAKHA','KATHMANDU',
                       'KAVREPALANCHOK','LALITPUR','MAKAWANPUR','NUWAKOT',
                       'RAMECHHAP','RASUWA','SINDHULI','SINDHUPALCHOK']
    bad_dist = df[~df['district'].isin(valid_districts)]['district'].unique()
    checks.append(("District Spelling Standardized", len(bad_dist) == 0))
    
    print("\n" + "="*50)
    print("POST-CLEANING VALIDATION RESULTS (Zero-Fill & Int64 Strategy)")
    print("="*50)
    all_passed = True
    for label, status in checks:
        icon = "✅" if status else "❌"
        print(f"{icon} {label}")
        if not status: all_passed = False
    
    print("="*50)
    if all_passed:
        print("STATUS: DATA IS CLEAN (Zero-filled & Integer cast complete).")
        print("⚠️  Warning: Decimal precision in rates/percentages has been removed per request.")
    else:
        print("STATUS: ERRORS DETECTED.")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_post_validation()
