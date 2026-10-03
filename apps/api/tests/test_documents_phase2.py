from dataclasses import replace
from pathlib import Path
import asyncio
import base64
import hashlib
from io import BytesIO
from uuid import uuid4
import pytest
import pymupdf
from PIL import Image
from app.core.config import ROOT
from app.core.identity import Identity
from app.documents.config import DocumentLimits
from app.documents.processor import DocumentProcessor, DocumentFailure, parse, sniff
from app.documents.malware import UnconfiguredMalwareAdapter
from app.integrations.storage import LocalStorage

CORPUS=ROOT/'data/documents_phase2'


def test_native_pdf_actual_original_spans_pages_and_hash():
    content=(CORPUS/'vendor_multipage.pdf').read_bytes();sha=hashlib.sha256(content).hexdigest()
    result=parse(content)
    assert [p['page'] for p in result['pages']]==[1,2]
    for page in result['pages']:
        assert 'P2-INV-00128' in page['native_text']
        assert page['route']=='NATIVE_TEXT_AVAILABLE'
        assert hashlib.sha256(base64.b64decode(page['preview_base64'])).hexdigest()==page['page_sha256']
        assert page['transform']['crop'] is None
        assert all(0<=v<=1 for span in page['spans'] if span['bbox'] for v in span['bbox'].values())
    assert hashlib.sha256(content).hexdigest()==sha


@pytest.mark.parametrize('name,code',[('password_protected.pdf','PASSWORD_PROTECTED'),('corrupt.pdf','CORRUPT_DOCUMENT')])
def test_unsafe_pdf(name,code):
    with pytest.raises(DocumentFailure,match=code):parse((CORPUS/name).read_bytes())


def test_sniff_and_binary_size_limits():
    for bad in (b'<html>pretend.pdf</html>',b'MZ\x00',b'GIF89a'):
        with pytest.raises(DocumentFailure,match='UNSUPPORTED'):sniff(bad)
    content=(CORPUS/'receipt_scan.png').read_bytes()
    assert parse(content,replace(DocumentLimits(),maximum_bytes=len(content)))['detected_mime']=='image/png'
    with pytest.raises(DocumentFailure,match='DOCUMENT_SIZE_LIMIT'):parse(content,replace(DocumentLimits(),maximum_bytes=len(content)-1))


def test_page_and_pixel_boundaries():
    d=pymupdf.open()
    for _ in range(30):d.new_page(width=10,height=10)
    assert len(parse(d.tobytes())['pages'])==30
    d.new_page(width=10,height=10)
    with pytest.raises(DocumentFailure,match='PAGE_LIMIT'):parse(d.tobytes())
    f=BytesIO();Image.new('RGB',(20,20),'white').save(f,format='PNG');content=f.getvalue()
    assert parse(content,replace(DocumentLimits(),maximum_pixels=400))['pages'][0]['page']==1
    with pytest.raises(DocumentFailure,match='PIXEL_LIMIT'):parse(content,replace(DocumentLimits(),maximum_pixels=399))


def test_photo_orientation_and_real_visual_route():
    p=parse((CORPUS/'receipt_photo.jpg').read_bytes())['pages'][0]
    assert p['transform']['exif_orientation']==6 and p['transform']['rotation_degrees']==90
    assert p['transform']['original_dimensions']==[1584,1224]
    assert p['transform']['derived_dimensions']==[1224,1584]
    assert p['route']=='VISUAL_REQUIRED' and not p['spans']
    assert p['quality']['laplacian_variance']>=0
    assert parse((CORPUS/'receipt_scan.pdf').read_bytes())['pages'][0]['route']=='VISUAL_REQUIRED'


def test_pdf_rotation_coordinate_mapping():
    d=pymupdf.open(stream=(CORPUS/'receipt_native.pdf').read_bytes(),filetype='pdf');d[0].set_rotation(90)
    p=parse(d.tobytes())['pages'][0]
    assert p['transform']['rotation_degrees']==90
    s=next(s for s in p['spans'] if 'Receipt number' in s['text'])
    assert s['bbox']['x1']>.5


def test_active_pdf_is_rejected():
    d=pymupdf.open(stream=(CORPUS/'receipt_native.pdf').read_bytes(),filetype='pdf')
    xref=d.get_new_xref();d.update_object(xref,r'<< /S /JavaScript /JS (app.alert\(1\)) >>')
    d.xref_set_key(d.pdf_catalog(),'OpenAction',f'{xref} 0 R')
    with pytest.raises(DocumentFailure,match='UNSAFE_ACTIVE_CONTENT'):parse(d.tobytes())


def test_isolated_processor_real_pdf(tmp_path):
    p=tmp_path/'source';p.write_bytes((CORPUS/'vendor_native.pdf').read_bytes())
    data=DocumentProcessor().process(p)
    assert data['pages'][0]['route']=='NATIVE_TEXT_AVAILABLE'
    p.write_bytes(b'%PDF-1.7 corrupt')
    with pytest.raises(DocumentFailure,match='CORRUPT'):DocumentProcessor().process(p)


def test_storage_incremental_hash_bound_and_scope(tmp_path):
    ctx=Identity(uuid4(),uuid4(),uuid4(),frozenset({'FINANCE_REVIEWER'}),'Test')
    store=LocalStorage(tmp_path)
    async def chunks():
        for b in (b'original',b' bytes'):yield b
    key,sha,size=asyncio.run(store.ingest(ctx,chunks(),maximum=14))
    assert store.get(ctx,key)==b'original bytes' and sha==hashlib.sha256(b'original bytes').hexdigest() and size==14
    with pytest.raises(ValueError):asyncio.run(store.ingest(ctx,chunks(),maximum=13))
    assert len(list(tmp_path.rglob('*.part')))==0
    other=Identity(uuid4(),ctx.legal_entity_id,ctx.actor_id,ctx.roles,'Other')
    with pytest.raises(ValueError):store.get(other,key)


def test_scanner_unknown_never_clean():
    assert UnconfiguredMalwareAdapter().scan('unused').status=='NOT_CONFIGURED'


def test_configuration_is_typed_and_bounded():
    with pytest.raises(ValueError):DocumentLimits(maximum_bytes=True)
    with pytest.raises(ValueError):DocumentLimits(maximum_pages=31)
    with pytest.raises(ValueError):DocumentLimits(preview_long_edge=9000)
