// raster3d runner: one headless Chromium (SwiftShader WebGL2, no GPU), many frames. node render.js job.json -> PNGs + timing JSON on stdout.
const { chromium } = require('/opt/node22/lib/node_modules/playwright'); const fs = require('fs'); const path = require('path');
(async () => {
  const job = JSON.parse(fs.readFileSync(process.argv[2])); const here = __dirname; const T0 = Date.now();
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: job.size[0], height: job.size[1] } });
  p.on('pageerror', e => console.error('pageerror', e.message)); p.on('console', m => { if (m.type() === 'error') console.error('console', m.text()); });
  await p.route('http://raster.local/**', async r => {                    // /f<abs path> = any local file; otherwise files of tools/raster3d
    const u = new URL(r.request().url()); let f = decodeURIComponent(u.pathname); f = f.startsWith('/f/') ? f.slice(2) : path.join(here, f);
    try { const body = fs.readFileSync(f); const ct = f.endsWith('.js') ? 'text/javascript' : f.endsWith('.html') ? 'text/html' : f.endsWith('.json') ? 'application/json' : f.endsWith('.png') ? 'image/png' : 'application/octet-stream';
      await r.fulfill({ body, contentType: ct }); } catch (e) { await r.fulfill({ status: 404, body: 'nf' }); }
  });
  await p.goto('http://raster.local/page.html'); await p.waitForFunction(() => window.ready === true);
  await p.evaluate(j => window.init(j), job); const T1 = Date.now(); const per = [];
  for (const fj of job.frames) {
    const r = await p.evaluate(u => window.renderFrame(u), '/f' + fj);
    const out = path.join(job.out, path.basename(fj).replace(/\.json$/, job.fmt === 'png' ? '.png' : '.jpg')); fs.writeFileSync(out, Buffer.from(r.png.split(',')[1], 'base64'));
    per.push({ frame: path.basename(fj), build_ms: Math.round(r.build_ms), draw_ms: Math.round(r.draw_ms), encode_ms: Math.round(r.encode_ms) });
  }
  await b.close();
  console.log(JSON.stringify({ frames: per.length, startup_s: (T1 - T0) / 1000, total_s: (Date.now() - T0) / 1000, per_frame: per }));
})().catch(e => { console.error(e); process.exit(1); });
