// ─────────────────────────────────────────────────────────────────────────────
// Profile: TBMeasure
//
// Profile on the FHIR R4 Measure resource for Nepal NTP TB programme indicators.
// Covers all 13 indicators:
//   - 7 ratio   (monthly notification: new cases, relapse, total notified)
//   - 6 cohort  (annual treatment outcomes: pbc_reg, cured, failed, died, ltfu, not_eval)
//
// Canonical base: https://iihms.gov.np/fhir
// ─────────────────────────────────────────────────────────────────────────────

Profile:     TBMeasure
Parent:      Measure
Id:          tb-measure
Title:       "Nepal TB Measure"
Description: """
Profile on the FHIR R4 **Measure** resource for Nepal's National Tuberculosis
Programme (NTP) aggregate reporting. All 13 TB performance indicators defined
in this IG conform to this profile.

Two scoring types are used:

- **ratio** — for 7 monthly notification indicators (numerator = case count;
  denominator = CBS mid-year district population).
- **cohort** — for 6 annual treatment outcome indicators (initial-population =
  registered cohort pbc_reg).

All population criteria are expressed as plain-text descriptions referencing
the corresponding DHIS2/CSV column name.
"""

// ── Required metadata ─────────────────────────────────────────────────────────
* url         1..1 MS
* identifier  1..* MS
* identifier.use    1..1 MS
* identifier.system 1..1 MS
* identifier.value  1..1 MS
* version     1..1 MS
* name        1..1 MS
* title       1..1 MS
* status      1..1 MS
* date        1..1 MS
* publisher   1..1 MS
* description 1..1 MS

// ── Scoring — must be ratio or cohort ─────────────────────────────────────────
* scoring        1..1 MS
* scoring from   $MeasureScoring (required)

// ── Measure group — exactly one group per indicator ───────────────────────────
* group          1..* MS

// ── Population — at least one population entry per group ──────────────────────
* group.population          1..* MS
* group.population.code     1..1 MS
* group.population.code from $MeasurePopType (required)

// ── Criteria — plain-text CQL-lite description of the population source ───────
* group.population.criteria          1..1 MS
* group.population.criteria.language 1..1 MS
* group.population.criteria.language = #text/plain
