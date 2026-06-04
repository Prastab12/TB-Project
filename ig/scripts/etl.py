"""
IG ETL — Nepal NTP TB FHIR MeasureReport pipeline
===================================================
Stack  : fhir.resources 8.x (Pydantic v2) + pandas
Input  : data/final/final_cleaned_data.csv  (60 rows × 37 cols, Kathmandu)
Output : ig/fhir-output/measure-reports/    (all 1,920 MeasureReport JSON files)
         ig/input/resources/               (3 canonical IG example files)

Architectural rules:
  - External references only — NO contained resources.
  - Profile declared in meta.profile for every MeasureReport.
  - Ratio indicators  → numerator + denominator populations + measureScore.
  - Cohort indicators → initial-population only, no measureScore.
  - Under-reported months (BS 2078 Baishak / Jestha / Asar) and any empty
    CSV cell trigger FHIR Data Absent Reason (not-reported) on the affected
    population._count and measureScore._value fields.

Usage:
  python3 etl.py              # generate all 780 + 3 IG examples
  python3 etl.py --examples   # generate only the 3 IG example files
"""

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.extension import Extension
from fhir.resources.measurereport import (
    MeasureReport,
    MeasureReportGroup,
    MeasureReportGroupPopulation,
)
from fhir.resources.meta import Meta
from fhir.resources.period import Period
from fhir.resources.quantity import Quantity
from fhir.resources.reference import Reference

# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE       = Path(__file__).resolve().parent          # ig/scripts/
_IG_ROOT    = _HERE.parent                             # ig/
_PROJ_ROOT  = _IG_ROOT.parent                          # TB Project root

INPUT_CSV   = _PROJ_ROOT / "data" / "final" / "final_cleaned_data.csv"
OUT_ALL     = _IG_ROOT / "fhir-output" / "measure-reports" / "by_indicator"
OUT_EXAMPLES = _IG_ROOT / "input" / "resources"

# ── FHIR canonicals ────────────────────────────────────────────────────────────
FHIR_BASE       = "https://iihms.gov.np/fhir"
PROFILE_MR      = f"{FHIR_BASE}/StructureDefinition/tb-measure-report"
NEPALI_EXT_URL  = f"{FHIR_BASE}/StructureDefinition/nepali-fiscal-period"
DAR_URL         = "http://hl7.org/fhir/StructureDefinition/data-absent-reason"
POP_SYS         = "http://terminology.hl7.org/CodeSystem/measure-population"
UCUM_SYS        = "http://unitsofmeasure.org"
DENOMINATOR_COL = "district_pop_mid_year_cbs"

# Months where DHIS2 source data was not collected for Kathmandu
UNDER_REPORTED = {("2078", "Baishak"), ("2078", "Jestha"), ("2078", "Asar")}

# ── Calendar helpers ───────────────────────────────────────────────────────────
_MONTH_TO_GM = {
    "Baishak": 4, "Jestha": 5, "Asar": 6,    "Shrawan": 7,
    "Bhadra":  8, "Ashwin": 9, "Kartik": 10, "Mangsir": 11,
    "Poush":  12, "Magh":   1, "Falgun":  2, "Chaitra":  3,
}
_FY_ORDER = [
    "Shrawan", "Bhadra", "Ashwin", "Kartik", "Mangsir", "Poush",
    "Magh", "Falgun", "Chaitra", "Baishak", "Jestha", "Asar",
]


def _iso_period(bs_year: int, bs_month: str) -> tuple[str, str]:
    """Return Gregorian (start, end) ISO dates for a BS year+month."""
    m = _MONTH_TO_GM[bs_month]
    g_year = bs_year - 57 if m >= 4 else bs_year - 56
    nm, ny = (m + 1, g_year) if m < 12 else (1, g_year + 1)
    return f"{g_year}-{m:02d}-16", f"{ny}-{nm:02d}-15"


def _fiscal_year(bs_year: int, bs_month: str) -> str:
    """Return the Nepali fiscal year string, e.g. '2078/79'."""
    pos = _FY_ORDER.index(bs_month) + 1
    if pos <= 9:
        return f"{bs_year}/{str(bs_year + 1)[-2:]}"
    return f"{bs_year - 1}/{str(bs_year)[-2:]}"


# ── Variable specs ─────────────────────────────────────────────────────────────
# (measure-id-suffix, csv_column, gap_affected)
# gap_affected=True  → apply data-absent-reason for Baishak/Jestha/Asar 2078
RATIO_INDICATORS = [
    ("new-cases-total",   "new_cases_total",  False),
    ("new-cases-female",  "new_cases_female", True),
    ("new-cases-male",    "new_cases_male",   True),
    ("relapse-total",     "relapse_total",    True),
    ("relapse-female",    "relapse_female",   True),
    ("relapse-male",      "relapse_male",     True),
    ("total-tb-notified", "total_tb_mf",      True),
    ("total-tb-female",   "total_tb_female",  True),
    ("total-tb-male",     "total_tb_male",    True),
    ("hiv-positive",      "tb_hiv_positive",  False),
    ("age-0to4-f",        "0_to_4_f",         True),
    ("age-0to4-m",        "0_to_4_m",         True),
    ("age-5to14-f",       "5_to_14_f",        True),
    ("age-5to14-m",       "5_to_14_m",        True),
    ("age-15to24-f",      "15_to_24_f",       True),
    ("age-15to24-m",      "15_to_24_m",       True),
    ("age-25to34-f",      "25_to_34_f",       True),
    ("age-25to34-m",      "25_to_34_m",       True),
    ("age-35to44-f",      "35_to_44_f",       True),
    ("age-35to44-m",      "35_to_44_m",       True),
    ("age-45to54-f",      "45_to_54_f",       True),
    ("age-45to54-m",      "45_to_54_m",       True),
    ("age-55to64-f",      "55_to_64_f",       True),
    ("age-55to64-m",      "55_to_64_m",       True),
    ("age-65plus-f",      "65_f",             True),
    ("age-65plus-m",      "65_m",             True),
]

COHORT_INDICATORS = [
    ("pbc-reg",  "pbc_reg"),
    ("cured",    "cured"),
    ("failed",   "failed"),
    ("died",     "died"),
    ("ltfu",     "ltfu"),
    ("not-eval", "not_eval"),
]

# ── FHIR builder helpers ───────────────────────────────────────────────────────

def _dar_primitive() -> dict:
    """Primitive extension dict for Data Absent Reason = not-reported."""
    return {"extension": [{"url": DAR_URL, "valueCode": "not-reported"}]}


def _pop_code(code: str) -> CodeableConcept:
    return CodeableConcept(
        coding=[Coding(
            system=POP_SYS,
            code=code,
            display=code.replace("-", " ").title(),
        )]
    )


def _build_period(bs_year: int, bs_month: str) -> Period:
    """Build a FHIR Period with Gregorian dates and NepaliCalendarPeriod extension."""
    start, end = _iso_period(bs_year, bs_month)
    fy = _fiscal_year(bs_year, bs_month)
    nepali_ext = Extension(
        url=NEPALI_EXT_URL,
        extension=[
            Extension(url="bs-year",     valueInteger=bs_year),
            Extension(url="bs-month",    valueString=bs_month),
            Extension(url="fiscal-year", valueString=fy),
        ],
    )
    return Period(extension=[nepali_ext], start=start, end=end)


def _ratio_group(
    row: pd.Series, ind_id: str, num_col: str, gap_affected: bool,
    bs_year: str, bs_month: str
) -> MeasureReportGroup:
    """Build the MeasureReportGroup for a ratio (notification) variable."""
    absent  = (gap_affected and (bs_year, bs_month) in UNDER_REPORTED) \
              or str(row[num_col]).strip() in ("", "nan")
    num_raw = str(row[num_col]).strip()
    den_raw = str(row[DENOMINATOR_COL]).strip()
    num_val = int(float(num_raw)) if num_raw not in ("", "nan") else 0
    den_val = int(float(den_raw))

    if absent:
        numer_pop = MeasureReportGroupPopulation.model_validate(
            {"code": _pop_code("numerator").model_dump(), "_count": _dar_primitive()}
        )
        score = Quantity.model_validate(
            {"unit": "1", "system": UCUM_SYS, "code": "1", "_value": _dar_primitive()}
        )
    else:
        numer_pop = MeasureReportGroupPopulation(
            code=_pop_code("numerator"), count=num_val
        )
        ratio = round(num_val / den_val, 8) if den_val > 0 else 0.0
        score = Quantity(value=ratio, unit="1", system=UCUM_SYS, code="1")

    denom_pop = MeasureReportGroupPopulation(
        code=_pop_code("denominator"), count=den_val
    )

    return MeasureReportGroup(
        id=f"group-nepal-tb-{ind_id}",
        population=[numer_pop, denom_pop],
        measureScoreQuantity=score,
    )


def _cohort_group(
    row: pd.Series, ind_id: str, csv_col: str
) -> MeasureReportGroup:
    """Build the MeasureReportGroup for a cohort (treatment outcome) indicator."""
    raw     = str(row[csv_col]).strip()
    missing = raw in ("", "nan")
    val     = int(float(raw)) if not missing else 0

    if missing:
        pop = MeasureReportGroupPopulation.model_validate(
            {"code": _pop_code("initial-population").model_dump(), "_count": _dar_primitive()}
        )
    else:
        pop = MeasureReportGroupPopulation(code=_pop_code("initial-population"), count=val)

    return MeasureReportGroup(id=f"group-nepal-tb-{ind_id}", population=[pop])


def _measure_report(
    row: pd.Series, ind_id: str, group: MeasureReportGroup, now_str: str
) -> MeasureReport:
    """Assemble a complete FHIR R4 MeasureReport using fhir.resources models."""
    bs_year  = int(row["bs_year"])
    bs_month = str(row["bs_month"]).strip()

    return MeasureReport(
        id=f"tb-{ind_id}-kathmandu-{bs_year}-{bs_month.lower()}",
        meta=Meta(profile=[PROFILE_MR]),
        status="complete",
        type="summary",
        measure=f"{FHIR_BASE}/Measure/nepal-tb-{ind_id}",
        subject=Reference(
            reference="Location/loc-kathmandu",
            display="Kathmandu District, Nepal",
        ),
        date=now_str,
        reporter=Reference(
            reference="Organization/org-ntp",
            display="National Tuberculosis Programme",
        ),
        period=_build_period(bs_year, bs_month),
        group=[group],
    )


# ── R4 serialization ──────────────────────────────────────────────────────────
# fhir.resources 8.x uses R5-style choice-type field names (e.g.
# measureScoreQuantity).  FHIR R4 wire format uses the un-suffixed name
# (measureScore).  We post-process the dict to rename the field back.

_R5_TO_R4 = {"measureScoreQuantity": "measureScore"}


def _to_r4(obj: dict | list) -> dict | list:
    """Recursively rename R5 choice-type keys to their R4 equivalents."""
    if isinstance(obj, list):
        return [_to_r4(i) for i in obj]
    if isinstance(obj, dict):
        return {_R5_TO_R4.get(k, k): _to_r4(v) for k, v in obj.items()}
    return obj


# ── Output helpers ─────────────────────────────────────────────────────────────

def _write(path: Path, mr: MeasureReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = _to_r4(json.loads(mr.model_dump_json()))
    path.write_text(json.dumps(raw, indent=2))


# ── Main pipeline ──────────────────────────────────────────────────────────────

def run(examples_only: bool = False) -> None:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    df = pd.read_csv(INPUT_CSV, dtype=str).fillna("")
    df["bs_month"] = df["bs_month"].str.strip()
    print(f"Loaded {len(df)} rows from {INPUT_CSV.name}")

    if not examples_only:
        if OUT_ALL.exists():
            shutil.rmtree(OUT_ALL)
        OUT_ALL.mkdir(parents=True)

    total, dar_count = 0, 0

    # Track 3 canonical IG examples (written once)
    ig_examples: dict[str, MeasureReport] = {}

    for _, row in df.iterrows():
        bs_year  = str(row["bs_year"])
        bs_month = str(row["bs_month"])

        # ── Ratio variables ───────────────────────────────────────────────────
        for ind_id, num_col, gap_affected in RATIO_INDICATORS:
            group = _ratio_group(row, ind_id, num_col, gap_affected, bs_year, bs_month)
            mr    = _measure_report(row, ind_id, group, now_str)

            is_dar = gap_affected and (bs_year, bs_month) in UNDER_REPORTED
            if is_dar:
                dar_count += 1

            if not examples_only:
                out_path = OUT_ALL / ind_id / f"{mr.id}.json"
                _write(out_path, mr)

            # Capture IG examples:
            #   ratio     → new-cases-total, Shrawan 2078  (full data, no DAR)
            #   ratio-dar → new-cases-female, Baishak 2078 (gap month, DAR applied)
            if ind_id == "new-cases-total" and bs_year == "2078" \
                    and bs_month == "Shrawan" and "ratio" not in ig_examples:
                ig_examples["ratio"] = mr
            if ind_id == "new-cases-female" and bs_year == "2078" \
                    and bs_month == "Baishak" and "ratio-dar" not in ig_examples:
                ig_examples["ratio-dar"] = mr

            total += 1

        # ── Cohort indicators ─────────────────────────────────────────────────
        for ind_id, csv_col in COHORT_INDICATORS:
            group = _cohort_group(row, ind_id, csv_col)
            mr    = _measure_report(row, ind_id, group, now_str)

            if not examples_only:
                out_path = OUT_ALL / ind_id / f"{mr.id}.json"
                _write(out_path, mr)

            # Capture IG example (first cohort)
            if ind_id == "cured" and bs_year == "2078" and bs_month == "Shrawan" \
                    and "cohort" not in ig_examples:
                ig_examples["cohort"] = mr

            total += 1

    # ── Write IG examples ─────────────────────────────────────────────────────
    example_map = {
        "ratio":     "example-mr-ratio.json",
        "ratio-dar": "example-mr-ratio-dar.json",
        "cohort":    "example-mr-cohort.json",
    }
    for key, filename in example_map.items():
        if key in ig_examples:
            _write(OUT_EXAMPLES / filename, ig_examples[key])
            print(f"  IG example → {filename}")

    # ── Summary ───────────────────────────────────────────────────────────────
    if not examples_only:
        print(f"\nGenerated : {total} MeasureReport files")
        print(f"DAR entries: {dar_count}")
        print(f"Output dir : {OUT_ALL}")
    print(f"IG examples: {OUT_EXAMPLES}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Nepal NTP TB FHIR ETL — fhir.resources + pandas"
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Generate only the 3 canonical IG example files (fast mode)",
    )
    args = parser.parse_args()
    run(examples_only=args.examples)
