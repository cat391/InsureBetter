# Member 1 Implementation Steps

Goal: Build the denial data assets and demo PDFs required for the end-to-end demo and backend lookup flow.

Deliverables
1. data/denial_database.json
2. data/carc_lookup.json
3. data/category_descriptions.json
4. data/state_medicaid_contacts.json
5. data/sample_denials/keystone_aca_co197.pdf
6. data/sample_denials/medicare_co50_msn.pdf
7. data/sample_denials/anthem_erisa_co16.pdf
8. data/sample_denials/pa_medicaid_co96.pdf

Steps
1. Build data/denial_database.json with the 7 categories and 4 tracks each (ACA, Medicare, ERISA, Medicaid).
2. For each track, fill in regulations, deadline, process, strategy, evidence, escalation, and template key.
3. Add a plain-English description and common_grounds for each category.
4. Create data/carc_lookup.json mapping each CARC code to category_id.
5. Create data/category_descriptions.json mapping numeric codes to category_id.
6. Create data/state_medicaid_contacts.json for all 50 states plus DC.
7. Create 4 synthetic denial PDFs in data/sample_denials/ using the plan’s scenarios.
8. Hand off the JSON files and PDFs to Member 2.
