"""Safe structured request telemetry: route templates, no URL/query/body/token/exception text."""
import json
import logging
import time
from starlette.responses import JSONResponse
log=logging.getLogger('ap.release')
if not log.handlers:log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)
log.propagate=False

def mount(app):
    @app.middleware('http')
    async def telemetry(request,call_next):
        started=time.monotonic()
        try:response=await call_next(request)
        except Exception:
            # Business sessions have unwound/rolled back; never log provider payloads.
            response=JSONResponse(status_code=503,content={'error':{'code':'INTERNAL_UNAVAILABLE','message':'The operation could not complete. Retry with the same operation key after checking system health.','details':{},'retryable':True},'correlation_id':getattr(request.state,'correlation','')})
        route=getattr(request.scope.get('route'),'path','UNMATCHED')
        log.info(json.dumps({'event':'http_request','method':request.method,'route':route,'status':response.status_code,'duration_ms':round((time.monotonic()-started)*1000,3),'correlation_id':getattr(request.state,'correlation',None)},sort_keys=True))
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='same-origin'
        response.headers['Cache-Control']='private, no-store'
        return response
