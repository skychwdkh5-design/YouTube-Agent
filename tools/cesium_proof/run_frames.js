const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const fs=require('fs');const N=+process.argv[2]||4, OFF=+process.argv[4]||0, STEP=+process.argv[5]||1, T0=Date.now(), LIMIT=+process.argv[3]||540000;
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const p=await b.newPage({viewport:{width:1280,height:720}});
 p.on('pageerror',e=>console.log('PAGEERR',e.message.slice(0,200)));
 await p.goto('http://127.0.0.1:8765/');await p.waitForFunction('window.ready===true',null,{timeout:60000});
 console.log('loaded',Date.now()-T0);
 for(let i=OFF;i<N;i+=STEP){
  if(Date.now()-T0>LIMIT){console.log('TIME LIMIT at frame',i);break;}
  const u=N>1?i/(N-1):0; const t=Date.now(); let n=0;
  await p.evaluate(u=>setFrame(u),u);
  for(;n<60;n++){ const ok=await p.evaluate(()=>{window.setFrame; return settled()}); if(ok&&n>2)break; await p.waitForTimeout(150); await p.evaluate(u=>setFrame(u),u);} 
  await p.waitForTimeout(400);await p.evaluate(u=>setFrame(u),u);await p.screenshot({path:`frames/f${String(i).padStart(4,'0')}.png`});
  if(i%10==OFF%10)console.log('frame',i,'polls',n,'ms',Date.now()-t);
 }
 await b.close();console.log('total ms',Date.now()-T0);
})();
