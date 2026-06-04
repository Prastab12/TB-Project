"""
Phase 4 — Internal FHIR R4 validation.
Validates all 32 Measure definitions and 1,920 MeasureReport instances.
Produces outputs/reports/08_FHIR_Validation_Report.txt
"""

import csv, json, os, re
from datetime import datetime, timezone

BASE         = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEASURES_DIR = os.path.join(BASE, "fhir", "measures")
BY_VAR_DIR   = os.path.join(BASE, "fhir", "measure_reports", "by_indicator")
BUNDLES_DIR  = os.path.join(BASE, "fhir", "measure_reports", "bundles")
CSV_PATH     = os.path.join(BASE, "data", "final", "final_cleaned_data.csv")
REPORT_PATH  = os.path.join(BASE, "outputs", "reports",
                             "08_FHIR_Validation_Report.txt")

FHIR_BASE = "https://iihms.gov.np/fhir"
NCP_URL   = f"{FHIR_BASE}/StructureDefinition/nepali-fiscal-period"
DAR_URL   = "http://hl7.org/fhir/StructureDefinition/data-absent-reason"
POP_SYS   = "http://terminology.hl7.org/CodeSystem/measure-population"
UCUM_SYS  = "http://unitsofmeasure.org"
SCR_SYS   = "http://terminology.hl7.org/CodeSystem/measure-scoring"

RATIO_VARIABLES = [
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
COHORT_VARIABLES = [
    ("pbc-reg",  "pbc_reg"),
    ("cured",    "cured"),
    ("failed",   "failed"),
    ("died",     "died"),
    ("ltfu",     "ltfu"),
    ("not-eval", "not_eval"),
]

ALL_VARIABLES = [(v[0], v[1]) for v in RATIO_VARIABLES] + list(COHORT_VARIABLES)
RATIO_IDS     = {v[0] for v in RATIO_VARIABLES}
COHORT_IDS    = {v[0] for v in COHORT_VARIABLES}
GAP_AFFECTED  = {v[0] for v in RATIO_VARIABLES if v[2]}
VAR_COLS      = {v[0]: v[1] for v in RATIO_VARIABLES}
VAR_COLS.update({v[0]: v[1] for v in COHORT_VARIABLES})
DENOM_COL     = "district_pop_mid_year_cbs"
GAP_MONTHS    = {("2078", "Baishak"), ("2078", "Jestha"), ("2078", "Asar")}

EXPECTED_MEASURES         = 32
EXPECTED_MR_PER_VAR       = 60
EXPECTED_TOTAL_MR         = EXPECTED_MEASURES * EXPECTED_MR_PER_VAR   # 1920
EXPECTED_BUNDLE_ENTRIES   = 3 + EXPECTED_MR_PER_VAR                   # 63
EXPECTED_MASTER_ENTRIES   = 3 + EXPECTED_TOTAL_MR                     # 1923

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}Z)?$")


# ── Reporter ──────────────────────────────────────────────────────────────────
class Rpt:
    def __init__(self):
        self.errors = []
        self.warns  = []
        self.passed = 0
        self.log    = []

    def err(self, ctx, msg):
        self.errors.append(f"  ERROR   [{ctx}] {msg}")
        self.log.append(f"    [FAIL] {msg}")

    def warn(self, ctx, msg):
        self.warns.append(f"  WARNING [{ctx}] {msg}")
        self.log.append(f"    [WARN] {msg}")

    def ok(self, msg=""):
        self.passed += 1
        if msg: self.log.append(f"    [PASS] {msg}")

    def sec(self, title):
        self.log += ["", f"  {title}", "  " + "-" * (len(title) + 2)]


# ── Measure validation ────────────────────────────────────────────────────────
def validate_measure(data, ctx, rpt):
    rpt.sec(f"Measure: {data.get('id', ctx)}")
    for f in ["resourceType", "id", "url", "status", "scoring", "group"]:
        if f not in data: rpt.err(ctx, f"Missing required field: '{f}'")
        else:             rpt.ok(f"'{f}' present")

    if data.get("resourceType") != "Measure":
        rpt.err(ctx, f"resourceType must be 'Measure'")
    else: rpt.ok("resourceType = 'Measure'")

    url = data.get("url", "")
    if not url.startswith(f"{FHIR_BASE}/Measure/nepal-tb-"):
        rpt.err(ctx, f"url invalid: '{url}'")
    else: rpt.ok(f"canonical url valid")

    if data.get("status") != "active":
        rpt.err(ctx, f"status must be 'active', got '{data.get('status')}'")
    else: rpt.ok("status = 'active'")

    codings      = data.get("scoring", {}).get("coding", [])
    scoring_code = codings[0].get("code") if codings else None
    if scoring_code not in ("ratio", "cohort"):
        rpt.err(ctx, f"scoring.code must be 'ratio' or 'cohort', got '{scoring_code}'")
    else: rpt.ok(f"scoring.code = '{scoring_code}'")

    groups = data.get("group", [])
    if not groups:
        rpt.err(ctx, "group is empty"); return
    pops = groups[0].get("population", [])
    if scoring_code == "ratio":
        if len(pops) != 2:
            rpt.err(ctx, f"ratio measure must have 2 populations, got {len(pops)}")
        else:
            rpt.ok("population count = 2 (numerator + denominator)")
            for i, exp in enumerate(["numerator", "denominator"]):
                code = pops[i].get("code", {}).get("coding", [{}])[0].get("code")
                if code != exp: rpt.err(ctx, f"population[{i}].code must be '{exp}'")
                else:           rpt.ok(f"population[{i}].code = '{exp}'")
    else:
        if len(pops) != 1:
            rpt.err(ctx, f"cohort measure must have 1 population, got {len(pops)}")
        else:
            code = pops[0].get("code", {}).get("coding", [{}])[0].get("code")
            if code != "initial-population":
                rpt.err(ctx, f"population.code must be 'initial-population'")
            else: rpt.ok("population.code = 'initial-population'")


# ── MeasureReport validation ──────────────────────────────────────────────────
def validate_mr(data, ctx, rpt, csv_row=None, var_id=None, standalone=True):
    for f in ["resourceType", "id", "status", "type", "measure", "period"]:
        if f not in data: rpt.err(ctx, f"Missing required field: '{f}'")
        else:             rpt.ok()

    if data.get("resourceType") != "MeasureReport":
        rpt.err(ctx, "resourceType must be 'MeasureReport'")
    else: rpt.ok()

    if data.get("status") != "complete":
        rpt.err(ctx, f"status must be 'complete'")
    else: rpt.ok()

    if data.get("type") != "summary":
        rpt.err(ctx, f"type must be 'summary'")
    else: rpt.ok()

    measure = data.get("measure", "")
    if not measure.startswith(f"{FHIR_BASE}/Measure/"):
        rpt.err(ctx, f"measure URL invalid")
    else: rpt.ok()

    period = data.get("period", {})
    for p in ["start", "end"]:
        if p not in period:
            rpt.err(ctx, f"period.{p} missing")
        elif not DATE_RE.match(period[p]):
            rpt.err(ctx, f"period.{p} invalid: '{period[p]}'")
        else: rpt.ok()

    if "start" in period and "end" in period:
        try:
            s = datetime.strptime(period["start"][:10], "%Y-%m-%d")
            e = datetime.strptime(period["end"][:10],   "%Y-%m-%d")
            if s >= e: rpt.err(ctx, "period.start must be before period.end")
            else:      rpt.ok()
        except ValueError:
            pass

    ext_urls = [ex.get("url", "") for ex in period.get("extension", [])]
    if NCP_URL not in ext_urls:
        rpt.warn(ctx, "period missing nepali-fiscal-period extension")
    else: rpt.ok()

    if standalone:
        contained = data.get("contained", [])
        if len(contained) != 3:
            rpt.err(ctx, f"standalone must have 3 contained, has {len(contained)}")
        else: rpt.ok()

    groups = data.get("group", [])
    if not groups:
        rpt.err(ctx, "group array empty"); return
    g    = groups[0]
    pops = g.get("population", [])
    ms   = g.get("measureScore")

    is_ratio = var_id in RATIO_IDS if var_id else ("nepal-tb-" in data.get("measure","") and
               data["measure"].split("nepal-tb-")[-1] in RATIO_IDS)

    if is_ratio:
        if len(pops) != 2:
            rpt.err(ctx, f"ratio must have 2 populations, has {len(pops)}")
        else:
            for i, exp in enumerate(["numerator", "denominator"]):
                pop  = pops[i]
                code = pop.get("code", {}).get("coding", [{}])[0].get("code")
                if code != exp: rpt.err(ctx, f"population[{i}].code must be '{exp}'")
                else:           rpt.ok()
                if "_count" not in pop and "count" not in pop:
                    rpt.err(ctx, f"population[{i}] must have 'count' or '_count'")
                elif "_count" in pop:
                    dar = [e.get("url") for e in pop["_count"].get("extension", [])]
                    if DAR_URL not in dar: rpt.err(ctx, f"population[{i}]._count missing DAR")
                    else:                  rpt.ok()
                else:
                    if not isinstance(pop["count"], int) or pop["count"] < 0:
                        rpt.err(ctx, f"population[{i}].count invalid")
                    else: rpt.ok()
    else:
        if len(pops) != 1:
            rpt.err(ctx, f"cohort must have 1 population, has {len(pops)}")
        else:
            pop  = pops[0]
            code = pop.get("code", {}).get("coding", [{}])[0].get("code")
            if code != "initial-population":
                rpt.err(ctx, "population.code must be 'initial-population'")
            else: rpt.ok()
            if "count" not in pop:
                rpt.err(ctx, "population.count missing")
            elif not isinstance(pop["count"], int) or pop["count"] < 0:
                rpt.err(ctx, f"population.count invalid: {pop.get('count')}")
            else: rpt.ok()

    if ms is None:
        rpt.err(ctx, "measureScore missing")
    else:
        if "_value" in ms:
            dar = [e.get("url") for e in ms["_value"].get("extension", [])]
            if DAR_URL not in dar: rpt.err(ctx, "measureScore._value missing DAR")
            else:                   rpt.ok()
        elif "value" in ms:
            if not isinstance(ms["value"], (int, float)) or ms["value"] < 0:
                rpt.err(ctx, f"measureScore.value invalid: {ms.get('value')}")
            else: rpt.ok()
        else:
            rpt.err(ctx, "measureScore must have 'value' or '_value'")

    # CSV cross-check
    if csv_row and var_id:
        yr  = csv_row["bs_year"]
        mo  = csv_row["bs_month"].strip()
        col = VAR_COLS.get(var_id, "")
        is_gap = var_id in GAP_AFFECTED and (yr, mo) in GAP_MONTHS
        exp_val = int(float(csv_row.get(col, 0))) if col else None

        if is_ratio and pops:
            numer = pops[0]
            if is_gap:
                if "_count" not in numer:
                    rpt.err(ctx, f"expected DAR for {yr} {mo} [{col}]")
                else: rpt.ok()
            elif exp_val is not None:
                actual = numer.get("count")
                if actual != exp_val:
                    rpt.err(ctx, f"CSV cross-check [{col}]: CSV={exp_val}, file={actual}")
                else: rpt.ok()
        elif not is_ratio and pops:
            actual = pops[0].get("count")
            if exp_val is not None and actual != exp_val:
                rpt.err(ctx, f"CSV cross-check [{col}]: CSV={exp_val}, file={actual}")
            else: rpt.ok()


# ── Bundle validation ─────────────────────────────────────────────────────────
def validate_bundle(path, rpt, expected_mr):
    ctx  = os.path.basename(path)
    data = json.load(open(path, encoding="utf-8"))

    if data.get("resourceType") != "Bundle":
        rpt.err(ctx, "resourceType must be 'Bundle'"); return
    else: rpt.ok()
    if data.get("type") != "collection":
        rpt.err(ctx, "type must be 'collection'")
    else: rpt.ok()
    if "total" in data:
        rpt.err(ctx, "'total' not allowed in collection bundles")
    else: rpt.ok()

    entries  = data.get("entry", [])
    expected = 3 + expected_mr
    if len(entries) != expected:
        rpt.err(ctx, f"Expected {expected} entries, got {len(entries)}")
    else: rpt.ok(f"entry count = {len(entries)}")

    seen = set()
    for e in entries[3:]:
        fu  = e.get("fullUrl", "")
        r   = e.get("resource", {})
        rid = r.get("id", "?")
        if not fu.startswith(f"{FHIR_BASE}/MeasureReport/"):
            rpt.err(ctx, f"{rid}: fullUrl invalid")
        if "contained" in r:
            rpt.err(ctx, f"{rid}: must not have 'contained' in bundle entry")
        if rid in seen: rpt.err(ctx, f"Duplicate id: {rid}")
        else:           seen.add(rid); rpt.ok()
        validate_mr(r, f"{ctx}/{rid}", rpt, standalone=False)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    rpt  = Rpt()
    now  = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    L    = []

    def h(t=""): L.append(t)
    def sep(c="="): L.append(c * 72)

    with open(CSV_PATH, encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))

    sep(); h("  FHIR R4 INTERNAL VALIDATION REPORT")
    h(f"  Generated  : {now}")
    h(f"  Project    : TB Performance Dashboard — Kathmandu District, Nepal")
    h(f"  FHIR Ver   : R4 (4.0.1)")
    sep()

    # ── Section 1: Measure files ──────────────────────────────────────────────
    h(); sep()
    h("SECTION 1 — MEASURE DEFINITION FILES  (fhir/measures/)")
    sep()
    measure_files = sorted([
        f for f in os.listdir(MEASURES_DIR)
        if f.endswith(".json") and "bundle" not in f
    ])
    h(f"  Files found: {len(measure_files)}  (expected: {EXPECTED_MEASURES})")
    if len(measure_files) != EXPECTED_MEASURES:
        rpt.err("measures", f"Expected {EXPECTED_MEASURES}, found {len(measure_files)}")
    else: rpt.ok()

    for fname in measure_files:
        data = json.load(open(os.path.join(MEASURES_DIR, fname), encoding="utf-8"))
        validate_measure(data, fname, rpt)
    for line in rpt.log: h(line)
    rpt.log.clear()

    # ── Section 2: MeasureReport files ───────────────────────────────────────
    h(); sep()
    h(f"SECTION 2 — MEASUREREPORT FILES  (fhir/measure_reports/by_indicator/)")
    h(f"  Expected: {EXPECTED_MEASURES} variables × {EXPECTED_MR_PER_VAR} months "
      f"= {EXPECTED_TOTAL_MR} files")
    sep()

    total_files = 0
    dar_total   = 0
    summary     = []

    for var_id, csv_col in ALL_VARIABLES:
        var_dir = os.path.join(BY_VAR_DIR, var_id)
        if not os.path.exists(var_dir):
            rpt.err(var_id, "directory missing"); continue

        files = sorted(os.listdir(var_dir))
        if len(files) != EXPECTED_MR_PER_VAR:
            rpt.err(var_id, f"Expected {EXPECTED_MR_PER_VAR} files, found {len(files)}")
        else: rpt.ok()

        var_errors = 0
        var_dar    = 0
        h(f"\n  Variable: nepal-tb-{var_id}  (csv: {csv_col})")

        for fname in files:
            path = os.path.join(var_dir, fname)
            data = json.load(open(path, encoding="utf-8"))
            ctx  = f"{var_id}/{fname}"
            m    = re.match(r"tb-.+-kathmandu-(\d+)-(.+)\.json", fname)
            if not m:
                rpt.err(ctx, "filename pattern mismatch"); continue
            yr, mo_lc = m.groups()
            csv_row   = next(
                (r for r in csv_rows
                 if r["bs_year"] == yr and r["bs_month"].strip().lower() == mo_lc),
                None)

            before = len(rpt.errors)
            validate_mr(data, ctx, rpt, csv_row=csv_row,
                        var_id=var_id, standalone=True)
            errs = len(rpt.errors) - before
            if errs: var_errors += 1

            g    = (data.get("group") or [{}])[0]
            pops = g.get("population", [])
            if var_id in RATIO_IDS and pops and "_count" in pops[0]:
                var_dar  += 1
                dar_total += 1

            total_files += 1

        summary.append((var_id, len(files), var_errors, var_dar))
        h(f"    → {len(files)} files, {var_errors} errors, DAR: {var_dar}")

    for line in rpt.log: h(line)
    rpt.log.clear()

    h(); sep("-")
    h("  VARIABLE SUMMARY")
    sep("-")
    h(f"  {'Variable':<30} {'Files':>6} {'Errors':>7} {'DAR':>5}")
    h("  " + "-" * 52)
    for vid, n, errs, dar in summary:
        h(f"  {vid:<30} {n:>6} {errs:>7} {dar:>5}")
    h("  " + "-" * 52)
    h(f"  {'TOTAL':<30} {total_files:>6} {sum(e for _,_,e,_ in summary):>7} {dar_total:>5}")

    # ── Section 3: Bundles ────────────────────────────────────────────────────
    h(); sep()
    h("SECTION 3 — MEASUREREPORT BUNDLES  (fhir/measure_reports/bundles/)")
    sep()

    # Per-variable bundles
    h(f"\n  Per-variable bundles  ({EXPECTED_BUNDLE_ENTRIES} entries each)")
    h(f"  {'Bundle':<44} {'Entries':>8}  Status")
    h("  " + "-" * 62)
    for var_id, _ in ALL_VARIABLES:
        bpath = os.path.join(BUNDLES_DIR, f"bundle-{var_id}.json")
        if not os.path.exists(bpath):
            rpt.err("bundles", f"bundle-{var_id}.json missing")
            h(f"  bundle-{var_id+'.json':<37} {'—':>8}  MISSING")
        else:
            before = len(rpt.errors)
            validate_bundle(bpath, rpt, EXPECTED_MR_PER_VAR)
            errs = len(rpt.errors) - before
            data = json.load(open(bpath, encoding="utf-8"))
            n    = len(data.get("entry", []))
            status = "PASS" if errs == 0 else f"FAIL ({errs} errors)"
            h(f"  {'bundle-'+var_id+'.json':<44} {n:>8}  {status}")

    # Master bundle
    h(f"\n  Master bundle  ({EXPECTED_MASTER_ENTRIES} entries)")
    h("  " + "-" * 62)
    master_path = os.path.join(BUNDLES_DIR, "bundle-all.json")
    if not os.path.exists(master_path):
        rpt.err("bundles", "bundle-all.json missing")
    else:
        before = len(rpt.errors)
        validate_bundle(master_path, rpt, EXPECTED_TOTAL_MR)
        errs   = len(rpt.errors) - before
        data   = json.load(open(master_path, encoding="utf-8"))
        n      = len(data.get("entry", []))
        status = "PASS" if errs == 0 else f"FAIL ({errs} errors)"
        h(f"  bundle-all.json{'':<29} {n:>8}  {status}")

    for line in rpt.log: h(line)
    rpt.log.clear()

    # ── Summary ───────────────────────────────────────────────────────────────
    h(); sep()
    h("VALIDATION SUMMARY")
    sep()
    h(f"  Measure definition files     : {len(measure_files)}")
    h(f"  MeasureReport files          : {total_files}")
    h(f"  Per-variable bundles         : {len(ALL_VARIABLES)}")
    h(f"  Master bundle                : 1")
    h("")
    h(f"  Checks passed  : {rpt.passed}")
    h(f"  Errors         : {len(rpt.errors)}")
    h(f"  Warnings       : {len(rpt.warns)}")
    h(f"  DAR entries    : {dar_total}  (data-absent-reason: not-reported)")
    h("")
    if rpt.errors:
        h("  ERRORS:")
        for e in rpt.errors: h(e)
        h("")
    if rpt.warns:
        h("  WARNINGS:")
        for w in rpt.warns: h(w)
        h("")
    if not rpt.errors:
        h("  RESULT: ALL CHECKS PASSED")
        h("  STATUS: Ready for external HAPI FHIR R4 validation")
    else:
        h("  RESULT: VALIDATION FAILED")
    sep()

    report_text = "\n".join(L)
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"  Errors: {len(rpt.errors)}  Warnings: {len(rpt.warns)}  "
          f"Passed: {rpt.passed}  DAR: {dar_total}")
    print(f"  Report → {REPORT_PATH}")
    print("Phase 4 — Validation complete.")


if __name__ == "__main__":
    main()
