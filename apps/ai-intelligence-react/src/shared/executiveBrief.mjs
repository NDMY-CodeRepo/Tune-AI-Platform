// Presentation only. Use the existing SQL aggregates and comparison coverage;
// never infer causes, forecasts or missing plan amounts.
export function managementBrief(rows,money,pct){
  const available=value=>value!==null&&value!==undefined&&value!==''&&Number.isFinite(Number(value));
  const comparable=row=>row&&row.KEY_COUNT>0&&row.MISSING_ACTUAL===0&&row.MISSING_PLAN===0&&
    ['GWP','PLAN_GWP','GWP_VARIANCE'].every(field=>available(row[field]));
  const total=rows.find(row=>row.LEVEL==='TOTAL');
  const groups=level=>rows.filter(row=>row.LEVEL===level&&comparable(row)).sort((a,b)=>a.GWP_VARIANCE-b.GWP_VARIANCE);
  const line=groups('LINE')[0],channel=groups('CHANNEL')[0];
  const gap=row=>`${money(Math.abs(row.GWP_VARIANCE))}${available(row.GWP_VARIANCE_PCT)?` (${pct(Math.abs(row.GWP_VARIANCE_PCT))})`:''}`;
  const contributors=[line,channel].filter(Boolean).map(row=>{
    const name=row.LEVEL==='LINE'?row.LINE_OF_BUSINESS:`The ${row.DISTRIBUTION_CHANNEL} channel`;
    return row.GWP_VARIANCE===0?`${name} is on its premium target.`:
      `${name} is ${gap(row)} ${row.GWP_VARIANCE<0?'below':'above'} its premium target.`;
  });
  if(!comparable(total))return {
    finding:'We cannot reliably compare total premiums with the business plan for this selection.',
    contributors,
    action:'Confirm that actual and planned figures cover the same reporting periods and business areas before drawing a conclusion.'
  };
  const finding=total.GWP_VARIANCE===0?'Gross written premium is on plan for the selected period.':
    `Gross written premium is ${gap(total)} ${total.GWP_VARIANCE<0?'below':'above'} the business plan for the selected period.`;
  const focus=[line?.GWP_VARIANCE<0?line.LINE_OF_BUSINESS:null,channel?.GWP_VARIANCE<0?`the ${channel.DISTRIBUTION_CHANNEL} channel`:null].filter(Boolean);
  const action=focus.length?`Start with ${focus.join(' and ')}. Ask the business owners to review the premium gaps, establish the reasons and agree on next steps.`:
    total.GWP_VARIANCE<0?'Review the premium shortfall with the business owners. Confirm which areas need attention and agree on next steps.':
    'Review these results with the business owners to confirm whether any follow-up is needed. A positive overall result can still include areas below plan.';
  return {finding,contributors,action};
}
