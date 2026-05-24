import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response

app = FastAPI(
    title="TB FHIR R4 Reference Server",
    description="FHIR R4 reference API — Kathmandu TB indicators BS 2078–2082",
    version="2.0.0",
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

FHIR_CONTENT_TYPE = "application/fhir+json; charset=utf-8"

VALID_INDICATORS = {
    "new-cases-total", "new-cases-female", "new-cases-male",
    "relapse-total", "relapse-female", "relapse-male",
    "total-tb-notified", "pbc-reg", "cured", "failed", "died", "ltfu", "not-eval",
}


def fhir_response(data: dict) -> Response:
    return Response(content=json.dumps(data), media_type=FHIR_CONTENT_TYPE)


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Dashboard ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    return '<meta http-equiv="refresh" content="0; url=/dashboard">'

@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard():
    path = os.path.join(os.path.dirname(__file__), "dashboard.html")
    with open(path, encoding="utf-8") as f:
        return f.read()


# ── Measure endpoints ─────────────────────────────────────────────────────────

@app.get("/Measure", tags=["FHIR"])
def list_measures():
    """Return a FHIR Bundle containing all 13 Measure definitions."""
    path = os.path.join(MEASURES_DIR, "nepal-tb-measures-bundle.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Measures bundle not found")
    return fhir_response(load_json(path))


@app.get("/Measure/{measure_id}", tags=["FHIR"])
def get_measure(measure_id: str):
    """Retrieve a single FHIR Measure by its ID."""
    path = os.path.join(MEASURES_DIR, f"{measure_id}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Measure '{measure_id}' not found")
    return fhir_response(load_json(path))


# ── MeasureReport endpoints ───────────────────────────────────────────────────

@app.get("/MeasureReport", tags=["FHIR"])
def list_measure_reports():
    """Return master FHIR Bundle — 3 shared resources + 780 MeasureReports (783 entries)."""
    path = os.path.join(BUNDLES_DIR, "bundle-all.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="MeasureReport bundle not found")
    return fhir_response(load_json(path))


@app.get("/MeasureReport/{report_id}", tags=["FHIR"])
def get_measure_report(report_id: str):
    """
    Retrieve a single FHIR MeasureReport by its ID.
    ID format: tb-{indicator-id}-kathmandu-{bs-year}-{bs-month}
    Example:   tb-cured-kathmandu-2080-shrawan
    """
    prefix        = "tb-"
    suffix_marker = "-kathmandu-"
    if report_id.startswith(prefix) and suffix_marker in report_id:
        after_prefix = report_id[len(prefix):]
        ind_end      = after_prefix.index(suffix_marker)
        indicator    = after_prefix[:ind_end]
        if indicator in VALID_INDICATORS:
            path = os.path.join(BY_INDICATOR_DIR, indicator, f"{report_id}.json")
            if os.path.exists(path):
                return fhir_response(load_json(path))

    # Fallback: scan all indicator folders
    for ind_folder in os.listdir(BY_INDICATOR_DIR):
        path = os.path.join(BY_INDICATOR_DIR, ind_folder, f"{report_id}.json")
        if os.path.exists(path):
            return fhir_response(load_json(path))

    raise HTTPException(status_code=404, detail=f"MeasureReport '{report_id}' not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fhir_server:app", host="127.0.0.1", port=8000, reload=True)
