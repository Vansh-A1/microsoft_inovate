"""Versioned, bounded CPU document settings. No GPU requirement on clients."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentLimits:
    maximum_bytes: int = 25 * 1024 * 1024
    maximum_pages: int = 30
    maximum_pixels: int = 40_000_000
    preview_long_edge: int = 1800
    maximum_text_chars: int = 300_000
    maximum_spans: int = 20_000
    maximum_derived_bytes: int = 100 * 1024 * 1024
    parser_timeout_seconds: int = 30
    parser_memory_bytes: int = 1536 * 1024 * 1024
    upload_lifetime_seconds: int = 3600
    upload_receive_timeout_seconds: int = 60
    malware_required: bool = False

    def __post_init__(self):
        for name, value in vars(self).items():
            if name == 'malware_required':
                if type(value) is not bool: raise ValueError('malware_required must be boolean')
            elif type(value) is not int or value < 1: raise ValueError(f'{name} must be positive integer')
        if self.maximum_pages > 30: raise ValueError('extraction-v1 supports at most 30 pages')
        if self.preview_long_edge > 3000: raise ValueError('Bound preview resolution to 3000 pixels')


@dataclass(frozen=True)
class ProviderSettings:
    endpoint: str | None = None
    model: str | None = None
    tokenizer_path: str | None = None
    timeout_seconds: int = 30
    maximum_rows: int = 200
    maximum_calls: int = 32
    ocr_executable: str | None = None
    ocr_data_directory: str | None = None
    ocr_library_directory: str | None = None

    def __post_init__(self):
        if not 1 <= self.timeout_seconds <= 120: raise ValueError('Provider timeout must be bounded')
        if not 1 <= self.maximum_rows <= 200: raise ValueError('Rows must fit extraction-v1')
        if not 1 <= self.maximum_calls <= 256: raise ValueError('Provider call budget must be bounded')
        if bool(self.endpoint) != bool(self.model): raise ValueError('Endpoint and model must be configured together')
        if self.endpoint:
            from urllib.parse import urlparse
            u = urlparse(self.endpoint)
            if u.scheme not in ('http', 'https') or not u.hostname or u.username or u.password or u.query or u.fragment:
                raise ValueError('Use a configured HTTP endpoint without embedded credentials')
