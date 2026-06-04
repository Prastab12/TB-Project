# TB Variables & Indicators

This IG defines **32 surveillance variables** — 26 monthly notification (ratio scoring)
and 6 annual treatment cohort (cohort scoring) — covering Kathmandu District,
BS 2078 Baishak through BS 2082 Chaitra (60 months, 1,920 MeasureReport instances total).

---

### Monthly Notification Variables — Ratio Scoring

Numerator = monthly TB case count from NTP reporting.  
Denominator = CBS mid-year district population (annual figure, constant across all 12 months of a BS year).  
MeasureScore = numerator ÷ denominator (dimensionless; multiply by 100,000 for rate per 100k population).

#### Summary Counts

| Measure ID | Title | CSV Column | DAR for gap months? |
|---|---|---|---|
| `nepal-tb-new-cases-total` | New TB Cases (Total) | `new_cases_total` | No — valid all 60 months |
| `nepal-tb-new-cases-female` | New TB Cases (Female) | `new_cases_female` | Yes |
| `nepal-tb-new-cases-male` | New TB Cases (Male) | `new_cases_male` | Yes |
| `nepal-tb-relapse-total` | TB Relapse Cases (Total) | `relapse_total` | Yes |
| `nepal-tb-relapse-female` | TB Relapse Cases (Female) | `relapse_female` | Yes |
| `nepal-tb-relapse-male` | TB Relapse Cases (Male) | `relapse_male` | Yes |
| `nepal-tb-total-tb-notified` | Total TB Cases Notified (M+F) | `total_tb_mf` | Yes |
| `nepal-tb-total-tb-female` | Total TB Cases Notified (Female) | `total_tb_female` | Yes |
| `nepal-tb-total-tb-male` | Total TB Cases Notified (Male) | `total_tb_male` | Yes |
| `nepal-tb-hiv-positive` | TB Patients with HIV Co-infection | `tb_hiv_positive` | No — valid all 60 months |

#### Age-Sex Band Counts (New Cases Only)

Each of the 16 age-sex band variables represents the monthly count of **new** TB cases
in that specific age group and sex. All 16 carry `data-absent-reason: not-reported`
for the three gap months (BS 2078 Baishak, Jestha, Asar).

| Measure ID | Age Group | Sex | CSV Column |
|---|---|---|---|
| `nepal-tb-age-0to4-f` | 0–4 | Female | `0_to_4_f` |
| `nepal-tb-age-0to4-m` | 0–4 | Male | `0_to_4_m` |
| `nepal-tb-age-5to14-f` | 5–14 | Female | `5_to_14_f` |
| `nepal-tb-age-5to14-m` | 5–14 | Male | `5_to_14_m` |
| `nepal-tb-age-15to24-f` | 15–24 | Female | `15_to_24_f` |
| `nepal-tb-age-15to24-m` | 15–24 | Male | `15_to_24_m` |
| `nepal-tb-age-25to34-f` | 25–34 | Female | `25_to_34_f` |
| `nepal-tb-age-25to34-m` | 25–34 | Male | `25_to_34_m` |
| `nepal-tb-age-35to44-f` | 35–44 | Female | `35_to_44_f` |
| `nepal-tb-age-35to44-m` | 35–44 | Male | `35_to_44_m` |
| `nepal-tb-age-45to54-f` | 45–54 | Female | `45_to_54_f` |
| `nepal-tb-age-45to54-m` | 45–54 | Male | `45_to_54_m` |
| `nepal-tb-age-55to64-f` | 55–64 | Female | `55_to_64_f` |
| `nepal-tb-age-55to64-m` | 55–64 | Male | `55_to_64_m` |
| `nepal-tb-age-65plus-f` | 65+ | Female | `65_f` |
| `nepal-tb-age-65plus-m` | 65+ | Male | `65_m` |

---

### Annual Treatment Cohort Variables — Cohort Scoring

Population = `initial-population` count from the annual NTP treatment cohort.
The same annual count is repeated for all 12 months of the BS fiscal year.
No measureScore is set for cohort variables.

| Measure ID | Title | CSV Column |
|---|---|---|
| `nepal-tb-pbc-reg` | PBC Registered Cohort | `pbc_reg` |
| `nepal-tb-cured` | TB Patients Cured | `cured` |
| `nepal-tb-failed` | TB Treatment Failures | `failed` |
| `nepal-tb-died` | TB Patients Died | `died` |
| `nepal-tb-ltfu` | TB Patients Lost to Follow-up | `ltfu` |
| `nepal-tb-not-eval` | TB Treatment Outcomes Not Evaluated | `not_eval` |

---

### Data Absent Reason

BS 2078 Baishak, Jestha, and Asar have no sex or age data in the DHIS2 source.
For these three months, **24 variables** carry `data-absent-reason: not-reported` —
a total of **72 affected MeasureReport instances**.

Variables **not** affected (valid for all 60 months):
`nepal-tb-new-cases-total`, `nepal-tb-hiv-positive`, and all 6 cohort variables.

**Pattern applied to affected ratio MeasureReports:**

```json
"population": [
  {
    "code": { "coding": [{ "code": "numerator" }] },
    "_count": {
      "extension": [{
        "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
        "valueCode": "not-reported"
      }]
    }
  },
  {
    "code": { "coding": [{ "code": "denominator" }] },
    "count": 2049618
  }
],
"measureScore": {
  "unit": "1", "system": "http://unitsofmeasure.org", "code": "1",
  "_value": {
    "extension": [{
      "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
      "valueCode": "not-reported"
    }]
  }
}
```

The denominator (CBS population) is always present; only the numerator and
measureScore are absent for gap months.
