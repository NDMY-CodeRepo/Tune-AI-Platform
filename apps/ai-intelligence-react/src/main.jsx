import React,{useState,useEffect,useMemo} from 'react';

import {createRoot} from 'react-dom/client';

import {BarChart3,Users,Target,RefreshCw,Sparkles,Layers,Shield,FileText,Percent,ArrowDownRight,ArrowUpRight,ArrowRight,CalendarDays,ChevronRight,ChevronDown,Menu,X,LoaderCircle,CheckCircle2,Info,Search,UserRound,SlidersHorizontal,ArrowUpDown,Plane} from 'lucide-react';

import {ResponsiveContainer,LineChart,Line,CartesianGrid,XAxis,YAxis,Tooltip,BarChart,Bar,Cell,ReferenceLine,PieChart,Pie} from 'recharts';

import './styles.css';
import Sidebar,{Information} from './shared/Sidebar';
import {sourceLabel,errorLabel,formatDate,formatNumber} from './shared/presentation.mjs';
import Select from './Select';
import CustomerOpportunityDrawer from './CustomerOpportunityDrawer';
import {customerSegments,renewalTiming,recordedHoldings,friendlyCustomerText} from './shared/customerViews.mjs';
import FloatingExecutiveChat from './FloatingExecutiveChat';
import {managementBrief} from './shared/executiveBrief.mjs';


const RED='#D71942',BLUE='#7289A9',GREEN='#237D75',COLORS=[RED,BLUE,'#243D60','#A6B8C6','#6B8C88','#C59B9F'];

const valid=v=>v!==null&&v!==undefined&&Number.isFinite(Number(v));

const number=formatNumber;
const money=(v,exact=false)=>{if(!valid(v))return 'Unavailable';const n=Number(v),a=Math.abs(n);return 'RM '+(exact?n.toLocaleString('en-MY',{minimumFractionDigits:2,maximumFractionDigits:2}):a>=1e6?(n/1e6).toFixed(2)+'M':a>=1e3?(n/1e3).toFixed(1).replace(/\.0$/,'')+'K':n.toLocaleString('en-MY',{maximumFractionDigits:2}));};

const pct=v=>valid(v)?(Number(v)*100).toFixed(1)+'%':'Unavailable';

const month=v=>v?new Date(v.slice(0,10)+'T00:00:00').toLocaleDateString('en-GB',{month:'short',year:'numeric'}):'Unavailable';

const dateKey=v=>v?.slice(0,10);

const query=o=>new URLSearchParams(o).toString();



async function api(path,body,signal){

  const response=await fetch('/api'+path,{signal,...(body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{})});

  const result=await response.json();

  if(!response.ok)throw Error(typeof result.detail==='string'?errorLabel(result.detail):'Please check the selected filters and try again.');
  return result;

}

function useData(path,revision=0){

  const [state,setState]=useState({data:null,loading:true,error:null});

  useEffect(()=>{if(!path)return;const controller=new AbortController();setState({data:null,loading:true,error:null});api(path,null,controller.signal).then(data=>setState({data,loading:false,error:null})).catch(e=>{if(e.name!=='AbortError')setState({data:null,loading:false,error:e.message});});return()=>controller.abort();},[path,revision]);

  return state;

}

function Panel({title,subtitle,action,children,className=''}){return <section className={'panel '+className}><div className="panel-heading"><div><h2>{title}</h2>{subtitle&&<p className="muted small">{subtitle}</p>}</div>{action}</div>{children}</section>;}

function Loading(){return <div className="loading" role="status"><LoaderCircle className="spin" size={26}/><div>Preparing your reporting data<span>Loading the selected view</span></div></div>;}
function ErrorState({message}){return <div className="notice error" role="alert"><Info size={20}/><div><strong>We couldn’t load this view</strong><p>{message}</p><small>Refresh data to try again.</small></div></div>;}
function Empty({children}){return <div className="empty"><Search size={24}/><p>{children||'No data for this selection. Try broadening the filters.'}</p></div>;}

function Badge({value}){return <span className={'badge '+(value==='High'?'risk-high':value==='Medium'?'risk-medium':value==='Low'?'risk-low':'neutral')}>{value||'Unavailable'}</span>;}

function Delta({value,plan}){return <div className={'delta '+(!valid(value)?'muted':value<0?'negative':'positive')}>{valid(value)&&(value<0?<ArrowDownRight size={15}/>:<ArrowUpRight size={15}/>)}<span>{valid(value)?pct(value)+' vs plan':'Comparison unavailable'}{valid(plan)&&<span className="plan-note"> · {money(plan)}</span>}</span></div>;}

function KPI({label,value,icon:Icon,detail,delta,plan,exact}){return <div className="kpi"><div className="metric-icon"><Icon size={21} strokeWidth={1.6}/></div><div className="kpi-body"><div className="metric-label">{label}</div><div className="metric-value" title={exact}>{value}</div>{delta!==undefined?<Delta value={delta} plan={plan}/>:<div className="metric-note">{detail}</div>}</div></div>;}

function ChartTip({active,payload,label,ratio=false}){if(!active||!payload?.length)return null;return <div className="chart-tooltip"><strong>{typeof label==='string'&&label.match(/^\d{4}-/)?month(label):label}</strong>{payload.map((p,i)=><div key={i}><span className="dot" style={{background:p.color||RED}}/>{p.name}<b>{ratio?pct(p.value):money(p.value,true)}</b></div>)}</div>;}

function Legend(){return <div className="legend"><span><i style={{background:RED}}/>Actual</span><span><i style={{background:BLUE}}/>Plan</span></div>;}



function Insights({brief,module='EXEC',scope,customer,filters,ai,rows=[]}){
  const [result,setResult]=useState(brief),[busy,setBusy]=useState(false);
  useEffect(()=>{setResult(brief);},[brief]);
  async function generate(){setBusy(true);try{setResult(await api('/explain',{module,scope,customer_id:customer,...filters,ai}));}catch(e){setResult({...brief,source:'Deterministic explanation · '+e.message});}finally{setBusy(false);}}
  if(!result)return null;
  const display=result.short_facts||result.facts;
  const executive=module==='EXEC'?managementBrief(rows,money,pct):null;
  const contributors=executive?executive.contributors:result.ids.slice(0,3).map(i=>display[i]);
  return <><section className={'panel insights '+(module==='EXEC'?'executive-insights':'customer-brief')} aria-busy={busy}>
    <div className="panel-heading"><div className="insight-title"><Sparkles size={23}/><h2>{module==='EXEC'?'AI Performance Insights':module==='NBO'?'Engagement brief':'Recommended retention action'}</h2><span className="pill">{ai?'AI assisted':'Business rules'}</span></div><button className="button primary" disabled={busy} onClick={generate}>{busy?<LoaderCircle size={16} className="spin"/>:<Sparkles size={16}/>} {busy?'Preparing brief…':module==='EXEC'?'Prepare management brief':module==='NBO'?'Generate engagement brief':'Explain recommendation'}</button></div>
    <div className="insight-grid"><div><div className="eyebrow muted">{executive?'WHAT THIS MEANS':'KEY FINDING'}</div><p className="finding">{executive?executive.finding:result.finding}</p></div><div><div className="eyebrow muted">{executive?'WHERE TO FOCUS':'TOP CONTRIBUTORS'}</div>{contributors.length?<ul>{contributors.map((text,i)=><li key={i}>{text}</li>)}</ul>:<p>There is not enough comparable information to identify a business line or channel to focus on.</p>}</div><div><div className="eyebrow muted">{executive?'WHAT TO DO NEXT':'RECOMMENDED INVESTIGATION'}</div><p>{executive?executive.action:result.action}</p></div></div>
    <div className="insight-source" role="status">{busy?'Reviewing the supporting evidence…':sourceLabel(result.source)} · {module==='EXEC'?'These figures show where results differ from plan, not why. Business line and channel gaps overlap and should not be added together.':'Human review required. No customer message is sent.'}</div>
    <details><summary>{executive?'See the figures behind this summary':'Supporting evidence'}<ChevronDown size={16}/></summary>{result.source.startsWith('AI-curated')&&<p className="footnote">AI-selected facts are highlighted below; all amounts remain calculated from the active reporting scope.</p>}<ul>{result.facts.map((fact,i)=><li className={result.source.startsWith('AI-curated')&&result.ids.includes(i)?'cortex-selected':undefined} key={i}>{fact}</li>)}</ul></details>
  </section>
    {module==='EXEC'&&<FloatingExecutiveChat key={JSON.stringify(brief.facts)} scope={scope} ai={ai} send={(body,signal)=>api('/chat',body,signal)}/>}
  </>;
}


const TREND={'GWP actual vs plan':['GWP','PLAN_GWP'],'NEP actual vs plan':['NEP','PLAN_NEP'],'Net incurred claims':['NET_INCURRED_CLAIMS',null],'Net loss ratio':['LOSS_RATIO',null]};
function Trend({rows}){

  const [measure,setMeasure]=useState('GWP actual vs plan'),[field,plan]=TREND[measure],ratio=field==='LOSS_RATIO';
  const data=rows.filter(r=>r.LEVEL==='MONTH').sort((a,b)=>a.ACCOUNTING_MONTH.localeCompare(b.ACCOUNTING_MONTH)).map(r=>({...r,Actual:r[field],Plan:plan?r[plan]:null}));

  return <Panel title="Monthly performance" className="executive-monthly" action={<Select label="Trend metric" value={measure} onChange={setMeasure} options={Object.keys(TREND)}/> }><div className="chart-topline"><span className="muted small">{measure}</span>{plan?<Legend/>:<span className="pill">Actuals only</span>}</div><div className="chart trend-chart"><ResponsiveContainer width="100%" height="100%"><LineChart data={data} margin={{top:16,right:18,bottom:8,left:12}}><CartesianGrid stroke="#EEF0F4" vertical={false}/><XAxis dataKey="ACCOUNTING_MONTH" tickFormatter={month} axisLine={false} tickLine={false} minTickGap={24}/><YAxis width={78} tickFormatter={v=>ratio?pct(v):money(v)} axisLine={false} tickLine={false} domain={['auto','auto']}/><Tooltip content={<ChartTip ratio={ratio}/>}/>{plan&&<Line type="linear" dataKey="Plan" stroke={BLUE} strokeWidth={2} dot={{r:3,fill:'white',strokeWidth:2}} connectNulls={false} isAnimationActive={false}/>}<Line type="linear" dataKey="Actual" stroke={RED} strokeWidth={2.3} dot={{r:3,fill:'white',strokeWidth:2}} connectNulls={false} isAnimationActive={false}/></LineChart></ResponsiveContainer></div>{!plan&&<p className="footnote">Plan claims basis is unconfirmed. Claims and loss-ratio comparisons remain unavailable.</p>}</Panel>;
}

function Variance({rows,level,metric}){

  const key=metric+'_VARIANCE',name=level==='LINE'?'LINE_OF_BUSINESS':'DISTRIBUTION_CHANNEL';

  const group=rows.filter(r=>r.LEVEL===level),data=group.filter(r=>valid(r[key])&&r.MISSING_ACTUAL===0&&r.MISSING_PLAN===0&&r.KEY_COUNT>0).sort((a,b)=>a[key]-b[key]);

  return <Panel title={level==='LINE'?'By business line':'By distribution channel'}>{!data.length?<Empty>No comparable actual and plan results for these filters.</Empty>:<div className="chart"><ResponsiveContainer width="100%" height="100%"><BarChart data={data} layout="vertical" margin={{top:12,right:22,bottom:8,left:0}} barSize={25}><CartesianGrid stroke="#EEF0F4" horizontal={false}/><XAxis type="number" tickFormatter={v=>money(v)} axisLine={false} tickLine={false}/><YAxis type="category" dataKey={name} width={level==='LINE'?70:120} axisLine={false} tickLine={false} tick={{fontSize:11}}/><Tooltip formatter={v=>money(v,true)} labelFormatter={v=>v}/><ReferenceLine x={0} stroke="#DFE4EC"/><Bar dataKey={key} name={metric+' variance'} radius={3} isAnimationActive={false}>{data.map((r,i)=><Cell key={i} fill={r[key]<0?RED:GREEN}/>)}</Bar></BarChart></ResponsiveContainer></div>}<p className="footnote">{metric} actual − plan · Red below plan / green above plan{group.length>data.length?` · ${group.length-data.length} unavailable groups excluded`:''}</p></Panel>;
}

function Mix({rows,level,metric}){

  const data=rows.filter(r=>r.LEVEL===level).sort((a,b)=>b[metric]-a[metric]),field=level==='LINE'?'LINE_OF_BUSINESS':'DISTRIBUTION_CHANNEL',share=metric+'_SHARE';

  return <Panel title={level==='LINE'?'Business line premium mix':'Distribution channel premium mix'}>{!data.length||data.some(r=>!valid(r[share]))?<Empty>Shares unavailable for missing, negative or zero-total premium.</Empty>:<div className="mix-layout"><div className="donut"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={data} dataKey={share} nameKey={field} innerRadius="62%" outerRadius="90%" paddingAngle={2} stroke="white" isAnimationActive={false}>{data.map((r,i)=><Cell key={i} fill={COLORS[i%COLORS.length]}/>)}</Pie><Tooltip formatter={v=>pct(v)}/></PieChart></ResponsiveContainer><div className="donut-center">{metric}<small>premium mix</small></div></div><div className="mix-legend">{data.map((r,i)=><div key={r[field]}><span className="dot" style={{background:COLORS[i%COLORS.length]}}/><span title={r[field]}>{r[field]}</span><b title={money(r[metric],true)}>{pct(r[share])}</b></div>)}</div></div>}<p className="footnote">Share of selected actual {metric}. Each premium measure uses its own total.</p></Panel>;
}

function LineCard({line,row}){return <Panel title={line} action={<span className="line-icon">{line==='Motor'?<Shield size={20}/>:<Target size={20}/>}</span>}>{!row?<Empty>Not present in the selected scope.</Empty>:<><div className="metric-label">Actual gross written premium</div><div className="line-primary" title={money(row.GWP,true)}>{money(row.GWP)}</div><Delta value={row.GWP_VARIANCE_PCT} plan={row.PLAN_GWP}/><div className="line-support"><div><span>Net earned premium</span><b title={money(row.NEP,true)}>{money(row.NEP)}</b></div><div><span>Net incurred claims</span><b title={money(row.NET_INCURRED_CLAIMS,true)}>{money(row.NET_INCURRED_CLAIMS)}</b></div><div><span>Net loss ratio</span><b>{pct(row.LOSS_RATIO)}</b></div></div></>}</Panel>;}

function ChannelTable({rows}){

  const [sort,setSort]=useState(['GWP',-1]);

  const fields=[['DISTRIBUTION_CHANNEL','Channel'],['GWP','GWP actual'],['PLAN_GWP','GWP plan'],['GWP_VARIANCE','GWP variance'],['GWP_VARIANCE_PCT','Variance %'],['NEP','NEP'],['NET_INCURRED_CLAIMS','Net incurred'],['LOSS_RATIO','Loss ratio']];

  const data=[...rows.filter(r=>r.LEVEL==='CHANNEL')].sort((a,b)=>{const x=a[sort[0]],y=b[sort[0]];if(x===null)return 1;if(y===null)return -1;return (typeof x==='string'?x.localeCompare(y):x-y)*sort[1];});

  return <Panel title="Channel performance scorecard" subtitle="Compare distribution performance. Select a column heading to sort."><div className="table-scroll"><table><thead><tr>{fields.map(([key,label])=><th key={key} aria-sort={sort[0]===key?(sort[1]===1?'ascending':'descending'):'none'}><button onClick={()=>setSort([key,sort[0]===key?-sort[1]:1])}>{label}<ArrowUpDown size={12}/></button></th>)}</tr></thead><tbody>{data.map(r=><tr key={r.DISTRIBUTION_CHANNEL}>{fields.map(([key])=><td key={key} title={key==='DISTRIBUTION_CHANNEL'?undefined:money(r[key],true)} className={key.includes('VARIANCE')&&valid(r[key])?(r[key]<0?'negative':'positive'):''}>{key==='DISTRIBUTION_CHANNEL'?r[key]:key.includes('PCT')||key==='LOSS_RATIO'?pct(r[key]):money(r[key])}</td>)}</tr>)}</tbody></table></div></Panel>;

}

function Detail({total,rows}){return <Panel title="Financial detail" subtitle="Exact amounts in RM · Display rounding elsewhere does not change the underlying calculations."><div className="table-scroll"><table><thead><tr>{['Metric','Actual','Plan','Variance','Variance %'].map(t=><th key={t}>{t}</th>)}</tr></thead><tbody>{[['Gross written premium','GWP'],['Net earned premium','NEP']].map(([label,f])=><tr key={f}><td>{label}</td><td>{money(total[f],true)}</td><td>{money(total['PLAN_'+f],true)}</td><td className={total[f+'_VARIANCE']<0?'negative':'positive'}>{money(total[f+'_VARIANCE'],true)}</td><td>{pct(total[f+'_VARIANCE_PCT'])}</td></tr>)}<tr><td>Net incurred claims</td><td>{money(total.NET_INCURRED_CLAIMS,true)}</td><td className="muted">Not comparable</td><td>—</td><td>—</td></tr><tr><td>Net loss ratio</td><td>{pct(total.LOSS_RATIO)}</td><td className="muted">Not established</td><td>—</td><td>—</td></tr></tbody></table></div><details><summary>Reporting basis & source evidence<ChevronDown size={16}/></summary><p>Actual and plan are independently aggregated at accounting month, entity, business line and distribution channel before joining. Variance = actual − plan; variance % = variance / plan.</p><p>Net incurred claims = gross claims paid + reserve movement + IBNR movement − reinsurance recoveries. Net loss ratio = summed net incurred claims / summed net earned premium. Missing values and zero denominators remain unavailable. The plan claims basis is unconfirmed.</p><p>Source: TUNE_BI_DB.GOLD.GI_ENTERPRISE_WIDE_MART, GI_PLAN_MONTHLY and DERIVED_METRIC. Illustrative Data, not production records. Reporting reads may be cached for up to five minutes.</p><pre>{JSON.stringify(rows,null,2)}</pre></details></Panel>;}
function Executive({revision,ai}){

  const options=useData('/finance/options',revision),[scope,setScope]=useState(null),[varMetric,setVarMetric]=useState('GWP'),[mixMetric,setMixMetric]=useState('GWP');

  useEffect(()=>{if(options.data?.months.length){const m=options.data.months;setScope(old=>old||{start:m.find(x=>x.slice(0,4)===m.at(-1).slice(0,4)),end:m.at(-1),line:'All',channel:'All'});}},[options.data]);

  const result=useData(scope?'/finance?'+query(scope):null,revision),data=result.data,rows=data?.rows||[],total=rows.find(r=>r.LEVEL==='TOTAL');

  const update=(key,value)=>setScope(s=>({...s,[key]:value}));

  return <><PageHeader title="Executive Intelligence" subtitle="Financial performance, portfolio insights and the gaps that matter."/>

    {scope&&<div className="filter-bar"><div className="date-range"><Select label="From month" icon={CalendarDays} value={scope.start} onChange={v=>update('start',v)} options={options.data?.months.map(value=>({value,label:month(value)}))||[]}/><span className="muted">to</span><Select label="To month" value={scope.end} onChange={v=>update('end',v)} options={options.data?.months.map(value=>({value,label:month(value)}))||[]}/></div><Select label="Business line" value={scope.line} onChange={v=>update('line',v)} options={['All','Motor','Travel'].map(value=>({value,label:'Business line: '+value}))}/><Select label="Distribution channel" value={scope.channel} onChange={v=>update('channel',v)} options={['All',...(options.data?.channels||[])].map(value=>({value,label:'Channel: '+value}))}/></div>}

    {options.error||result.error?<ErrorState message={options.error||result.error}/>:options.loading||result.loading?<Loading/>:!total?<Empty/>:<>

      <div className="kpi-grid"><KPI label="Gross written premium" value={money(total.GWP)} exact={money(total.GWP,true)} icon={Layers} delta={total.GWP_VARIANCE_PCT} plan={total.PLAN_GWP}/><KPI label="Net earned premium" value={money(total.NEP)} exact={money(total.NEP,true)} icon={Shield} delta={total.NEP_VARIANCE_PCT} plan={total.PLAN_NEP}/><KPI label="Net incurred claims" value={money(total.NET_INCURRED_CLAIMS)} exact={money(total.NET_INCURRED_CLAIMS,true)} icon={FileText} detail="Net of reinsurance recoveries"/><KPI label="Net loss ratio" value={pct(total.LOSS_RATIO)} icon={Percent} detail="Plan comparison unavailable"/></div>


      {total.MISSING_ACTUAL+total.MISSING_PLAN>0&&<div className="notice">Some accounting keys lack an actual or plan counterpart. Affected comparisons are unavailable.</div>}

      <Trend rows={rows}/>

      <SectionHeading title="Variance intelligence" subtitle="Where the selected portfolio differs from plan" action={<MetricSwitch value={varMetric} onChange={setVarMetric}/>}/><div className="two-grid"><Variance rows={rows} level="LINE" metric={varMetric}/><Variance rows={rows} level="CHANNEL" metric={varMetric}/></div>

      <SectionHeading title="Portfolio composition" subtitle="Premium contribution within the selected reporting scope" action={<MetricSwitch value={mixMetric} onChange={setMixMetric}/>}/><div className="two-grid"><Mix rows={rows} level="LINE" metric={mixMetric}/><Mix rows={rows} level="CHANNEL" metric={mixMetric}/></div>

      <SectionHeading title="Motor vs Travel" subtitle="A side-by-side view of business line performance"/><div className="two-grid"><LineCard line="Motor" row={rows.find(r=>r.LEVEL==='LINE'&&r.LINE_OF_BUSINESS==='Motor')}/><LineCard line="Travel" row={rows.find(r=>r.LEVEL==='LINE'&&r.LINE_OF_BUSINESS==='Travel')}/></div>

      <ChannelTable rows={rows}/><Detail total={total} rows={rows}/>
      <Insights key={query(scope)+JSON.stringify(rows)} brief={data.brief} scope={scope} ai={ai} rows={rows}/>

    </>}

  </>;

}

function MetricSwitch({value,onChange}){return <div className="segmented" aria-label="Premium measure">{['GWP','NEP'].map(v=><button key={v} onClick={()=>onChange(v)} className={value===v?'active':''} aria-pressed={value===v}>{v}</button>)}</div>;}

function PageHeader({title,subtitle}){return <header className="page-header"><div><div className="eyebrow">TUNE PROTECT / AI INTELLIGENCE</div><h1>{title}</h1><p>{subtitle}</p></div></header>;}
function SectionHeading({title,subtitle,action}){return <div className="section-heading"><div><h2>{title}</h2>{subtitle&&<p>{subtitle}</p>}</div>{action}</div>;}



function customerTab(){
  const hash=location.hash.slice(1);
  if(hash==='NBA'||hash==='CUSTOMERS/retention')return 'RETENTION';
  if(hash==='NBO'||hash==='CUSTOMERS/cross-sell')return 'CROSS_SELL';
  return 'PRIORITIES';
}
function UnifiedBrief({profile,view,customer,filters,ai}){
  const [result,setResult]=useState(profile.combined),[busy,setBusy]=useState(false);
  async function generate(){setBusy(true);try{setResult(await api('/customer-intelligence/brief',{view,customer_id:customer,...filters,ai}));}catch(e){setResult({...profile.combined,source:'Deterministic explanation · '+e.message});}finally{setBusy(false);}}
  const offerView=view==='CROSS_SELL'&&profile.offer;
  return <section className="panel insights" aria-busy={busy}><div className="panel-heading"><div className="insight-title"><Sparkles size={23}/><h2>{offerView?`Plan the ${profile.product} conversation`:'AI-assisted retention explanation'}</h2><span className="pill">{ai?'AI assisted':'Business rules'}</span></div><button className="button primary" disabled={busy} onClick={generate}>{busy?<LoaderCircle className="spin" size={16}/>:<Sparkles size={16}/>} {busy?'Preparing brief…':offerView?'Prepare conversation brief':'Generate engagement brief'}</button></div>
    <div className="insight-grid"><div><div className="eyebrow muted">{offerView?'PRODUCT TO EXPLORE':'RETENTION ACTION'}</div><p className="finding">{offerView?`${profile.product} · Review before offering`:result.finding}</p></div><div><div className="eyebrow muted">{offerView?'WHAT WE KNOW ABOUT THIS CUSTOMER':'VERIFIED CUSTOMER EVIDENCE'}</div><ul>{result.ids.slice(0,3).map(i=><li key={i}>{offerView?friendlyCustomerText(result.facts[i]):result.facts[i]}</li>)}</ul></div><div><div className="eyebrow muted">{offerView?'HOW TO START THE CONVERSATION':'RECOMMENDED RETENTION ACTION'}</div><p>{offerView?friendlyCustomerText(profile.offer.action):profile.retention.action}</p></div></div>
    <p className="insight-source" role="status">{busy?(offerView?'Reviewing the customer information…':'Reviewing the supporting evidence…'):offerView&&result.source==='Rule-based recommendation'?'Based on the customer’s recorded information':sourceLabel(result.source)}{offerView?' · Review before use. No message is sent to the customer.':' · Human review required. No customer message is sent.'}</p>
    <details><summary>Supporting evidence for this brief<ChevronDown size={16}/></summary><ul>{result.facts.map((fact,i)=><li key={i}>{fact}</li>)}</ul></details>
  </section>;
}
function CustomerSegmentation({segments,field,title}){
  const groups=customerSegments(segments,field),maximum=Math.max(1,...groups.map(group=>group.count));
  return <Panel title={title} subtitle="Full portfolio · Existing customer segments">
    {!groups.length?<Empty>No segment breakdown is available.</Empty>:<div className="customer-segmentation">{groups.map(group=><div className="customer-segment-row" key={group.label}><span>{field==='RETENTION_RISK_BAND'?<Badge value={group.label}/>:group.label}</span><div className="customer-segment-track" aria-hidden="true"><i style={{width:`${100*group.count/maximum}%`}}/></div><b>{number(group.count)}</b></div>)}</div>}
  </Panel>;
}
function CustomerOverview({data,onNavigate}){
  return <div className="customer-management-overview">
    <div className="opportunity-summary-grid">
      <section className="panel opportunity-summary retention-summary"><div className="opportunity-summary-heading"><Shield size={21}/><h2>Retention focus</h2></div><div className="opportunity-summary-number">{number(data.counts.priority)}</div><p className="opportunity-summary-label">priority retention opportunities</p><p>High-risk, High/Top-value customers renewing within the defined window.</p><div className="opportunity-summary-facts"><span><b>{number(data.counts.high_risk)}</b> high-risk customers</span><span><b>{number(data.counts.high_value_at_risk)}</b> high-value customers at risk</span></div><button className="button primary" onClick={()=>onNavigate('RETENTION','retention')}>View retention actions<ArrowRight size={15}/></button></section>
      <section className="panel opportunity-summary growth-summary"><div className="opportunity-summary-heading"><Target size={21}/><h2>Cross-sell growth opportunities</h2></div><div className="opportunity-summary-number">{number(data.summary.cross_sell_candidates)}</div><p className="opportunity-summary-label">source-recorded product candidates</p><p>Existing next-best-product recommendations with marketing consent. Product holdings and suitability require review.</p><div className="opportunity-review-note"><Info size={15}/><span>Candidate segment only. Product eligibility and suitability require human review.</span></div><button className="button primary" onClick={()=>onNavigate('CROSS_SELL','cross-sell')}>View cross-sell opportunities<ArrowRight size={15}/></button></section>
    </div>
    <div className="two-grid"><CustomerSegmentation segments={data.segments} field="RETENTION_RISK_BAND" title="Portfolio by retention risk"/><CustomerSegmentation segments={data.segments} field="LIFETIME_VALUE_BAND" title="Portfolio by customer value"/></div>
    <p className="customer-overlap-note">{data.summary.overlap_note} Overview charts use the full portfolio aggregates, not the first 200 customers. Customer filters are available in the action tabs.</p>
  </div>;
}
function CustomerFacts({row}){
  return <dl><div><dt>Renewal month</dt><dd>{month(dateKey(row.NEXT_RENEWAL_MONTH))}</dd></div><div><dt>Preferred channel</dt><dd>{row.PREFERRED_CHANNEL}</dd></div><div><dt>Active policies</dt><dd>{number(row.ACTIVE_POLICY_COUNT)}</dd></div><div><dt>Marketing consent</dt><dd>{row.MARKETING_CONSENT}</dd></div><div><dt>Holds Motor / Travel</dt><dd>{row.HOLDS_MOTOR} / {row.HOLDS_TRAVEL}</dd></div></dl>;
}
function RetentionProfile({row,profile}){
  return <Panel title="Retention review" className="spotlight retention-profile" action={<Shield size={20}/>}>
    <div className="customer-id">{row.CUSTOMER_ID}</div>
    <div className="travel-product-hero"><span className="travel-product-icon"><Shield size={26}/></span><div><div className="eyebrow">RECOMMENDED RETENTION ACTION</div><h3>{row.ACTION}</h3></div></div>
    <div className="profile-stats"><div><span>Retention risk</span><Badge value={row.RETENTION_RISK_BAND}/><small>Risk score {number(row.RETENTION_RISK_SCORE)}</small></div><div><span>Customer value</span><b title={money(row.LIFETIME_VALUE,true)}>{money(row.LIFETIME_VALUE)}</b><small>{row.LIFETIME_VALUE_BAND} value segment</small></div></div>
    <div className="renewal-focus"><CalendarDays size={17}/><div><strong>{month(dateKey(row.NEXT_RENEWAL_MONTH))}</strong><span>{renewalTiming(row.UPCOMING)}</span></div></div>
    <div className="channel-focus"><div className="eyebrow muted">PREFERRED WAY TO CONNECT</div><strong>{row.PREFERRED_CHANNEL}</strong></div>
    <div className="offer-engagement"><div className="eyebrow muted">SUGGESTED NEXT STEP</div><p>{profile.retention.action}</p></div>
    <details className="profile-evidence"><summary>Why this customer needs attention<ChevronDown size={14}/></summary><ul>{profile.retention.facts.map((fact,i)=><li key={i}>{fact}</li>)}</ul></details>
    <details className="profile-evidence"><summary>Customer details<ChevronDown size={14}/></summary><CustomerFacts row={row}/></details>
    {profile.offer&&<details className="profile-evidence"><summary>Additional cross-sell context<ChevronDown size={14}/></summary><p>{profile.offer.finding}</p><p>{profile.offer.action}</p></details>}
    <div className="review-note"><Info size={16}/><span>Confirm renewal needs and the permitted contact route. No automatic customer contact.</span></div>
  </Panel>;
}
function CrossSellProfile({row,profile}){
  return <Panel title="Product recommendation" className="spotlight cross-sell-profile" action={<Target size={20}/>}>
    <div className="offer-customer-reference">Selected customer <strong>{row.CUSTOMER_ID}</strong></div><div className="channel-focus"><div className="eyebrow muted">EXISTING COVER · MOTOR & TRAVEL</div><strong>{recordedHoldings(row)}</strong><p className="footnote">This view shows Motor and Travel cover only. Please check any other policies with the customer.</p></div>
    {profile.offer?<>
      <div className="travel-product-hero"><span className="travel-product-icon"><Target size={26}/></span><div><div className="eyebrow">PRODUCT TO CONSIDER</div><h3>{row.CANDIDATE_PRODUCT}</h3><span className="eligibility-review">Review eligibility before offering</span></div></div>
      <div className="profile-stats"><div><span>Customer value</span><b title={money(row.LIFETIME_VALUE,true)}>{money(row.LIFETIME_VALUE)}</b><small>{row.LIFETIME_VALUE_BAND} value segment</small></div><div><span>Retention risk</span><Badge value={row.RETENTION_RISK_BAND}/><small>Keep in mind when reaching out</small></div></div>
      <div className="channel-focus"><div className="eyebrow muted">PREFERRED WAY TO CONNECT</div><strong>{row.PREFERRED_CHANNEL}</strong></div>
      <div className="product-rationale"><h3>Why consider {row.CANDIDATE_PRODUCT}?</h3><p>The customer’s profile lists {row.CANDIDATE_PRODUCT} as a product to consider, and they have given marketing consent. Check their existing cover and needs before making an offer.</p><details><summary>Supporting product evidence<ChevronDown size={14}/></summary><ul>{profile.offer.facts.map((fact,i)=><li key={i}>{fact}</li>)}</ul></details></div>
      <div className="offer-engagement"><div className="eyebrow muted">SUGGESTED NEXT STEP</div><p>{friendlyCustomerText(profile.offer.action)}</p></div>
      <div className="review-note"><Info size={16}/><span>This is a starting point for a conversation, not a confirmed offer. A team member must check existing cover, eligibility and suitability. It does not predict whether the customer will buy.</span></div>
    </>:<Empty>No consented product candidate is available for this customer.</Empty>}
    <details className="profile-evidence secondary-retention-context"><summary>Retention context and customer details<ChevronDown size={14}/></summary><p><strong>{row.ACTION}</strong></p><p>{profile.retention.action}</p><CustomerFacts row={row}/></details>
  </Panel>;
}
function CustomerIntelligence({revision,ai}){
  const [view,setView]=useState(customerTab),[filters,setFilters]=useState({risk:'All',value:'All',channel:'All',holding:'All',product:'All'}),[selected,setSelected]=useState(null),[search,setSearch]=useState('');
  useEffect(()=>{const update=()=>{setView(customerTab());setSelected(null);setSearch('');};window.addEventListener('hashchange',update);return()=>window.removeEventListener('hashchange',update);},[]);
  const nbo=view==='CROSS_SELL',priorities=view==='PRIORITIES';
  const result=useData('/customer-intelligence?'+query({view,...filters,...(!nbo?{holding:'All',product:'All'}:{})}),revision),data=result.data;
  const rows=data?.rows||[],visible=rows.filter(r=>r.CUSTOMER_ID.toLowerCase().includes(search.toLowerCase())),row=visible.find(r=>r.CUSTOMER_ID===selected)||null,counts=data?.counts,profile=row?data.profiles[row.CUSTOMER_ID]:null;
  const snapshot=data?.snapshot,renewalStart=snapshot?new Date(snapshot.slice(0,7)+'-01T00:00:00'):null;
  if(renewalStart)renewalStart.setMonth(renewalStart.getMonth()+1);
  const renewalEnd=renewalStart?new Date(renewalStart):null;if(renewalEnd){renewalEnd.setMonth(renewalEnd.getMonth()+3);renewalEnd.setDate(renewalEnd.getDate()-1);}
  const change=(key,value)=>{setFilters(f=>({...f,[key]:value}));setSelected(null);setSearch('');};
  function selectCustomer(id,event){const trigger=event.currentTarget.matches('button')?event.currentTarget:event.currentTarget.querySelector('.customer-select');trigger?.focus({preventScroll:true});setSelected(id);}
  const tabs=[['PRIORITIES','Customer Priorities','priorities'],['RETENTION','Retention Actions','retention'],['CROSS_SELL','Cross-Sell Opportunities','cross-sell']];
  function tab(value,slug){setView(value);setSelected(null);setSearch('');location.hash='CUSTOMERS/'+slug;}
  function tabKey(event,index){if(!['ArrowRight','ArrowLeft','Home','End'].includes(event.key))return;event.preventDefault();const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tab(tabs[next][0],tabs[next][2]);document.getElementById('tab-'+tabs[next][0])?.focus();}
  return <><PageHeader title="Customer Growth & Retention Intelligence" subtitle="One customer view. Retention-led priorities and evidence-based growth opportunities."/>
    <div className="customer-tabs" role="tablist" aria-label="Customer intelligence views">{tabs.map(([id,label,slug],index)=><button type="button" key={id} id={'tab-'+id} role="tab" tabIndex={view===id?0:-1} onKeyDown={event=>tabKey(event,index)} aria-selected={view===id} aria-controls="customer-workspace" className={view===id?'active':''} onClick={()=>tab(id,slug)}>{label}</button>)}</div>
    <div id="customer-workspace" role="tabpanel" aria-labelledby={'tab-'+view}>
    <div className="customer-view-intro"><div className="eyebrow">{priorities?'MANAGEMENT OVERVIEW':nbo?'PRODUCT-LED ENGAGEMENT':'RETENTION WORKSPACE'}</div><h2>{priorities?'Where should we focus?':nbo?'What should we offer?':'Who should we retain?'}</h2><p>{priorities?'Portfolio priorities and opportunity segments, with clear paths to action.':nbo?'Review source-recorded product candidates, supporting evidence and the engagement approach.':'Focus on retention risk, customer value and renewal timing.'}</p></div>
    {result.error?<ErrorState message={result.error}/>:result.loading||data?.view!==view?<Loading/>:<>
      {nbo&&<div className="opportunity-headline"><span className="metric-icon"><Target size={23}/></span><div><h2>{number(counts.total)} cross-sell candidates</h2><p>Existing validated segment. Eligibility, suitability and propensity are not established.</p></div></div>}
      <div className="kpi-grid">{(priorities?[['Customers in portfolio',data.summary.portfolio_total,Users],['Priority retention opportunities',counts.priority,Shield],['Cross-sell candidates',data.summary.cross_sell_candidates,Target],['High-value at risk',counts.high_value_at_risk,Layers]]:nbo?[['Total candidates',counts.total,Users],['High / Top value',counts.high_value,Layers],['High-risk candidates',counts.high_risk,Shield],['Priority opportunities',counts.priority,Target]]:[['Customers in portfolio',counts.total,Users],['High-risk customers',counts.high_risk,Shield],['High-value at risk',counts.high_value_at_risk,Layers],['Priority retention opportunities',counts.priority,Target]]).map(([label,value,icon])=><KPI key={label} label={label} value={number(value)} icon={icon} detail={label.includes('Priority')?(nbo?'Low risk · High/Top value':'High risk · High/Top value · Renewal window'):priorities?'Full portfolio · Overlapping segments':'Full segment overview'}/>)}</div>
      <div className="scope-note"><CheckCircle2 size={14}/>As at {formatDate(snapshot)} · {priorities?'Full portfolio overview · Opportunity categories overlap':'Totals cover all product opportunities; filters apply to the customer list'} · Values in RM</div>
      {priorities?<CustomerOverview data={data} onNavigate={tab}/>:<>
      <div className={'customer-filters '+(nbo?'product-opportunity-filters':'')}><SlidersHorizontal size={17}/>{['risk','value','channel',...(nbo?['holding','product']:[])].map(key=><Select key={key} label={key==='risk'?'Retention risk':key==='value'?'Customer value':key==='holding'?'Existing product holding':key==='product'?'Candidate next-best-product':'Preferred channel'} value={filters[key]} onChange={v=>change(key,v)} options={['All',...data.options[key]].map(value=>({value,label:(key==='risk'?'Risk':key==='value'?'Value':key==='holding'?'Holding':key==='product'?'Candidate product':'Channel')+': '+value}))}/>)}</div>
      <div className={'customer-grid '+(nbo?'cross-sell-workspace':'retention-workspace')}><Panel title={nbo?'Ranked product candidates':'Retention worklist'} subtitle={`${number(data.filtered_total)} customers match · First ${number(rows.length)} shown`} action={<label className="search"><Search size={15}/><input aria-label="Find in displayed customers" placeholder="Find customer ID" value={search} onChange={e=>setSearch(e.target.value)}/></label>}>
        {!visible.length?<Empty>No customers match. Try broader filters or clear your search.</Empty>:<div className="table-scroll customer-table unified-worklist"><table><thead><tr>{(nbo?['Customer','Value (RM)','Value band','Candidate offer','Preferred channel','Renewal','Risk']:['Customer','Risk','Value (RM)','Value band','Renewal','Timing','Recommended retention action','Preferred channel']).map(label=><th key={label}>{label}</th>)}</tr></thead><tbody>{visible.map(r=><tr key={r.CUSTOMER_ID} className={r.CUSTOMER_ID===row?.CUSTOMER_ID?'selected':''} onClick={event=>selectCustomer(r.CUSTOMER_ID,event)}><td><button className="customer-select" onClick={event=>{event.stopPropagation();selectCustomer(r.CUSTOMER_ID,event);}} aria-haspopup="dialog" aria-expanded={r.CUSTOMER_ID===row?.CUSTOMER_ID} aria-label={`View ${nbo?'product recommendation':'retention review'} for ${r.CUSTOMER_ID}`}>{r.CUSTOMER_ID}<ChevronRight size={13}/></button></td>{nbo?<><td>{money(r.LIFETIME_VALUE,true)}</td><td><span className="value-band">{r.LIFETIME_VALUE_BAND}</span></td><td>{r.CANDIDATE_PRODUCT?<span className="offer-tag">{r.CANDIDATE_PRODUCT} · review</span>:<span className="muted">Not supported</span>}</td><td>{r.PREFERRED_CHANNEL}</td><td>{month(dateKey(r.NEXT_RENEWAL_MONTH))}</td><td><Badge value={r.RETENTION_RISK_BAND}/></td></>:<><td><Badge value={r.RETENTION_RISK_BAND}/></td><td>{money(r.LIFETIME_VALUE,true)}</td><td><span className="value-band">{r.LIFETIME_VALUE_BAND}</span></td><td>{month(dateKey(r.NEXT_RENEWAL_MONTH))}</td><td><span className={r.UPCOMING===true?'renewal-pill':'muted'}>{renewalTiming(r.UPCOMING)}</span></td><td className="action-cell">{r.ACTION}</td><td>{r.PREFERRED_CHANNEL}</td></>}</tr>)}</tbody></table></div>}
        <div className="worklist-footer"><span className="dot"/>Prioritized using existing business rules · {nbo?'Risk, customer value and renewal timing':'Retention action, customer value and risk score'} · Select a customer to view their profile</div>
      </Panel>
      </div>
      {row&&<CustomerOpportunityDrawer key={view+row.CUSTOMER_ID+query(filters)} customer={row.CUSTOMER_ID} heading={nbo?'Product recommendation':'Retention review'} backLabel={nbo?'Back to candidates':'Back to retention worklist'} onClose={()=>setSelected(null)}>{nbo?<CrossSellProfile row={row} profile={profile}/>:<RetentionProfile row={row} profile={profile}/>}<UnifiedBrief key={JSON.stringify(profile)} profile={profile} view={view} customer={row.CUSTOMER_ID} filters={filters} ai={ai}/></CustomerOpportunityDrawer>}
      </>}
      <details className="methodology"><summary>Segment definitions & prioritization rules<ChevronDown size={16}/></summary><p>Customer priorities and retention actions follow this order: High risk + High/Top value + upcoming renewal → Priority retention review. Other High risk → Retention review. Medium + upcoming renewal → Proactive renewal engagement. Other Medium → Monitor retention needs. Low → Standard relationship maintenance. Ties: value, risk score and customer ID.</p><p>Cross-sell opportunities use the existing next-best-product field and marketing consent Yes. Blank and no-recommendation values are excluded. Motor and Travel candidates must not already hold that product; holdings for other candidate products require review. Product filters reflect source-supported combinations only. Ranking remains Low risk, Medium, High; lifetime value descending; upcoming renewal first; renewal month and customer ID. A high-risk candidate’s retention needs must be reviewed before a product discussion.</p><p>Renewal window: {renewalStart?.toLocaleDateString('en-GB')}–{renewalEnd?.toLocaleDateString('en-GB')}, the next three full months after the snapshot. Missing renewal dates never qualify as upcoming. Portfolio and opportunity categories overlap and must not be added. No new model, eligibility decision or automatic contact.</p></details>
    </>}
    </div>
  </>;
}

function App(){

  const [page,setPage]=useState(()=>/^(CUSTOMERS(?:\/|$)|NBA$|NBO$)/.test(location.hash.slice(1))?'CUSTOMERS':'EXEC'),[ai,setAI]=useState(true),[revision,setRevision]=useState(0),[refreshing,setRefreshing]=useState(false),[navOpen,setNavOpen]=useState(false),[refreshError,setRefreshError]=useState('');
  useEffect(()=>{const change=()=>setPage(/^(CUSTOMERS(?:\/|$)|NBA$|NBO$)/.test(location.hash.slice(1))?'CUSTOMERS':'EXEC');window.addEventListener('hashchange',change);return()=>window.removeEventListener('hashchange',change);},[]);
  function navigate(id){setPage(id);location.hash=id;setNavOpen(false);window.scrollTo({top:0});}

  async function refresh(){setRefreshing(true);setRefreshError('');try{await api('/refresh',{});setRevision(v=>v+1);}catch(e){setRefreshError(e.message);}finally{setRefreshing(false);}}

  return <div className="app-shell">
    <Sidebar eyebrow="TUNE AI INTELLIGENCE" title="Business Intelligence" kind="intelligence" open={navOpen} onToggle={()=>setNavOpen(x=>!x)} active={page} onNavigate={navigate}
      items={[{id:'EXEC',label:'Executive Intelligence',icon:BarChart3},{id:'CUSTOMERS',label:'Customer Growth & Retention Intelligence',icon:Users}]}
      utility={<><label className="toggle"><input type="checkbox" checked={ai} onChange={e=>setAI(e.target.checked)}/><span className="toggle-track"/><span>AI assistance</span></label><button className="icon-button" aria-label="Refresh data" title="Refresh data" disabled={refreshing} onClick={refresh}><RefreshCw size={18} className={refreshing?'spin':''}/></button></>}/>
    <main>{refreshError&&<ErrorState message={refreshError}/>}<div key={page} className={page==='EXEC'?'executive-view':undefined}>{page==='EXEC'?<Executive revision={revision} ai={ai}/>:<CustomerIntelligence revision={revision} ai={ai}/>}</div><footer className="tune-footer">Tune Protect Group <span>Trusted Insights. Smarter Business Decisions.</span><Information kind="intelligence"/></footer></main>
  </div>;

}

class RenderBoundary extends React.Component {

  state={failed:false};

  static getDerivedStateFromError(){return {failed:true};}

  render(){return this.state.failed?<div style={{padding:40,maxWidth:700,margin:'auto'}}><h1>Let’s reload your workspace</h1><p style={{margin:'18px 0'}}>The interface encountered an unexpected error. Your information is unchanged.</p><button className="button primary" onClick={()=>location.reload()}>Reload application</button></div>:this.props.children;}
}

createRoot(document.getElementById('root')).render(<RenderBoundary><App/></RenderBoundary>);

