import pandas as pd
import re
import os

RAW_PATH   = os.path.join("..", "..", "data", "raw", "Original Final_KTM_data_set.xlsx")
CLEAN_PATH = os.path.join("..", "..", "data", "cleaned", "cleaned_data.csv")


def clean_column_name(col):
    col = str(col)
    col = re.sub(r'[\*\(\)]', '', col)       # remove *, (, )
    col = col.replace('+', '')               # remove + (handles 65+ and TB-HIV +ve)
    col = re.sub(r'[\n\s\-]+', '_', col)    # spaces/hyphens → _
    col = col.replace('%', '_pct')
    col = col.replace(':', '_to_')
    col = re.sub(r'_+', '_', col)           # collapse multiple underscores
    col = col.strip('_').lower()
    return col


def main():
    print(f"Loading: {RAW_PATH}")
    df = pd.read_excel(RAW_PATH, sheet_name="Monthly Summary", header=0)
    df.columns = df.columns.str.strip()

    # Exclude TOTAL summary row
    df = df[df["BS_Year"].notna()].reset_index(drop=True)
    print(f"  Rows after excluding TOTAL row: {len(df)}")

    # Pre-rename ambiguous column before standardisation
    df.rename(columns={"TB-HIV +ve": "TB-HIV Positive"}, inplace=True)

    # Standardise column names to snake_case
    df.columns = [clean_column_name(c) for c in df.columns]

    # Add chronological order (1-based)
    df.insert(0, "chron_order", range(1, len(df) + 1))

    # Strip whitespace from month names
    df["bs_month"] = df["bs_month"].str.strip()

    os.makedirs(os.path.dirname(CLEAN_PATH), exist_ok=True)
    df.to_csv(CLEAN_PATH, index=False)

    print(f"  Final shape   : {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"  Columns       : {list(df.columns)}")
    print(f"  Saved → {CLEAN_PATH}")
    print("Script 01 complete.")


if __name__ == "__main__":
    main()
