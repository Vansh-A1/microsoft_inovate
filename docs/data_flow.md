# Document, decision and administration data flows

```mermaid
flowchart TD
    Intake[Create upload session] --> Bytes[Server-generated key / streamed original / SHA-256]
    Bytes --> Finalize[Finalize integrity and content checks]
    Finalize -->|unsafe| Quarantine[Quarantined: no finance decision]
    Finalize -->|supported| Process[Immutable pages / native spans / quality / transforms]
    Process --> Route[Native text first; OCR or configured visual boundary when required]
    Route --> Observe[Versioned field observations with uncertainty and reliable source bindings]
    Observe --> Normalize[Normalization traces / Decimal and currency / ambiguous dates]
    Normalize --> Verify[Human source inspection and business reference mapping]
    Verify --> Canonical[Immutable canonical transaction version / attachments]
    Canonical --> Queue[Durable evaluation job / pinned references]
    Queue --> Controls[Rules / matching / duplicates / approvals / capacity]
    Controls --> Commit[Atomic eligibility, allocations, evaluation, audit and outbox]
    Commit --> Result[Plain-language result / source / next actions / report]
    Result --> Review[Owner/version-guarded correction or resolution]
    Review --> Canonical
```

Originals never become corrected documents. Derived previews are separate objects; page numbers are 1-based and boxes are shown only when measured coordinates exist. Import evidence retains batch/sheet/row/column/raw/parsed/validation. A spreadsheet attachment flag is insufficient without an actual document link. Spreadsheet formulas are not executed; CSV exports escape executable prefixes.

```mermaid
flowchart LR
    Admin[Authorized business form] --> Draft[Expected version / reason / typed changes]
    Draft --> Validate[Existing reference validator]
    Validate --> Activate[Explicit authorized activation]
    Activate --> Version[New reference version with effective dates]
    Version --> Future[Future matching selects applicable version]
    Version --> Audit[Actor / reason / time / retained old versions]
    History[Historical evaluation and snapshot] --> Unchanged[Original report remains unchanged]
```

The hotel demonstration changes INR 8,000 to 9,000 per eligible night from 2026-11-01. Integration tests check both sides of that date, version conflicts, scoped permissions and the immutable prior snapshot. Browser tests retain the historical report and show the activation reason/version history.

Intelligence operates on already canonical facts, separately from document VLM extraction. Features exclude current/future facts and incompatible currencies. Statistical factors may request REVIEW and cannot clear HOLD. No representative supervised dataset exists; classifier probability, calibration and SHAP are deferred.
