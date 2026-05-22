import csv
import json
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TB FHIR R4 Reference Server",
    description="File-system FHIR R4 API — Kathmandu TB indicators BS 2078–2082",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR            = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
MEASURES_DIR        = os.path.join(BASE_DIR, "fhir/measures/measures")
MEASURE_REPORTS_DIR = os.path.join(BASE_DIR, "fhir/measure_reports")
BUNDLES_DIR         = os.path.join(MEASURE_REPORTS_DIR, "bundles")
BY_INDICATOR_DIR    = os.path.join(MEASURE_REPORTS_DIR, "by_indicator")
CSV_PATH            = os.path.join(BASE_DIR, "data/final/final_cleaned_data.csv")

FHIR_CONTENT_TYPE = "application/fhir+json; charset=utf-8"

VALID_INDICATORS = {
    "tsr-cure", "notification-rate", "mortality-rate", "ltfu-rate",
    "failure-rate", "not-eval-rate", "bacteriological-confirmation",
    "xpert-coverage", "hiv-coinfection", "art-coverage", "gender-ratio",
}


def fhir_response(data: dict) -> Response:
    """Return a FHIR-compliant JSON response with correct Content-Type."""
    return Response(
        content=json.dumps(data),
        media_type=FHIR_CONTENT_TYPE,
    )


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── UI ────────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def read_root():
    return '<meta http-equiv="refresh" content="0; url=/dashboard">'


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def serve_dashboard():
    html_path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


# ── CSV data (internal, used by dashboard) ────────────────────────────────────

@app.get("/api/csv-data", tags=["Internal"])
def get_csv_data():
    """Return all 60 Kathmandu monthly rows from the source CSV."""
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return JSONResponse(content=rows)


# ── FHIR Capability Statement ─────────────────────────────────────────────────

@app.get("/metadata", tags=["FHIR"])
def capability_statement():
    """FHIR R4 CapabilityStatement describing this server."""
    stmt = {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2026-05-21",
        "kind": "instance",
        "fhirVersion": "4.0.1",
        "format": ["application/fhir+json"],
        "implementationGuide": [],
        "rest": [{
            "mode": "server",
            "resource": [
                {
                    "type": "Measure",
                    "interaction": [
                        {"code": "read"},
                        {"code": "search-type"},
                    ],
                    "searchParam": [],
                },
                {
                    "type": "MeasureReport",
                    "interaction": [
                        {"code": "read"},
                        {"code": "search-type"},
                    ],
                    "searchParam": [
                        {"name": "indicator", "type": "token",
                         "documentation": "Filter by indicator ID (e.g. tsr-cure)"},
                    ],
                },
            ],
        }],
    }
    return fhir_response(stmt)


# ── Measure endpoints ─────────────────────────────────────────────────────────

@app.get("/Measure", tags=["FHIR"])
def list_measures():
    """Return the FHIR Bundle containing all 11 Measure definitions."""
    path = os.path.join(MEASURES_DIR, "nepal-tb-measures-bundle.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Measures bundle not found")
    return fhir_response(load_json(path))


@app.get("/Measure/{measure_id}", tags=["FHIR"])
def get_measure(measure_id: str):
    """Retrieve a specific FHIR Measure by its ID."""
    path = os.path.join(MEASURES_DIR, f"{measure_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Measure '{measure_id}' not found")
    return fhir_response(load_json(path))


# ── MeasureReport endpoints ───────────────────────────────────────────────────

@app.get("/MeasureReport", tags=["FHIR"])
def list_measure_reports(
    indicator: str = Query(
        default=None,
        description="Filter by indicator ID, e.g. 'tsr-cure'. "
                    "Returns the per-indicator bundle (63 entries). "
                    "Omit for full bundle (663 entries).",
    )
):
    """
    Return a FHIR R4 collection Bundle of MeasureReports.

    - No params → master bundle (3 shared resources + 660 MeasureReports)
    - `?indicator=tsr-cure` → indicator bundle (3 shared + 60 MeasureReports)
    """
    if indicator:
        if indicator not in VALID_INDICATORS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown indicator '{indicator}'. "
                       f"Valid values: {sorted(VALID_INDICATORS)}",
            )
        path = os.path.join(BUNDLES_DIR, f"bundle-{indicator}.json")
    else:
        path = os.path.join(BUNDLES_DIR, "bundle-all.json")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="MeasureReport bundle not found")
    return fhir_response(load_json(path))


@app.get("/MeasureReport/bundle/{indicator_id}", tags=["FHIR"])
def get_indicator_bundle(indicator_id: str):
    """
    Return the per-indicator bundle (63 entries: 3 shared + 60 MeasureReports).
    Equivalent to GET /MeasureReport?indicator={indicator_id}.
    """
    if indicator_id not in VALID_INDICATORS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown indicator '{indicator_id}'. "
                   f"Valid values: {sorted(VALID_INDICATORS)}",
        )
    path = os.path.join(BUNDLES_DIR, f"bundle-{indicator_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Bundle for '{indicator_id}' not found")
    return fhir_response(load_json(path))


@app.get("/MeasureReport/{report_id}", tags=["FHIR"])
def get_measure_report(report_id: str):
    """
    Retrieve a specific FHIR MeasureReport by its ID.
    ID format: tb-{indicator-id}-kathmandu-{bs-year}-{bs-month}
    Example:   tb-tsr-cure-kathmandu-2080-shrawan
    """
    # Extract indicator from ID directly — avoids scanning all folders
    # Pattern: tb-{indicator}-kathmandu-{year}-{month}
    prefix = "tb-"
    suffix_marker = "-kathmandu-"
    if report_id.startswith(prefix) and suffix_marker in report_id:
        after_prefix = report_id[len(prefix):]
        ind_end = after_prefix.index(suffix_marker)
        indicator = after_prefix[:ind_end]
        if indicator in VALID_INDICATORS:
            path = os.path.join(BY_INDICATOR_DIR, indicator, f"{report_id}.json")
            if os.path.exists(path):
                return fhir_response(load_json(path))

    # Fallback: scan all indicator folders (handles unexpected ID formats)
    for ind_folder in os.listdir(BY_INDICATOR_DIR):
        path = os.path.join(BY_INDICATOR_DIR, ind_folder, f"{report_id}.json")
        if os.path.exists(path):
            return fhir_response(load_json(path))

    raise HTTPException(status_code=404, detail=f"MeasureReport '{report_id}' not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fhir_server:app", host="127.0.0.1", port=8000, reload=True)
