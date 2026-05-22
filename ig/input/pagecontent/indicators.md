# TB Indicators

This IG defines 13 indicators — 7 monthly notification (ratio scoring) and
6 annual treatment cohort (cohort scoring).

---

### Monthly Notification Indicators — Ratio Scoring

Numerator = monthly TB case count from NTP reporting.
Denominator = CBS mid-year district population (annual, same for all 12 months of a BS year).
MeasureScore = numerator ÷ denominator (dimensionless ratio; multiply by 100,000 for rate per 100k).

| Measure ID | Title | Numerator column |
|---|---|---|
| `nepal-tb-new-cases-total` | New TB Cases (Total) | `new_cases_total` |
| `nepal-tb-new-cases-female` | New TB Cases (Female) | `new_cases_female` |
| `nepal-tb-new-cases-male` | New TB Cases (Male) | `new_cases_male` |
| `nepal-tb-relapse-total` | TB Relapse Cases (Total) | `relapse_total` |
| `nepal-tb-relapse-female` | TB Relapse Cases (Female) | `relapse_female` |
| `nepal-tb-relapse-male` | TB Relapse Cases (Male) | `relapse_male` |
| `nepal-tb-total-tb-notified` | Total TB Cases Notified | `total_tb_m+f` |

---

### Annual Treatment Cohort Indicators — Cohort Scoring

Population = `initial-population` count drawn from the annual NTP treatment cohort.
The same annual count is repeated for all 12 months of the BS fiscal year.

| Measure ID | Title | CSV column |
|---|---|---|
| `nepal-tb-pbc-reg` | PBC Registered Cohort | `pbc_reg` |
| `nepal-tb-cured` | TB Patients Cured | `cured` |
| `nepal-tb-failed` | TB Treatment Failures | `failed` |
| `nepal-tb-died` | TB Patients Died | `died` |
| `nepal-tb-ltfu` | TB Patients Lost to Follow-up | `ltfu` |
| `nepal-tb-not-eval` | TB Treatment Outcomes Not Evaluated | `not_eval` |

---

### Data Absent Reason

BS 2078 Baishak, Jestha, and Asar are under-reported in the DHIS2 source.
For these three months, all seven ratio-indicator MeasureReports carry:

```json
"population": [{
  "code": { "coding": [{ "code": "numerator" }] },
  "_count": {
    "extension": [{
      "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
      "valueCode": "not-reported"
    }]
  }
}]
```

The denominator (CBS population) is always present; only the numerator is absent.
