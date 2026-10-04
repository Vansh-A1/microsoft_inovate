from types import SimpleNamespace
import subprocess
import pytest
from app.documents.malware import ClamAVMalwareAdapter,configured_scanner,scanner_health

@pytest.mark.parametrize('exit_code,stdout,expected',[(0,b'Scanned files: 1\n','CLEAN'),(0,b'Scanned files: 0\n','ERROR'),
    (0,b'Nothing scanned','ERROR'),(1,b'Scanned files: 1\n','INFECTED'),(2,b'Cannot load signatures','ERROR')])
def test_scanner_result_requires_one_actual_scanned_file(monkeypatch,tmp_path,exit_code,stdout,expected):
    engine=tmp_path/'scanner';engine.write_text('synthetic executable contract fixture')
    original=tmp_path/'original';original.write_bytes(b'private original')
    calls=[]
    def run(args,**kw):
        calls.append((args,kw))
        return SimpleNamespace(returncode=0,stdout=b'ClamAV 1.4.3/definitions',stderr=b'') if args[-1]=='--version' else SimpleNamespace(returncode=exit_code,stdout=stdout,stderr=b'')
    monkeypatch.setattr(subprocess,'run',run)
    scanner=ClamAVMalwareAdapter(engine);result=scanner.scan(original)
    assert result.status==expected and result.version=='1.4.3'
    assert calls[-1][0][-1]==str(original) and 'shell' not in calls[-1][1]
    assert calls[-1][1]['timeout']==30 and calls[-1][1]['env']=={'PATH':__import__('os').defpath,'LANG':'C','LC_ALL':'C'}

def test_scanner_missing_configuration_or_invalid_path_never_clean(monkeypatch):
    monkeypatch.delenv('AP_MALWARE_SCANNER_EXECUTABLE',raising=False)
    assert configured_scanner().scan('unused').status=='NOT_CONFIGURED' and scanner_health()=='NOT_CONFIGURED'
    monkeypatch.setenv('AP_MALWARE_SCANNER_EXECUTABLE','relative-not-authorized')
    assert configured_scanner().scan('unused').status=='ERROR' and scanner_health()=='UNAVAILABLE'

def test_scanner_timeout_redacts_engine_output(monkeypatch,tmp_path):
    engine=tmp_path/'scanner';engine.touch();original=tmp_path/'original';original.touch()
    def run(args,**kw):
        if args[-1]=='--version':return SimpleNamespace(stdout=b'ClamAV 1.4.3/definitions')
        raise subprocess.TimeoutExpired(args,30,output=b'confidential invoice contents')
    monkeypatch.setattr(subprocess,'run',run)
    result=ClamAVMalwareAdapter(engine).scan(original)
    assert result.status=='ERROR' and 'confidential' not in str(result)
