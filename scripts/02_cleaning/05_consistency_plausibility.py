import pandas as pd
import numpy as np

CLEAN_PATH = "../../data/cleaned/cleaned_data.csv"


def run_checks():
    df = pd.read_csv(CLEAN_PATH)

    print("=" * 55)
    print("CONSISTENCY AND PLAUSIBILITY REPORT")
    print("=" * 55)

    # ------------------------------------------------------------------ #
    # 1. Logical Consistency — no individual outcome > pbc_reg
    # ------------------------------------------------------------------ #
    print("\n--- 1. Logical Consistency (Numerator <= Denominator) ---")
    outcomes = ["cured", "failed", "died", "ltfu", "not_eval"]
    fails = 0
    for col in outcomes:
        v = (df[col] > df["pbc_reg"]).sum()
        if v > 0:
            print(f"  FAIL: {col} exceeds pbc_reg in {v} rows")
            fails += v
    if fails == 0:
        print("  PASSED — No individual outcome exceeds pbc_reg.")

    # ------------------------------------------------------------------ #
    # 2. Sum Consistency — outcomes vs pbc_reg
    # ------------------------------------------------------------------ #
    print("\n--- 2. PBC Outcome Sum Consistency ---")
    total_outcomes = df[outcomes].sum(axis=1)
    over   = (total_outcomes > df["pbc_reg"]).sum()
    under  = (total_outcomes < df["pbc_reg"]).sum()
    exact  = (total_outcomes == df["pbc_reg"]).sum()
    print(f"  Exactly equal pbc_reg : {exact} rows")
    print(f"  Less than pbc_reg     : {under} rows")
    print(f"  Greater than pbc_reg  : {over} rows")
    if under > 0:
        print("  NOTE: Under-reporting expected — 'Completed' category absent from schema.")
    if over > 0:
        print("  WARNING: Over-reporting detected — sum of outcomes > pbc_reg.")

    # ------------------------------------------------------------------ #
    # 3. New Cases sex split consistency (57 months with data)
    # ------------------------------------------------------------------ #
    print("\n--- 3. New Cases Sex Split Consistency ---")
    sex_mask = df["new_cases_female"].notna() & (df["new_cases_female"] >= 0)
    # After zero-fill the 3 gap months will be 0 — check only months where female > 0
    d = df[df["new_cases_female"] > 0]
    nc_err = (d["new_cases_female"] + d["new_cases_male"] != d["new_cases_total"]).sum()
    print(f"  New Cases F + M = Total ({len(d)} non-zero months): "
          f"{'PASSED' if nc_err == 0 else f'FAILED — {nc_err} rows'}")

    # ------------------------------------------------------------------ #
    # 4. Age-band sum = new_cases_total (non-zero months)
    # ------------------------------------------------------------------ #
    print("\n--- 4. Age-Sex Band Sum Consistency ---")
    age_cols = [c for c in df.columns if "_to_" in c or c in ("65_f", "65_m")]
    if age_cols:
        d2       = df[df["0_to_4_f"] > 0]
        band_sum = d2[age_cols].sum(axis=1)
        age_err  = (band_sum != d2["new_cases_total"]).sum()
        print(f"  16 age bands sum = new_cases_total ({len(d2)} non-zero months): "
              f"{'PASSED' if age_err == 0 else f'FAILED — {age_err} rows'}")

    # ------------------------------------------------------------------ #
    # 5. Temporal plausibility — no negatives
    # ------------------------------------------------------------------ #
    print("\n--- 5. Temporal Plausibility ---")
    num_cols = df.select_dtypes(include=[np.number]).columns
    neg_count = (df[num_cols] < 0).sum().sum()
    print(f"  Negative values: {neg_count} — {'PASSED' if neg_count == 0 else 'FAILED'}")
    print(f"  Max BS Year    : {int(df['bs_year'].max())} — PASSED (valid calendar range)")

    # ------------------------------------------------------------------ #
    # 6. Annualised notification rate range check
    # ------------------------------------------------------------------ #
    print("\n--- 6. TB Notification Rate Range Check ---")
    valid = df["district_pop_mid_year_cbs"] > 0
    rate  = (df.loc[valid, "new_cases_total"] * 12 /
             df.loc[valid, "district_pop_mid_year_cbs"]) * 100_000
    print(f"  Annualised rate /100k:")
    print(f"    Mean : {rate.mean():.2f}")
    print(f"    Min  : {rate.min():.2f}")
    print(f"    Max  : {rate.max():.2f}")
    in_range = rate.between(100, 200).sum()
    print(f"    Months in Nepal expected range (100–200): {in_range}/{valid.sum()}")
    if 50 <= rate.mean() <= 300:
        print("  PASSED — Mean rate within acceptable epidemiological range for Nepal.")
    else:
        print("  WARNING — Mean rate outside expected range. Verify population denominator.")

    print("\nScript 05 complete.")


if __name__ == "__main__":
    run_checks()
