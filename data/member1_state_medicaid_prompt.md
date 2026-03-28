# Member 1: LLM Prompt for Building state_medicaid_contacts.json

## Reference Sources (for spot-checking LLM output)
- **Medicaid.gov state directory:** https://www.medicaid.gov/about-us/where-is-medicaid-administered/index.html
- **CMS state fair hearing info:** https://www.cms.gov/
- **Google verification queries:** Search "[state] Medicaid fair hearing" to confirm agency name and phone
- **Priority spot-check states:** PA, NY, CA, TX, FL, IL, OH, GA, NC, MI (check at least these 10)

---

## PROMPT (run once — generates all 50 states + DC)

```
Generate a JSON object containing Medicaid appeal contact information for all 50 US states plus the District of Columbia.

This data will be used to personalize Medicaid appeal letters with the correct state agency name, contact info, and mailing address. The legal citations in the appeal letter remain federal (42 CFR Part 431 Subpart E) — the state info is only for routing the appeal to the right place.

For each state, provide:
1. The full state name
2. The state Medicaid agency name (e.g., "Department of Health and Human Services", "Department of Social Services")
3. The appeal/fair hearing body name (e.g., "Bureau of Hearings and Appeals", "Office of Administrative Hearings")
4. The phone number for requesting a fair hearing (toll-free if available)
5. The online portal URL for filing an appeal or requesting a fair hearing (if one exists; otherwise null)
6. The mailing address for submitting a written fair hearing request
7. Any important state-specific notes (e.g., "Must appeal to MCO first before requesting state fair hearing", "Expedited hearings available for urgent medical situations")

Output as a JSON object where each key is the two-letter state abbreviation. Match this schema EXACTLY:

{
  "AL": {
    "state_name": "Alabama",
    "agency": "Alabama Medicaid Agency",
    "appeal_body": "Name of the fair hearing body",
    "phone": "1-800-XXX-XXXX",
    "online_portal": "https://... or null if none exists",
    "mailing_address": "Full mailing address for fair hearing requests",
    "notes": "Any state-specific appeal quirks or important info"
  },
  "AK": {
    ...
  },
  ...through all 50 states and DC (use "DC" as key for District of Columbia)
}

IMPORTANT GUIDELINES:
- Use the most current agency names and contact information you have
- For phone numbers, prefer the Medicaid member services or fair hearing request line, NOT the general state switchboard
- For online portals, only include URLs that specifically allow appeal/hearing requests — do NOT include general Medicaid homepages
- For mailing addresses, provide the address where a written fair hearing request should be sent
- In the notes field, include:
  - Whether the state requires appealing to the MCO (managed care organization) first before requesting a state fair hearing
  - Any notably short or different deadlines beyond the federal 90-day floor
  - Whether expedited hearings are available and how to request them
  - Any other quirk a consumer should know

Return ONLY the JSON object. No preamble, no markdown fences, no explanation.
```

---

## AFTER GENERATION: Spot-Check Procedure

The LLM will generally get agency names right but phone numbers and URLs can be wrong. 
Spot-check at MINIMUM these 10 states by Googling "[state] Medicaid fair hearing request":

1. **Pennsylvania** — PA DHS, Bureau of Hearings and Appeals
2. **New York** — NY Office of Temporary and Disability Assistance (OTDA)
3. **California** — CA DHCS, State Hearings Division
4. **Texas** — TX HHS, Office of Inspector General (fair hearings)
5. **Florida** — FL AHCA or DCF
6. **Illinois** — IL DHS, Bureau of Hearings
7. **Ohio** — OH Medicaid, Bureau of State Hearings
8. **Georgia** — GA DCH or DHS
9. **North Carolina** — NC DHHS, Office of Administrative Hearings
10. **Michigan** — MI DHHS, Michigan Administrative Hearing System (MAHS)

For each spot-check:
- [ ] Agency name is correct
- [ ] Phone number is correct (call it or verify on the state website)
- [ ] Online portal URL loads and is relevant (not a dead link or generic homepage)
- [ ] Mailing address is plausible (correct city/state for the agency)

If a phone number or URL is wrong, manually correct it. This takes ~2 minutes per state.

---

## QUICK VALIDATION CHECKLIST

After generating and spot-checking:
- [ ] JSON has exactly 51 entries (50 states + DC)
- [ ] Every entry has all 7 fields (state_name, agency, appeal_body, phone, online_portal, mailing_address, notes)
- [ ] No duplicate state keys
- [ ] Phone numbers are formatted consistently (1-800-XXX-XXXX or 1-XXX-XXX-XXXX)
- [ ] online_portal is either a valid URL string or null (not an empty string)
- [ ] Notes field is not empty — every state should have at least "Expedited hearings available for urgent medical situations" or similar
- [ ] PA entry is correct (since you're at Penn State, judges may check this one)
