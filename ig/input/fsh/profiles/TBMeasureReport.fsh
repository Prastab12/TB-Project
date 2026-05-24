// ─────────────────────────────────────────────────────────────────────────────
// Profile: TBMeasureReport
//
// Profile on the FHIR R4 MeasureReport resource for Kathmandu District monthly
// TB aggregate reports.
//
// Each instance represents one indicator × one BS month × Kathmandu District.
// 780 instances total: 13 indicators × 60 months (BS 2078 Shrawan – 2082 Asar).
//
// Key design decisions:
//   - status fixed to #complete; type fixed to #summary.
//   - subject constrained to Location (Kathmandu District).
//   - reporter constrained to Organization (NTP).
//   - period carries the NepaliCalendarPeriod extension (BS year/month/FY).
//   - Ratio MeasureReports: 2 populations (numerator + denominator) + measureScore.
//   - Cohort MeasureReports: 1 population (initial-population); no measureScore.
//   - Under-reported months use Data Absent Reason on population._count
//     and measureScore._value (DAR applied in generation scripts, not constrained
//     here as a fixed invariant).
// ─────────────────────────────────────────────────────────────────────────────

Profile:     TBMeasureReport
Parent:      MeasureReport
Id:          tb-measure-report
Title:       "Nepal TB MeasureReport"
Description: """
Profile on the FHIR R4 **MeasureReport** resource for Nepal NTP monthly district-level
TB reporting. Each instance covers one TB indicator for one Bikram Sambat month in
Kathmandu District.

**Period encoding:** The `period` element carries both mandatory Gregorian ISO 8601
dates and a `NepaliCalendarPeriod` extension preserving the Bikram Sambat year,
month name, and Nepali fiscal year string.

**Scoring types:**
- Ratio indicators carry `numerator` and `denominator` populations plus a
  dimensionless `measureScore` (UCUM unit `1`).
- Cohort indicators carry a single `initial-population` and no `measureScore`.

**Data Absent Reason:** For under-reported months (BS 2078 Baishak, Jestha, Asar),
the `data-absent-reason` extension (`valueCode: not-reported`) replaces the
`count` and `measureScore.value` fields on affected ratio MeasureReports.
"""

// ── Fixed status and type ─────────────────────────────────────────────────────
* status 1..1 MS
* status = #complete

* type   1..1 MS
* type   = #summary

// ── Canonical reference to parent Measure ─────────────────────────────────────
* measure 1..1 MS

// ── Subject — Kathmandu District Location ─────────────────────────────────────
* subject        1..1 MS
* subject only   Reference(Location)

// ── Reporter date ─────────────────────────────────────────────────────────────
* date      1..1 MS

// ── Reporter — NTP Organization ───────────────────────────────────────────────
* reporter       1..1 MS
* reporter only  Reference(Organization)

// ── Period with Bikram Sambat calendar extension ───────────────────────────────
* period                    1..1 MS
* period.start              1..1 MS
* period.end                1..1 MS
* period.extension contains NepaliCalendarPeriod named nepali-period 0..1 MS

// ── Group — one group per MeasureReport ───────────────────────────────────────
* group                 1..* MS

// ── Population — code required; count present or replaced by DAR extension ────
* group.population      1..* MS
* group.population.code 1..1 MS
* group.population.code from $MeasurePopType (required)

// ── MeasureScore — present for ratio indicators; absent for cohort indicators ──
// When present, value is a dimensionless UCUM quantity (unit "1").
* group.measureScore              0..1 MS
* group.measureScore.system       0..1 MS
* group.measureScore.system = "http://unitsofmeasure.org"
* group.measureScore.code         0..1 MS
* group.measureScore.code   = #1
