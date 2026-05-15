import pandas as pd
import os

raw_path = "../../data/raw/Data.xlsx"
clean_path = "../../data/cleaned/cleaned_data.csv"

def inspect_data():
    print("--- 1. FILE INVENTORY ---")
    print(f"Total Raw Files: 1 (Data.xlsx)")
    size_mb = os.path.getsize(raw_path) / (1024 * 1024)
    print(f"File Size: {size_mb:.2f} MB")
    
    xl = pd.ExcelFile(raw_path)
    print(f"Sheet Names in Raw File: {xl.sheet_names}")
    
    print("\n--- 2. STRUCTURAL INSPECTION (Cleaned Data) ---")
    df = pd.read_csv(clean_path)
    
    print(f"Shape: {df.shape}")
    print(f"Duplicate Rows: {df.duplicated().sum()}")
    
    print("\nFiscal Year Coverage:")
    print(df['bs_year'].unique().tolist())
    
    print("\nDistrict Coverage (Count):")
    print(f"Total Districts: {df['district'].nunique()}")
    print(df['district'].unique().tolist()[:5], "...")
    
    print("\nMonthly Completeness:")
    print(df['bs_month'].unique().tolist())
    
    vaccine_cols = [c for c in df.columns if 'vaccin' in c.lower() or 'dose' in c.lower() or 'vax' in c.lower()]
    print(f"\nVaccine Columns Found: {vaccine_cols if vaccine_cols else 'None'}")
    
    print("\nMissing Values Breakdown:")
    missing = df.isnull().sum()
    print(missing[missing > 0])
    
    print("\nData Types:")
    print(df.dtypes.value_counts())

if __name__ == "__main__":
    inspect_data()
