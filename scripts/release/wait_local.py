#!/usr/bin/env python3
import time,urllib.request
for attempt in range(30):
    try:
        for url in ['http://127.0.0.1:8000/api/v1/health/ready','http://127.0.0.1:3000/health']:
            with urllib.request.urlopen(url,timeout=2) as response:assert response.status==200
        break
    except Exception:time.sleep(1)
else:raise SystemExit('Owned local app failed readiness within 30 attempts.')
