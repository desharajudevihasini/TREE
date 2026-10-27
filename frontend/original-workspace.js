/* Only presentation/navigation. All energy calculations remain in Python. */
'use strict';
(function(){
  const destinations=new Set(['locate','home','plan','future','chat','memory','household','methods']);
  const route=()=>{
    const requested=decodeURIComponent(window.location.hash.slice(1)||'locate');
    if(destinations.has(requested)&&typeof view==='function') view(requested);
  };
  document.querySelectorAll('[data-step]').forEach(button=>button.addEventListener('click',()=>{
    window.location.hash=button.dataset.step;
    if(typeof view==='function')view(button.dataset.step);
  }));
  document.querySelectorAll('[data-chat-prompt]').forEach(button=>button.addEventListener('click',()=>{
    const input=document.getElementById('chatText');
    if(!input)return;
    input.value=button.dataset.chatPrompt;
    if(typeof view==='function')view('chat');
    input.focus();
  }));
  window.addEventListener('hashchange',route);
  // basic.js and onboarding.js are defer-loaded before this script.
  route();
})();
