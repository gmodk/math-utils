import { PrismView } from './dihedral-prism.js';

export function createDihedralLab(api, escapeHtml, subscript) {
  const $ = s => document.querySelector(s);
  const root = $('#view-dihedral');
  let data, selected=0, mode='2d', style='numbers', prism, request=0, frame=0, progress=1;
  const motion=matchMedia('(prefers-reduced-motion: reduce)');
  const names=['Triangle','Square','Pentagon','Hexagon','Heptagon','Octagon','Nonagon','Decagon','Hendecagon','Dodecagon'];
  const prisms=['Triangular prism','Cube / square prism','Pentagonal prism','Hexagonal prism','Heptagonal prism','Octagonal prism','Nonagonal prism','Decagonal prism','Hendecagonal prism','Dodecagonal prism'];
  $('#dihedral-shapes').innerHTML=names.map((name,i)=>`<button class="button" data-n="${i+3}" aria-pressed="false">D${subscript(i+3)} · ${name}<small>${prisms[i]}</small></button>`).join('');
  $('#dihedral-shapes').addEventListener('click',e=>{const b=e.target.closest('[data-n]'); if(b) load(Number(b.dataset.n));});
  $('#dihedral-shapes').addEventListener('keydown',e=>{
    const buttons=[...$('#dihedral-shapes').querySelectorAll('button')];
    let i=buttons.indexOf(document.activeElement); if(i<0) return;
    if(e.key==='ArrowRight') i=Math.min(buttons.length-1,i+1);
    else if(e.key==='ArrowLeft') i=Math.max(0,i-1);
    else if(e.key==='Home') i=0; else if(e.key==='End') i=buttons.length-1; else return;
    e.preventDefault(); buttons[i].focus(); buttons[i].scrollIntoView({block:'nearest',inline:'nearest'}); buttons[i].click();
  });
  function labels() {return data.geometry.labels[style];}
  function heading() {
    $('#dihedral-object-name').textContent=`D${subscript(data.m)} · ${data.geometry.names[mode==='2d'?'polygon':'prism']}`;
    $('#dihedral-order').textContent=`|D${subscript(data.m)}| = ${data.order}`;
    $('#dihedral-spatial-note').textContent=mode==='3d' ? (data.m===4 ? 'Cube: this displays a distinguished D₄ subgroup of order 8, not the full cube symmetry group (24 rotations, 48 spatial symmetries).' : `Prism realization of D${subscript(data.m)}: rotations and horizontal half-turns act on ${data.m} cyclic vertex pairs.`) : 'Dₙ is the symmetry group of the regular n-gon, of order 2n.';
  }
  function details() {
    const e=data.elements[selected], a=e.animation, ls=labels();
    $('#dihedral-selected').innerHTML=`<h3>${escapeHtml(a.formula)}</h3><p>${escapeHtml(a.description)}</p><p class="code-line">Permutation: ${escapeHtml(e.one_line)}</p><p class="code-line">Cycles: ${escapeHtml(e.cycles)} · Order: ${e.order} · Parity: ${e.parity}</p>`;
    $('#dihedral-mapping').innerHTML=e.permutation.map((j,i)=>`<span class="mapping-chip ${i!==j?'moved':''}" title="Vertex index ${i} maps to ${j}">${ls[i]} → ${ls[j]}</span>`).join('');
    $('#dihedral-description').textContent= mode==='2d' ? 'Solid labels move to the dotted canonical positions. Reflection intermediate frames interpolate the mapping; only the final frame is the symmetry.' : 'Each cyclic class labels a vertical vertex pair. A and B distinguish its original top and bottom endpoints; half-turns exchange the layers. Gold vertices move between classes.';
    root.querySelectorAll('[data-element]').forEach(b=>{const active=Number(b.dataset.element)===selected; b.setAttribute('aria-pressed',active); b.closest('tr').classList.toggle('selected',active);});
    $('#dihedral-element').value=selected;
  }
  function polygon(t) {
    const e=data.elements[selected], a=e.animation, ls=labels(), g=data.geometry;
    const toSvg=([x,y])=>[250+185*x,250+185*y];
    let points;
    if(e.type==='rotation') {
      const angle=a.rotation_angle_rad*t, c=Math.cos(angle), s=Math.sin(angle);
      points=g.polygon.map(([x,y])=>[c*x-s*y,s*x+c*y]);
    } else points=g.polygon.map((p,i)=>p.map((v,j)=>v+(a.polygon_targets[i][j]-v)*t));
    // Snap the final SVG positions to Python's exact permutation targets.
    if(t===1) points=a.polygon_targets;
    let axis='';
    if(e.type==='reflection') {
      const [x,,z]=a.axis_vector;
      axis=`<line class="axis" x1="${250-226*x}" y1="${250+226*z}" x2="${250+226*x}" y2="${250-226*z}"/>`;
    }
    $('#polygon-svg').innerHTML=`<title>${escapeHtml(data.geometry.names.polygon)} · ${escapeHtml(a.formula)}</title>${axis}<polygon class="polygon-edge" points="${points.map(toSvg).map(p=>p.join(',')).join(' ')}"/><circle class="center-mark" cx="250" cy="250" r="4"/>`+
      g.polygon.map((p,i)=>{const [x,y]=toSvg(p);return `<circle class="canonical-slot" cx="${x}" cy="${y}" r="21"/><text class="target-index" x="${250+218*p[0]}" y="${255+218*p[1]}">${ls[i]}</text>`;}).join('')+
      points.map((p,i)=>{const [x,y]=toSvg(p);return `<g data-vertex="${i}" data-target="${e.permutation[i]}"><circle class="vertex ${e.permutation[i]!==i?'moved':''}" cx="${x}" cy="${y}" r="17"/><text class="vertex-label" x="${x}" y="${y}">${ls[i]}</text></g>`;}).join('');
  }
  function draw(t) {
    progress=t; root.dataset.progress=String(t); root.dataset.selected=String(selected); root.dataset.mode=mode;
    if(mode==='2d') polygon(t); else prism?.setAction(data.elements[selected],t);
  }
  function replay() {
    if(!data) return; cancelAnimationFrame(frame);
    if(motion.matches) {draw(1);return;}
    draw(0); const start=performance.now(), duration=1300/Number($('#dihedral-speed').value);
    const animate=now=>{const t=Math.min(1,(now-start)/duration); draw(t*t*(3-2*t)); if(t<1) frame=requestAnimationFrame(animate);};
    frame=requestAnimationFrame(animate);
  }
  function select(index) {selected=index; details(); replay();}
  function setMode(next) {
    mode=next;
    $('#polygon-svg').toggleAttribute('hidden',mode!=='2d'); $('#prism-viewport').hidden=mode!=='3d'; $('#dihedral-camera').hidden=mode!=='3d';
    $('#dihedral-2d').setAttribute('aria-pressed',mode==='2d'); $('#dihedral-3d').setAttribute('aria-pressed',mode==='3d');
    try {
      if(mode==='3d') {
        if(!prism) {prism=new PrismView($('#prism-viewport')); prism.build(data,style);}
        prism.resize();
      }
      heading(); details(); draw(progress);
    } catch(error) {
      $('#dihedral-description').textContent=`3D renderer unavailable: ${error.message}. Use 2D polygon; WebGL 2 is required.`;
    }
  }
  function setLabels(next) {
    style=next; $('#dihedral-numbers').setAttribute('aria-pressed',style==='numbers'); $('#dihedral-greek').setAttribute('aria-pressed',style==='greek');
    if(!data) return; if(prism) prism.build(data,style); details(); draw(progress);
  }
  async function load(n) {
    const token=++request; root.setAttribute('aria-busy','true');
    try {
      const next=await api(`/api/dihedral?m=${n}`); if(token!==request) return;
      cancelAnimationFrame(frame); data=next; selected=0; progress=1;
      $('#dihedral-m').value=data.m;
      root.querySelectorAll('[data-n]').forEach(b=>b.setAttribute('aria-pressed',Number(b.dataset.n)===data.m));
      $('#dihedral-relations').innerHTML=data.relations.map(r=>`<code>${escapeHtml(r)}</code>`).join('');
      $('#dihedral-summary').textContent=`D${subscript(data.m)} has ${data.order} elements: ${data.m} rotations and ${data.m} reflections.`;
      $('#dihedral-table tbody').innerHTML=data.elements.map((e,i)=>`<tr><td class="code-line"><button class="element-button" data-element="${i}" aria-pressed="false">${escapeHtml(e.name)}</button></td><td>${e.type}</td><td class="code-line">${escapeHtml(e.cycles)}</td><td>${e.order}</td></tr>`).join('');
      $('#dihedral-element').innerHTML=data.elements.map((e,i)=>`<option value="${i}">${escapeHtml(e.name)} · ${e.type}</option>`).join('');
      if(prism) prism.build(data,style); setMode(mode);
    } catch(error) {if(token===request) $('#dihedral-summary').textContent=error.message;}
    finally {if(token===request) root.setAttribute('aria-busy','false');}
  }
  $('#dihedral-table').addEventListener('click',e=>{const row=e.target.closest('tbody tr');const b=row?.querySelector('[data-element]');if(b) select(Number(b.dataset.element));});
  $('#dihedral-element').addEventListener('change',e=>select(Number(e.target.value)));
  $('#dihedral-replay').addEventListener('click',replay);
  $('#dihedral-2d').addEventListener('click',()=>data&&setMode('2d'));
  $('#dihedral-3d').addEventListener('click',()=>data&&setMode('3d'));
  $('#dihedral-numbers').addEventListener('click',()=>setLabels('numbers'));
  $('#dihedral-greek').addEventListener('click',()=>setLabels('greek'));
  $('#dihedral-reset').addEventListener('click',()=>prism?.reset());
  $('#dihedral-zoom-in').addEventListener('click',()=>prism?.zoom(1/1.15));
  $('#dihedral-zoom-out').addEventListener('click',()=>prism?.zoom(1.15));
  $('#dihedral-m').addEventListener('keydown',e=>{if(e.key==='Enter') load(Number(e.target.value));});
  motion.addEventListener('change',()=>{if(motion.matches&&data){cancelAnimationFrame(frame);draw(1);}});
  return {load};
}
