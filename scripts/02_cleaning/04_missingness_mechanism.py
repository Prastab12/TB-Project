import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import logit
import warnings
warnings.filterwarnings('ignore')

def test_missingness():
    df = pd.read_csv("../../data/cleaned/cleaned_data.csv")
    print("==================================================")
    print("MISSINGNESS MECHANISM TESTING REPORT")
    print("==================================================")
    
    # We will test missingness mechanisms for key variables with nulls
    test_vars = ['art_cov_pct', 'm_to_f_ratio', 'new_cases_total']
    
    print("Method: Logistic regression of missingness indicator (1=Missing, 0=Observed)")
    print("Covariates: District, Fiscal Year (bs_year)")
    print("Threshold: Alpha = 0.05 to reject MCAR\n")
    
    for target in test_vars:
        if df[target].isnull().sum() == 0:
            continue
            
        print(f"--- Variable: {target} ({df[target].isnull().sum()} missing rows) ---")
        
        # Create missingness indicator
        df['is_missing'] = df[target].isnull().astype(int)
        
        # Logistic Regression formula using categorical covariates
        formula = "is_missing ~ C(district) + C(bs_year)"
        try:
            # Fit the logistic model
            model = logit(formula, data=df).fit(disp=0)
            p_values = model.pvalues
            
            # Check for significant predictors (excluding intercept)
            sig_covariates = p_values[(p_values < 0.05) & (p_values.index != 'Intercept')]
            
            if len(sig_covariates) > 0:
                print("MCAR Hypothesis: REJECTED")
                print("Classification: MAR (Missing at Random) or MNAR")
                print("Details: Missingness is significantly predicted by observed covariates.")
                print("Significant Predictors (p < 0.05):")
                for idx, pval in sig_covariates.items():
                    print(f"  * {idx} (p = {pval:.4e})")
                
                # Apply the 20% rule for final classification
                missing_pct = (df[target].isnull().sum() / len(df)) * 100
                if missing_pct > 20:
                    print("--> FINAL CLASSIFICATION: MNAR / GAP (Because missingness > 20%)")
                else:
                    print("--> FINAL CLASSIFICATION: MAR (Safe for MICE imputation)")
            else:
                print("MCAR Hypothesis: NOT REJECTED")
                print("Classification: MCAR (Missing Completely at Random)")
                print("Details: Missingness does not depend on District or Year.")
                print("--> FINAL CLASSIFICATION: MCAR (Safe for MICE imputation)")
                
        except Exception as e:
            print(f"Error fitting model for {target}. It may be perfectly separated: {e}")
        print("")

if __name__ == "__main__":
    test_missingness()
