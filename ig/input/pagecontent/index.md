# Nepal NTP TB FHIR R4 Implementation Guide

**Version:** 1.0.0 &nbsp;|&nbsp; **Status:** STU1 &nbsp;|&nbsp; **FHIR Version:** R4 (4.0.1)

---

### Background

This Implementation Guide (IG) defines FHIR R4 profiles, extensions, and canonical
instances for the **National Tuberculosis Programme (NTP)** of Nepal. It is developed
as part of a Master's thesis on integrating DHIS2 aggregate data into a
standards-compliant FHIR ecosystem using the Bikram Sambat (BS) calendar.

### Scope

The IG covers **Kathmandu district** aggregate monthly TB reporting for BS years
**2078–2082**, including:

- Monthly **Case Notification Rate** — new and relapse TB cases per 100,000 population
- Annual **Treatment Outcome** indicators — Cured, Failed, Died, LTFU, Not Evaluated
- Custom extensions for the **Bikram Sambat (BS) calendar** and Nepali fiscal year

### Architecture

```
DHIS2 CSV export
      │
      ▼
Python ETL (pandas + fhir.resources)
      │
      ├──▶ FHIR Measure resources  (Measure definitions)
      └──▶ FHIR MeasureReport resources  (monthly data instances)
                    │
                    ▼
         FHIR R4 Reference API  (FastAPI)
                    │
                    ▼
         Analytical Dashboard  (Chart.js)
```

### Key Profiles

| Profile | Base Resource | Purpose |
|---|---|---|
| [TBMeasure](StructureDefinition-TBMeasure.html) | Measure | Defines a TB indicator with ratio or cohort scoring |
| [TBMeasureReport](StructureDefinition-TBMeasureReport.html) | MeasureReport | Stores one month of aggregate data for a district |

### Key Extension

| Extension | Purpose |
|---|---|
| [NepaliCalendarPeriod](StructureDefinition-NepaliCalendarPeriod.html) | Carries BS year, BS month, and Nepali fiscal year alongside the Gregorian `period` dates |

### Data Source

Data originates from the **DHIS2** system of the Ministry of Health and Population,
Nepal, exported as monthly aggregate CSV and transformed via a Python ETL pipeline.
Population denominators are drawn from CBS (Central Bureau of Statistics) mid-year
district estimates.

### Under-reported Months

BS 2078 Baishak, Jestha, and Asar are under-reported in the source data. MeasureReport
instances for these months carry a
`data-absent-reason` extension with code `not-reported` on the numerator population count.

### Contact

**Publisher:** Integrated Health Information Management System (IIHMS), Nepal
&nbsp; | &nbsp; <https://iihms.gov.np>
