/* Location-first, evidence-aware TREE onboarding. Existing scoring/retrofit APIs remain the only calculation owners. */
'use strict';
let intakeRecord=null, intakeEvidence={}, intakeAnswered=[], intakeDraft=null, epcRecords=[];
let applianceItems=[];
try { applianceItems=JSON.parse(localStorage.getItem('tree-appliance-inventory')||'[]');if(!Array.isArray(applianceItems))applianceItems=[]; } catch(_){applianceItems=[];}
const mark = (v)=>v===null||v===undefined?'unknown':String(v);
const tri = (sel) => !sel?.value ? null : sel.value === 'true';
const asNum=(el)=>el && el.value!==''?Number(el.value):null;
function intakeFeedback(message,warning=false){$('#epcStatus').innerHTML=`<p class="${warning?'warning':'fine'}">${safe(message)}</p>`;}
function manualDraft() {return {property_id:'custom_home',name:'My UK home',region:'Unknown', property_type:null, floor_area_m2:null,
 construction_age_band:'unknown',epc_rating:null,heating_type:null,loft_insulated:null,wall_insulated:null,glazing:null,solar_kwp:0,
 smart_controls:null,roof_suitable:null,outdoor_space:null,annual_electricity_kwh:null,annual_gas_kwh:null,
 baseline_source:'synthetic_fallback_if_missing',property_value_gbp:null,electricity_price_gbp_kwh:0.28,gas_price_gbp_kwh:0.07,budget_gbp:5000};}
function readyToReport(){return !!(intakeDraft && Number(intakeDraft.floor_area_m2)>=10 && Number(intakeDraft.floor_area_m2)<=1000 && ['detached','semi_detached','terraced','flat','bungalow'].includes(intakeDraft.property_type));}
function showIntakeStatus(){
 const fields=Object.entries(intakeEvidence);
 $('#intakeEvidence').innerHTML=fields.length?fields.slice(0,10).map(([k,v])=>`<span class="pill">${safe(k.replaceAll('_',' '))}: ${safe(v.status==='homeowner_confirmed'?'confirmed by you':'EPC record')}</span>`).join(''):'<span class="pill">Manual, self-reported inputs</span>';
 $('#finishIntake').disabled=!readyToReport();
}
function setIntake(draft,evidence={}){
 current='custom'; property={...manualDraft(),...draft}; intakeDraft={...property};
 intakeEvidence={...evidence}; intakeAnswered=[];chatSession=null;chosen.clear();
 $('#demoSelect').value='custom'; fillForm(property);showIntakeStatus();nextIntake();
}
function acceptIntakeValue(field,val){
 if(!intakeDraft)return;
 intakeDraft[field]=val; property[field]=val;
 if(val!==null)intakeEvidence[field]={source:'homeowner',status:'homeowner_confirmed'};
 intakeAnswered.push(field);fillForm(property);showIntakeStatus();nextIntake();
}
async function nextIntake(){
 if(!intakeDraft)return;
 try {
   const r=await api('intake/next-question',{property:intakeDraft, answered:intakeAnswered,budget_gbp:intakeDraft.budget_gbp||5000,objective:'money'});
   const area=$('#intakeWizard');
   if(!r.field){area.innerHTML='<p>All currently supported questions have been answered or skipped. You can still edit inputs on the Home tab.</p>';return;}
   let controls='';
   if(r.type==='bool')controls='<div class="button-stack"><button type="button" data-value="true">Yes</button><button type="button" data-value="false">No</button></div>';
   else if(r.type==='choice') controls=`<div class="button-stack">${r.options.map(x=>`<button type="button" data-value="${safe(x)}">${safe(x.replaceAll('_',' '))}</button>`).join('')}</div>`;
   else controls='<form id="intakeAnswerForm" class="inline-confirm"><label>My answer<input type="number" id="intakeAnswer" step="any" min="0" placeholder="Enter a known number" required></label><button class="secondary" type="submit">Confirm →</button></form>';
   area.innerHTML=`<div class="eyebrow">SMART QUESTION · ${safe(r.field.replaceAll('_',' '))}</div><p class="question-title">${safe(r.question)}</p><p class="fine">${safe(r.why)}</p>${controls}<div class="buttons"><button class="ghost" type="button" id="skipIntake">I don't know / skip</button></div><p class="fine">${r.missing.length} unconfirmed field(s) still eligible for questions · scores and savings update when evidence changes.</p>`;
   area.querySelectorAll('[data-value]').forEach(el=>el.addEventListener('click',()=>acceptIntakeValue(r.field,r.type==='bool'?el.dataset.value==='true':el.dataset.value)));
   if(r.type==='number') $('#intakeAnswerForm').addEventListener('submit',e=>{e.preventDefault();const v=Number($('#intakeAnswer').value);if(!Number.isFinite(v)||v<0||(r.field==='floor_area_m2'&&(v<10||v>1000))){notice('Enter a sensible number: area must be between 10 and 1000 square metres.');return;}acceptIntakeValue(r.field,v);});
   $('#skipIntake').addEventListener('click',()=>{intakeAnswered.push(r.field);nextIntake();});
 }catch(e){$('#intakeWizard').textContent='Question engine unavailable: '+e.message;}
}
$('#useLocation').addEventListener('click',()=>doAction(async()=>{
  if(!navigator.geolocation)throw Error('Geolocation is not available. Please type your UK postcode.');
  intakeFeedback('Requesting permission. The postcode lookup is optional.');
  const pos=await new Promise((resolve,reject)=>navigator.geolocation.getCurrentPosition(resolve,reject,{enableHighAccuracy:false,timeout:8000,maximumAge:0}));
  const result=await api('intake/geolocate-postcode',{
    latitude:pos.coords.latitude,longitude:pos.coords.longitude});
  intakeFeedback(result.message,true);
  if(result.postcode){$('#postcode').value=result.postcode;$('#postcode').focus();}
  // Do not automatically fetch anyone's certificate: the user must search and select the exact home.
}));
$('#postcodeForm').addEventListener('submit',e=>{e.preventDefault();doAction(async()=>{
 const pc=$('#postcode').value.trim(); intakeFeedback('Checking provider access and property records…');$('#epcMatches').innerHTML='';
 const data=await api('intake/epc/search?postcode='+encodeURIComponent(pc));
 intakeFeedback(data.message, data.status!=='live_epc');
 epcRecords=data.properties||[];
 if(epcRecords.length){$('#epcMatches').innerHTML=epcRecords.map((x,i)=>`<button class="epc-choice" type="button" data-record="${i}"><b>${safe(x.address)}</b><small>${safe(x.postcode)} · EPC ${safe(x.rating||'unknown')} · lodged ${safe(x.lodged||'date unavailable')}</small><small>Use this exact address →</small></button>`).join('');
   $$('#epcMatches .epc-choice').forEach(b=>b.addEventListener('click',()=>doAction(async()=>{
      const x=epcRecords[Number(b.dataset.record)];if(!x)return;
      const ok=window.confirm(`I confirm the EPC record is for my property:\n${x.address}, ${x.postcode}\nEPCs can be outdated. Continue?`);
      if(!ok)return;
      const mapped=await api('intake/epc/confirm',x.selection);
      setIntake(mapped.property,mapped.evidence);intakeFeedback('Selected EPC record; confirm the remaining building details.');
   })));
 } else if(data.status==='live_epc'){intakeFeedback('No certificates were returned for this postcode. Please use manual entry.',true);}
});});
$('#manualStart').addEventListener('click',()=>{setIntake(manualDraft());intakeFeedback('Manual mode: no live EPC record has been retrieved.');});
$('#finishIntake').addEventListener('click',()=>doAction(async()=>{
 if(!readyToReport())throw Error('Please confirm property type and floor area before calculating your score.');
 property={...intakeDraft};fillForm(property);await calculateReport();view('home');
}));
$('#demoSelect').addEventListener('change',()=>{if($('#demoSelect').value!=='custom'){
 intakeFeedback('This is a fictional demo property, not a live EPC.');view('home');
 }else{setIntake(manualDraft());}}
);
$('#inspectEvidence').addEventListener('click',()=>doAction(async()=>{
 const file=$('#homeEvidence').files[0];if(!file)throw Error('Select a file first.');
 const fd=new FormData();fd.append('file',file,file.name);const resp=await fetch('/api/evidence/inspect',{method:'POST',body:fd});
 let r={};try{r=await resp.json()}catch(_){}
 if(!resp.ok)throw Error(typeof r.detail==='string'?r.detail:'Upload inspection failed');
 const cand=r.analysis?.candidates||[];
 $('#uploadEvidence').innerHTML=`<div class="notice-card"><strong>${safe(r.message)}</strong><p class="fine">${safe(r.analysis?.warning||'No extracted consumption is available.')} No file is saved.</p>${cand.map((x,i)=>`<div class="appliance-entry"><span>${safe(x.fuel)}: ${fmt(x.fuel==='water'?x.value_m3:x.value_kwh,1)} ${x.fuel==='water'?'m³':'kWh'} — period unknown</span><button class="secondary" data-confirm-bill="${i}">Confirm only if annual</button></div>`).join('')}</div>`;
 $$('[data-confirm-bill]',$('#uploadEvidence')).forEach(btn=>btn.addEventListener('click',()=>{
   const x=cand[Number(btn.dataset.confirmBill)];if(!x||!intakeDraft){notice('Choose your property first.');return;}
   if(!window.confirm(`Is ${x.fuel==='water'?x.value_m3:x.value_kwh} ${x.fuel==='water'?'m³':'kWh'} the TOTAL annual ${x.fuel} usage for THIS home, not a single billing period?`))return;
   if(x.fuel==='water'){ $('#waterAnnual').value=String(x.value_m3);$('#uploadEvidence').insertAdjacentHTML('beforeend','<p class="pill">Annual water volume confirmed for separate sustainability audit, NOT energy score.</p>');return;}
   acceptIntakeValue(x.fuel==='gas'?'annual_gas_kwh':'annual_electricity_kwh',x.value_kwh);
   $('#uploadEvidence').insertAdjacentHTML('beforeend','<p class="pill">Value recorded as homeowner-confirmed annual use.</p>');
 }));
}));

$('#reviewImage').addEventListener('click',()=>doAction(async()=>{
 const file=$('#homeEvidence').files[0];if(!file)throw Error('Select a photo first.');
 if(!$('#visionConsent').checked)throw Error('Explicit consent is required to send a photo to Gemini.');
 if(!/\.(png|jpe?g|webp)$/i.test(file.name))throw Error('Optional Gemini vision accepts an image only, not a video or PDF.');
 const fd=new FormData();fd.append('file',file,file.name);fd.append('consent','true');
 const resp=await fetch('/api/evidence/vision-candidates',{method:'POST',body:fd});let r={};try{r=await resp.json()}catch(_){}
 if(!resp.ok)throw Error(r.detail||'Gemini review unavailable.');
 $('#uploadEvidence').innerHTML=`<div class="notice-card"><strong>Optional Gemini photo observations · NOT VERIFIED</strong><p>${safe(r.candidate_observations)}</p><p class="fine">${safe(r.privacy)} Confirm any relevant facts manually. These observations were NOT used to generate scores or energy estimates.</p></div>`;
}));

function saveAppliances(){localStorage.setItem('tree-appliance-inventory',JSON.stringify(applianceItems));}
function renderInventory(){
 const total=applianceItems.reduce((a,x)=>a+(Number(x.quantity)||0),0);if($('#homeApplianceCount'))$('#homeApplianceCount').textContent=fmt(total);
 $('#applianceList').innerHTML=applianceItems.length?applianceItems.map((x,i)=>`<div class="appliance-entry"><div><strong>${safe(x.name)} × ${fmt(x.quantity)}</strong><p class="fine">${x.rated_watts===null?'Power unknown':fmt(x.rated_watts)+' W'} · ${x.hours_per_day===null?'Daily hours unknown':fmt(x.hours_per_day,1)+' h/day'}</p></div><button class="ghost" data-remove-app="${i}">Remove</button></div>`).join(''):'<p class="fine">No appliances entered yet. Start with the ones you know.</p>';
 $$('[data-remove-app]',$('#applianceList')).forEach(b=>b.addEventListener('click',()=>{applianceItems.splice(Number(b.dataset.removeApp),1);saveAppliances();renderInventory();runHousehold();}));
}
function householdPayload(){return {appliances:applianceItems,occupants:asNum($('#occupants')),kitchen_waste_kg_week:asNum($('#foodWaste')),
 annual_water_m3:asNum($('#waterAnnual')),outdoor_water_reuse_possible:tri($('#waterReuse')),garden:tri($('#garden')),off_peak_shift_possible:tri($('#offpeak')),has_solar_water_heater:tri($('#solarWater')),paper_recycling:tri($('#paperRecycle')),
 recent_electricity_bill_kwh:property?.annual_electricity_kwh??null};}
async function runHousehold(){
 const payload=householdPayload();const [a,ex]=await Promise.all([api('household/appliances',payload),api('household/extensions',payload)]);
 $('#applianceResults').innerHTML=`<div class="metric-grid">${item('Appliances counted',fmt(a.count))}${item('Known-item estimated electricity',fmt(a.estimated_annual_kwh_for_known_items,1)+' kWh/yr')}</div><p class="fine">${safe(a.warning)}</p>`;
 $('#extendedResults').innerHTML=`<h3>Additional green ideas (not scored)</h3>${ex.water.annual_water_m3===null?'':'<p class="fine">From confirmed water bill: '+fmt(ex.water.annual_water_m3,1)+' m³/year · '+fmt(ex.water.litres_per_day,1)+' litres/day. Not part of the formal energy score.</p>'}${ex.extensions.map(x=>`<div class="notice-card"><strong>${safe(x.title)}</strong><span class="tag">${safe(x.category)} · ${safe(x.suitability)}</span><p class="fine">${safe(x.reason)}</p></div>`).join('')}<p class="fine">${safe(ex.warning)}</p>`;
}
$('#addAppliance').addEventListener('click',()=>doAction(async()=>{
 const name=$('#appName').value.trim();if(!name||name.length>70)throw Error('Enter a name of up to 70 characters.');
 const qty=Number($('#appQty').value);if(!Number.isInteger(qty)||qty<1||qty>80)throw Error('Quantity must be 1–80.');
 const watts=asNum($('#appWatts')),hours=asNum($('#appHours')),standby=asNum($('#appStandby'));
 if((watts!==null&&(watts<0||watts>30000))||(hours!==null&&(hours<0||hours>24))||(standby!==null&&(standby<0||standby>1000)))throw Error('Invalid appliance power or usage hours.');
 if(applianceItems.length>=60)throw Error('Inventory limit: 60 entries.');
 applianceItems.push({name,quantity:qty,rated_watts:watts,hours_per_day:hours,standby_watts:standby,days_per_year:365});saveAppliances();renderInventory();await runHousehold();
 $('#appName').value='';$('#appWatts').value='';$('#appHours').value='';$('#appStandby').value='';
}));
$('#resetAppliances').addEventListener('click',()=>doAction(async()=>{applianceItems=[];saveAppliances();renderInventory();await runHousehold();}));
$('#runHousehold').addEventListener('click',()=>doAction(runHousehold));
async function checkAlerts(){const r=await api('household/notifications',householdPayload());
 if(property && report){const finance=await api('household/finance-tips',property);r.notifications.push(...finance.notifications);}
 $('#alertsList').innerHTML=(report?`<div class="notice-card"><strong>Green Home Score check: ${fmt(report.score.score)}/100</strong><p class="fine">Your score changes when property details or energy evidence change, not automatically every day. Review uncertain inputs before acting.</p></div>`:'<div class="notice-card"><strong>Complete your home profile</strong><p class="fine">Calculate your Green Home Score after confirming property details.</p></div>')+(r.notifications.length?r.notifications.map(n=>`<div class="notice-card"><strong>${safe(n.title)}</strong><p class="fine">${safe(n.body)}</p></div>`).join(''):'<p class="fine">No other reminders due from the supplied information.</p>');
 return r.notifications;}
$('#checkAlerts').addEventListener('click',()=>doAction(checkAlerts));
$('#enableReminders').addEventListener('click',()=>doAction(async()=>{
 if(!('Notification' in window))throw Error('This browser does not support Notification permission. In-app reminders are still available.');
 const permission=await Notification.requestPermission();if(permission!=='granted')throw Error('Notification permission not granted; in-app reminders still work.');
 localStorage.setItem('tree-daily-reminder','enabled');await checkAlerts();notice('Enabled: reminders can appear when you open TREE on a new day. TREE cannot notify you while closed.');
}));
async function notifyOnOpen(){
 if(localStorage.getItem('tree-daily-reminder')!=='enabled'||!('Notification' in window)||Notification.permission!=='granted')return;
 const date=new Date().toLocaleDateString('en-CA');if(localStorage.getItem('tree-last-notification')===date)return;
 try{const alerts=await checkAlerts();if(alerts.length){new Notification('TREE · Daily green home check',{body:alerts[0].title+' — '+alerts[0].body.slice(0,110)});localStorage.setItem('tree-last-notification',date);}}catch(_){}
}
renderInventory();
runHousehold().catch(()=>{});
notifyOnOpen();
