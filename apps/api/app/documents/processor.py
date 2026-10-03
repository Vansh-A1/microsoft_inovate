"""Immutable PDF/image derivatives. Coordinates describe the original displayed page."""
from dataclasses import asdict
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from app.documents.config import DocumentLimits

PROCESSOR_VERSION = 'document-processor-v1'


class DocumentFailure(Exception):
    def __init__(self, code, *, retryable=False):
        self.code, self.retryable = code, retryable
        super().__init__(code)


def sniff(content):
    if content.startswith(b'%PDF-'): return 'application/pdf'
    if content.startswith(b'\x89PNG\r\n\x1a\n'): return 'image/png'
    if content.startswith(b'\xff\xd8\xff'): return 'image/jpeg'
    raise DocumentFailure('UNSUPPORTED_CONTENT')


def metrics(image, text):
    import cv2
    import numpy as np
    cv2.setNumThreads(1)
    gray = np.asarray(image.convert('L'))
    # Defined measurements, not a model score or probability.
    return {'laplacian_variance': round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 4),
        'mean_luminance_0_255': round(float(gray.mean()), 4),
        'dark_pixel_fraction': round(float((gray < 20).mean()), 6),
        'light_pixel_fraction': round(float((gray > 245).mean()), 6),
        'native_text_characters': len(text.strip()),
        'native_text_characters_per_megapixel': round(len(text.strip()) / max(1, image.width * image.height) * 1_000_000, 4),
        'preview_width': image.width, 'preview_height': image.height}


def parse(content, limits=None):
    """Pure bounded parser, called in a child process in production."""
    import io
    import warnings
    import pymupdf as fitz
    from PIL import Image, ImageOps
    limits = limits or DocumentLimits()
    if len(content) > limits.maximum_bytes: raise DocumentFailure('DOCUMENT_SIZE_LIMIT')
    mime = sniff(content)
    pages = []
    total_text = total_spans = total_derived = 0
    def add(image, number, text, spans, transform, original_dimensions):
        nonlocal total_text, total_spans, total_derived
        total_text += len(text); total_spans += len(spans)
        if total_text > limits.maximum_text_chars or total_spans > limits.maximum_spans:
            raise DocumentFailure('TEXT_RESOURCE_LIMIT')
        image.thumbnail((limits.preview_long_edge, limits.preview_long_edge))
        output = io.BytesIO(); image.save(output, format='PNG')
        png = output.getvalue(); total_derived += len(png)
        if total_derived > limits.maximum_derived_bytes: raise DocumentFailure('DERIVED_RESOURCE_LIMIT')
        transform.update({'version': PROCESSOR_VERSION, 'original_dimensions': original_dimensions,
            'derived_dimensions': [image.width, image.height], 'crop': None,
            'scale': [image.width / original_dimensions[0], image.height / original_dimensions[1]],
            'bbox_convention': 'normalized_original_page'})
        quality = metrics(image, text)
        route = 'NATIVE_TEXT_AVAILABLE' if len(text.strip()) >= 80 else ('NATIVE_TEXT_LOW_COVERAGE' if text.strip() else 'VISUAL_REQUIRED')
        pages.append({'page': number, 'native_text': text, 'spans': spans, 'transform': transform,
            'quality': quality, 'route': route, 'page_sha256': hashlib.sha256(png).hexdigest(),
            'preview_base64': base64.b64encode(png).decode('ascii')})
    try:
        if mime == 'application/pdf':
            with fitz.open(stream=content, filetype='pdf') as pdf:
                if pdf.needs_pass: raise DocumentFailure('PASSWORD_PROTECTED')
                if not 1 <= len(pdf) <= limits.maximum_pages: raise DocumentFailure('PAGE_LIMIT')
                if pdf.embfile_count(): raise DocumentFailure('UNSAFE_EMBEDDED_CONTENT')
                for xref in range(1, pdf.xref_length()):
                    obj = pdf.xref_object(xref, compressed=False)
                    if any(token in obj for token in ('/JavaScript', '/JS', '/Launch', '/RichMedia', '/XFA')):
                        raise DocumentFailure('UNSAFE_ACTIVE_CONTENT')
                for i, page in enumerate(pdf):
                    rect = page.rect
                    if rect.width <= 0 or rect.height <= 0 or rect.width > 10000 or rect.height > 10000:
                        raise DocumentFailure('UNSAFE_PAGE_DIMENSIONS')
                    zoom = min(2, limits.preview_long_edge / max(rect.width, rect.height))
                    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False, annots=False)
                    image = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
                    text = page.get_text('text', sort=True)
                    spans = []
                    for block in page.get_text('dict', flags=fitz.TEXTFLAGS_TEXT)['blocks']:
                        for line in block.get('lines', []):
                            for span in line.get('spans', []):
                                box = fitz.Rect(span['bbox']) * page.rotation_matrix
                                coords = [box.x0 / rect.width, box.y0 / rect.height, box.x1 / rect.width, box.y1 / rect.height]
                                # Retain text; omit coordinates that overflow actual page bounds.
                                bbox = dict(zip(('x1','y1','x2','y2'), coords)) if all(0 <= v <= 1 for v in coords) else None
                                spans.append({'text': span['text'], 'bbox': bbox, 'font_size_points': span['size']})
                    add(image, i+1, text, spans, {'rotation_degrees': page.rotation,
                        'orientation_operation': 'PDF_DISPLAY_ROTATION', 'pdf_rotation_matrix': list(page.rotation_matrix)},
                        [rect.width, rect.height])
        else:
            Image.MAX_IMAGE_PIXELS = limits.maximum_pixels
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(content)) as check:
                    if check.width * check.height > limits.maximum_pixels: raise DocumentFailure('PIXEL_LIMIT')
                    if check.format != {'image/png':'PNG','image/jpeg':'JPEG'}[mime] or getattr(check, 'n_frames', 1) != 1:
                        raise DocumentFailure('UNSUPPORTED_IMAGE')
                    check.verify()
                with Image.open(io.BytesIO(content)) as source:
                    dims = [source.width, source.height]; orientation = source.getexif().get(274, 1)
                    derived = ImageOps.exif_transpose(source).convert('RGB')
                    add(derived, 1, '', [], {'rotation_degrees': {3:180,6:90,8:270}.get(orientation, 0),
                        'exif_orientation': orientation, 'orientation_operation': 'EXIF_TRANSPOSE',
                        'oriented_dimensions': [derived.width, derived.height], 'deskew_applied': False}, dims)
        return {'version': PROCESSOR_VERSION, 'detected_mime': mime, 'pages': pages}
    except DocumentFailure: raise
    except MemoryError: raise DocumentFailure('PARSER_RESOURCE_FAILURE') from None
    except (Image.DecompressionBombError, Image.DecompressionBombWarning): raise DocumentFailure('PIXEL_LIMIT') from None
    except Exception: raise DocumentFailure('CORRUPT_DOCUMENT') from None


class DocumentProcessor:
    def __init__(self, limits=None): self.limits = limits or DocumentLimits()

    def process(self, path):
        # Parsers receive no application credentials or inherited provider tokens.
        env = {'PATH':os.defpath,'LANG':'C.UTF-8','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','OMP_THREAD_LIMIT':'1',
            'PYTHONPATH':str(Path(__file__).resolve().parents[2])}
        try:
            result = subprocess.run([sys.executable, '-m', 'app.documents.processor', str(Path(path).resolve()),
                json.dumps(asdict(self.limits))], capture_output=True, env=env,
                timeout=self.limits.parser_timeout_seconds + 2, check=False)
        except subprocess.TimeoutExpired: raise DocumentFailure('PARSER_TIMEOUT') from None
        if result.returncode or len(result.stdout) > self.limits.maximum_derived_bytes * 2:
            raise DocumentFailure('PARSER_RESOURCE_FAILURE')
        try: data = json.loads(result.stdout)
        except (ValueError, UnicodeError): raise DocumentFailure('PARSER_RESOURCE_FAILURE') from None
        if 'failure' in data: raise DocumentFailure(data['failure'])
        return data


def main():
    import resource
    limits = DocumentLimits(**json.loads(sys.argv[2]))
    resource.setrlimit(resource.RLIMIT_AS, (limits.parser_memory_bytes, limits.parser_memory_bytes))
    resource.setrlimit(resource.RLIMIT_CPU, (limits.parser_timeout_seconds, limits.parser_timeout_seconds))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    try: data = parse(Path(sys.argv[1]).read_bytes(), limits)
    except DocumentFailure as exc: data = {'failure': exc.code}
    print(json.dumps(data, allow_nan=False))


if __name__ == '__main__': main()
