"""Optional verified user-space CPU OCR for the Ubuntu 24.04 development host.

No sudo/system package install; only extract four pinned packages inside runtime.
English OCR data is a small explicitly authorized CPU OCR asset, not VLM weights.
"""
from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess

ROOT=Path(__file__).resolve().parents[2]
PINS={
    'tesseract-ocr=5.3.4-1build5':('tesseract-ocr_5.3.4-1build5_amd64.deb','2dfac382d77215aee0c3de4a2a2205505d5f2195e72e79b54ad32154fc08da77'),
    'libtesseract5=5.3.4-1build5':('libtesseract5_5.3.4-1build5_amd64.deb','a38438115dc203b5abc1e6a6b24eb5273ba82161a11faa2f619bf5f7622efb14'),
    'liblept5=1.82.0-3build4':('liblept5_1.82.0-3build4_amd64.deb','c2bb81d58f032b09917c0d50994cce905287a1596304a4e99681a03601456ea8'),
    'tesseract-ocr-eng=1:4.1.0-2':('tesseract-ocr-eng_1%3a4.1.0-2_all.deb','b1996b3113c78663f4dd16cf18aa1f288b07e9624f8d4a0ddbd7d9b52a234ba7'),
}


def main():
    if platform.system()!='Linux' or platform.machine()!='x86_64':raise SystemExit('Optional OCR bootstrap is supported only on the documented Ubuntu x86_64 host.')
    root=ROOT/'runtime/tools/ocr';packages=root/'packages';packages.mkdir(parents=True,exist_ok=True)
    for package,(name,sha) in PINS.items():
        path=packages/name
        if not path.exists():subprocess.run(['apt-get','download',package],cwd=packages,check=True,timeout=120)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=sha:raise SystemExit('OCR package checksum mismatch; nothing configured.')
        subprocess.run(['dpkg-deb','-x',str(path),str(root)],check=True,timeout=30)
    executable=root/'usr/bin/tesseract';data=root/'usr/share/tesseract-ocr/5/tessdata';library=root/'usr/lib/x86_64-linux-gnu'
    checked=subprocess.run([str(executable),'--version'],env=dict(os.environ,LD_LIBRARY_PATH=str(library)),capture_output=True,check=True,timeout=5)
    if not checked.stdout.startswith(b'tesseract 5.3.4') or not (data/'eng.traineddata').is_file():raise SystemExit('OCR runtime verification failed.')
    settings=ROOT/'runtime/dev/settings.json'
    if settings.exists():
        value=json.loads(settings.read_text());providers=value.setdefault('document_providers',{})
        providers.update(ocr_executable=str(executable),ocr_data_directory=str(data),ocr_library_directory=str(library))
        settings.write_text(json.dumps(value,indent=2)+'\n');os.chmod(settings,0o600)
    print('Verified local Tesseract 5.3.4 and English OCR configured; VLM remains external.')


if __name__=='__main__':main()
