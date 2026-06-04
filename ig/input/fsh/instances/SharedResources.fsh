// ─────────────────────────────────────────────────────────────────────────────
// Shared canonical instances referenced by all TBMeasureReport resources.
//
// These three resources appear as `contained` resources inside every generated
// MeasureReport JSON. Defining them here as standalone IG instances gives them
// proper canonical identities for external reference and IG documentation.
//
// Instances:
//   Organization/org-mohp      — Ministry of Health and Population, Nepal
//   Organization/org-ntp       — National Tuberculosis Programme (child of MoHP)
//   Location/loc-kathmandu     — Kathmandu District, Nepal
// ─────────────────────────────────────────────────────────────────────────────


// ── Organization: Ministry of Health and Population ───────────────────────────

Instance:    org-mohp
InstanceOf:  Organization
Usage:       #example
Title:       "Ministry of Health and Population, Nepal"
Description: "The Government of Nepal ministry responsible for national health policy, including TB programme oversight."

* id                     = "org-mohp"
* active                 = true
* name                   = "Ministry of Health and Population, Nepal"
* alias[+]               = "MoHP"
* identifier[+].system   = $NamingOrg
* identifier[=].value    = "org-mohp"


// ── Organization: National Tuberculosis Programme ─────────────────────────────

Instance:    org-ntp
InstanceOf:  Organization
Usage:       #example
Title:       "National Tuberculosis Programme"
Description: "Nepal's National Tuberculosis Programme (NTP), operating under the Ministry of Health and Population. The NTP is the reporter for all TB MeasureReport instances in this IG."

* id                     = "org-ntp"
* active                 = true
* name                   = "National Tuberculosis Programme"
* alias[+]               = "NTP"
* identifier[+].system   = $NamingOrg
* identifier[=].value    = "org-ntp"
* partOf                 = Reference(org-mohp)


// ── Location: Kathmandu District ──────────────────────────────────────────────

Instance:    loc-kathmandu
InstanceOf:  Location
Usage:       #example
Title:       "Kathmandu District, Nepal"
Description: "Kathmandu District, Bagmati Province, Nepal. The subject location for all 1,920 TBMeasureReport instances in this IG, covering BS 2078 Baishak through BS 2082 Chaitra (60 months × 32 variables)."

* id                     = "loc-kathmandu"
* status                  = #active
* name                   = "Kathmandu District, Nepal"
* identifier[+].system   = $NamingLoc
* identifier[=].value    = "loc-kathmandu"
* physicalType           = $LocPhysType#jdn "Jurisdiction"
