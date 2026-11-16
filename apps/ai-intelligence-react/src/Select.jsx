import React,{useState,useEffect,useRef,useId} from 'react';
import {ChevronDown,Check} from 'lucide-react';

export default function Select({label,value,onChange,options,icon:Icon}){
  const items=options.map(o=>typeof o==='string'?{value:o,label:o}:o);
  const selected=items.findIndex(o=>o.value===value);
  const [open,setOpen]=useState(false),[active,setActive]=useState(0),[up,setUp]=useState(false);
  const root=useRef(null),trigger=useRef(null),list=useRef(null),id=useId(),typed=useRef(''),timer=useRef(null);
  useEffect(()=>{if(!open)return;const close=e=>{if(!root.current?.contains(e.target))setOpen(false);};document.addEventListener('pointerdown',close);return()=>document.removeEventListener('pointerdown',close);},[open]);
  useEffect(()=>{if(open)list.current?.querySelector(`[data-index="${active}"]`)?.scrollIntoView({block:'nearest'});},[active,open]);
  useEffect(()=>()=>clearTimeout(timer.current),[]);
  function show(){const rect=trigger.current.getBoundingClientRect();setUp(rect.bottom+280>window.innerHeight&&rect.top>280);setActive(Math.max(0,selected));setOpen(true);}
  function choose(index){if(items[index])onChange(items[index].value);setOpen(false);trigger.current?.focus();}
  function keydown(e){
    if(e.key==='Tab'){setOpen(false);return;}
    if(e.key==='Escape'){e.preventDefault();setOpen(false);return;}
    if(['ArrowDown','ArrowUp','Home','End','Enter',' '].includes(e.key)){
      e.preventDefault();
      if(!open){show();return;}
      if(e.key==='Enter'||e.key===' '){choose(active);return;}
      setActive(i=>e.key==='Home'?0:e.key==='End'?items.length-1:Math.max(0,Math.min(items.length-1,i+(e.key==='ArrowDown'?1:-1))));
    }else if(e.key.length===1&&!e.ctrlKey&&!e.metaKey&&!e.altKey){
      e.preventDefault();typed.current+=e.key.toLowerCase();clearTimeout(timer.current);timer.current=setTimeout(()=>{typed.current='';},700);
      const index=items.findIndex(o=>o.label.toLowerCase().startsWith(typed.current));
      if(index>=0){if(!open)show();setActive(index);}
    }
  }
  return <div ref={root} className={'select-control custom-select '+(open?'is-open':'')}>
    <button ref={trigger} type="button" role="combobox" className="select-trigger" aria-label={label} aria-expanded={open} aria-haspopup="listbox" aria-controls={id} aria-activedescendant={open?`${id}-${active}`:undefined} onClick={()=>open?setOpen(false):show()} onKeyDown={keydown}>
      {Icon&&<Icon size={16}/>}<span>{items[selected]?.label||'Select…'}</span><ChevronDown size={15}/>
    </button>
    {open&&<div ref={list} id={id} role="listbox" aria-label={label} className={'select-menu '+(up?'opens-up':'')}>
      {items.map((o,index)=><div key={o.value} id={`${id}-${index}`} data-index={index} role="option" aria-selected={o.value===value} className={'select-option '+(index===active?'highlighted':'')+(o.value===value?' chosen':'')} onMouseEnter={()=>setActive(index)} onMouseDown={e=>e.preventDefault()} onClick={()=>choose(index)}><span>{o.label}</span>{o.value===value&&<Check size={15}/>}</div>)}
    </div>}
  </div>;
}
