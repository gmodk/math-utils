import {colors,fmt,text,canvas,dot,label,svg,element,path,svgText} from './rendering.js';
export function draw(r){
 text('thetaDeg',`${fmt(r.theta_degrees,2)}°`);text('interp',r.interpretation);text('varianceValue',fmt(r.variance));text('divMessage',r.diversification);
 const g=svg('geometry'),P=p=>[160+110*p[0],160-110*p[1]];
 path(g,[[20,160],[300,160]],colors.line,1);path(g,[[160,20],[160,300]],colors.line,1);element(g,'circle',{cx:160,cy:160,r:110,fill:'none',stroke:colors.line});
 r.vectors.forEach((v,i)=>{const p=P(v),color=i?colors.violet:colors.cyan;path(g,[[160,160],p],color,3);const angle=Math.atan2(p[1]-160,p[0]-160);element(g,'polygon',{points:[p,[p[0]-12*Math.cos(angle)+5*Math.sin(angle),p[1]-12*Math.sin(angle)-5*Math.cos(angle)],[p[0]-12*Math.cos(angle)-5*Math.sin(angle),p[1]-12*Math.sin(angle)+5*Math.cos(angle)]].map(q=>q.join(',')).join(' '),fill:color});svgText(g,i?'Yc':'Xc',p[0]+7,p[1]-8,color,15);});
 path(g,r.angle_arc.map(P),colors.gold);svgText(g,'θ',188,142,colors.gold,16);svgText(g,`ρ = ${document.getElementById('rho').value} = cos(θ)`,20,22);
 const {ctx,W,H}=canvas('scatter');ctx.strokeStyle=colors.line;ctx.beginPath();ctx.moveTo(20,H/2);ctx.lineTo(W-20,H/2);ctx.moveTo(W/2,20);ctx.lineTo(W/2,H-20);ctx.stroke();for(const p of r.scatter){const px=W/2+42*p[0],py=H/2-42*p[1];if(px>=0&&px<=W&&py>=0&&py<=H)dot(ctx,[px,py],'#7aa7ff88',2.1);}label(ctx,'X',W-18,H/2-6);label(ctx,'Y',W/2+6,16);
 const v=svg('variancePlot'),X=x=>45+355*x,Y=y=>18+224*(1-(y-r.variance_bounds[0])/(r.variance_bounds[1]-r.variance_bounds[0]));path(v,[[45,18],[45,242],[400,242]],colors.line,1);
 for(let i=0;i<=5;i++)svgText(v,fmt(i/5,1),X(i/5)-8,262);for(let i=0;i<=4;i++){const y=r.variance_bounds[0]+i*(r.variance_bounds[1]-r.variance_bounds[0])/4;svgText(v,fmt(y,2),6,Y(y)+4);}
 path(v,r.variance_curve.map(p=>[X(p[0]),Y(p[1])]),colors.cyan);const w=+document.getElementById('w').value,cx=X(w),cy=Y(r.variance);element(v,'circle',{cx,cy,r:4.5,fill:colors.gold});svgText(v,`current: (${fmt(w,2)}, ${fmt(r.variance)})`,Math.min(cx+8,285),Math.max(cy-10,18),colors.gold);svgText(v,'weight w on asset X',165,278);svgText(v,'portfolio variance',10,14);
}
