import pandas as pd
import numpy as np
import os

def calculate_indicators():
    input_file = "data/final/final_cleaned_data.csv"
    output_file = "data/harmonized/harmonized_tb_data.csv"
    os.makedirs("data/harmonized", exist_ok=True)

    df = pd.read_csv(input_file)
    df['notification_rate_100k'] = (df['total_tb_m+f'] / df['district_pop_mid_year_cbs']) * 100000
    df['tsr_cure_rate'] = np.where(df['pbc_reg'] > 0, df['cured'] / df['pbc_reg'], 0)
    df['mortality_rate'] = np.where(df['pbc_reg'] > 0, df['died'] / df['pbc_reg'], 0)
    df['ltfu_rate'] = np.where(df['pbc_reg'] > 0, df['ltfu'] / df['pbc_reg'], 0)
    df['failure_rate'] = np.where(df['pbc_reg'] > 0, df['failed'] / df['pbc_reg'], 0)
    df['not_eval_rate'] = np.where(df['pbc_reg'] > 0, df['not_eval'] / df['pbc_reg'], 0)
    df['bacteriological_confirmation_pct'] = np.where(df['total_tb_m+f'] > 0, df['pbc_reg'] / df['total_tb_m+f'], 0)
    
    indicator_cols = ['notification_rate_100k', 'tsr_cure_rate', 'mortality_rate', 
                      'ltfu_rate', 'failure_rate', 'not_eval_rate', 'bacteriological_confirmation_pct']
    df[indicator_cols] = df[indicator_cols].round(4)
    df.to_csv(output_file, index=False)
    print(f"Harmonized Data → {output_file}")

if __name__ == "__main__":
    calculate_indicators()
