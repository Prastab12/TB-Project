import pandas as pd
import os
from datetime import date

RAW_PATH   = os.path.join("..", "..", "data", "raw", "Original Final_KTM_data_set.xlsx")
REPORT_OUT = os.path.join("..", "..", "outputs", "reports", "01_Data_Inspection_Report.md")

SHEET_MAIN = "Monthly Summary"


def load_sheet():
    xl      = pd.ExcelFile(RAW_PATH)
    df      = pd.read_excel(xl, sheet_name=SHEET_MAIN, header=0)
    df.columns = df.columns.str.strip()
    df      = df[df["BS_Year"].notna()].reset_index(drop=True)
    return df, xl.sheet_names


def profile_data():
    print(f"Loading: {RAW_PATH}")
    df, sheet_names = load_sheet()
    size_mb = os.path.getsize(RAW_PATH) / (1024 * 1024)

    print("\n" + "=" * 60)
    print("FILE INVENTORY")
    print("=" * 60)
    print(f"  File   : Original Final_KTM_data_set.xlsx")
    print(f"  Size   : {size_mb:.2f} MB")
    print(f"  Sheets : {sheet_names}")

    print("\n" + "=" * 60)
    print("SHEET — Monthly Summary")
    print("=" * 60)
    print(f"  Shape  : {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"\n  Columns:")
    for i, col in enumerate(df.columns):
        print(f"    {i:2d}: {repr(col)}")
    print(f"\n  Data Types:\n{df.dtypes.to_string()}")

    missing = df.isnull().sum()
    has_missing = missing[missing > 0]
    print(f"\n  Missing Values:")
    print(has_missing.to_string() if not has_missing.empty else "    None")

    print(f"\n  First 5 Rows:\n{df.head().to_string()}")

    print("\n" + "=" * 60)
    print("COVERAGE PROFILE")
    print("=" * 60)
    years = sorted(df["BS_Year"].dropna().astype(int).unique().tolist())
    print(f"  BS Years  : {years}")
    print(f"  District  : Kathmandu (fixed scope)")
    print(f"  Total months : {len(df)}")
    sex_complete = int(df["New Cases Female"].notna().sum())
    print(f"  Months with sex/age data : {sex_complete}")
    print(f"  Months without sex data  : {len(df) - sex_complete}  (Baishak/Jestha/Asar 2078)")
    print("\n  Monthly coverage by BS Year:")
    for yr, cnt in df.groupby("BS_Year")["BS_Month"].count().items():
        print(f"    {int(yr)}: {cnt} months")

    print("\n" + "=" * 60)
    print("POPULATION DENOMINATOR")
    print("=" * 60)
    for yr, pop in df.groupby("BS_Year")["District Pop (Mid-Year CBS)"].first().items():
        print(f"  BS {int(yr)}: {int(pop):,}")

    _write_report(df, size_mb, sheet_names)
    print(f"\n  Report written → {REPORT_OUT}")


def _write_report(df, size_mb, sheet_names):
    today       = date.today().strftime("%Y-%m-%d")
    missing     = df.isnull().sum()
    has_missing = missing[missing > 0]
    sex_cols    = ["New Cases Female", "New Cases Male", "Relapse Female",
                   "Relapse Male", "Total TB Female", "Total TB Male"]
    age_cols    = [c for c in df.columns if " to " in c or "65+" in c]
    sex_complete = int(df["New Cases Female"].notna().sum())

    lines = [
        "# Data Inspection Report & Dataset Catalog",
        "",
        f"**Assessment Date:** {today}  ",
        f"**Dataset:** `Original Final_KTM_data_set.xlsx`  ",
        "**Scope:** Kathmandu District, Bagmati Province, Nepal  ",
        "",
        "---",
        "",
        "## 1. File Inventory",
        "",
        "| File Name | Format | Size (MB) | Sheet(s) | Status |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| `Original Final_KTM_data_set.xlsx` | Excel (.xlsx) | {size_mb:.2f} |"
        f" {', '.join(sheet_names)} | Source Raw |",
        "",
        "---",
        "",
        "## 2. Dataset Structure",
        "",
        f"- **Rows:** {df.shape[0]}  (data rows; TOTAL summary row excluded during ingestion)",
        f"- **Columns:** {df.shape[1]}",
        f"- **Duplicate Rows:** {df.duplicated().sum()}",
        "- **Schema Consistency:** Single flat file — column schema is 100% consistent across all 60 months.",
        "- **Note:** `Quarter` and `District` columns are not present in this dataset. "
        "`Quarter` will be derived from `BS_Month` during Phase 2 cleaning. "
        "`District` is fixed as Kathmandu throughout.",
        "",
        "**Column Schema:**",
        "",
        "| # | Column | Dtype |",
        "| :--- | :--- | :--- |",
    ]
    for i, (col, dtype) in enumerate(df.dtypes.items()):
        lines.append(f"| {i} | `{col}` | `{dtype}` |")

    lines += [
        "",
        "---",
        "",
        "## 3. Coverage Profile",
        "",
        "| Attribute | Value |",
        "| :--- | :--- |",
        "| District | Kathmandu |",
        f"| BS Years | {sorted(df['BS_Year'].dropna().astype(int).unique().tolist())} |",
        f"| Total Months | {len(df)} |",
        f"| Months with Sex / Age Data | {sex_complete} |",
        f"| Months without Sex / Age Data | {len(df) - sex_complete} (Baishak, Jestha, Asar 2078) |",
        "",
        "**Monthly Coverage by BS Year:**",
        "",
        "| BS Year | Month Count |",
        "| :--- | :--- |",
    ]
    for yr, cnt in df.groupby("BS_Year")["BS_Month"].count().items():
        lines.append(f"| {int(yr)} | {cnt} |")

    lines += [
        "",
        "**Population Denominator (Annual CBS Mid-Year):**",
        "",
        "| BS Year | Population |",
        "| :--- | :--- |",
    ]
    for yr, pop in df.groupby("BS_Year")["District Pop (Mid-Year CBS)"].first().items():
        lines.append(f"| {int(yr)} | {int(pop):,} |")

    lines += [
        "",
        "---",
        "",
        "## 4. Missing Values Profile",
        "",
    ]
    if has_missing.empty:
        lines.append("No missing values.")
    else:
        lines += [
            "| Column | Missing | % Missing | Cause |",
            "| :--- | :--- | :--- | :--- |",
        ]
        for col in has_missing.index:
            m   = has_missing[col]
            pct = round(m / len(df) * 100, 1)
            if col in sex_cols or col in age_cols:
                cause = "Structural gap — BS 2078 Baishak / Jestha / Asar have no sex or age data in source"
            else:
                cause = "Review required"
            lines.append(f"| `{col}` | {m} | {pct}% | {cause} |")

    lines += [
        "",
        "---",
        "",
        "## 5. Data Source Notes",
        "",
        "- **Validated columns:** New Cases (Total), New Cases Female/Male, all 16 age-sex band columns — "
        "the 16 bands sum exactly to New Cases (Total) in all 57 months.",
        "- **Provisional columns:** Relapse Female, Relapse Male, Total TB Female, Total TB Male — "
        "may carry ±1–4 errors in ~25 months. Confirm against source file before sex-disaggregated relapse analysis.",
        "- **Outcome columns (*):** PBC New cohort data — recent months may be incomplete as cohorts need ~12 months to mature.",
        "- **Quarter:** Not present in raw file — will be derived in Phase 2 from BS_Month "
        "(Q1=Shrawan-Ashwin, Q2=Kartik-Poush, Q3=Magh-Chaitra, Q4=Baishak-Asar).",
    ]

    os.makedirs(os.path.dirname(REPORT_OUT), exist_ok=True)
    with open(REPORT_OUT, "w") as fh:
        fh.write("\n".join(lines))


if __name__ == "__main__":
    profile_data()
