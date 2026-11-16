import React,{useState,useEffect,useRef,useId} from 'react';
import {MessageSquareText,ChevronDown} from 'lucide-react';
import ExecutiveChat from './ExecutiveChat';

export default function FloatingExecutiveChat({scope,ai,send}){
  const [open,setOpen]=useState(false),[seen,setSeen]=useState(false);
  const launcher=useRef(null),windowRef=useRef(null),id=useId();
  function close(){setOpen(false);launcher.current?.focus({preventScroll:true});}
  useEffect(()=>{
    if(!open)return;
    const transcript=windowRef.current?.querySelector('.chat-transcript');
    if(transcript)transcript.scrollTop=transcript.scrollHeight;
    windowRef.current?.querySelector('textarea')?.focus({preventScroll:true});
    function escape(event){if(event.key==='Escape'){event.preventDefault();close();}}
    document.addEventListener('keydown',escape);
    return()=>document.removeEventListener('keydown',escape);
  },[open]);
  return <>
    {seen&&<div ref={windowRef} id={id} className="floating-chat-window" role="dialog" aria-modal="false" aria-label="Ask Tune AI financial assistant" hidden={!open}>
      <ExecutiveChat scope={scope} ai={ai} send={send} onClose={close}/>
    </div>}
    <button ref={launcher} type="button" className="floating-chat-launcher" aria-label={open?'Minimize Ask Tune AI':'Open Ask Tune AI'} aria-expanded={open} aria-controls={seen?id:undefined} onClick={()=>{if(open)close();else{setSeen(true);setOpen(true);}}}>
      {open?<ChevronDown size={20}/>:<MessageSquareText size={20}/>}<span>Ask Tune AI</span>
    </button>
  </>;
}
