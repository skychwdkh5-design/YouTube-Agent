// frame sequence capture: set the camera once, let Cesium render itself while tiles stream in, then one forced render + screenshot
const [N,LIMIT,OFF,STEP,FN,OUT,VW,VH,DSF]=[+process.argv[2],+process.argv[3],+process.argv[4],+process.argv[5],process.argv[6],process.argv[7],+process.argv[8],+process.argv[9],+process.argv[10]||1];
const {chromium}=require('/opt/node22/lib/node_modules/playwright');const fs=require('fs');const T0=Date.now();
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 const p=await b.newPage({viewport:{width:VW,height:VH},deviceScaleFactor:DSF});
 p.on('pageerror',e=>console.log('PAGEERR',e.message.slice(0,200)));
 await p.goto('http://127.0.0.1:8765/');await p.waitForFunction('window.ready===true',null,{timeout:90000});
 for(let i=OFF;i<N;i+=STEP){
  if(Date.now()-T0>LIMIT){console.log('TIME LIMIT at frame',i);break;}
  const u=N>1?i/(N-1):0, t=Date.now(); let ok=0,n=0;
  await p.evaluate(([f,u])=>window[f](u),[FN,u]);
  for(;n<120;n++){await p.waitForTimeout(250);const s=await p.evaluate(()=>window.settled());ok=s?ok+1:0;if(ok>=2)break;}
  await p.evaluate(([f,u])=>window[f](u),[FN,u]);await p.waitForTimeout(150);
  fs.writeFileSync(`${OUT}/p${String(i).padStart(4,'0')}.json`,JSON.stringify(await p.evaluate(()=>window.proj?window.proj():{})));
  await p.screenshot({path:`${OUT}/f${String(i).padStart(4,'0')}.png`});
  if(i%12==OFF%12)console.log('frame',i,'polls',n,'ms',Date.now()-t);
 }
 await b.close();console.log('total ms',Date.now()-T0);
})();
