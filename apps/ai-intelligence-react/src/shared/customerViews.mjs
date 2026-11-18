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
