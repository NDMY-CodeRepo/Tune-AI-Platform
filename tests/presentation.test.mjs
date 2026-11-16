import test from 'node:test';
import assert from 'node:assert/strict';
import {recordTitle,recordText,profileName,profileReference,displayMeta,formatDate,formatNumber,sourceLabel,RECORD_LABELS} from '../apps/ai-intelligence-react/src/shared/presentation.mjs';

test('illustrative title cleanup leaves ordinary business text intact',()=>{
  assert.equal(recordTitle('[Demo] Motor claims report'),'Motor claims report');
  assert.equal(recordTitle('[Validation] Workflow check'),'Workflow check');
  assert.equal(recordTitle('Test results for claims reconciliation'),'Test results for claims reconciliation');
  const original='[Demo] Motor claims report';recordTitle(original);assert.equal(original,'[Demo] Motor claims report');
});
test('seed wording stays explicitly illustrative without implying delivery',()=>{
  const text=recordText('Synthetic demonstration resolution. No actual report has been delivered.');
  assert.equal(text,'Illustrative resolution. No report delivery is implied.');
  assert.match(recordText('DEMO-OUTPUT: Motor report'),/^Illustrative reference:/);
});
test('profile labels round-trip to unchanged requester and owner identifiers',()=>{
  for(const id of ['motor.demo','demo.engineer','finance.user'])assert.equal(profileReference(profileName(id)),id);
});
test('professional metadata labels preserve workflow states and transitions',()=>{
  const meta={statuses:['NEW','TRIAGED','WAITING_FOR_BU'],status_labels:{NEW:'New',TRIAGED:'Triaged',WAITING_FOR_BU:'Waiting for BU'},transitions:{NEW:['NEW','TRIAGED']},categories:['REPORT_REQUEST']};
  const before=JSON.stringify(meta),view=displayMeta(meta);
  assert.deepEqual(view.statuses,meta.statuses);assert.equal(view.transitions,meta.transitions);
  assert.equal(view.status_labels.WAITING_FOR_BU,'Awaiting business response');
  assert.equal(JSON.stringify(meta),before);
});
test('existing presentation record filters retain original API values',()=>{
  assert.deepEqual(Object.keys(RECORD_LABELS),['Exclude validation','Synthetic demo only','All records']);
  assert.equal(RECORD_LABELS['Exclude validation'],'Business requests');
});
test('business date and count formats retain values and unavailable states',()=>{
  assert.equal(formatDate('2026-11-16'),'16 Nov 2026');assert.equal(formatNumber(10566),'10,566');
  assert.equal(formatNumber(null),'Unavailable');assert.equal(formatDate(null),'Not specified');
});
test('AI source labels distinguish calculated fallback from assisted evidence',()=>{
  assert.equal(sourceLabel('AI-curated explanation · Snowflake Cortex'),'AI-assisted explanation');
  assert.equal(sourceLabel('Deterministic explanation · Cortex unavailable or response rejected'),'Calculated explanation · AI assistance unavailable');
  assert.equal(sourceLabel('Rule-based recommendation'),'Business-rules explanation');
});
