"""Deterministic response replay. Does not parse text, PDF/image bytes or policy."""

from dataclasses import dataclass
from types import MappingProxyType

from app.domain.extraction import AdapterCapabilities, AdapterMetadata, DocumentBundle, ExtractionResult, SCHEMA_VERSION


FIXTURE_METADATA = AdapterMetadata("fixture-extraction", "fixture-v1", "synthetic-response-replay")


@dataclass(frozen=True, slots=True)
class FixtureResponse:
    input_digest: str
    result: ExtractionResult

    def __post_init__(self):
        if not isinstance(self.input_digest, str) or len(self.input_digest) != 64 or any(c not in "0123456789abcdef" for c in self.input_digest):
            raise ValueError("input_digest must be a SHA-256 hex digest")
        if not isinstance(self.result, ExtractionResult):
            raise TypeError("fixture response requires ExtractionResult")


class FixtureExtractionAdapter:
    metadata = FIXTURE_METADATA
    capabilities = AdapterCapabilities(page_locators=True, bounding_boxes=False, line_items=True, visual_input=False)

    def __init__(self, responses: tuple[FixtureResponse, ...]):
        if not isinstance(responses, tuple) or not all(isinstance(r, FixtureResponse) for r in responses):
            raise TypeError("responses must be a tuple of FixtureResponse")
        mapping = {}
        for response in responses:
            if response.input_digest in mapping:
                raise ValueError("duplicate fixture input digest")
            if response.result.metadata != self.metadata or response.result.schema_version != SCHEMA_VERSION:
                raise ValueError("fixture metadata/schema mismatch")
            if any(f.bbox is not None for f in response.result.observations()):
                raise ValueError("fixture adapter does not provide bounding boxes")
            mapping[response.input_digest] = response.result
        self._responses = MappingProxyType(mapping)

    def extract(self, document_bundle: DocumentBundle, schema_version: str) -> ExtractionResult:
        if not isinstance(document_bundle, DocumentBundle):
            raise TypeError("document_bundle must be DocumentBundle")
        if schema_version != SCHEMA_VERSION:
            raise ValueError("unsupported fixture extraction schema")
        if not document_bundle.synthetic:
            raise ValueError("fixture adapter accepts synthetic bundles only")
        try:
            result = self._responses[document_bundle.digest()]
        except KeyError as exc:
            raise ValueError("no fixture for this exact document bundle") from exc
        result.validate_binding(document_bundle, schema_version)
        return result
