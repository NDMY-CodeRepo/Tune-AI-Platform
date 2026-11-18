// Presentation only: combine the existing aggregate cells, never the bounded worklist.
export function customerSegments(segments,field){
  if(!['RETENTION_RISK_BAND','LIFETIME_VALUE_BAND'].includes(field))throw new Error('Unsupported customer breakdown');
  if(!Array.isArray(segments)||!segments.length)return [];
  const totals=new Map();
  for(const row of segments){
    if(row.CUSTOMERS===null||row.CUSTOMERS===undefined||typeof row.CUSTOMERS==='boolean'||String(row.CUSTOMERS).trim()===''||!Number.isInteger(Number(row.CUSTOMERS))||Number(row.CUSTOMERS)<0)return [];
    const label=row[field]||'Not specified';
    totals.set(label,(totals.get(label)||0)+Number(row.CUSTOMERS));
  }
  const order=field==='RETENTION_RISK_BAND'?['High','Medium','Low']:['Top','High','Medium','Low'];
  const rank=label=>order.includes(label)?order.indexOf(label):order.length;
  return [...totals].map(([label,count])=>({label,count})).sort((a,b)=>rank(a.label)-rank(b.label)||a.label.localeCompare(b.label));
}

// The server has already evaluated the renewal window; missing is not false.
export function renewalTiming(upcoming){
  return upcoming===true?'Upcoming renewal':upcoming===false?'Outside renewal window':'Timing unavailable';
}

export function recordedHoldings(row){
  const products=['Motor','Travel'];
  const held=products.filter(name=>row['HOLDS_'+name.toUpperCase()]==='Yes');
  const unknown=products.filter(name=>!['Yes','No'].includes(row['HOLDS_'+name.toUpperCase()]));
  return (held.join(' + ')||'No Motor or Travel cover on record')+(unknown.length?` · ${unknown.join(' / ')} holdings unavailable`:'');
}

// Display-only wording for existing evidence/actions; unknown text is kept intact.
export function friendlyCustomerText(text){
  return text
    .replace(/^Recommended retention action: Standard relationship maintenance\.$/,'Continue regular relationship care.')
    .replace(/^Recommended retention action: (.+)\.$/,'Retention next step: $1.')
    .replace(/^Customer value is MYR (.+) \((.+) band\)\.$/,'Customer value: RM $1 · $2 value segment.')
    .replace(/^Retention risk is (.+); source score .+\.$/,'$1 retention risk.')
    .replace(/^Prepare a human-reviewed (.+) needs discussion through (.+)\.$/,'Arrange a conversation through $2 to understand whether $1 meets the customer’s needs. Review their existing cover and suitability before making an offer.')
    .replace(/^Review retention needs first, then consider a (.+) discussion\.$/,'Start with the customer’s retention needs. Once these have been reviewed, consider a conversation about $1. Confirm existing cover and suitability before making an offer.');
}
