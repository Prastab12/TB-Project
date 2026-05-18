import os
import json
import time
import requests

HAPI_BASE = "https://hapi.fhir.org/baseR4"
REPORT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "fhir/kathmandu_monthly_measure_report"
)

def put_resource(resource_type, resource_id, body_bytes):
    url = f"{HAPI_BASE}/{resource_type}/{resource_id}"
    resp = requests.put(url, data=body_bytes, headers={"Content-Type": "application/fhir+json"})
    if resp.status_code in (200, 201):
        return resp.status_code, None
    return resp.status_code, resp.text[:200]

def main():
    files = sorted(f for f in os.listdir(REPORT_DIR) if f.endswith(".json"))
    total = len(files)
    print(f"Uploading {total} MeasureReports to {HAPI_BASE} via PUT...")

    success, failed = 0, 0
    for i, fname in enumerate(files, 1):
        path = os.path.join(REPORT_DIR, fname)
        with open(path, "rb") as f:
            body = f.read()

        resource_id = json.loads(body)["id"]
        status, err = put_resource("MeasureReport", resource_id, body)

        if status in (200, 201):
            success += 1
        else:
            failed += 1
            print(f"  FAILED [{status}] {fname}: {err[:120] if err else ''}")

        if i % 50 == 0:
            print(f"  Progress: {i}/{total}  (success={success}, failed={failed})")
        time.sleep(0.1)

    print(f"\nDone. Success: {success} | Failed: {failed}")

if __name__ == "__main__":
    main()
