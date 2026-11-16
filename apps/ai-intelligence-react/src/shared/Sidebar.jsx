import React,{useRef} from 'react';
import {Info,Menu,X} from 'lucide-react';
import './sidebar.css';

export function Information({kind,settings}){
  const dialog=useRef(null),desk=kind==='desk';
  return <>
    <button type="button" className="tune-information" onClick={()=>dialog.current?.showModal()}><Info size={14}/><span>Information</span></button>
    <dialog ref={dialog} className="tune-information-dialog" aria-label="Workspace information">
      <div className="tune-information-heading"><h2>Workspace information</h2><button type="button" className="tune-close" aria-label="Close information" onClick={()=>dialog.current?.close()}><X size={19}/></button></div>
      <h3>Illustrative Data</h3>
      <p>{desk?'This workspace includes illustrative requests and report catalogue entries. They are not Tune Protect production records and do not establish that business work or report delivery has occurred. Requests submitted here are retained in the request register.':'The financial and customer information is illustrative data held in Snowflake. It does not represent Tune Protect production results or customer records.'}</p>
      <h3>{desk?'Workspace access':'Measures and recommendations'}</h3>
      <p>{desk?'Workspace and profile selectors change the working view and identity. They are not sign-in, authentication or production authorization. Internal notes and workflow controls use the selected workspace.':'Financial measures use established accounting definitions. Retention and cross-sell recommendations use existing business rules. A Travel recommendation is a candidate for human review; eligibility, suitability and propensity are not established.'}</p>
      <h3>{desk?'Available capabilities':'AI assistance and data freshness'}</h3>
      <p>{desk?'Requests, ownership, status updates and conversations are retained. File attachments and external email, Teams, Jira or ServiceNow notifications are not implemented. Report links are shown only when provided; an illustrative catalogue entry does not establish report availability.':'Snowflake Cortex selects supporting evidence from calculated results; it cannot generate or execute user-supplied SQL. Calculated explanations remain available when AI is off or unavailable. Reporting reads may be cached for up to five minutes; Refresh data requests the latest results. No automatic customer contact or external notifications are sent.'}</p>
      {settings&&<details className="tune-view-settings"><summary>View settings</summary>{settings}<p>Quality-check requests are excluded from the normal business view. Their history is retained and remains accessible through All requests.</p></details>}
      <button type="button" className="tune-information-done" onClick={()=>dialog.current?.close()}>Close</button>
    </dialog>
  </>;
}

export default function Sidebar({eyebrow,title,items,active,onNavigate,open,onToggle,utility,kind='intelligence'}){
  return <>
    <button type="button" className="tune-mobile-menu" aria-label={open?'Close navigation':'Open navigation'} aria-expanded={open} onClick={onToggle}>{open?<X size={22}/>:<Menu size={22}/>}</button>
    {open&&<div className="tune-nav-scrim" onClick={onToggle}/>}
    <aside className={'tune-sidebar '+(open?'is-open':'')} aria-label={kind==='desk'?'Data Service Desk sidebar':'Business Intelligence sidebar'}>
      <div className="tune-brand"><img src="/tune-logo.png" alt="Tune Protect logo"/><span>{eyebrow}</span><h2>{title}</h2></div>
      <nav className="tune-nav" aria-label="Main navigation">{items.map(({id,label,icon:Icon})=><button type="button" key={id} className={active===id?'is-active':''} aria-current={active===id?'page':undefined} onClick={()=>onNavigate(id)}><Icon size={19}/><span>{label}</span></button>)}</nav>
      <div className="tune-sidebar-bottom">{utility&&<div className="tune-sidebar-utility">{utility}</div>}</div>
    </aside>
  </>;
}
