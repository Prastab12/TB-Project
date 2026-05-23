// ─────────────────────────────────────────────────────────────────────────────
// Extension: NepaliCalendarPeriod
//
// Applied to MeasureReport.period (type: Period).
// Carries Bikram Sambat calendar metadata alongside mandatory Gregorian dates.
//
// Gregorian date convention used in this IG:
//   period.start = {g_year}-{g_month}-16
//   period.end   = {g_year'}-{g_month+1}-15
//
// Canonical URL (matches all existing MeasureReport resources):
//   https://iihms.gov.np/fhir/StructureDefinition/nepali-fiscal-period
// ─────────────────────────────────────────────────────────────────────────────

Extension: NepaliCalendarPeriod
Id:          nepali-fiscal-period
Title:       "Nepali Calendar Period"
Description: """
Extends a FHIR `Period` element with Bikram Sambat (BS) calendar information
used in Nepal's health information systems. The three nested extensions carry:

- **bs-year** — the BS year as an integer (e.g. 2080)
- **bs-month** — the BS month name as a string (e.g. Shrawan)
- **fiscal-year** — the Nepali fiscal year as a slash string (e.g. 2080/81)

Nepal's fiscal year runs from **Shrawan** (4th BS month, ~mid-July) through
**Asar** (3rd BS month of the following year). Months Shrawan–Chaitra belong
to FY {year}/{year+1 mod 100}; months Baishak–Asar belong to FY {year-1}/{year mod 100}.
"""

* ^context[+].type       = #element
* ^context[=].expression = "Period"

// ── Sub-extensions ────────────────────────────────────────────────────────────
* extension contains
    bs-year     1..1 MS and
    bs-month    1..1 MS and
    fiscal-year 1..1 MS

// ── bs-year ───────────────────────────────────────────────────────────────────
* extension[bs-year] ^short      = "Bikram Sambat year"
* extension[bs-year] ^definition = "The BS year in which this reporting period falls. Example: 2080 (corresponds to Gregorian ~2023/24)."
* extension[bs-year].value[x] only integer

// ── bs-month ──────────────────────────────────────────────────────────────────
* extension[bs-month] ^short      = "Bikram Sambat month name"
* extension[bs-month] ^definition = "The BS month name as a string. Allowed values (calendar order): Baishak | Jestha | Asar | Shrawan | Bhadra | Ashwin | Kartik | Mangsir | Poush | Magh | Falgun | Chaitra. See ValueSet https://iihms.gov.np/fhir/ValueSet/bs-month-valueset."
* extension[bs-month].value[x] only string

// ── fiscal-year ───────────────────────────────────────────────────────────────
* extension[fiscal-year] ^short      = "Nepali fiscal year"
* extension[fiscal-year] ^definition = "Nepali fiscal year as a slash-separated string. Format: {BS_year}/{2-digit_next_BS_year} — e.g. '2080/81'."
* extension[fiscal-year].value[x] only string
