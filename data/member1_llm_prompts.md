# Member 1: LLM Prompts for Building denial_database.json

## Reference Sources (for spot-checking LLM output)
- **Official CARC codes:** https://x12.org/codes/claim-adjustment-reason-codes
- **CMS CARC/RARC tool:** https://www.cms.gov/medicare/regulations-guidance/administrative-simplification/rarc-carc-rarc
- **ACA appeal regs:** 42 USC §300gg-19, 29 CFR §2590.715-2719 → search law.cornell.edu
- **Medicare appeal regs:** 42 CFR Parts 405 and 422 → search ecfr.gov
- **ERISA appeal regs:** 29 USC §1133, 29 CFR §2560.503-1 → search law.cornell.edu
- **Medicaid fair hearing regs:** 42 CFR Part 431 Subpart E (§431.200–§431.246) → search ecfr.gov
- **Find-A-Code (readable descriptions):** https://www.findacode.com/medical-code-sets/carc-claim-adjustment-reason-codes.html
- **MD Clarity (plain English):** https://www.mdclarity.com/denial-code-carcs

---

## PROMPT 1 OF 7: Prior Authorization

```
Generate a JSON entry for our insurance denial appeal database.

Category: "Prior Authorization"
CARC codes in this category: CO-197, CO-15, CO-27, CO-204, CO-198

Official X12 descriptions for reference (verify against https://x12.org/codes/claim-adjustment-reason-codes):
- CO-197: Precertification/authorization/notification absent
- CO-15: The authorization number is missing, invalid, or does not apply to the billed services or provider
- CO-27: Expenses incurred after coverage terminated (used when auth expired before service was rendered)
- CO-204: This service/equipment/drug is not covered under the patient's current benefit plan (when tied to missing prior auth)
- CO-198: Precertification/authorization/notification/pre-treatment was not timely

For each of the following 4 insurance types, provide:
1. The specific federal regulations that govern appeals for this denial type
2. The appeal deadline
3. The step-by-step appeal process
4. The specific appeal strategy and arguments
5. What evidence the patient should include
6. The escalation path if the appeal is denied

Insurance types:
- ACA Marketplace (governed by 42 USC §300gg-19, 29 CFR §2590.715-2719)
- Medicare (governed by 42 CFR Parts 405 and 422)
- Employer-Sponsored / ERISA (governed by 29 USC §1133, 29 CFR §2560.503-1)
- Medicaid — FEDERAL FLOOR ONLY (governed by 42 CFR Part 431 Subpart E, §431.200–§431.246). Do NOT include state-specific rules. Focus on the federally guaranteed right to a fair hearing.

Output as a JSON object matching this schema EXACTLY:
{
  "denial_category": "Prior Authorization",
  "category_id": "prior_authorization",
  "carc_codes": ["197", "15", "27", "204", "198"],
  "description": "The claim was denied because the provider did not obtain prior authorization, the authorization number was missing or invalid, or precertification was not completed in time.",
  "tracks": {
    "aca": {
      "regulations": [{"citation": "string", "summary": "string"}],
      "appeal_deadline": "string",
      "appeal_process": ["step 1", "step 2", ...],
      "appeal_strategy": "string",
      "template_key": "prior_auth_aca",
      "escalation": "string",
      "required_evidence": ["string"]
    },
    "medicare": { ... same structure, template_key: "prior_auth_medicare" ... },
    "erisa": { ... same structure, template_key: "prior_auth_erisa" ... },
    "medicaid": { ... same structure, template_key: "prior_auth_medicaid", federal floor only ... }
  },
  "common_grounds": "string — general appeal arguments for this category"
}

Return ONLY the JSON object. No preamble, no markdown fences, no explanation.
```

---

## PROMPT 2 OF 7: Medical Necessity

```
Generate a JSON entry for our insurance denial appeal database.

Category: "Medical Necessity"
CARC codes in this category: CO-50, CO-150, CO-151, CO-54, CO-167, CO-146

Official X12 descriptions for reference (verify against https://x12.org/codes/claim-adjustment-reason-codes):
- CO-50: These are non-covered services because this is not deemed a "medical necessity" by the payer
- CO-150: Payer deems the information submitted does not support this level of service
- CO-151: Payer deems the information submitted does not support this many/frequency of services
- CO-54: Multiple reasons not deemed medically necessary (catch-all for level, frequency, dosage, days supply)
- CO-167: This (these) diagnosis(es) is (are) not covered (when used in context of medical necessity disputes)
- CO-146: Diagnosis was invalid for the date(s) of service reported (when tied to medical necessity documentation)

For each of the following 4 insurance types, provide:
1. The specific federal regulations that govern appeals for this denial type
2. The appeal deadline
3. The step-by-step appeal process
4. The specific appeal strategy and arguments
5. What evidence the patient should include
6. The escalation path if the appeal is denied

Insurance types:
- ACA Marketplace (governed by 42 USC §300gg-19, 29 CFR §2590.715-2719)
- Medicare (governed by 42 CFR Parts 405 and 422)
- Employer-Sponsored / ERISA (governed by 29 USC §1133, 29 CFR §2560.503-1)
- Medicaid — FEDERAL FLOOR ONLY (governed by 42 CFR Part 431 Subpart E, §431.200–§431.246). Do NOT include state-specific rules. Focus on the federally guaranteed right to a fair hearing.

Output as a JSON object matching this schema EXACTLY:
{
  "denial_category": "Medical Necessity",
  "category_id": "medical_necessity",
  "carc_codes": ["50", "150", "151", "54", "167", "146"],
  "description": "The claim was denied because the payer determined the service was not medically necessary, the documentation did not support the level or frequency of care, or the diagnosis did not justify the procedure.",
  "tracks": {
    "aca": {
      "regulations": [{"citation": "string", "summary": "string"}],
      "appeal_deadline": "string",
      "appeal_process": ["step 1", "step 2", ...],
      "appeal_strategy": "string",
      "template_key": "medical_necessity_aca",
      "escalation": "string",
      "required_evidence": ["string"]
    },
    "medicare": { ... same structure, template_key: "medical_necessity_medicare" ... },
    "erisa": { ... same structure, template_key: "medical_necessity_erisa" ... },
    "medicaid": { ... same structure, template_key: "medical_necessity_medicaid", federal floor only ... }
  },
  "common_grounds": "string — general appeal arguments for this category"
}

Return ONLY the JSON object. No preamble, no markdown fences, no explanation.
```

---

## PROMPT 3 OF 7: Out-of-Network / Coordination of Benefits

```
Generate a JSON entry for our insurance denial appeal database.

Category: "Out-of-Network / Coordination of Benefits"
CARC codes in this category: CO-11, CO-22, CO-109, CO-24, CO-119, CO-5

Official X12 descriptions for reference (verify against https://x12.org/codes/claim-adjustment-reason-codes):
- CO-11: The diagnosis is inconsistent with the procedure (often used with out-of-network code mismatches)
- CO-22: This care may be covered by another payer per coordination of benefits
- CO-109: Claim/service not covered by this payer/contractor
- CO-24: Charges are covered under a capitation agreement or managed care plan
- CO-119: Benefit maximum for this time period or occurrence has been reached
- CO-5: The procedure code is inconsistent with the place of service

For each of the following 4 insurance types, provide:
1. The specific federal regulations that govern appeals for this denial type
2. The appeal deadline
3. The step-by-step appeal process
4. The specific appeal strategy and arguments (include No Surprises Act protections where applicable)
5. What evidence the patient should include
6. The escalation path if the appeal is denied

Insurance types:
- ACA Marketplace (governed by 42 USC §300gg-19, 29 CFR §2590.715-2719)
- Medicare (governed by 42 CFR Parts 405 and 422)
- Employer-Sponsored / ERISA (governed by 29 USC §1133, 29 CFR §2560.503-1)
- Medicaid — FEDERAL FLOOR ONLY (governed by 42 CFR Part 431 Subpart E, §431.200–§431.246). Do NOT include state-specific rules. Focus on the federally guaranteed right to a fair hearing.

Output as a JSON object matching this schema EXACTLY:
{
  "denial_category": "Out-of-Network / Coordination of Benefits",
  "category_id": "out_of_network",
  "carc_codes": ["11", "22", "109", "24", "119", "5"],
  "description": "The claim was denied due to out-of-network billing, coordination of benefits disputes between multiple insurers, benefit maximums being reached, or place-of-service mismatches.",
  "tracks": {
    "aca": {
      "regulations": [{"citation": "string", "summary": "string"}],
      "appeal_deadline": "string",
      "appeal_process": ["step 1", "step 2", ...],
      "appeal_strategy": "string",
      "template_key": "out_of_network_aca",
      "escalation": "string",
      "required_evidence": ["string"]
    },
    "medicare": { ... same structure, template_key: "out_of_network_medicare" ... },
    "erisa": { ... same structure, template_key: "out_of_network_erisa" ... },
    "medicaid": { ... same structure, template_key: "out_of_network_medicaid", federal floor only ... }
  },
  "common_grounds": "string — general appeal arguments for this category"
}

Return ONLY the JSON object. No preamble, no markdown fences, no explanation.
```

---

## PROMPT 4 OF 7: Coding / Billing Error

```
Generate a JSON entry for our insurance denial appeal database.

Category: "Coding / Billing Error"
CARC codes in this category: CO-4, CO-16, CO-97, CO-18, CO-45, CO-6, CO-7, CO-8, CO-9, CO-125, CO-181

Official X12 descriptions for reference (verify against https://x12.org/codes/claim-adjustment-reason-codes):
- CO-4: The procedure code is inconsistent with the modifier used or a required modifier is missing
- CO-16: Claim/service lacks information or has submission/billing error(s)
- CO-97: The benefit for this service is included in the payment/allowance for another service/procedure (bundling)
- CO-18: Exact duplicate claim/service
- CO-45: Charge exceeds fee schedule/maximum allowable or contracted/legislated fee arrangement
- CO-6: The procedure/revenue code is inconsistent with the patient's age
- CO-7: The procedure/revenue code is inconsistent with the patient's gender
- CO-8: The procedure code is inconsistent with the provider type/specialty (taxonomy)
- CO-9: The diagnosis is inconsistent with the patient's age
- CO-125: Submission/billing error(s). At least one Remark Code must be provided
- CO-181: Procedure code was invalid on the date of service

For each of the following 4 insurance types, provide:
1. The specific federal regulations that govern appeals for this denial type
2. The appeal deadline
3. The step-by-step appeal process
4. The specific appeal strategy and arguments
5. What evidence the patient should include
6. The escalation path if the appeal is denied

Insurance types:
- ACA Marketplace (governed by 42 USC §300gg-19, 29 CFR §2590.715-2719)
- Medicare (governed by 42 CFR Parts 405 and 422)
- Employer-Sponsored / ERISA (governed by 29 USC §1133, 29 CFR §2560.503-1)
- Medicaid — FEDERAL FLOOR ONLY (governed by 42 CFR Part 431 Subpart E, §431.200–§431.246). Do NOT include state-specific rules. Focus on the federally guaranteed right to a fair hearing.

Output as a JSON object matching this schema EXACTLY:
{
  "denial_category": "Coding / Billing Error",
  "category_id": "coding_error",
  "carc_codes": ["4", "16", "97", "18", "45", "6", "7", "8", "9", "125", "181"],
  "description": "The claim was denied due to a coding or billing error, including wrong modifiers, missing information, duplicate submissions, bundling issues, fee schedule overages, or demographic mismatches in the claim.",
  "tracks": {
    "aca": {
      "regulations": [{"citation": "string", "summary": "string"}],
      "appeal_deadline": "string",
      "appeal_process": ["step 1", "step 2", ...],
      "appeal_strategy": "string",
      "template_key": "coding_error_aca",
      "escalation": "string",
      "required_evidence": ["string"]
    },
    "medicare": { ... same structure, template_key: "coding_error_medicare" ... },
    "erisa": { ... same structure, template_key: "coding_error_erisa" ... },
    "medicaid": { ... same structure, template_key: "coding_error_medicaid", federal floor only ... }
  },
  "common_grounds": "string — general appeal arguments for this category"
}

Return ONLY the JSON object. No preamble, no markdown fences, no explanation.
```

---

## PROMPT 5 OF 7: Timely Filing

```
Generate a JSON entry for our insurance denial appeal database.

Category: "Timely Filing"
CARC codes in this category: CO-29, CO-39

Official X12 descriptions for reference (verify against https://x12.org/codes/claim-adjustment-reason-codes):
- CO-29: The time limit for filing has expired
- CO-39: Services denied at the time the charges were incurred (related to retroactive denial windows)

For each of the following 4 insurance types, provide:
1. The specific federal regulations that govern appeals for this denial type
2. The appeal deadline
3. The step-by-step appeal process
4. The specific appeal strategy and arguments
5. What evidence the patient should include
6. The escalation path if the appeal is denied

Insurance types:
- ACA Marketplace (governed by 42 USC §300gg-19, 29 CFR §2590.715-2719)
- Medicare (governed by 42 CFR Parts 405 and 422)
- Employer-Sponsored / ERISA (governed by 29 USC §1133, 29 CFR §2560.503-1)
- Medicaid — FEDERAL FLOOR ONLY (governed by 42 CFR Part 431 Subpart E, §431.200–§431.246). Do NOT include state-specific rules. Focus on the federally guaranteed right to a fair hearing.

Output as a JSON object matching this schema EXACTLY:
{
  "denial_category": "Timely Filing",
  "category_id": "timely_filing",
  "carc_codes": ["29", "39"],
  "description": "The claim was denied because it was submitted after the payer's filing deadline, or services were retroactively denied after the charges were incurred.",
  "tracks": {
    "aca": {
      "regulations": [{"citation": "string", "summary": "string"}],
      "appeal_deadline": "string",
      "appeal_process": ["step 1", "step 2", ...],
      "appeal_strategy": "string",
      "template_key": "timely_filing_aca",
      "escalation": "string",
      "required_evidence": ["string"]
    },
    "medicare": { ... same structure, template_key: "timely_filing_medicare" ... },
    "erisa": { ... same structure, template_key: "timely_filing_erisa" ... },
    "medicaid": { ... same structure, template_key: "timely_filing_medicaid", federal floor only ... }
  },
  "common_grounds": "string — general appeal arguments for this category"
}

Return ONLY the JSON object. No preamble, no markdown fences, no explanation.
```

---

## PROMPT 6 OF 7: Experimental / Investigational

```
Generate a JSON entry for our insurance denial appeal database.

Category: "Experimental / Investigational"
CARC codes in this category: CO-55, CO-56, CO-183, CO-188

Official X12 descriptions for reference (verify against https://x12.org/codes/claim-adjustment-reason-codes):
- CO-55: Procedure/treatment/drug is deemed experimental/investigational by the payer
- CO-56: Procedure/treatment has not been deemed "proven to be effective" by the payer
- CO-183: The service/equipment/drug is not covered under the patient's current benefit plan (when denial reason cites clinical protocol or experimental status)
- CO-188: This product/procedure is only covered when used according to FDA recommendations

For each of the following 4 insurance types, provide:
1. The specific federal regulations that govern appeals for this denial type
2. The appeal deadline
3. The step-by-step appeal process
4. The specific appeal strategy and arguments (include FDA approval status, peer-reviewed evidence, state mandates for clinical trials coverage)
5. What evidence the patient should include
6. The escalation path if the appeal is denied

Insurance types:
- ACA Marketplace (governed by 42 USC §300gg-19, 29 CFR §2590.715-2719)
- Medicare (governed by 42 CFR Parts 405 and 422)
- Employer-Sponsored / ERISA (governed by 29 USC §1133, 29 CFR §2560.503-1)
- Medicaid — FEDERAL FLOOR ONLY (governed by 42 CFR Part 431 Subpart E, §431.200–§431.246). Do NOT include state-specific rules. Focus on the federally guaranteed right to a fair hearing.

Output as a JSON object matching this schema EXACTLY:
{
  "denial_category": "Experimental / Investigational",
  "category_id": "experimental",
  "carc_codes": ["55", "56", "183", "188"],
  "description": "The claim was denied because the payer considers the treatment experimental, investigational, not proven effective, not following FDA recommendations, or not meeting the payer's clinical protocol criteria.",
  "tracks": {
    "aca": {
      "regulations": [{"citation": "string", "summary": "string"}],
      "appeal_deadline": "string",
      "appeal_process": ["step 1", "step 2", ...],
      "appeal_strategy": "string",
      "template_key": "experimental_aca",
      "escalation": "string",
      "required_evidence": ["string"]
    },
    "medicare": { ... same structure, template_key: "experimental_medicare" ... },
    "erisa": { ... same structure, template_key: "experimental_erisa" ... },
    "medicaid": { ... same structure, template_key: "experimental_medicaid", federal floor only ... }
  },
  "common_grounds": "string — general appeal arguments for this category"
}

Return ONLY the JSON object. No preamble, no markdown fences, no explanation.
```

---

## PROMPT 7 OF 7: Coverage / Eligibility

```
Generate a JSON entry for our insurance denial appeal database.

Category: "Coverage / Eligibility"
CARC codes in this category: CO-26, CO-96, CO-1, CO-2, CO-3, CO-31, CO-32, CO-33, CO-170, CO-186

Official X12 descriptions for reference (verify against https://x12.org/codes/claim-adjustment-reason-codes):
- CO-26: Expenses incurred prior to coverage
- CO-96: Non-covered charge(s) — plan simply doesn't cover this service
- CO-1: Deductible amount
- CO-2: Coinsurance amount
- CO-3: Co-payment amount
- CO-31: Patient cannot be identified as our insured
- CO-32: Our records indicate the patient is not an eligible dependent
- CO-33: Insured has no dependent coverage
- CO-170: Payment is denied when performed/billed by this type of provider (when tied to plan exclusions)
- CO-186: Level of care change adjustment

For each of the following 4 insurance types, provide:
1. The specific federal regulations that govern appeals for this denial type
2. The appeal deadline
3. The step-by-step appeal process
4. The specific appeal strategy and arguments (include ACA essential health benefits mandates, preventive care coverage requirements where applicable)
5. What evidence the patient should include
6. The escalation path if the appeal is denied

Insurance types:
- ACA Marketplace (governed by 42 USC §300gg-19, 29 CFR §2590.715-2719)
- Medicare (governed by 42 CFR Parts 405 and 422)
- Employer-Sponsored / ERISA (governed by 29 USC §1133, 29 CFR §2560.503-1)
- Medicaid — FEDERAL FLOOR ONLY (governed by 42 CFR Part 431 Subpart E, §431.200–§431.246). Do NOT include state-specific rules. Focus on the federally guaranteed right to a fair hearing.

Output as a JSON object matching this schema EXACTLY:
{
  "denial_category": "Coverage / Eligibility",
  "category_id": "coverage_eligibility",
  "carc_codes": ["26", "96", "1", "2", "3", "31", "32", "33", "170", "186"],
  "description": "The claim was denied due to coverage or eligibility issues, including services before coverage started, non-covered services, deductible/coinsurance/copay amounts, patient not found as insured, dependent coverage issues, provider type exclusions, or level of care changes.",
  "tracks": {
    "aca": {
      "regulations": [{"citation": "string", "summary": "string"}],
      "appeal_deadline": "string",
      "appeal_process": ["step 1", "step 2", ...],
      "appeal_strategy": "string",
      "template_key": "coverage_eligibility_aca",
      "escalation": "string",
      "required_evidence": ["string"]
    },
    "medicare": { ... same structure, template_key: "coverage_eligibility_medicare" ... },
    "erisa": { ... same structure, template_key: "coverage_eligibility_erisa" ... },
    "medicaid": { ... same structure, template_key: "coverage_eligibility_medicaid", federal floor only ... }
  },
  "common_grounds": "string — general appeal arguments for this category"
}

Return ONLY the JSON object. No preamble, no markdown fences, no explanation.
```

---

## AFTER ALL 7 PROMPTS: Assembly

Combine all 7 JSON objects into a single array and save as `data/denial_database.json`:

```json
[
  { /* prompt 1 result - prior_authorization */ },
  { /* prompt 2 result - medical_necessity */ },
  { /* prompt 3 result - out_of_network */ },
  { /* prompt 4 result - coding_error */ },
  { /* prompt 5 result - timely_filing */ },
  { /* prompt 6 result - experimental */ },
  { /* prompt 7 result - coverage_eligibility */ }
]
```

---

## UPDATED carc_lookup.json (build this manually after collecting all outputs)

```json
{
  "197": "prior_authorization",
  "15": "prior_authorization",
  "27": "prior_authorization",
  "204": "prior_authorization",
  "198": "prior_authorization",
  "50": "medical_necessity",
  "150": "medical_necessity",
  "151": "medical_necessity",
  "54": "medical_necessity",
  "167": "medical_necessity",
  "146": "medical_necessity",
  "11": "out_of_network",
  "22": "out_of_network",
  "109": "out_of_network",
  "24": "out_of_network",
  "119": "out_of_network",
  "5": "out_of_network",
  "4": "coding_error",
  "16": "coding_error",
  "97": "coding_error",
  "18": "coding_error",
  "45": "coding_error",
  "6": "coding_error",
  "7": "coding_error",
  "8": "coding_error",
  "9": "coding_error",
  "125": "coding_error",
  "181": "coding_error",
  "29": "timely_filing",
  "39": "timely_filing",
  "55": "experimental",
  "56": "experimental",
  "183": "experimental",
  "188": "experimental",
  "26": "coverage_eligibility",
  "96": "coverage_eligibility",
  "1": "coverage_eligibility",
  "2": "coverage_eligibility",
  "3": "coverage_eligibility",
  "31": "coverage_eligibility",
  "32": "coverage_eligibility",
  "33": "coverage_eligibility",
  "170": "coverage_eligibility",
  "186": "coverage_eligibility"
}
```

## UPDATED category_descriptions.json (same mapping, used for prose fallback)

This is identical to carc_lookup.json — copy it and save as `data/category_descriptions.json`.

---

## QUICK CHECKLIST BEFORE HANDING OFF TO MEMBER 2

- [ ] All 7 categories present in denial_database.json
- [ ] Each category has all 4 tracks (aca, medicare, erisa, medicaid)
- [ ] carc_lookup.json has all ~40 codes mapped
- [ ] category_descriptions.json matches carc_lookup.json
- [ ] Every code in carc_lookup.json appears in some category's carc_codes array in denial_database.json
- [ ] No duplicate codes across categories
- [ ] template_key values are unique per category+track combo
