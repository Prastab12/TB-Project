import pandas as pd
import os

# Define paths
raw_data_path = os.path.join("..", "..", "data", "raw", "Data.xlsx")

def profile_data():
    print(f"Loading data from {raw_data_path}...")
    try:
        df = pd.read_excel(raw_data_path, header=2)
    except Exception as e:
        print(f"Error loading data: {e}")
        return

    print("\n" + "="*50)
    print("DATASET OVERVIEW")
    print("="*50)
    print(f"Total Rows: {df.shape[0]}")
    print(f"Total Columns: {df.shape[1]}")
    
    print("\n" + "="*50)
    print("COLUMNS & DATA TYPES")
    print("="*50)
    print(df.dtypes)
    
    print("\n" + "="*50)
    print("MISSING VALUES")
    print("="*50)
    missing = df.isnull().sum()
    print(missing[missing > 0])
    
    print("\n" + "="*50)
    print("FIRST 5 ROWS")
    print("="*50)
    print(df.head())

if __name__ == "__main__":
    profile_data()
