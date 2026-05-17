import json
import os
import glob
from datetime import datetime

def main():
    measures_dir = "fhir/measures"
    output_bundle_path = os.path.join(measures_dir, "nepal-tb-measures-bundle.json")
    
    # Read all individual json files in fhir/measures (except any existing bundle)
    json_files = glob.glob(os.path.join(measures_dir, "*.json"))
    json_files = [f for f in json_files if not f.endswith("nepal-tb-measures-bundle.json")]
    
    bundle_entries = []
    
    for file_path in sorted(json_files):
        with open(file_path, "r") as f:
            measure_resource = json.load(f)
            
        canonical_url = measure_resource.get("url")
        
        bundle_entries.append({
            "fullUrl": canonical_url,
            "resource": measure_resource
        })
        
    # Construct the FHIR Bundle
    bundle = {
        "resourceType": "Bundle",
        "id": "nepal-tb-measures-bundle",
        "identifier": {
            "use": "official",
            "system": "https://iihms.gov.np/fhir/NamingSystem/bundle-identifiers",
            "value": "nepal-tb-measures-bundle"
        },
        "type": "collection",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "entry": bundle_entries
    }
    
    with open(output_bundle_path, "w") as f:
        json.dump(bundle, f, indent=2)
        
    print(f"Successfully created FHIR Bundle with {len(bundle_entries)} entries at:")
    print(f"  → {output_bundle_path}")

if __name__ == "__main__":
    main()
