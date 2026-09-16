/* CSV preview never mutates the displayed graph. Apply persists only a valid result. */
window.reviewCSV = async function(files,onApply){
  const fileData=[];
  for(const file of files)fileData.push({name:file.name,text:await file.text()});
  const dialog=document.createElement('dialog');dialog.id='importModal';dialog.className='import-dialog';document.body.append(dialog);
  let response;
  const escape=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  async function render(){
    dialog.innerHTML='<h2>Validating CSV…</h2><button id="cancelImport">Cancel</button>';dialog.querySelector('button').onclick=()=>dialog.remove();
    try{
      const r=await fetch('/api/csv/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({files:fileData})});
      if(!r.ok)throw Error(`Validation failed (${r.status})`);response=await r.json();
      dialog.innerHTML=`<h2>Review CSV import</h2><p data-schema-help>${escape(response.schema.help)}</p><p>The current graph stays active until Apply. Missing node rows generate labeled endpoint placeholders with a warning; no relation or provenance is invented.</p><div id="mappingTables"></div><div id="csvErrors" role="alert"></div><p id="previewCounts"></p><button id="cancelImport">Cancel</button> <button id="applyImport">Apply snapshot</button>`;
      const box=dialog.querySelector('#mappingTables');
      for(const table of response.tables){
        const index=fileData.findIndex(f=>f.name===table.name);fileData[index].role=table.role;fileData[index].mapping=table.mapping;
        const section=document.createElement('section');section.innerHTML=`<h3>${escape(table.name)} · ${table.rows.length} rows</h3>`;
        const role=document.createElement('select');role.setAttribute('aria-label',`${table.name} role`);
        for(const value of ['nodes','edges','adjacency','ignore'])role.add(new Option(value,value,value===table.role,value===table.role));
        role.onchange=()=>{fileData[index].role=role.value;delete fileData[index].mapping;render();};section.append(role);
        if(table.role!=='ignore')for(const [field,column] of Object.entries(table.mapping)){
          const label=document.createElement('label');label.textContent=field+' ';label.style.display='inline-block';label.style.margin='6px';
          const select=document.createElement('select');select.setAttribute('aria-label',`${table.name} ${field}`);select.add(new Option('— none —',''));
          table.headers.forEach(h=>select.add(new Option(h,h)));select.value=column;
          select.onchange=()=>{fileData[index].mapping[field]=select.value;render();};label.append(select);section.append(label);
        }
        box.append(section);
      }
      const errors=[...response.errors.map(e=>({...e,prefix:'Error'})),...response.warnings.map(e=>({...e,prefix:'Warning'}))];
      dialog.querySelector('#csvErrors').textContent=errors.map(e=>`${e.prefix}: ${e.file} row ${e.row}, ${e.column}: ${e.message}`).join('\n');
      dialog.querySelector('#previewCounts').textContent=response.graph?`${response.graph.nodes.length} nodes · ${response.graph.edges.length} relations`: 'Fix the errors before applying.';
      dialog.querySelector('#cancelImport').onclick=()=>dialog.remove();
      const apply=dialog.querySelector('#applyImport');apply.disabled=!!response.errors.length;
      apply.onclick=async()=>{
        apply.disabled=true;
        try{
          const r=await fetch('/api/csv/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({files:fileData})});
          if(!r.ok)throw Error('Validation changed; review the files again.');
          await onApply(await r.json(),{source:'CSV import',filenames:fileData.map(f=>f.name),importedAt:new Date().toISOString(),warnings:response.warnings});
          dialog.remove();
        }catch(error){dialog.querySelector('#csvErrors').textContent=error.message;apply.disabled=false;}
      };
    }catch(error){dialog.innerHTML=`<h2>Import failed</h2><p>${escape(error.message)}</p><button>Close</button>`;dialog.querySelector('button').onclick=()=>dialog.remove();}
  }
  dialog.showModal();await render();
};
