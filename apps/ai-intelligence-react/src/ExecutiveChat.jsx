import React,{useState,useRef,useEffect} from 'react';
import {MessageSquareText,ArrowUp,Sparkles,LoaderCircle,ChevronDown,RotateCcw,X} from 'lucide-react';

import {sourceLabel} from './shared/presentation.mjs';

const SUGGESTIONS=['Which business line has the largest GWP shortfall?','Which channel is furthest below plan?','How does the net loss ratio compare for Motor and Travel?'];
const month=date=>new Date(date+'T00:00:00').toLocaleDateString('en-GB',{month:'short',year:'numeric'});

export default function ExecutiveChat({scope,ai,send,onClose}){
  const [turns,setTurns]=useState([]),[question,setQuestion]=useState(''),[busy,setBusy]=useState(false);
  const controller=useRef(null),latest=useRef(null),input=useRef(null);
  useEffect(()=>()=>controller.current?.abort(),[]);
  useEffect(()=>{if(turns.length&&latest.current?.getClientRects().length)latest.current.scrollIntoView({block:'nearest'});},[turns.length,busy]);
  async function ask(text){
    const q=text.trim();if(!q||busy)return;
    const prior=turns.filter(t=>!t.error).map(t=>t.question).slice(-4);
    setQuestion('');setBusy(true);setTurns(t=>[...t.slice(-11),{question:q,pending:true}]);
    controller.current=new AbortController();
    try{
      const answer=await send({scope,question:q,history:prior,ai},controller.current.signal);
      setTurns(t=>[...t.slice(0,-1),{question:q,...answer}]);
    }catch(e){
      if(e.name!=='AbortError')setTurns(t=>[...t.slice(0,-1),{question:q,error:'I couldn’t retrieve verified results. Please try again; no answer has been invented.'}]);
    }finally{setBusy(false);if(input.current?.getClientRects().length)input.current.focus({preventScroll:true});}
  }
  return <div className="executive-chat">
    <div className="chat-heading"><div><h3><MessageSquareText size={19}/>Ask Tune AI</h3><p>Ask about the financial results in this view.</p></div><div className="chat-header-actions"><button type="button" className="icon-button" disabled={busy||!turns.length} onClick={()=>setTurns([])} aria-label="Clear chat" title="Clear chat"><RotateCcw size={16}/></button>{onClose&&<button type="button" className="icon-button" aria-label="Close chat" title="Close chat" onClick={onClose}><X size={18}/></button>}</div></div>
    <div className="chat-scope"><span className="dot"/>{month(scope.start)} – {month(scope.end)}<span>·</span>{scope.line==='All'?'Motor + Travel':scope.line}<span>·</span>{scope.channel==='All'?'All channels':scope.channel}</div>
    {!turns.length&&<div className="chat-suggestions">{SUGGESTIONS.map(text=><button key={text} disabled={busy} onClick={()=>ask(text)}><Sparkles size={13}/>{text}</button>)}</div>}
    {!!turns.length&&<div className="chat-transcript" role="log" aria-label="Financial questions and answers" aria-live="polite" aria-busy={busy}>{turns.map((turn,i)=><div className="chat-turn" key={i} ref={i===turns.length-1?latest:null}>
      <div className="chat-question"><span>You</span><p>{turn.question}</p></div>
      <div className="chat-answer"><span className="assistant-label"><Sparkles size={14}/>Tune AI</span>
        {turn.pending?<div className="chat-thinking" role="status"><LoaderCircle size={15} className="spin"/>Reviewing the selected financial results…</div>:turn.error?<p role="alert" className="negative">{turn.error}</p>:<>
          <p>{turn.answer}</p>
          {turn.evidence.length>0&&<ul>{turn.evidence.map((e,j)=><li key={e.id}>{e.text}<span className="evidence-number">[{j+1}]</span></li>)}</ul>}
          <div className="chat-answer-source">{sourceLabel(turn.source)}</div>
          {turn.evidence.length>0&&<details><summary>Supporting evidence<ChevronDown size={14}/></summary>{turn.evidence.map((e,j)=><div className="chat-evidence" key={e.id}><strong>[{j+1}] {e.text}</strong><p>{e.source}</p></div>)}<p>{turn.note}</p></details>}
        </>}
      </div>
    </div>)}</div>}
    <form className="chat-composer" onSubmit={e=>{e.preventDefault();ask(question);}}><textarea ref={input} value={question} maxLength={600} disabled={busy} onChange={e=>setQuestion(e.target.value)} placeholder="Ask about premium, plan variance, claims or loss ratio…" aria-label="Ask a financial question" rows={2} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey&&!e.nativeEvent.isComposing){e.preventDefault();ask(question);}}}/><button type="submit" className="chat-send" disabled={busy||!question.trim()} aria-label="Send question">{busy?<LoaderCircle className="spin" size={18}/>:<ArrowUp size={19}/>}</button></form>
    <p className="chat-limit">{ai?'AI-assisted answers':'AI assistance is off · Calculated answers remain available'} · Uses verified financial results. Review the supporting evidence before acting. Changing filters starts a new conversation.</p>
  </div>;
}
