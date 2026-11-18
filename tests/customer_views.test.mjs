import test from 'node:test';
import assert from 'node:assert/strict';
import {customerSegments,renewalTiming,recordedHoldings,friendlyCustomerText} from '../apps/ai-intelligence-react/src/shared/customerViews.mjs';

test('overview sums existing aggregate cells across value and channel without using customer rows',()=>{
  const cells=[
    {RETENTION_RISK_BAND:'High',LIFETIME_VALUE_BAND:'Top',PREFERRED_CHANNEL:'Agency',CUSTOMERS:3},
    {RETENTION_RISK_BAND:'High',LIFETIME_VALUE_BAND:'Top',PREFERRED_CHANNEL:'Direct',CUSTOMERS:2},
    {RETENTION_RISK_BAND:'Low',LIFETIME_VALUE_BAND:'Low',PREFERRED_CHANNEL:'Agency',CUSTOMERS:7},
  ];
  const before=JSON.stringify(cells);
  assert.deepEqual(customerSegments(cells,'RETENTION_RISK_BAND'),[{label:'High',count:5},{label:'Low',count:7}]);
  assert.deepEqual(customerSegments(cells,'LIFETIME_VALUE_BAND'),[{label:'Top',count:5},{label:'Low',count:7}]);
  assert.equal(JSON.stringify(cells),before);
});
test('bounded worklists cannot be mistaken for portfolio aggregates',()=>{
  assert.deepEqual(customerSegments([{CUSTOMER_ID:'C1',RETENTION_RISK_BAND:'High'}],'RETENTION_RISK_BAND'),[]);
});
test('missing or invalid aggregate counts stay unavailable instead of becoming zero',()=>{
  for(const count of [null,undefined,-1,1.5,'invalid','',true,false])assert.deepEqual(customerSegments([{RETENTION_RISK_BAND:'High',CUSTOMERS:count}],'RETENTION_RISK_BAND'),[]);
});
test('unknown bands are retained and zero is a valid source count',()=>{
  assert.deepEqual(customerSegments([{RETENTION_RISK_BAND:null,CUSTOMERS:2},{RETENTION_RISK_BAND:'Low',CUSTOMERS:0}],'RETENTION_RISK_BAND'),[{label:'Low',count:0},{label:'Not specified',count:2}]);
});
test('renewal presentation uses the SQL flag and preserves missing timing',()=>{
  assert.equal(renewalTiming(true),'Upcoming renewal');
  assert.equal(renewalTiming(false),'Outside renewal window');
  assert.equal(renewalTiming(null),'Timing unavailable');
  assert.equal(renewalTiming(undefined),'Timing unavailable');
});

test('holdings show only source flags and keep missing information explicit',()=>{
  assert.equal(recordedHoldings({HOLDS_MOTOR:'Yes',HOLDS_TRAVEL:'Yes'}),'Motor + Travel');
  assert.equal(recordedHoldings({HOLDS_MOTOR:'No',HOLDS_TRAVEL:'Yes'}),'Travel');
  assert.equal(recordedHoldings({HOLDS_MOTOR:'No',HOLDS_TRAVEL:'No'}),'No Motor or Travel cover on record');
  assert.match(recordedHoldings({HOLDS_MOTOR:'Yes',HOLDS_TRAVEL:null}),/Motor.*Travel holdings unavailable/);
});

test('conversation wording preserves retention-first and review requirements',()=>{
  const high=friendlyCustomerText('Review retention needs first, then consider a Fire discussion.');
  assert.match(high,/Start with the customer’s retention needs/);
  assert.ok(high.indexOf('retention needs')<high.indexOf('conversation about Fire'));
  assert.match(high,/Confirm existing cover and suitability before making an offer/);
  const low=friendlyCustomerText('Prepare a human-reviewed Personal Accident needs discussion through Agency.');
  assert.match(low,/through Agency/);
  assert.match(low,/whether Personal Accident meets/);
  assert.match(low,/Review their existing cover and suitability/);
  assert.equal(friendlyCustomerText('Unrecognized source information.'),'Unrecognized source information.');
});
