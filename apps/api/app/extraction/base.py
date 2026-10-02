"""The minimal replaceable provider boundary from specification section 3.3."""

from typing import Protocol, runtime_checkable

from app.domain.extraction import AdapterCapabilities, AdapterMetadata, DocumentBundle, ExtractionResult


@runtime_checkable
class ExtractionAdapter(Protocol):
    metadata: AdapterMetadata
    capabilities: AdapterCapabilities

    def extract(self, document_bundle: DocumentBundle, schema_version: str) -> ExtractionResult:
        """Return observations for this scoped document revision and schema.

        Unknown fields stay explicit. Exceptions may be reported by the harness;
        a typed response never establishes factual correctness or eligibility.
        """
        ...
