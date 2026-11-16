// Display-only labels. Stored record values, identities and API parameters stay unchanged.
export const RECORD_LABELS={'Exclude validation':'Business requests','Synthetic demo only':'Illustrative requests','All records':'All requests'};
export const PROFILES={'motor.demo':'Motor business user','demo.engineer':'Data specialist'};
export const profileName=value=>PROFILES[value]||value||'Not specified';
export const profileReference=value=>Object.entries(PROFILES).find(([,label])=>label===value)?.[0]||value;
export const statusLabels={NEW:'New',TRIAGED:'Reviewed',IN_PROGRESS:'In progress',WAITING_FOR_BU:'Awaiting business response',RESOLVED:'Resolved',CLOSED:'Closed'};
export const categoryLabels={REPORT_REQUEST:'Report or dashboard',DATA_EXTRACT:'Data extract',DATA_ISSUE:'Data issue',ACCESS_REQUEST:'Access request',ENHANCEMENT:'Enhancement',OTHER:'Other'};
export function displayMeta(meta){return {...meta,status_labels:{...meta.status_labels,...statusLabels},category_labels:{...meta.category_labels,...categoryLabels}};}
export function recordTitle(value){return String(value||'').replace(/^(?:\s*\[(?:demo|sample|mock|test|validation|synthetic)\]\s*)+/i,'');}
export function recordText(value){
  return recordTitle(value)
    .replaceAll('Synthetic demonstration request. No real business data or delivery is implied.','Illustrative request for the data service workflow. No production request or delivery is implied.')
    .replaceAll('Synthetic demo: supports monthly review.','Supports the monthly review using illustrative data.')
    .replaceAll('Synthetic demonstration resolution. No actual report has been delivered.','Illustrative resolution. No report delivery is implied.')
    .replaceAll('Synthetic example: ','')
    .replaceAll('DEMO-OUTPUT: ','Illustrative reference: ')
    .replaceAll('Demo Data Team','Data Team');
}
export function formatDate(value){
  if(!value)return 'Not specified';
  const date=new Date(String(value).slice(0,10)+'T00:00:00');
  return Number.isNaN(date.getTime())?'Not specified':date.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});
}
export function formatDateTime(value){
  if(!value)return 'Not specified';
  const date=new Date(value);
  return Number.isNaN(date.getTime())?'Not specified':date.toLocaleString('en-GB',{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'});
}
export function formatNumber(value){return value!==null&&value!==undefined&&Number.isFinite(Number(value))?Number(value).toLocaleString('en-GB'):'Unavailable';}
export function sourceLabel(value){
  const text=String(value||'');
  if(/unavailable|response rejected/i.test(text))return 'Calculated explanation · AI assistance unavailable';
  if(text.startsWith('AI-curated'))return text.includes('engagement')?'AI-assisted engagement brief':'AI-assisted explanation';
  if(text.startsWith('Cortex-assisted'))return 'AI-assisted answer';
  if(text.includes('Cortex disabled'))return 'Calculated answer · AI assistance off';
  if(text.startsWith('Calculated answer'))return 'Calculated answer';
  if(text.startsWith('Calculated'))return 'Calculated overview';
  if(text.startsWith('Deterministic')||text.startsWith('Rule-based'))return 'Business-rules explanation';
  return text;
}
export function errorLabel(value){
  const text=String(value||'');
  if(text.includes('Snowflake is unavailable')||text.includes('source validation failed'))return 'We could not connect to the reporting data. Please refresh and try again.';
  return text.replaceAll('Enter a demo identity.','Choose a working profile to continue.');
}
