# Kivo local panel walkthrough

This is a suggested 3–5 minute walkthrough, not an official event format. User-provided Day1 is **Wednesday 7 October 2026**; target readiness is **6 October evening IST**, before 7 October morning. Exact reporting time, submission format and any deck/video requirement have not been supplied. Use only the fictional local company. No invoice payment is executed.

## Prepare the established checkout

From `/data/vansh/microsoft_inovate`, with the existing database, production build and isolated model already installed:

```bash
.venv/bin/python scripts/demo.py start-cpu
./scripts/demo-health.sh --require-vlm
.venv/bin/python scripts/release/judge_verify.py
.venv/bin/python scripts/release/panel_prepare.py
```

`start-cpu` starts or checks the existing CPU application without seeding identities or starting/stopping inference. Preparation creates one distinct **fictional Hotel policy** through the existing validated reference API, using the established local reference administrator. Its `DEMO-PANEL-HOTEL-…` business code appears in the command output and Admin selector. Repeated preparation preserves its current version; it does not reset it to INR8000 after an edit. The private journal is `runtime/kivo-panel/operator-policy.json`. Do not run the old full start/restart/stop commands during this presentation: they also control inference. Do not run environment setup, migrations, identity setup or model installation.

Open **http://127.0.0.1:3000/welcome**. Use a laptop browser. Phone viewport screenshots verify responsive layout; remote phone access is not configured or requested.

Have these tabs ready, with their actual computed data:

- `/welcome` for first-time entry.
- `/documents` in **Finance workspace**, and the original **`data/kivo_panel/d01.pdf`** selected through the file picker.
- `/demo`, using its existing local fictional reviewer, for **source-confirmed vendor**, **paid duplicate** and **daily allowance** cases. Use the displayed links; do not paste invented UUIDs.
- `/admin` in **Policy administrator**, with the code printed by preparation selected under **Allowances & receipts**.

The normal Finance and Admin sign-in choices use configured development identities, not a production identity provider. Switching role does not grant new permissions. Keep runtime journals, credentials and generated case IDs out of presentation handouts and Git.

## Suggested live sequence

**0:00–0:35 — The result and the boundary.** Start at Welcome → Get started → Finance workspace. Say: “The assistant preserves the invoice, asks about uncertain facts and applies the configured finance controls. It screens a case; it does not pay it.” Point to the separate Admin entry and local fictional-company notice.

**0:35–1:50 — Actual unfamiliar intake and evidence.** Upload `data/kivo_panel/d01.pdf` as **Vendor invoice**. The preserved original and asynchronous five-stage progress stay available. This is a newly authored development/presentation source, now spent through rehearsal; do not call the live repetition a held-out test. The printed `10/02/2026` stays ambiguous. Select **Source page 2**; zoom to150–200% if needed. It explicitly says **2 October 2026 / ISO date2026-10-02**. Expand **Review all extracted facts and correct values**, enter `2026-10-02` for Invoice date and choose correction source page **2**. Expand **Match supplier, budget and business references** and explicitly set **Submission date** to the actual current business submission date, no earlier than2October. The rehearsal used5October; do not silently accept the old September fixture date. Other business references are fictional configured sample context; this does not automatically match a real company. Enter the reason below, check source confirmation, then **Verify facts and evaluate**:

> Page 2 supplier clarification explicitly states 2 October 2026 and ISO date 2026-10-02.

Expect **On hold** while approval and any duplicate disposition requirements remain. Read the actual reasons and next steps. Do not attempt to force Ready. Show **Source documents → Source correction history**: the human correction cites original page2 and retains the original ambiguous observation. The entered submission date is business context, not a value extracted from the invoice.

**1:50–2:50 — Three honest results.** In the prepared `/demo` tab, open the source-confirmed vendor case: **Ready for processing** only with actual PO/GRN, budget, source confirmation and independent approval evidence. Open paid duplicate: **On hold**, with the matching paid record and a disposition step. Open daily allowance: **Needs review**, actual fictional INR1800 aggregate against INR1500 configured allowance. Drill into evidence only as needed. All are retained computations from the existing finance engine; the invoice alone does not grant clearance.

**2:50–3:50 — A safe policy change.** Switch to Policy administrator and select the prepared `DEMO-PANEL-HOTEL-…` code, not the established `DEMO-EXP-HOTEL`. Confirm the isolated **PANEL-CITY-… / G1 / IN / INR / eligible night** scope and fictional-policy notice. If still version1/INR8000, enter **9000.00**, **effective from2026-11-15**, **effective until2027-01-01**, and a reason explaining the fictional allowance change. Validate and save draft, review the proposed version, then activate. Show the success notice and **Policy versions and audit metadata**, including the retained INR8000 version, new INR9000 version, effective dates and recorded reason. If already changed during rehearsal, show that actual history; do not claim a new live activation or reset the record. Finance cannot open this catalog; this administrator cannot read finance transactions.

**3:50–4:30 — Retention and recovery.** Return to Finance History or the saved source-linked case. Reload: the committed version, original source, correction and evaluation remain. Explain that an interrupted confirmation retries the same body/key as the same case; it does not create another financial effect. The browser suite actually tests dropped replies after commit and reload. An unavailable provider is disclosed and unresolved facts stay unresolved.

Use the remaining time for questions or original-source inspection. Keep JSON, internal rule IDs and model metadata collapsed until a technical question requires them.

## Recovery and fallback

For a CPU application interruption, after any active upload finishes:

```bash
.venv/bin/python scripts/demo.py restart-cpu
./scripts/demo-health.sh --require-vlm
.venv/bin/python scripts/release/judge_verify.py
```

This verified recovery preserves the resident inference processes, PostgreSQL and evidence. The measured first CPU restart took1.69seconds; this is one observed local restart, not a startup guarantee. The role session is server-backed; re-enter the existing configured workspace if needed. Use History to return to a completed upload, rather than uploading the same source again. If a commit reply is lost, reload its source, supply the **same** facts/reason, and retry; retained replay keys cover that body in this browser session. Changing the body is a different operation.

If health is degraded, use the **actual retained** computed cases and source/correction history. Explicitly say this is retained evidence, not live extraction. If the provider is unavailable, sufficiently mapped native/OCR sources may still reach review; a visual request requiring the unavailable provider cannot be represented as successful. Do not restart the GPU, kill unrelated processes, install packages, reseed, alter credentials, reset the database, enable a fixture fallback or publish a site. If CPU recovery fails, retain the safe error and use local screenshots of the actual rehearsed results as a labeled fallback.

## Defensible claims

- Existing deterministic finance engine retained, with Decimal amounts, scoped authorization, evidence, immutable revisions, mandatory controls and capacity/replay safeguards. No trained finance-risk classifier or SHAP: representative adjudicated labels are absent.
- One difficult **spent** scan previously took49.941–53.097seconds with3VLM calls and0/6 checked row values. The measured generic table-heading association fix subsequently took8.631/8.456seconds with0VLM calls and6/6 row values; missing facts stayed unresolved. This is the same development source, not broad accuracy or a cold GPU benchmark.
- REL-05 newly frozen fictional check:4sources in2newly drawn native/scanned layout families,28/28 checked headers and28/28 row values,32/32 required abstentions,3.101–8.195seconds. These correlated variants were reserved before first extraction and are now spent. No production tuning followed their output. Every source still required input before finance evaluation: ambiguous date/currency or missing printed tax basis, extras and explicit per-line financial fields. The score checks selected printed cells, not complete normalized invoices. Business reference/approval checks were not run by this intake-only benchmark. Extraction-ready and Ready for processing are different states.
- Separate actual resident Qwen/TypeLLM check on an **existing spent** rotation:14.799seconds,7/7 checked headers,12/12 row values and6/6 required abstentions; `NEEDS_INPUT`, no finance clearance. Read-only sampling of the owned serving process tree saw12948MiB baseline/13766MiB peak; this is resident/allocator footprint, not attributable per-request peak. GPU cold load was not repeated.
- Local presentation verification does not establish customer accuracy, production capacity, a live pilot, real corporate policy, production SSO, real malware scanning, a paid deployment or model license clearance. Supporting commands and final counts are in [readiness verification](../kivo_panel_readiness.md).

## Submission inventory

The working specification §25 asks for six end-to-end synthetic finance scenarios and retained correction/approval evidence. The original team work plan §9–10 asks for code/contracts, fixtures, tests, evidence/dependencies/assumptions, short working module demos and combined acceptance cases. The local repository contains the application, migration/setup/release artifacts, source fixtures, API/rule/policy catalogs, measured verification, handoff/runbooks and user guide PDF. Preserve the supplied pack/ZIP and historical reviews.

No official event deck/video template, scoring rubric, upload portal, artifact deadline, reporting time or presentation duration was found in the supplied pack/repository. `output/pdf/Kivo-quick-start.pdf` is a user guide, not a pitch deck. A panel slide deck and narrated demo video are not present. The parent should confirm whether those are required and prioritize them separately; this walkthrough does not invent competition requirements or claim those deliverables exist.
