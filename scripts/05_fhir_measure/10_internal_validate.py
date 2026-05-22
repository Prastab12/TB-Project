"""
Internal FHIR R4 validation for Measure and MeasureReport resources.
Produces a detailed txt report covering every check performed.
"""

import csv, json, os, re
from datetime import datetime, timezone

BASE         = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MEASURES_DIR = os.path.join(BASE, "fhir/measures/measures")
BY_IND       = os.path.join(BASE, "fhir/measure_reports/by_indicator")
BUNDLES      = os.path.join(BASE, "fhir/measure_reports/bundles")
CSV_PATH     = os.path.join(BASE, "data/final/final_cleaned_data.csv")
REPORT_PATH  = os.path.join(BASE, "fhir/VALIDATION_REPORT.txt")
FHIR_BASE    = "https://iihms.gov.np/fhir"

RATIO_INDICATORS = [
    ("new-cases-total",   "new_cases_total"),
    ("new-cases-female",  "new_cases_female"),
    ("new-cases-male",    "new_cases_male"),
    ("relapse-total",     "relapse_total"),
    ("relapse-female",    "relapse_female"),
    ("relapse-male",      "relapse_male"),
    ("total-tb-notified", "total_tb_m+f"),
]
COHORT_INDICATORS = [
    ("pbc-reg",  "pbc_reg"),
    ("cured",    "cured"),
    ("failed",   "failed"),
    ("died",     "died"),
    ("ltfu",     "ltfu"),
    ("not-eval", "not_eval"),
]
INDICATORS   = RATIO_INDICATORS + COHORT_INDICATORS
RATIO_IDS    = {i[0] for i in RATIO_INDICATORS}
COHORT_IDS   = {i[0] for i in COHORT_INDICATORS}
IND_IDS      = [i[0] for i in INDICATORS]
IND_COLS     = {i[0]: i[1] for i in INDICATORS}
DENOMINATOR_COL = "district_pop_mid_year_cbs"

UNDER_REPORTED = {("2078", "Baishak"), ("2078", "Jestha"), ("2078", "Asar")}

DAR_URL             = "http://hl7.org/fhir/StructureDefinition/data-absent-reason"
POP_CODE_SYS        = "http://terminology.hl7.org/CodeSystem/measure-population"
UCUM_SYS            = "http://unitsofmeasure.org"
MEASURE_SCORING_SYS = "http://terminology.hl7.org/CodeSystem/measure-scoring"
DATE_RE             = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}Z)?$")

VALID_STATUS         = {"complete", "pending", "error"}
VALID_TYPE           = {"individual", "subject-list", "summary", "data-collection"}
VALID_MEASURE_STATUS = {"draft", "active", "retired", "unknown"}


# ── Report collector ──────────────────────────────────────────────────────────
class Report:
    def __init__(self):
        self.errors   = []
        self.warnings = []
        self.passed   = 0
        self.log      = []   # detailed per-check lines

    def err(self, ctx, msg):
        self.errors.append(f"  ERROR   [{ctx}] {msg}")
        self.log.append(f"    [FAIL] {msg}")

    def warn(self, ctx, msg):
        self.warnings.append(f"  WARNING [{ctx}] {msg}")
        self.log.append(f"    [WARN] {msg}")

    def ok(self, msg=""):
        self.passed += 1
        if msg:
            self.log.append(f"    [PASS] {msg}")

    def section(self, title):
        self.log.append("")
        self.log.append("  " + title)
        self.log.append("  " + "-" * (len(title) + 2))


def check_date(val):
    return bool(DATE_RE.match(val)) if isinstance(val, str) else False


# ── Measure validation ────────────────────────────────────────────────────────
def validate_measure(data, ctx, rpt):
    rpt.section(f"Measure: {data.get('id', ctx)}")

    for field in ["resourceType", "id", "url", "status", "scoring", "group"]:
        if field not in data:
            rpt.err(ctx, f"Missing required field: '{field}'")
        else:
            rpt.ok(f"Required field '{field}' present")

    if data.get("resourceType") != "Measure":
        rpt.err(ctx, f"resourceType must be 'Measure', got '{data.get('resourceType')}'")
    else:
        rpt.ok("resourceType = 'Measure'")

    if data.get("status") not in VALID_MEASURE_STATUS:
        rpt.err(ctx, f"Invalid status '{data.get('status')}'")
    else:
        rpt.ok(f"status = '{data.get('status')}'")

    url = data.get("url", "")
    if not url.startswith(f"{FHIR_BASE}/Measure/"):
        rpt.err(ctx, f"url invalid: '{url}'")
    else:
        rpt.ok(f"url canonical: {url}")

    if not data.get("meta", {}).get("profile"):
        rpt.warn(ctx, "meta.profile missing")
    else:
        rpt.ok("meta.profile present")

    if not data.get("identifier"):
        rpt.warn(ctx, "identifier missing")
    else:
        rpt.ok("identifier present")

    scoring  = data.get("scoring", {})
    codings  = scoring.get("coding", [])
    if not codings:
        rpt.err(ctx, "scoring.coding is empty")
        scoring_code = None
    else:
        c = codings[0]
        if c.get("system") != MEASURE_SCORING_SYS:
            rpt.err(ctx, f"scoring system invalid: '{c.get('system')}'")
        else:
            rpt.ok(f"scoring.system = '{MEASURE_SCORING_SYS}'")
        scoring_code = c.get("code")
        if scoring_code not in ("ratio", "cohort"):
            rpt.err(ctx, f"scoring code must be 'ratio' or 'cohort', got '{scoring_code}'")
        else:
            rpt.ok(f"scoring.code = '{scoring_code}'")

    groups = data.get("group", [])
    if not groups:
        rpt.err(ctx, "group array empty")
    else:
        rpt.ok(f"group present ({len(groups)} group(s))")
        pops = groups[0].get("population", [])
        if not pops:
            rpt.err(ctx, "group.population empty")
        elif scoring_code == "ratio":
            if len(pops) != 2:
                rpt.err(ctx, f"ratio measure must have 2 populations, got {len(pops)}")
            else:
                rpt.ok("group.population count = 2 (ratio: numerator + denominator)")
                exp_codes = ["numerator", "denominator"]
                for i, exp_code in enumerate(exp_codes):
                    c = pops[i].get("code", {}).get("coding", [{}])[0]
                    if c.get("code") != exp_code:
                        rpt.err(ctx, f"population[{i}] code must be '{exp_code}', got '{c.get('code')}'")
                    else:
                        rpt.ok(f"population[{i}].code = '{exp_code}'")
                    if "criteria" not in pops[i]:
                        rpt.err(ctx, f"population[{i}].criteria missing")
                    else:
                        rpt.ok(f"population[{i}].criteria present")
        else:
            rpt.ok(f"group.population present ({len(pops)} entry)")
            code = pops[0].get("code", {}).get("coding", [{}])[0]
            if code.get("code") != "initial-population":
                rpt.err(ctx, f"population code must be 'initial-population', got '{code.get('code')}'")
            else:
                rpt.ok("population code = 'initial-population'")
            if "criteria" not in pops[0]:
                rpt.err(ctx, "group.population[0].criteria missing")
            else:
                rpt.ok("criteria present")

    for field in ["publisher", "description", "title"]:
        if not data.get(field):
            rpt.warn(ctx, f"'{field}' missing (recommended)")
        else:
            rpt.ok(f"'{field}' present")


# ── MeasureReport validation ──────────────────────────────────────────────────
def validate_measure_report(data, ctx, rpt, csv_row=None, ind_id=None,
                             standalone=True, detailed=False):
    if detailed:
        rpt.section(f"MeasureReport: {data.get('id', ctx)}")

    def _ok(msg=""): rpt.ok(msg if detailed else "")
    def _err(m):     rpt.err(ctx, m)
    def _warn(m):    rpt.warn(ctx, m)

    for field in ["resourceType", "id", "status", "type", "measure", "period"]:
        if field not in data:
            _err(f"Missing required field: '{field}'")
        else:
            _ok(f"Required field '{field}' present")

    if data.get("resourceType") != "MeasureReport":
        _err(f"resourceType must be 'MeasureReport'")
    else:
        _ok("resourceType = 'MeasureReport'")

    if data.get("status") not in VALID_STATUS:
        _err(f"Invalid status '{data.get('status')}'")
    else:
        _ok(f"status = '{data.get('status')}'")

    if data.get("type") not in VALID_TYPE:
        _err(f"Invalid type '{data.get('type')}'")
    else:
        _ok(f"type = '{data.get('type')}'")

    measure = data.get("measure", "")
    if not measure.startswith(f"{FHIR_BASE}/Measure/"):
        _err(f"measure URL invalid: '{measure}'")
    else:
        _ok(f"measure canonical URL valid")

    if not data.get("meta", {}).get("profile"):
        _warn("meta.profile missing")
    else:
        _ok("meta.profile present")

    period = data.get("period", {})
    for p in ["start", "end"]:
        if p not in period:
            _err(f"period.{p} missing")
        elif not check_date(period[p]):
            _err(f"period.{p} invalid: '{period[p]}'")
        else:
            _ok(f"period.{p} = '{period[p]}'")

    if "start" in period and "end" in period:
        try:
            s = datetime.strptime(period["start"][:10], "%Y-%m-%d")
            e = datetime.strptime(period["end"][:10],   "%Y-%m-%d")
            if s >= e:
                _err("period.start must be before period.end")
            else:
                _ok("period start < end")
        except ValueError:
            pass

    ext_urls = [ex.get("url", "") for ex in period.get("extension", [])]
    if f"{FHIR_BASE}/StructureDefinition/nepali-fiscal-period" not in ext_urls:
        _warn("period missing nepali-fiscal-period extension")
    else:
        _ok("nepali-fiscal-period extension present")

    if "date" not in data:
        _warn("date field missing")
    elif not check_date(data["date"]):
        _err(f"date invalid: '{data['date']}'")
    else:
        _ok(f"date = '{data['date']}'")

    for ref_field in ["subject", "reporter"]:
        ref = data.get(ref_field, {})
        if "reference" not in ref:
            _warn(f"{ref_field}.reference missing")
        else:
            r = ref["reference"]
            if standalone:
                if not r.startswith("#"):
                    _warn(f"{ref_field}.reference should be '#...' in standalone")
                else:
                    _ok(f"{ref_field}.reference = '{r}' (local contained)")
            else:
                if not r.startswith("http"):
                    _err(f"{ref_field}.reference must be absolute URL in bundle")
                else:
                    _ok(f"{ref_field}.reference absolute URL valid")

    if standalone:
        contained = data.get("contained", [])
        if len(contained) != 3:
            _err(f"standalone must have 3 contained, has {len(contained)}")
        else:
            _ok("contained has 3 resources")
            types = [c.get("resourceType") for c in contained]
            for rt in ["Organization", "Location"]:
                if rt not in types:
                    _err(f"contained missing '{rt}'")
                else:
                    _ok(f"contained has '{rt}'")

    groups = data.get("group", [])
    if not groups:
        _err("group array empty")
    else:
        _ok(f"group present ({len(groups)} group(s))")
        g = groups[0]
        if "id" not in g:
            _warn("group.id missing")
        else:
            _ok(f"group.id = '{g['id']}'")

        # Auto-detect ratio vs cohort from measure URL when ind_id not supplied
        if ind_id:
            is_ratio = ind_id in RATIO_IDS
        else:
            measure_url = data.get("measure", "")
            ind_part    = measure_url.split("nepal-tb-")[-1] if "nepal-tb-" in measure_url else ""
            is_ratio    = ind_part in RATIO_IDS
        pops = g.get("population", [])

        if is_ratio:
            if len(pops) != 2:
                _err(f"ratio must have exactly 2 populations, has {len(pops)}")
            else:
                _ok("population count = 2 (ratio: numerator + denominator)")
                for i, exp_code in enumerate(["numerator", "denominator"]):
                    pop    = pops[i]
                    coding = pop.get("code", {}).get("coding", [{}])[0]
                    if coding.get("system") != POP_CODE_SYS:
                        _err(f"population[{i}] system invalid")
                    else:
                        _ok(f"population[{i}].code.system valid")
                    if coding.get("code") != exp_code:
                        _err(f"population[{i}] code must be '{exp_code}', got '{coding.get('code')}'")
                    else:
                        _ok(f"population[{i}].code = '{exp_code}'")
                    has_count = "count" in pop
                    has_ext   = "_count" in pop
                    if not has_count and not has_ext:
                        _err(f"population[{i}] must have 'count' or '_count'")
                    elif has_ext:
                        dar_urls = [e.get("url") for e in pop["_count"].get("extension", [])]
                        if DAR_URL not in dar_urls:
                            _err(f"population[{i}]._count missing data-absent-reason")
                        else:
                            _ok(f"population[{i}]._count has data-absent-reason")
                    else:
                        if not isinstance(pop["count"], int) or pop["count"] < 0:
                            _err(f"population[{i}].count invalid: {pop.get('count')}")
                        else:
                            _ok(f"population[{i}].count = {pop['count']}")
        else:
            if len(pops) != 1:
                _err(f"cohort must have exactly 1 population, has {len(pops)}")
            else:
                _ok("population count = 1 (cohort)")
                pop    = pops[0]
                coding = pop.get("code", {}).get("coding", [{}])[0]
                if coding.get("system") != POP_CODE_SYS:
                    _err("population system invalid")
                else:
                    _ok("population.code.system valid")
                if coding.get("code") != "initial-population":
                    _err(f"population code must be 'initial-population'")
                else:
                    _ok("population.code = 'initial-population'")
                has_count = "count" in pop
                has_ext   = "_count" in pop
                if not has_count and not has_ext:
                    _err("population must have 'count' or '_count'")
                elif has_ext:
                    dar_urls = [e.get("url") for e in pop["_count"].get("extension", [])]
                    if DAR_URL not in dar_urls:
                        _err("_count missing data-absent-reason extension")
                    else:
                        _ok("_count has data-absent-reason (not-reported)")
                else:
                    if not isinstance(pop["count"], int):
                        _err(f"count must be integer, got {type(pop['count']).__name__}")
                    elif pop["count"] < 0:
                        _err(f"count is negative: {pop['count']}")
                    else:
                        _ok(f"count = {pop['count']} (non-negative integer)")

        ms = g.get("measureScore")
        if ms is None:
            _err("measureScore missing")
        else:
            has_val  = "value" in ms
            has_vext = "_value" in ms
            if not has_val and not has_vext:
                _err("measureScore must have 'value' or '_value'")
            elif has_vext:
                dar_urls = [e.get("url") for e in ms["_value"].get("extension", [])]
                if DAR_URL not in dar_urls:
                    _err("measureScore._value missing data-absent-reason")
                else:
                    _ok("measureScore._value has data-absent-reason (not-reported)")
            else:
                if not isinstance(ms["value"], (int, float)):
                    _err("measureScore.value must be numeric")
                elif ms["value"] < 0:
                    _err(f"measureScore.value negative: {ms['value']}")
                else:
                    _ok(f"measureScore.value = {ms['value']}")
                if ms.get("system") != UCUM_SYS:
                    _err(f"measureScore.system must be '{UCUM_SYS}'")
                else:
                    _ok("measureScore.system = UCUM")
                if not ms.get("code"):
                    _err("measureScore.code missing")
                else:
                    _ok(f"measureScore.code = '{ms.get('code')}'")

    # CSV cross-validation
    if csv_row and ind_id:
        yr      = csv_row["bs_year"]
        mo      = csv_row["bs_month"].strip()
        col     = IND_COLS[ind_id]
        raw     = csv_row.get(col, "").strip()
        # UNDER_REPORTED only affects ratio (monthly notification) indicators
        no_data = raw == "" or (ind_id in RATIO_IDS and (yr, mo) in UNDER_REPORTED)

        g    = (data.get("group") or [{}])[0]
        pops = g.get("population", [])

        if ind_id in RATIO_IDS:
            # Cross-check numerator (TB count)
            if len(pops) >= 1:
                numer = pops[0]
                act_dar   = "_count" in numer
                act_count = numer.get("count") if not act_dar else None
                if no_data:
                    if not act_dar:
                        _err(f"CSV cross-check: expected numerator DAR for {yr} {mo} [{col}], got count={act_count}")
                    else:
                        _ok(f"CSV cross-check: numerator DAR correct for {yr} {mo} [{col}]")
                else:
                    exp = int(float(raw))
                    if act_count != exp:
                        _err(f"CSV cross-check: [{col}] CSV={exp}, file={act_count}")
                    else:
                        _ok(f"CSV cross-check: [{col}] numerator={act_count} matches CSV")
            # Cross-check denominator (district population)
            if len(pops) >= 2:
                denom     = pops[1]
                den_count = denom.get("count")
                exp_den   = int(float(csv_row.get(DENOMINATOR_COL, "0").strip()))
                if den_count != exp_den:
                    _err(f"CSV cross-check: denominator CSV={exp_den}, file={den_count}")
                else:
                    _ok(f"CSV cross-check: denominator={den_count} matches CBS population")
        else:
            if pops:
                pop       = pops[0]
                act_count = pop.get("count") if "_count" not in pop else None
                act_dar   = "_count" in pop
                if no_data:
                    if not act_dar:
                        _err(f"CSV cross-check: expected DAR for {yr} {mo} [{col}], got count={act_count}")
                    else:
                        _ok(f"CSV cross-check: DAR correct for {yr} {mo} [{col}]")
                else:
                    exp_count = int(float(raw))
                    if act_count != exp_count:
                        _err(f"CSV cross-check: [{col}] CSV={exp_count}, file={act_count}")
                    else:
                        _ok(f"CSV cross-check: [{col}] count={act_count} matches CSV")


# ── Bundle validations ────────────────────────────────────────────────────────
def validate_mr_bundle(path, rpt, is_master=False):
    ctx  = os.path.basename(path)
    data = json.load(open(path))

    if data.get("resourceType") != "Bundle":
        rpt.err(ctx, "resourceType must be 'Bundle'"); return
    else:
        rpt.ok(f"resourceType = 'Bundle'")

    if data.get("type") != "collection":
        rpt.err(ctx, f"Bundle type must be 'collection'")
    else:
        rpt.ok("type = 'collection'")

    if "total" in data:
        rpt.err(ctx, "'total' not allowed in collection bundles")
    else:
        rpt.ok("'total' absent (correct for collection)")

    if not data.get("meta", {}).get("profile"):
        rpt.warn(ctx, "meta.profile missing")
    else:
        rpt.ok("meta.profile present")

    if not data.get("timestamp"):
        rpt.warn(ctx, "timestamp missing")
    else:
        rpt.ok(f"timestamp = '{data['timestamp']}'")

    entries          = data.get("entry", [])
    expected_reports = 780 if is_master else 60
    expected_total   = 3 + expected_reports

    if len(entries) != expected_total:
        rpt.err(ctx, f"Expected {expected_total} entries, got {len(entries)}")
    else:
        rpt.ok(f"entry count = {len(entries)} (3 shared + {expected_reports} MeasureReports)")

    expected_shared = [
        ("Organization", f"{FHIR_BASE}/Organization/org-mohp"),
        ("Organization", f"{FHIR_BASE}/Organization/org-ntp"),
        ("Location",     f"{FHIR_BASE}/Location/loc-kathmandu"),
    ]
    for i, (exp_rt, exp_url) in enumerate(expected_shared):
        e = entries[i] if i < len(entries) else {}
        if e.get("fullUrl") != exp_url:
            rpt.err(ctx, f"entry[{i}].fullUrl expected '{exp_url}'")
        else:
            rpt.ok(f"entry[{i}] shared resource fullUrl correct ({exp_rt})")
        if e.get("resource", {}).get("resourceType") != exp_rt:
            rpt.err(ctx, f"entry[{i}] resourceType expected '{exp_rt}'")
        else:
            rpt.ok(f"entry[{i}] resourceType = '{exp_rt}'")

    seen_ids = set()
    for e in entries[3:]:
        fu  = e.get("fullUrl", "")
        r   = e.get("resource", {})
        rid = r.get("id", "?")

        if not fu.startswith(f"{FHIR_BASE}/MeasureReport/"):
            rpt.err(ctx, f"{rid}: fullUrl invalid")
        else:
            rpt.ok()

        if "contained" in r:
            rpt.err(ctx, f"{rid}: must not have 'contained' in bundle")
        else:
            rpt.ok()

        if r.get("subject", {}).get("reference", "").startswith("#"):
            rpt.err(ctx, f"{rid}: subject.reference must be absolute URL")
        else:
            rpt.ok()

        if rid in seen_ids:
            rpt.err(ctx, f"Duplicate id: {rid}")
        else:
            seen_ids.add(rid)
            rpt.ok()

        validate_measure_report(r, f"{ctx}/{rid}", rpt, standalone=False)


def validate_measures_bundle(path, rpt):
    ctx  = os.path.basename(path)
    data = json.load(open(path))

    if data.get("resourceType") != "Bundle":
        rpt.err(ctx, "resourceType must be 'Bundle'"); return
    else:
        rpt.ok("resourceType = 'Bundle'")

    if data.get("type") != "collection":
        rpt.err(ctx, "Bundle type must be 'collection'")
    else:
        rpt.ok("type = 'collection'")

    if "total" in data:
        rpt.err(ctx, "'total' not allowed in collection bundles")
    else:
        rpt.ok("'total' absent (correct)")

    entries = data.get("entry", [])
    if len(entries) != 13:
        rpt.err(ctx, f"Expected 13 entries, got {len(entries)}")
    else:
        rpt.ok(f"entry count = 13")

    seen_ids = set()
    for e in entries:
        fu  = e.get("fullUrl", "")
        r   = e.get("resource", {})
        rid = r.get("id", "?")

        if not fu.startswith(f"{FHIR_BASE}/Measure/"):
            rpt.err(ctx, f"{rid}: fullUrl invalid")
        else:
            rpt.ok(f"{rid}: fullUrl valid")

        if rid in seen_ids:
            rpt.err(ctx, f"Duplicate Measure id: {rid}")
        else:
            seen_ids.add(rid)
            rpt.ok(f"{rid}: id unique")

        validate_measure(r, f"{ctx}/{rid}", rpt)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    rpt = Report()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    with open(CSV_PATH) as f:
        csv_rows = list(csv.DictReader(f))

    lines = []
    def h(text=""):  lines.append(text)
    def sep(c="="):  lines.append(c * 70)

    sep()
    h("  FHIR R4 INTERNAL VALIDATION REPORT")
    h(f"  Generated  : {now}")
    h(f"  Project    : TB Performance Dashboard — Kathmandu, Nepal")
    h(f"  FHIR Ver   : R4 (4.0.1)")
    h(f"  Validator  : scripts/05_fhir_measure/10_internal_validate.py")
    sep()

    # ── SECTION 1: Measure files ──────────────────────────────────────────────
    h()
    sep()
    h("SECTION 1 — MEASURE DEFINITION FILES")
    sep()
    measure_files = sorted([
        f for f in os.listdir(MEASURES_DIR)
        if f.endswith(".json") and "bundle" not in f
    ])
    h(f"  Directory  : fhir/measures/measures/")
    h(f"  Files found: {len(measure_files)}  (expected: 13)")
    h()

    if len(measure_files) != 13:
        rpt.err("measures", f"Expected 13 files, found {len(measure_files)}")
    else:
        rpt.ok("13 Measure files found")

    for fname in measure_files:
        path = os.path.join(MEASURES_DIR, fname)
        data = json.load(open(path))
        rpt.section(f"FILE: {fname}")
        validate_measure(data, fname, rpt)

    for line in rpt.log:
        h(line)
    rpt.log.clear()

    # ── SECTION 2: Measures bundle ────────────────────────────────────────────
    h()
    sep()
    h("SECTION 2 — MEASURES BUNDLE (bundle-all-measures.json)")
    sep()
    h(f"  File: fhir/measure_reports/bundles/bundle-all-measures.json")
    h()

    mb_path = os.path.join(BUNDLES, "bundle-all-measures.json")
    if not os.path.exists(mb_path):
        rpt.err("bundles", "bundle-all-measures.json not found")
    else:
        rpt.section("FILE: bundle-all-measures.json")
        validate_measures_bundle(mb_path, rpt)

    for line in rpt.log:
        h(line)
    rpt.log.clear()

    # ── SECTION 3: Individual MeasureReport files ─────────────────────────────
    h()
    sep()
    h("SECTION 3 — INDIVIDUAL MEASUREREPORT FILES (standalone, with contained)")
    sep()
    h(f"  Directory  : fhir/measure_reports/by_indicator/{{indicator}}/")
    h(f"  Indicators : {len(INDICATORS)}")
    h(f"  Files each : 60  (BS 2078 Shrawan – 2082 Asar)")
    h(f"  Total      : {len(INDICATORS) * 60}")
    h()

    total_files = 0
    dar_count   = 0

    ind_summary = []
    for ind_id, csv_col in INDICATORS:
        ind_dir = os.path.join(BY_IND, ind_id)
        if not os.path.exists(ind_dir):
            rpt.err(ind_id, f"Directory missing"); continue

        files = sorted(os.listdir(ind_dir))
        if len(files) != 60:
            rpt.err(ind_id, f"Expected 60 files, found {len(files)}")
        else:
            rpt.ok(f"[{ind_id}] 60 files found")

        ind_errors = 0
        ind_dar    = 0
        h(f"  Indicator: {ind_id}  (csv col: {csv_col})")
        h(f"  {'File':<50} {'Count / DAR':<20} {'Status'}")
        h("  " + "-" * 68)

        for fname in files:
            path    = os.path.join(ind_dir, fname)
            data    = json.load(open(path))
            ctx     = f"{ind_id}/{fname}"
            m       = re.match(r"tb-.+-kathmandu-(\d+)-(.+)\.json", fname)
            if not m:
                rpt.err(ctx, "filename pattern mismatch"); continue

            yr, mo_lc = m.groups()
            csv_row = next(
                (r for r in csv_rows
                 if r["bs_year"] == yr and r["bs_month"].strip().lower() == mo_lc),
                None
            )

            before_err = len(rpt.errors)
            validate_measure_report(data, ctx, rpt,
                                    csv_row=csv_row, ind_id=ind_id, standalone=True)
            new_errs = len(rpt.errors) - before_err

            grp  = (data.get("group") or [{}])[0]
            pops = grp.get("population", [])
            if not pops:
                count_str = "no population"
            elif ind_id in RATIO_IDS:
                numer = pops[0]
                if "_count" in numer:
                    count_str = "DAR / pop"
                    ind_dar  += 1
                    dar_count += 1
                else:
                    den = pops[1].get("count", "?") if len(pops) > 1 else "?"
                    count_str = f"{numer.get('count','?')}/{den}"
            else:
                pop = pops[0]
                if "_count" in pop:
                    count_str = "DAR (not-reported)"
                    ind_dar  += 1
                    dar_count += 1
                else:
                    count_str = str(pop.get("count", "?"))

            status = "PASS" if new_errs == 0 else f"FAIL ({new_errs} errors)"
            if new_errs > 0:
                ind_errors += 1
            h(f"  {fname:<50} {count_str:<20} {status}")
            total_files += 1

        dar_label = f"{ind_dar} DAR file(s)" if ind_dar else "none"
        ind_summary.append((ind_id, len(files), ind_errors, ind_dar))
        h(f"  → Subtotal: {len(files)} files, {ind_errors} errors, DAR entries: {dar_label}")
        h()

    # Per-indicator summary table
    h()
    sep("-")
    h("  INDICATOR SUMMARY")
    sep("-")
    h(f"  {'Indicator':<30} {'Files':>6} {'Errors':>7} {'DAR':>5}")
    h("  " + "-" * 52)
    for ind_id, n, errs, dar in ind_summary:
        h(f"  {ind_id:<30} {n:>6} {errs:>7} {dar:>5}")
    h("  " + "-" * 52)
    h(f"  {'TOTAL':<30} {total_files:>6} {sum(e for _,_,e,_ in ind_summary):>7} {dar_count:>5}")
    h()

    # ── SECTION 4: MeasureReport bundles ─────────────────────────────────────
    h()
    sep()
    h("SECTION 4 — MEASUREREPORT BUNDLES")
    sep()
    h(f"  Directory: fhir/measure_reports/bundles/")
    h()

    # Master bundle
    master_path = os.path.join(BUNDLES, "bundle-all.json")
    h("  bundle-all.json  (master — 3 shared + 780 MeasureReports = 783 entries)")
    h("  " + "-" * 66)
    rpt.section("FILE: bundle-all.json")
    validate_mr_bundle(master_path, rpt, is_master=True)
    for line in rpt.log:
        h(line)
    rpt.log.clear()
    h()

    # Per-indicator bundles
    h("  Per-indicator bundles  (3 shared + 60 MeasureReports = 63 entries each)")
    h("  " + "-" * 66)
    h(f"  {'Bundle file':<42} {'Entries':>8} {'Status'}")
    h("  " + "-" * 58)
    for ind_id in IND_IDS:
        bpath = os.path.join(BUNDLES, f"bundle-{ind_id}.json")
        if not os.path.exists(bpath):
            rpt.err("bundles", f"bundle-{ind_id}.json not found")
            h(f"  bundle-{ind_id}.json  — NOT FOUND")
        else:
            before_err = len(rpt.errors)
            validate_mr_bundle(bpath, rpt, is_master=False)
            new_errs = len(rpt.errors) - before_err
            data     = json.load(open(bpath))
            n        = len(data.get("entry", []))
            status   = "PASS" if new_errs == 0 else f"FAIL ({new_errs} errors)"
            h(f"  bundle-{ind_id+'.json':<35} {n:>8}   {status}")
    h()

    # ── SUMMARY ──────────────────────────────────────────────────────────────
    h()
    sep()
    h("VALIDATION SUMMARY")
    sep()
    h(f"  Resources validated")
    h(f"    Measure definition files  : 13")
    h(f"    Measure bundles           : 1  (bundle-all-measures.json)")
    h(f"    MeasureReport files       : {total_files}")
    h(f"    MeasureReport bundles     : 14  (1 master + 13 per-indicator)")
    h()
    h(f"  Results")
    h(f"    Checks passed  : {rpt.passed}")
    h(f"    Errors         : {len(rpt.errors)}")
    h(f"    Warnings       : {len(rpt.warnings)}")
    h(f"    DAR entries    : {dar_count}  (data-absent-reason, not-reported)")
    h()

    if rpt.errors:
        h("  ERRORS:")
        for e in rpt.errors:
            h(e)
        h()

    if rpt.warnings:
        h("  WARNINGS:")
        for w in rpt.warnings:
            h(w)
        h()

    if not rpt.errors:
        h("  RESULT: ALL CHECKS PASSED")
        h("  STATUS: Ready for external HAPI FHIR R4 validation")
    else:
        h("  RESULT: VALIDATION FAILED — fix errors before external submission")

    sep()

    report_text = "\n".join(lines)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(report_text)
    print(f"\nSaved → {REPORT_PATH}")


if __name__ == "__main__":
    main()
