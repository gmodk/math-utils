/* Canvas and SVG presentation only. Statistical geometry arrives from Python. */
export const colors={ink:'#e9f1ff',muted:'#94a2b8',line:'#263449',cyan:'#52e0c4',blue:'#7aa7ff',violet:'#a994ff',gold:'#ffbd62'};
export const fmt=(value,d=3)=>Number(value).toFixed(d);
export function text(id,value){document.getElementById(id).textContent=value;}
export function canvas(id){const c=document.getElementById(id),ctx=c.getContext('2d');ctx.clearRect(0,0,c.width,c.height);ctx.font='13px system-ui';ctx.fillStyle=colors.ink;ctx.strokeStyle=colors.line;ctx.lineWidth=1;return {ctx,W:c.width,H:c.height};}
export function line(ctx,points,color=colors.cyan,width=2){ctx.strokeStyle=color;ctx.lineWidth=width;ctx.beginPath();points.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.stroke();}
export function dot(ctx,p,color=colors.blue,r=3){ctx.fillStyle=color;ctx.beginPath();ctx.arc(...p,r,0,2*Math.PI);ctx.fill();}
export function label(ctx,s,x,y,color=colors.muted){ctx.fillStyle=color;ctx.fillText(s,x,y);}
export function bounds(values,pad=.12){const lo=Math.min(...values),hi=Math.max(...values),p=(hi-lo||1)*pad;return [lo-p,hi+p];}
export function axes(ctx,W,H,xb,yb,xlabel='',ylabel=''){
 const X=x=>48+(W-68)*(x-xb[0])/(xb[1]-xb[0]),Y=y=>H-38-(H-62)*(y-yb[0])/(yb[1]-yb[0]);
 line(ctx,[[48,24],[48,H-38],[W-20,H-38]],colors.line,1);
 for(let i=0;i<=4;i++){let x=xb[0]+i*(xb[1]-xb[0])/4,y=yb[0]+i*(yb[1]-yb[0])/4;label(ctx,fmt(x,1),X(x)-10,H-18);label(ctx,fmt(y,1),2,Y(y)+4);}
 label(ctx,xlabel,W-35,H-45);label(ctx,ylabel,52,18);return {X,Y};
}
export function arrow(ctx,from,to,name,color=colors.cyan){line(ctx,[from,to],color,2);const angle=Math.atan2(to[1]-from[1],to[0]-from[0]);line(ctx,[[to[0]-9*Math.cos(angle-.4),to[1]-9*Math.sin(angle-.4)],to,[to[0]-9*Math.cos(angle+.4),to[1]-9*Math.sin(angle+.4)]],color,2);label(ctx,name,to[0]+6,to[1]-6,color);}
export function camera(yaw,pitch,scale=78,dist=6,cx=250,cy=220){const a=yaw*Math.PI/180,b=pitch*Math.PI/180;return p=>{const x=Math.cos(a)*p[0]+Math.sin(a)*p[2],z=-Math.sin(a)*p[0]+Math.cos(a)*p[2],y=Math.cos(b)*p[1]-Math.sin(b)*z,depth=Math.sin(b)*p[1]+Math.cos(b)*z,k=dist/(dist+depth);return [cx+scale*x*k,cy-scale*y*k];};}
export function svg(id){const s=document.getElementById(id);s.replaceChildren();return s;}
export function element(parent,tag,attrs,content){const el=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [key,value] of Object.entries(attrs))el.setAttribute(key,value);if(content!==undefined)el.textContent=content;parent.append(el);return el;}
export function path(parent,points,color=colors.cyan,width=2){return element(parent,'path',{d:points.map((p,i)=>`${i?'L':'M'} ${p.join(' ')}`).join(' '),fill:'none',stroke:color,'stroke-width':width});}
export function svgText(parent,s,x,y,color=colors.muted,size=13){element(parent,'text',{x,y,fill:color,'font-size':size,'font-family':'system-ui'},s);}
