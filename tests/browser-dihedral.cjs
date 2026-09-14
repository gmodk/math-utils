const {chromium}=require('C:/Users/danie/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message)); page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('requestfailed',r=>errors.push(r.url()+': '+r.failure().errorText));
 await page.goto('http://127.0.0.1:8003/');
 await page.locator('[data-view="dihedral"]').click();
 await page.waitForFunction(()=>document.querySelector('#dihedral-element').options.length===10);
 await page.locator('#dihedral-3d').click();
 await page.waitForTimeout(1500);
 await page.screenshot({path:'validation-results/dihedral-first.png',fullPage:true});
 console.log(JSON.stringify({errors,heading:await page.locator('#dihedral-object-name').textContent(),canvas:await page.locator('canvas').count(),description:await page.locator('#dihedral-description').textContent()}));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
