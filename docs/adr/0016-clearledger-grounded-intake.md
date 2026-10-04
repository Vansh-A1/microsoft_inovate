# ADR-0016 — ClearLedger grounded intake and presentation

Status: accepted within the delegated local ClearLedger hardening scope, 2026-10-04.

The working finance engine, historical outcomes, migration head and ADR-0015
runtime remain authoritative. This is an additive hardening milestone, not a
replacement application or approval for publication or external inference.

## Decisions

Use measured PyMuPDF spans and Tesseract word coordinates to associate explicit
printed labels and table headings. Association uses upright preview coordinates;
citations use the inverse EXIF transform into the original. A region crossing
columns, conflicting repeated identity, incomplete table or ambiguous value
abstains. The existing labeled/pipe parser remains available.

Printed mapping sufficiency controls whether inference is useful; it cannot
authorize finance processing. Complete observed core headers and rows can skip
VLM even when optional charges or tax treatment are absent. Those fields remain
missing and the existing normalizer/validator requests human evidence. Do not
call a model merely to fill absent accounting facts. Incomplete coverage retains
the pinned Qwen/TypeLLM path and existing bounded crop/call budget. Uncorroborated
model-only tax treatment becomes AMBIGUOUS, preserving its raw candidate.

Auto intake is a suggestion from printed invoice/receipt identities, never a
finance branch decision based on amounts or a supplied file name. Record the
original AUTO choice in the immutable scoped upload audit. Use the existing
SUPPORTING_DOCUMENT enum until purpose is established; no migration is needed.
Unclear purpose stops after safety preprocessing. An authorized, generation-bound,
idempotent confirmation appends an audit event and schedules extraction. Original
bytes and page evidence remain unchanged. Canonical source confirmation is still
required for every branch.

Map PASS/REVIEW/HOLD to Ready for processing/Needs review/On hold in normal
Finance presentation. Keep processing, stale eligibility, human ownership and
approval states separate. Stale PASS cannot imply readiness; stale mandatory HOLD
keeps On hold while requiring a fresh screening. Detailed controls, raw facts, IDs and provenance remain
accessible. ClearLedger is a centralized presentation name. Local role entry
uses existing configured server identities and HttpOnly sessions; enterprise
entry points to the established Microsoft identity integration. No identity
provider is provisioned or password credential invented.

An operator may supply an already installed local clamscan executable. The
adapter uses a bounded subprocess without shell, content logging, network calls
or file removal. A skipped file, engine error or timeout is never CLEAN. Required
scanning remains fail-closed. Authenticated intake capability status and Admin
health disclose NOT_CONFIGURED/UNAVAILABLE/CONFIGURED_UNVERIFIED; configuration
alone is not a successful scan. No scanner or signature database is installed.

Contain known transient PostgreSQL contention or invalidated connections at the
scoped worker cycle. Back off for one second, emit only an allowlisted stage/reason,
and continue other scopes. Preserve existing transaction rollback, committed lease
expiry, maximum attempts and idempotent finalization. Unknown database errors and
business configuration failures remain visible; they are not suppressed. This
repairs an observed lock timeout that escaped a claim and stopped the app supervisor.

## Consequences

The small frozen synthetic layout benchmark supports a measured reduction in
unnecessary inference, not representative invoice accuracy. Unknown real
layouts, wrapped tables, degraded scans, unsupported tax meaning and multi-invoice
segmentation still require review. Cold model startup and resident request times
must be reported separately. Stronger provider, real SSO, commercial checkpoint
use, representative private invoices and production scanner acceptance remain
external inputs. No master-data mutation, new finance rule, model switch,
dependency upgrade, host change or public deployment follows from this decision.
