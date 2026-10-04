# ClearLedger — bounded local hackathon readiness

ClearLedger supports an honest local fictional demonstration of invoice/expense controls, evidence, source confirmation and versioned governance. It is **not production-ready, a deployed pilot, or a generally reliable automatic invoice processor**. CL-10 is a bounded core-extraction stopping point; the latest instruction defers further UI redesign.

## Original challenge and current evidence

The working [approved specification](AP_Exception_Assistant_Codex_Spec.md) remains authoritative and unchanged. [Phase-6 local exit review](phase6_exit_review.md) is historical evidence for its supported local gate, not a blanket claim for subsequent OCR/model/business deployment. [CL-09](clearledger_source_repair.md) and [CL-10](clearledger_rotation_robustness.md) add actual runtime/source evidence without rewriting those exit reviews.

| Challenge / input gate | Current local disposition |
|---|---|
| Invoice AND employee expense workflows (AC01–08) | Working retained engine: durable intake, observations/corrections, Decimal normalization, 28 controls, separate screening/human/processing states, scoped evidence/reports/history. Eight judge scenarios use computed outcomes, not hard-coded UI flags. |
| PASS/REVIEW/HOLD and plain outcome | Existing mappings “Ready for processing”, “Needs review”, “On hold”; readiness requires finance controls/approvals/capacity, never extraction coverage. Documents missing source/accounting facts show confirmation and cannot commit. No payment execution. |
| T01–T42 / AC09 | Historical **39 complete, T30 partial, T31/T34 data-deferred** stays unchanged. Core new geometry/partial-cell cases supplement T29/T33/T39; no fabricated classifier/SHAP completion. |
| Security/capacity/audit/versioning (AC10–14) | Retained tenant/entity/role/SoD/RLS/idempotency/stale-version/budget/PO-GRN/shared-receipt/audit rollback behavior. CL-10 finance/security regressions and real migrated source/commit tests verify affected boundaries. |
| Actual extraction/TypeLLM (AC15) | Native PyMuPDF and bounded local OCR, source/crop geometry, actual resident Qwen2.5-VL-3B/TypeLLM fallback; fixed limited source failures, honest human abstention. ADR-0015 BF16/driver/runtime unchanged. This is experimental local factual evidence, not general invoice fidelity. |
| Risk/model governance (AC16–17) | RULES_ONLY / transparent robust anomaly alternative; zero representative adjudicated labels. No classifier, fake zero score, probability/SHAP, online training or low-score override. |
| Handoff/performance (AC18–19) | Local runbooks/recovery/release artifacts and limited measured tables exist. CL-10 distinguishes CPU startup/repeat, pipeline versus actual upload/durable latency, resident versus unmeasured cold GPU, and whole-device versus unmeasured request VRAM. No universal SLA/accuracy promise. |
| Hosted pilot (AC20) | DEFERRED_EXTERNAL: no provisioned identity/cloud/network/scanner/pilot restore/rollback/production load. Source licenses, real-data authorization/residency, business policy/reference ownership and deployment inputs remain gates. |

## Demo input discipline

Use the existing **Synthetic finance workspace** and fictional judge cases. The role-aware local login/session is development authentication; hosted SSO is not provisioned. The fictional hotel allowance and version/audit/history are configured demo policy, not universal company rules. Missing policy/reference/source facts hold or require review; no fabricated real employee/vendor/bank/master changes.

Keep original files, source boxes, raw observation states and trace history available. Do not press a demo template into missing quantities/tax/currency. q06 now captures visible description/amount/other rows while asking for both absent quantity and price. A rotated scan may align successfully yet contain disagreeing glyphs; those remain human questions. The seven new reserved variants are now spent, not perpetual holdouts.

A credible judge walkthrough can show actual computed clean invoice/expense/shared-receipt PASS, paid duplicate/partial-delivery/overflow HOLD, allowance REVIEW, and a source-corrected retained prior HOLD/new evaluation. Existing views keep Finance/Admin roles separate; production UI was not changed in CL-10. Long technical source-review tables/mobile source presentation remain known polish work for a separately bounded UI responsibility.

## Remaining acceptance limits

- **40–60 independently adjudicated authorized real/anonymized invoices**, including fresh vendor/layout families and source-verified blank/illegible/ambiguous facts, are absent. Original generated corpus, four spent public fictional sources, two same-template extra probes and new correlated synthetic rotations do not substitute for that gate. No more collection was performed in CL-10.
- Missing supplier reads, source disagreements, perspective/mixed rotations and Arabic fidelity remain. Orthogonal/small-global-skew support is bounded, not a universal image deskew system. A stronger model/runtime/training change is neither needed for this checkpoint nor authorized.
- Business-owned policies/allowances/employees/vendors/approval hierarchy/budgets/PO-GRN/tax treatment, actual identity memberships and approved secure storage/inference/scanner definitions remain external. Configuration paths do not prove real-service health or legal compliance.
- Hosted Azure/CI/image/registry/network/monitoring/backup restore/rollback and pilot load require approved subscription/region/identities/network/residency/spend/deployment inputs. No credentials, paid resources, public deploy or push was requested or performed.

The appropriate claim is **functioning local ClearLedger with measured limited extraction improvements and preserved finance/source safety**. Core work stops here after the scoped final checks and local reviewed commit. Next candidate responsibility, only under a new bounded instruction, is simplifying source confirmation and result presentation using the working Finance/Admin UI.

The subsequent [bounded final acceptance](clearledger_final_acceptance.md) verifies current clean readiness, source-matched duplicate/limit outcomes, exact unclear-source questions, retained policy form/history, local role boundaries and loading/error/retry recovery. The supported fictional demo gates pass; core stops. Generic duplicate/allowance summaries and long technical history remain contained UI work requiring one new bounded approval; real corpus/business/identity/scanner/pilot inputs remain separate.
