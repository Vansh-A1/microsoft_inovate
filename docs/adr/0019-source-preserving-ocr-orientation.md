# ADR-0019 — measured source-preserving OCR orientation

Date: 2026-10-04. Status: accepted within the delegated bounded CL-10 extraction responsibility.

## Context

The unchanged pinned CPU detector reads some rotated text but its original page coordinates prevent reliable header/table association. The spent rotated public scan required repeated VLM inventory/row calls; the spent q06 PDF lost measured rows around two blank cells. Finance arithmetic cannot supply those values. Originals, source coordinates and canonical uncertainty must survive any preprocessing.

## Decision

Retain the current native → optional pinned local CPU OCR → actual Qwen/TypeLLM → human route and ADR-0015 BF16 runtime. Add four orthogonal **layout** candidates from actual OCR quadrilaterals, independently printed labels/table columns, and physical text axes. Unique sufficient measured coverage selects orientation; ties/weak coverage abstain. A small global skew requires at least five sufficiently consistent measured long baselines, 70% support within two degrees, and at most eight degrees. This is a geometry gate, not confidence or a financial decision.

Only a selected nonidentity transform can request **one** full CPU OCR reread of a bounded private in-memory aligned derivative. Originals/previews remain unchanged. Record its actual PNG hash, dimensions, rigid transform and Pillow version. Inverse-map actual detector quadrilaterals to the original preview and through retained EXIF mapping. Layout can be refined from these measured quadrilaterals without another image reread. Existing maximum three numeric-cell crops and the original per-page/document deadlines remain. Back-projected crop extents are context, never field boxes.

Corresponding actual reads with conflicting text remain AMBIGUOUS/canonical null; no model vote resolves them. Preserve disagreement literals in the scoped private extraction sidecar. Independent right table panels cannot inherit left header baselines. A measured description/amount under unique columns can retain two missing quantity/price slots and following rows. These slots retain raw/canonical null and precise source questions; no derived arithmetic/zero/UOM is added. Crossing/competing/unanchored rows still abstain.

No schema/migration, inference/model/dependency upgrade, host/system change, finance-engine rewrite or UI redesign. Historical runs retain old versions. New runs identify native adapter 8/layout 6 and measured alignment v1 in the versioned sidecar; strict extraction-v1 remains unchanged.

## Consequences and limits

The extra CPU reread increases raw CPU time on some scans but avoids expensive VLM reads when measured source coverage suffices. Coverage is not human confirmation or accounting completeness. Global rigid geometry does not solve perspective distortion, mixed rotations, Arabic recognition or missing business/source facts. Conservative read disagreement may require manual confirmation even when the second read is correct. Tesseract remains a real configured fallback; failure cannot return fixture answers.

Three original fictional layouts were frozen before tuning. Seven reserved variants from two new families were opened once on final code, with every wrong/missing/ambiguous check counted, and are now spent. They are correlated synthetic variants, not real-company accuracy or model-training holdouts. See [measured report](../clearledger_rotation_robustness.md) and [readiness](../clearledger_hackathon_readiness.md).
