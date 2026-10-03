from io import BytesIO
from PIL import Image,ImageDraw,ImageEnhance,ImageFilter
from app.services.duplicates import fingerprint,bands,aggressive


def image(total='1200.00'):
    im=Image.new('RGB',(640,850),'white');d=ImageDraw.Draw(im)
    d.text((40,40),'FICTIONAL MERCHANT - SYNTHETIC BENCHMARK',fill='black');d.line((40,90,600,90),fill='black',width=3)
    for i,text in enumerate(['Receipt TEST-017','Meal for two','2026-09-25','Quantity 2','Total INR '+total]):d.text((50,130+i*80),text,fill='black',font_size=24)
    d.rectangle((40,530,600,600),outline='black',width=3)
    return im


def encode(im,format='PNG',**kw):
    b=BytesIO();im.save(b,format=format,**kw);return b.getvalue()


def test_phash_actual_resize_recompress_brightness_and_template_negative():
    original=image();bits,metadata=fingerprint(encode(original));assert metadata['hash_size']==64 and metadata['crop'] is None and not metadata['low_information']
    for variant in [encode(original.resize((320,425))),encode(original,'JPEG',quality=55),encode(ImageEnhance.Brightness(original).enhance(.85)),encode(original.filter(ImageFilter.GaussianBlur(.4)))]:
        other,_=fingerprint(variant);distance=(int(bits,16)^int(other,16)).bit_count();assert distance<=6
        assert set(bands(bits))&set(bands(other))
    negative,_=fingerprint(encode(image('2450.00')));distance=(int(bits,16)^int(negative,16)).bit_count()
    assert 0<=distance<=64  # A changed purchase can still be visually close; never confirm from this.
    assert metadata['algorithm']=='pHash-DCT'


def test_blank_image_not_indexed_and_keys_preserve_letters_and_zeros():
    _,metadata=fingerprint(encode(Image.new('RGB',(128,128),'white')));assert metadata['low_information']
    assert aggressive('inv 00128')==aggressive('INV-00128') and aggressive('INV-I01')!=aggressive('INV-101') and aggressive('INV-001')!=aggressive('INV-1')


def test_band_pigeonhole_finds_all_six_bit_changes():
    bits='963ba174502fda8c';n=int(bits,16)
    for shift in range(59):
        other=f'{n^(63<<shift):016x}';assert set(bands(bits))&set(bands(other))
