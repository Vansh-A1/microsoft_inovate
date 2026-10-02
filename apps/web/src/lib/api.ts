import type { components } from './api-schema';
export type Canonical=components['schemas']['Canonical'];
export type Case={job:{id:string;state:string;stage:string;attempts:number;maximum_attempts:number;last_error:string|null}|null;id:string;branch:string;version:number;processing_state:string;decision:string|null;eligible:boolean;latest_evaluation_id:string|null;created_at:string;versions:{version:number;payload:Canonical;digest:string;author_id:string;reason:string;created_at:string}[]};
export type Evidence={id:string;reference:{kind:string;record_id:string;record_version:number|string;field_path:string|null}};
export type Rule={rule_id:string;version:string;status:string;decision_effect:string;reason:string;observed:unknown;expected:unknown;tolerance:string|null;evidence:Evidence[]};
export type Evaluation={evaluation_id:string;transaction_id:string;transaction_version:number;decision:string;completeness:string;eligible:boolean;current_eligible:boolean;model_status:string;reference_snapshot_id:string;ruleset_version:string;evaluated_at:string;rules:Rule[];next_actions:string[]};
export type QueueCase={id:string;transaction_id:string;evaluation_id:string;decision:string;branch:string;reasons:string[];created_at:string};
export type Batch={id:string;filename:string;state:string;row_count:number;valid_count:number;invalid_count:number;rows:{id:string;sheet:string;row_number:number;raw_values:unknown;errors:{field:string;message:string}[];transaction_id:string|null}[]};
export async function api<T>(path:string,options?:RequestInit):Promise<T>{
 const response=await fetch('/api/'+path,{...options,cache:'no-store'});
 const data=await response.json();if(!response.ok)throw new Error(data.error?.message||`Request failed (${response.status})`);return data as T;
}
export function mutate<T>(path:string,body:unknown,key:string){return api<T>(path,{method:'POST',headers:{'Content-Type':'application/json','Idempotency-Key':key},body:JSON.stringify(body)})}
