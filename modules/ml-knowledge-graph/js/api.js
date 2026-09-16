export function localJSON(path,payload){
  const request=new XMLHttpRequest();request.open('POST',path,false);request.setRequestHeader('Content-Type','application/json');request.send(JSON.stringify(payload));
  if(request.status>=400)throw new Error(`Local graph operation failed (${request.status}): ${request.responseText}`);
  return JSON.parse(request.responseText);
}
export async function csvSnapshot(){
  if(!sessionStorage.getItem('ml-use-csv'))return null;
  const fallback=()=>{try{return JSON.parse(localStorage.getItem('universal.constellation.graph.v2'))||null;}catch{return null;}};
  if(!window.indexedDB)return fallback();
  return new Promise(resolve=>{
    const request=indexedDB.open('universal.constellation.storage.v1',1);
    request.onerror=request.onblocked=()=>resolve(fallback());
    request.onsuccess=()=>{
      const db=request.result;
      if(!db.objectStoreNames.contains('snapshots')){db.close();resolve(fallback());return;}
      const tx=db.transaction('snapshots','readonly');const get=tx.objectStore('snapshots').get('active');
      get.onsuccess=()=>{resolve(get.result?.raw||fallback());};get.onerror=()=>resolve(fallback());tx.oncomplete=()=>db.close();
    };
  });
}
