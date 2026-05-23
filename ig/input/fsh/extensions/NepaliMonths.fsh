// ─────────────────────────────────────────────────────────────────────────────
// CodeSystem and ValueSet for Bikram Sambat (BS) calendar months.
//
// Used as the allowed value set for the bs-month sub-extension of
// NepaliCalendarPeriod. Values are strings in the MeasureReport resources
// (valueString), so this CodeSystem serves as a reference / documentation
// resource rather than a binding target.
// ─────────────────────────────────────────────────────────────────────────────

CodeSystem: BSMonthCS
Id:          bs-month-codes
Title:       "Bikram Sambat Month Codes"
Description: """
Code system for the 12 months of the Bikram Sambat (BS) calendar used in Nepal.
Months are listed in calendar order (Baishak = month 1).
Nepal's fiscal year starts from Shrawan (month 4).
"""

* ^url           = "https://iihms.gov.np/fhir/CodeSystem/bs-month-codes"
* ^status        = #active
* ^content       = #complete
* ^caseSensitive = true
* ^count         = 12

// Calendar order (month 1 → 12)
* #Baishak  "Baishak"  "1st BS month (~mid-April to mid-May, Gregorian month 4)"
* #Jestha   "Jestha"   "2nd BS month (~mid-May to mid-June, Gregorian month 5)"
* #Asar     "Asar"     "3rd BS month (~mid-June to mid-July, Gregorian month 6)"
* #Shrawan  "Shrawan"  "4th BS month (~mid-July to mid-August, Gregorian month 7). Starts Nepali fiscal year."
* #Bhadra   "Bhadra"   "5th BS month (~mid-August to mid-September, Gregorian month 8)"
* #Ashwin   "Ashwin"   "6th BS month (~mid-September to mid-October, Gregorian month 9)"
* #Kartik   "Kartik"   "7th BS month (~mid-October to mid-November, Gregorian month 10)"
* #Mangsir  "Mangsir"  "8th BS month (~mid-November to mid-December, Gregorian month 11)"
* #Poush    "Poush"    "9th BS month (~mid-December to mid-January, Gregorian month 12)"
* #Magh     "Magh"     "10th BS month (~mid-January to mid-February, Gregorian month 1)"
* #Falgun   "Falgun"   "11th BS month (~mid-February to mid-March, Gregorian month 2)"
* #Chaitra  "Chaitra"  "12th BS month (~mid-March to mid-April, Gregorian month 3)"


// ─────────────────────────────────────────────────────────────────────────────

ValueSet: BSMonthVS
Id:          bs-month-valueset
Title:       "Bikram Sambat Month Value Set"
Description: """
All 12 months of the Bikram Sambat calendar.
Used as reference documentation for the bs-month sub-extension in
NepaliCalendarPeriod. MeasureReport.period extension instances store
the month as a string matching one of these codes.
"""

* ^url    = "https://iihms.gov.np/fhir/ValueSet/bs-month-valueset"
* ^status = #active
* include codes from system BSMonthCS
