import React,{useEffect,useRef,useId} from 'react';
import {X,ArrowLeft} from 'lucide-react';

export default function CustomerOpportunityDrawer({customer,onClose,children}){
  const dialog=useRef(null),closeButton=useRef(null),title=useId();
  useEffect(()=>{
    const node=dialog.current,previousOverflow=document.body.style.overflow;
    node.showModal();document.body.style.overflow='hidden';
    closeButton.current?.focus({preventScroll:true});
    return()=>{node.close();document.body.style.overflow=previousOverflow;};
  },[]);
  function backdrop(event){
    if(event.target!==event.currentTarget)return;
    const box=event.currentTarget.getBoundingClientRect();
    if(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom)onClose();
  }
  return <dialog ref={dialog} className="opportunity-drawer" aria-labelledby={title} onCancel={event=>{event.preventDefault();onClose();}} onClick={backdrop}>
    <header className="opportunity-drawer-header"><div><div className="eyebrow">CUSTOMER {customer}</div><h2 id={title}>Product recommendation</h2></div><button ref={closeButton} type="button" className="drawer-close" aria-label="Close product recommendation" onClick={onClose}><X size={21}/></button></header>
    <div className="opportunity-drawer-content">{children}</div>
    <footer className="opportunity-drawer-footer"><button type="button" className="button" onClick={onClose}><ArrowLeft size={15}/>Back to candidates</button></footer>
  </dialog>;
}
