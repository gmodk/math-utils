import {fmt} from './rendering.js';
const engine=document.body.dataset.engine;
const renderers={correlation:()=>import('./correlation.js'),'multiple-regression':()=>import('./multiple-regression.js'),'bias-variance':()=>import('./bias-variance.js'),bayesian:()=>import('./bayesian.js')};
const dataControls={correlation:[], 'multiple-regression':['beta1','beta2','rho','sigma','n'],'bias-variance':['sigma','n'],bayesian:['beta','sigma','n']};
const viewControls=new Set(['yaw','pitch','point']);
let seed=2026,latest=null,controller=null,timer=null,sequence=0,renderer;
const status=document.getElementById('request-message'),state=document.querySelector('.request-state');
function newSeed(){seed=(seed+1)>>>0;}
function labels(){for(const input of document.querySelectorAll('input[type=range]')){const target=input.parentElement.querySelector('div:last-child');if(target)target.textContent=viewControls.has(input.id)&&input.id!=='point'?`${input.value}°`:Number(input.step)>=1?input.value:fmt(+input.value,2);}document.getElementById('seed-value').textContent=seed;}
function values(){return Object.fromEntries([...document.querySelectorAll('input[type=range]')].filter(x=>!viewControls.has(x.id)).map(x=>[x.id,Number(x.value)]));}
function showError(message){state.classList.add('error');status.textContent=message;document.getElementById('retry').hidden=false;}
async function request(){const ticket=++sequence;controller?.abort();controller=new AbortController();state.classList.remove('error');document.getElementById('retry').hidden=true;status.textContent='Calculating…';document.querySelector('main').setAttribute('aria-busy','true');
 try{const response=await fetch(`/api/v1/${engine}/analyze`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...values(),seed}),signal:controller.signal});const result=await response.json();if(ticket!==sequence)return;if(!response.ok)throw new Error(result.error?.message||`Request failed (${response.status})`);latest=result;renderer.draw(latest);status.textContent='Ready · results match the current controls';}
 catch(error){if(error.name!=='AbortError'&&ticket===sequence)showError(`${error.message}. Previous plots may be out of date.`);}
 finally{if(ticket===sequence)document.querySelector('main').setAttribute('aria-busy','false');}
}
function schedule(){controller?.abort();sequence++;clearTimeout(timer);status.textContent='Updating…';timer=setTimeout(request,160);}
async function start(){renderer=await renderers[engine]();
 for(const input of document.querySelectorAll('input[type=range]'))input.addEventListener('input',()=>{if(input.id==='n'&&engine==='multiple-regression'){const point=document.getElementById('point');point.max=input.value;if(+point.value>+input.value)point.value=input.value;}
 if(dataControls[engine].includes(input.id))newSeed();labels();if(viewControls.has(input.id)){if(latest)renderer.draw(latest);return;}schedule();});
 document.getElementById('resample')?.addEventListener('click',()=>{newSeed();labels();schedule();});document.getElementById('retry').addEventListener('click',request);labels();await request();
}
start().catch(error=>showError(error.message));
