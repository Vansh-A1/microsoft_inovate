"""CPU-only HTTP transport to the isolated real TypeLLM client process."""
import os
from types import SimpleNamespace
import httpx
from app.documents.processor import DocumentFailure


class GatewayTransport:
    def __init__(self,config):
        self.config=config
        self.provider_metadata=None

    def headers(self):
        token=os.environ.get(self.config.gateway_token_env,'')
        if not token:raise DocumentFailure('GATEWAY_AUTH_NOT_CONFIGURED')
        return {'Authorization':'Bearer '+token}

    def generate(self,**kwargs):
        try:
            response=httpx.post(self.config.endpoint.rstrip('/')+'/generate',headers=self.headers(),
                json={'model':self.config.model,**kwargs},timeout=kwargs['timeout'],follow_redirects=False)
            if response.status_code in (408,504):raise DocumentFailure('PROVIDER_TIMEOUT',retryable=True)
            if response.status_code in (401,403):raise DocumentFailure('GATEWAY_AUTH_FAILED')
            if response.status_code>=500:raise DocumentFailure('PROVIDER_UNAVAILABLE',retryable=True)
            if response.status_code!=200 or len(response.content)>256*1024:raise DocumentFailure('PROVIDER_RESPONSE_INVALID')
            data=response.json()
            if set(data)!={'result','provider_metadata'} or not isinstance(data['provider_metadata'],dict):raise ValueError()
            metadata=data['provider_metadata']
            if metadata.get('served_model')!=self.config.model or metadata.get('typellm')!='0.5.1':raise ValueError()
            if self.config.model_revision and metadata.get('model_revision')!=self.config.model_revision:raise ValueError()
            allowed={'served_model','model_source','model_revision','precision','python','typellm','transformers','sglang','torch','cuda_runtime','bridge','cache_isolation'}
            if set(metadata)-allowed or any(not isinstance(v,str) or len(v)>200 for v in metadata.values()):raise ValueError()
            if self.provider_metadata is not None and self.provider_metadata!=metadata:raise ValueError()
            self.provider_metadata=metadata
            return SimpleNamespace(result=data['result'])
        except DocumentFailure:raise
        except httpx.TimeoutException:raise DocumentFailure('PROVIDER_TIMEOUT',retryable=True) from None
        except httpx.RequestError:raise DocumentFailure('PROVIDER_UNAVAILABLE',retryable=True) from None
        except (ValueError,KeyError,TypeError):raise DocumentFailure('PROVIDER_RESPONSE_INVALID') from None

    def health(self):
        try:
            response=httpx.get(self.config.endpoint.rstrip('/')+'/health',headers=self.headers(),timeout=2,follow_redirects=False)
            data=response.json() if response.status_code==200 and len(response.content)<8192 else {}
            if data.get('status')=='AVAILABLE' and data.get('served_model')==self.config.model:
                if self.config.model_revision and data.get('model_revision')!=self.config.model_revision:return {'status':'MODEL_MISMATCH'}
                return {k:str(data[k])[:200] for k in ('status','model_source','model_revision','precision','gpu') if k in data}
        except (DocumentFailure,httpx.HTTPError,ValueError,KeyError):pass
        return {'status':'UNAVAILABLE'}
