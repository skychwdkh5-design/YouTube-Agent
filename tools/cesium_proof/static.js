const {chromium}=require('/opt/node22/lib/node_modules/playwright');
const views=JSON.parse(process.argv[2]); const T0=Date.now();
(async()=>{
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist']});
 for(const w of views){
  const p=await b.newPage({viewport:{width:1280,height:720}});
  await p.goto('http://127.0.0.1:8765/?cfg='+w.cfg);await p.waitForFunction('window.ready===true',null,{timeout:60000});
  const a=w.v; await p.evaluate(a=>setView(...a),a);
  for(let n=0;n<80;n++){await p.waitForTimeout(250);await p.evaluate(a=>setView(...a),a);if(n>3&&await p.evaluate(()=>settled()))break;}
  await p.waitForTimeout(800);await p.evaluate(a=>setView(...a),a);
  await p.screenshot({path:w.out});console.log(w.out,Date.now()-T0);await p.close();
 }
 await b.close();
})();
