import {colors,fmt,text,canvas,line,dot,label,axes} from './rendering.js';
export function draw(r){for(const [id,key] of Object.entries({train:'train_mse',test:'test_mse',bias:'bias_squared',var:'variance',noise:'noise'}))text(id,fmt(r[key],4));
 {const {ctx,W,H}=canvas('fit'),{X,Y}=axes(ctx,W,H,[-1,1],[-2.2,2.2],'x','y');line(ctx,r.curve.map(p=>[X(p[0]),Y(p[1])]),colors.gold);line(ctx,r.curve.map(p=>[X(p[0]),Y(p[2])]),colors.cyan);r.x.forEach((x,i)=>dot(ctx,[X(x),Y(r.y[i])],'#7aa7ff88'));label(ctx,'gold: true f(x) · cyan: fitted polynomial',70,18);}
 {const {ctx,W,H}=canvas('decomp'),values=[['bias²',r.bias_squared],['variance',r.variance],['noise',r.noise]],max=Math.max(...values.map(v=>v[1]),.001);values.forEach(([name,v],i)=>{let x=80+i*150,h=280*v/max;ctx.fillStyle=[colors.violet,colors.cyan,colors.gold][i];ctx.fillRect(x,H-55-h,80,h);label(ctx,name,x+8,H-30);label(ctx,fmt(v,4),x,H-65-h);});label(ctx,`approx expected error = ${fmt(r.expected_error,4)}`,25,25);}
}
