import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import missingno as msno
import os

CLEAN_PATH = "../../data/cleaned/cleaned_data.csv"
FIG_DIR    = "../../outputs/figures"


def assess_completeness():
    df = pd.read_csv(CLEAN_PATH)

    print("=" * 50)
    print("COMPLETENESS ASSESSMENT REPORT")
    print("=" * 50)

    identifiers = ["chron_order", "bs_month", "bs_year", "ad_year",
                   "district_pop_mid_year_cbs"]
    variables   = [c for c in df.columns if c not in identifiers]

    # 1. Variable-wise missingness
    print("\n--- 1. Variable-Wise Missingness ---")
    var_miss = (df[variables].isnull().sum() / len(df)) * 100
    print(f"{'Variable':<30} | {'Missing %':>10} | Status")
    print("-" * 58)
    flagged = []
    for var, pct in var_miss.items():
        if pct == 0:
            status = "Complete"
        elif pct <= 20:
            status = "Imputable (<=20%)"
        else:
            status = "GAP (>20%)"
            flagged.append((var, pct))
        print(f"{var:<30} | {pct:>9.2f}% | {status}")

    print("\n--- Flagged Variables (>20% Missingness) ---")
    if flagged:
        for var, pct in flagged:
            print(f"  {var}: {pct:.2f}% — document as gap, do NOT impute")
    else:
        print("  None. All variables <= 20% missing.")

    # 2. Record-wise missingness
    print("\n--- 2. Record-Wise Missingness Summary ---")
    row_miss = (df[variables].isnull().sum(axis=1) / len(variables)) * 100
    print(f"  Average record missingness : {row_miss.mean():.2f}%")
    print(f"  Max record missingness     : {row_miss.max():.2f}%")
    print(f"  Perfectly complete records : {(row_miss == 0).sum()} / {len(df)}")
    print(f"\n  Breakdown:")
    for _, row in df[row_miss > 0][["bs_month", "bs_year"]].iterrows():
        print(f"    BS {int(row['bs_year'])} {row['bs_month']} — structural reporting gap")

    # 3. Missingness heatmap
    print("\n--- 3. Generating Missingness Heatmap ---")
    df_sorted = df.sort_values(["bs_year", "chron_order"]).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(16, 8))
    msno.matrix(df_sorted[variables], ax=ax, sparkline=False, fontsize=9)
    ax.set_title("Missingness Matrix — Kathmandu District TB Data (Sorted Chronologically)",
                 fontsize=13)

    os.makedirs(FIG_DIR, exist_ok=True)
    fig_path = os.path.join(FIG_DIR, "missingness_matrix.png")
    plt.savefig(fig_path, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"  Missingness matrix saved → {fig_path}")

    print("\nScript 03 complete.")


if __name__ == "__main__":
    assess_completeness()
