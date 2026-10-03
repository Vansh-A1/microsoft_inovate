"""Bound request memory before JSON/multipart parsing, including chunked bodies."""
from uuid import uuid4
from starlette.responses import JSONResponse


class BoundedBody:
    def __init__(self,app,maximum=2300000):self.app,self.maximum=app,maximum

    async def __call__(self,scope,receive,send):
        if scope['type']!='http' or scope['method'] in ('GET','HEAD'):
            await self.app(scope,receive,send);return
        # Binary originals stream through the authenticated storage bound; structured limits remain unchanged.
        if scope['method']=='POST' and scope.get('path','').startswith('/api/v1/uploads/') and scope['path'].endswith('/bytes'):
            await self.app(scope,receive,send);return
        messages=[];size=0
        while True:
            message=await receive()
            if message['type']=='http.disconnect':return
            size+=len(message.get('body',b''))
            if size>self.maximum:
                response=JSONResponse(status_code=413,content={'error':{'code':'REQUEST_TOO_LARGE','message':'Request exceeds the structured intake limit.','details':{},'retryable':False},'correlation_id':str(uuid4())})
                await response(scope,receive,send);return
            messages.append(message)
            if not message.get('more_body',False):break
        async def replay():
            if messages:return messages.pop(0)
            return await receive()
        await self.app(scope,replay,send)
