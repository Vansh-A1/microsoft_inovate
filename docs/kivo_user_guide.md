# Kivo quick start and policy guide

Kivo is the configurable working name of the existing invoice/expense assistant. Open http://127.0.0.1:3000/welcome on this machine. The current local entry uses fictional server-configured identities, not production sign-in. Choose Finance to review documents or a permitted Admin role to configure business records. Server authorization applies independently of the visible navigation.

## Finance: from source to next action

1. Choose Upload & documents, add a PDF/PNG/JPEG, and select Auto, Vendor invoice, Employee expense or Supporting document. Files are bounded to 25 MiB/30 pages. The scanner notice reports the actual integration state; the local scope has no production malware protection.
2. Follow the persisted processing stages. Prepare review means the extracted draft exists, not that a person confirmed the source or finance cleared it. You can leave and return to the document.
3. On Check the source, read the exact questions first. Compare critical values with the original; choose a source field, page and zoom to inspect evidence. A field box appears only when coordinates were measured.
4. Open Review all extracted facts and correct values when needed. Raw extracted text, deterministic normalization and human corrections are distinct. Keep missing, ambiguous and illegible values unresolved. Do not infer tax treatment or calculate an absent quantity/price from other amounts. Obtain source-backed clarification when the source is blank.
5. Open Match supplier, budget and business references. Select actual approved records; the form cannot supply missing policies or approval authority. Enter a verification/correction reason and confirm only what you checked. Commit stays blocked when required facts or dependencies remain unresolved.
6. Read one finance outcome. Ready for processing requires applicable checks and current eligibility; it executes no payment. Needs review identifies an exception. On hold requires missing evidence, capacity, policy or approval resolution. Follow What to do next; expand Resolve this case and manage approvals for permitted actions.
7. Source documents retain originals and corrections. Full facts and detailed checks show rule/evidence details; Audit history shows retained actions. More case actions exposes reevaluation and revisions. History and reports retain earlier results when new versions are created. Export requires separate authority.

## Admin: change an allowance with history

This example is fictional, not a universal corporate allowance. The tested hotel record was changed from INR 8,000 to INR 9,000 per eligible night, effective 2026-11-01. Actual screenshots show the current INR 9,000 record, version 48; version numbers can increase after later authorized changes.

1. Open Admin Console with Policy administrator access; choose Allowances & receipts, then the Hotel configuration record.
2. Inspect What this rule covers: currency INR, Eligible night, grade G1, country IN, location DEMO-CITY and current version. Changing its amount does not broaden that scope. Use the correct business-owned rule, unit and currency; missing policy cannot permit processing.
3. For an authorized 8,000-to-9,000 change, enter 9000.00 in New allowance. If the current value is already 9,000, no change is needed solely to reproduce the example.
4. Set Effective from to the business-approved date, for example 2026-11-01. Effective until is exclusive; the illustrated rule ends before 2027-01-01. Check submission-window and receipt requirements rather than inventing them.
5. Enter a meaningful Configuration change reason. Click Validate and save draft. The server validates the fields and expected current version; validation errors require correction. A saved draft does not activate policy.
6. Review the old/new allowance, scope/unit/currency, effective period, reason and proposed new version. Editing inputs invalidates the displayed draft and requires validation again.
7. Click Activate new version only for the intended validated change. Activation appends a version and audit identity/reason. A concurrent change can reject a stale draft; reload the record and review the current values before retrying.
8. Open Policy versions and audit metadata, then Earlier versions if needed. Full audit record and identifiers exposes actor and complete records. Earlier finance outcomes and reference snapshots remain pinned; a new effective policy does not rewrite old reports.

## Other administration and limits

Approval hierarchy edits amount bands and required authority. People & teams manages permitted employee/cost-centre records. Vendors manages permitted supplier records. Budgets appends audited adjustments and protects reservations. Delegation & exceptions keeps scoped authority/waiver controls. Reference data and Health & recovery appear only for permitted roles; the latter shows actual dependency status, jobs, timing samples, failures and bounded recovery. Intelligence governance retains the supervised-label gate and explicit rules/statistical lifecycle.

Production sign-in, a working malware scanner, business-approved policies/references and independent adjudicated invoice acceptance remain external inputs. No real identity provider or paid service was provisioned, and no invoice was transmitted to an external inference service for this UI work. Kivo has no trademark/domain availability assertion. Do not interpret the fictional screenshot example as a guarantee that another invoice will pass.
