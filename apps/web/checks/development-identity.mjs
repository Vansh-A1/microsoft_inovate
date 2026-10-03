import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {serverIdentityToken} from '../src/lib/development-identity.ts';

test('a supplied demo cookie has authority only when demo identities are explicitly enabled',async()=>{
 const keys=['AP_ENABLE_DEMO_IDENTITIES','AP_IDENTITY_FILE','AP_DEV_TOKEN'];
 const previous=Object.fromEntries(keys.map(k=>[k,process.env[k]]));
 const directory=await mkdtemp(path.join(tmpdir(),'ap-identity-check-'));
 try{
  process.env.AP_IDENTITY_FILE=path.join(directory,'synthetic.json');process.env.AP_DEV_TOKEN='SYNTHETIC-DEFAULT';
  await writeFile(process.env.AP_IDENTITY_FILE,JSON.stringify({identities:{'SYNTHETIC-MANAGER':{label:'Synthetic manager',actor_id:'synthetic-actor',roles:['MANAGER']}}}),{mode:0o600});
  delete process.env.AP_ENABLE_DEMO_IDENTITIES;
  assert.equal(await serverIdentityToken('Synthetic manager'),'SYNTHETIC-DEFAULT');
  process.env.AP_ENABLE_DEMO_IDENTITIES='0';assert.equal(await serverIdentityToken('Synthetic manager'),'SYNTHETIC-DEFAULT');
  process.env.AP_ENABLE_DEMO_IDENTITIES='1';assert.equal(await serverIdentityToken('Synthetic manager'),'SYNTHETIC-MANAGER');
  assert.equal(await serverIdentityToken('Unconfigured CFO'),'SYNTHETIC-DEFAULT');
  assert.equal(await serverIdentityToken(),'SYNTHETIC-DEFAULT');
 }finally{
  for(const k of keys){if(previous[k]===undefined)delete process.env[k];else process.env[k]=previous[k];}
  await rm(directory,{recursive:true,force:true});
 }
});
