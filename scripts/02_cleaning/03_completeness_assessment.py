import pandas as pd
import missingno as msno
import matplotlib.pyplot as plt
import os

def assess_completeness():
    clean_path = "../../data/cleaned/cleaned_data.csv"
    df = pd.read_csv(clean_path)
    
    print("==================================================")
    print("COMPLETENESS ASSESSMENT REPORT")
    print("==================================================")
    
    # Identify variables (excluding identifiers)
    identifiers = ['chron_order', 'bs_month', 'bs_year', 'ad_year', 'quarter', 'district', 'code', 'eco_zone', 'district_pop_mid_year_cbs']
    variables = [col for col in df.columns if col not in identifiers]
    
    # 1. Variable-wise missingness (%)
    print("\n--- 1. Variable-Wise Missingness ---")
    var_missingness = (df[variables].isnull().sum() / len(df)) * 100
    
    print(f"{'Variable':<25} | {'Missing %':<10} | {'Status'}")
    print("-" * 55)
    flagged_vars = []
    for var, pct in var_missingness.items():
        if pct == 0:
            status = "✅ Complete"
        elif pct <= 20:
            status = "⚠️ Imputable (≤20%)"
        else:
            status = "❌ GAP (>20%)"
            flagged_vars.append((var, pct))
        print(f"{var:<25} | {pct:>8.2f}% | {status}")
        
    print("\n--- Flagged Variables (>20% Missingness) ---")
    if flagged_vars:
        for var, pct in flagged_vars:
            print(f" - {var}: {pct:.2f}% (Must be documented as gap, NOT imputed)")
    else:
        print("None. All variables are ≤20% missing.")
        
    # 2. Record-wise missingness
    print("\n--- 2. Record-Wise Missingness Summary ---")
    row_missingness = (df[variables].isnull().sum(axis=1) / len(variables)) * 100
    print(f"Average record missingness: {row_missingness.mean():.2f}%")
    print(f"Max record missingness:     {row_missingness.max():.2f}%")
    print(f"Perfectly complete records: {(row_missingness == 0).sum()} out of {len(df)}")
    
    # 3. Produce missingness heatmap
    print("\n--- 3. Generating Missingness Heatmap ---")
    # Sort by district and time for logical visual flow
    df_sorted = df.sort_values(['district', 'bs_year', 'chron_order']).reset_index(drop=True)
    
    fig = msno.matrix(df_sorted[variables], sparkline=False, figsize=(14, 8), fontsize=10)
    plt.title("Missingness Matrix (Sorted by District & Time)", fontsize=16)
    
    out_dir = "../../outputs/figures"
    os.makedirs(out_dir, exist_ok=True)
    fig_path = os.path.join(out_dir, "missingness_matrix.png")
    
    # Save the figure
    plt.savefig(fig_path, bbox_inches='tight', dpi=300)
    print(f"✅ Missingness matrix saved to {fig_path}")

if __name__ == "__main__":
    assess_completeness()
