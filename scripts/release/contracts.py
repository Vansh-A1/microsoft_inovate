#!/usr/bin/env python3
"""Export only the public OpenAPI schema; never serialize runtime configuration."""
import argparse,json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'apps/api'))
from app.core.config import Settings
from app.main import create_app

def main():
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');args=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='ap-openapi-') as private:
        schema=create_app(Settings('postgresql+psycopg://unused:unused@127.0.0.1/unused',{},Path(private))).openapi()
        text=json.dumps(schema,indent=2)+'\n';target=ROOT/'packages/api-client/openapi.json'
        if args.write:target.write_text(text)
        elif target.read_text()!=text:raise SystemExit('OpenAPI contract drift: export then regenerate and review the client.')
    print('Public OpenAPI contract matches.' if not args.write else 'Public OpenAPI schema exported.')
if __name__=='__main__':main()
