import pandas as pd
import os
import re

def clean_column_name(col):
    col = str(col)
    # Remove asterisks and parentheses
    col = re.sub(r'[\*\(\)]', '', col)
    # Replace newlines, spaces, and hyphens with underscores
    col = re.sub(r'[\n\s\-]+', '_', col)
    # Replace % with _pct
    col = col.replace('%', '_pct')
    # Replace colons (e.g. M:F Ratio -> m_to_f_ratio)
    col = col.replace(':', '_to_')
    # Remove trailing/leading underscores and convert to lowercase
    col = col.strip('_').lower()
    return col

def main():
    # Define paths relative to the script location
    raw_path = os.path.join("..", "..", "data", "raw", "Data.xlsx")
    clean_path = os.path.join("..", "..", "data", "cleaned", "cleaned_data.csv")
    
    print(f"Loading raw data...")
    df = pd.read_excel(raw_path, header=2)
    
    print(f"Original shape: {df.shape}")
    
    # 1. Standardize Column Names
    print("Cleaning column names...")
    df.columns = [clean_column_name(col) for col in df.columns]
    
    # 2. Filter out aggregated Province rows
    print("Filtering out 'BAGMATI PROVINCE' aggregate rows...")
    df = df[df['district'] != 'BAGMATI PROVINCE']
    
    # We are still NOT dropping any rows with missing data (no dropna)
    
    # 3. Save Cleaned Data
    print(f"Saving cleaned dataset to {clean_path}...")
    df.to_csv(clean_path, index=False)
    
    print(f"Cleaned shape: {df.shape}")
    print("First 5 cleaned column names:")
    for col in df.columns[:5]:
        print(f" - {col}")
    print("Cleaning step 1 completed successfully.")

if __name__ == "__main__":
    main()
