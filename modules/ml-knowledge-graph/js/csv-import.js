/* Additive CSV constellation; existing explorer controls and video API remain present. */
const button=document.createElement('button');button.id='import-csv';button.textContent='Import CSV / TDA';button.type='button';
const target=document.getElementById('settings-panel')||document.querySelector('#settings')||document.querySelector('body');
target.prepend(button);
const dialog=document.createElement('dialog');dialog.id='csv-explorer-dialog';
dialog.innerHTML='<div class="csv-dialog-bar"><strong>CSV graph · 2D / 3D constellation</strong><button id="close-csv-explorer">Return to ML explorer</button></div><iframe title="CSV graph explorer" src="about:blank"></iframe>';
document.body.append(dialog);
button.onclick=()=>{dialog.querySelector('iframe').src='/constellation/';dialog.showModal();};
document.getElementById('close-csv-explorer').onclick=()=>dialog.close();
window.addEventListener('message',event=>{
  if(event.origin!==location.origin||event.source!==dialog.querySelector('iframe').contentWindow)return;
  if(event.data?.type==='open-csv-in-ml'){
    // IndexedDB is shared with the constellation on this origin; the fork loads the same snapshot.
    sessionStorage.setItem('ml-use-csv','1');location.reload();
  }
});
const reset=document.createElement('button');reset.id='restore-ml-graph';reset.type='button';reset.textContent='Show bundled ML graph';reset.onclick=()=>{sessionStorage.removeItem('ml-use-csv');location.reload();};target.append(reset);
