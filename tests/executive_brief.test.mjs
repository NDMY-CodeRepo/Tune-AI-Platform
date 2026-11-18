import test from 'node:test';
import assert from 'node:assert/strict';
import {managementBrief} from '../apps/ai-intelligence-react/src/shared/executiveBrief.mjs';

const money=value=>`RM ${value}`,pct=value=>`${(value*100).toFixed(1)}%`;
const row=(LEVEL,variance,extra={})=>({LEVEL,GWP:100,PLAN_GWP:110,GWP_VARIANCE:variance,GWP_VARIANCE_PCT:variance/100,KEY_COUNT:1,MISSING_ACTUAL:0,MISSING_PLAN:0,...extra});
test('brief uses current aggregate gaps, names the line/channel and does not add overlapping amounts',()=>{
  const data=[row('TOTAL',-20),row('LINE',-15,{LINE_OF_BUSINESS:'Motor'}),row('LINE',-5,{LINE_OF_BUSINESS:'Travel'}),row('CHANNEL',-12,{DISTRIBUTION_CHANNEL:'Agency'})];
  const snapshot=JSON.stringify(data),result=managementBrief(data,money,pct);
  assert.match(result.finding,/RM 20 \(20.0%\) below/);
  assert.match(result.contributors[0],/Motor is RM 15/);
  assert.match(result.contributors[1],/Agency channel is RM 12/);
  assert.match(result.action,/Start with Motor and the Agency channel/);
  assert.match(result.action,/establish the reasons/);
  assert.equal(JSON.stringify(data),snapshot);
});
test('changed scope uses only its supplied results and never calls an above-plan amount a shortfall',()=>{
  const result=managementBrief([row('TOTAL',10),row('LINE',10,{LINE_OF_BUSINESS:'Travel'})],money,pct);
  assert.match(result.finding,/above/);
  assert.match(result.contributors[0],/Travel.*above/);
  assert.doesNotMatch(JSON.stringify(result),/Motor|Agency|Start with/);
});
test('positive total still identifies a negative business area without inventing causes',()=>{
  const result=managementBrief([row('TOTAL',5),row('LINE',-2,{LINE_OF_BUSINESS:'Motor'})],money,pct);
  assert.match(result.finding,/above/);
  assert.match(result.action,/Start with Motor/);
});
test('invalid coverage or missing amounts are withheld, not shown as zero',()=>{
  for(const update of [{MISSING_PLAN:1},{MISSING_ACTUAL:1},{GWP_VARIANCE:null},{GWP:null},{PLAN_GWP:null},{KEY_COUNT:0}]){
    const result=managementBrief([row('TOTAL',-2,update),row('LINE',-4,{LINE_OF_BUSINESS:'Motor',...update})],money,pct);
    assert.match(result.finding,/cannot reliably compare/);
    assert.deepEqual(result.contributors,[]);
    assert.doesNotMatch(JSON.stringify(result),/RM 0/);
  }
});
test('zero gap and unavailable percentage have clear distinct wording',()=>{
  assert.match(managementBrief([row('TOTAL',0)],money,pct).finding,/on plan/);
  const result=managementBrief([row('TOTAL',-5,{GWP_VARIANCE_PCT:null})],money,pct);
  assert.match(result.finding,/RM 5 below/);
  assert.doesNotMatch(result.finding,/%|null/);
});
