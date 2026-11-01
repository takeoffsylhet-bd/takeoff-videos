// usage: node render.js <project.json> preview|full
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const proj = JSON.parse(fs.readFileSync(process.argv[2]));
const mode = process.argv[3] || 'preview';
const outDir = path.join(__dirname, proj.id); fs.mkdirSync(outDir, { recursive: true });
const [W, H] = proj.o === 'h' ? [1920, 1080] : [1080, 1920];
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: W, height: H } });
  const list = [];
  for (let si = 0; si < proj.scenes.length; si++) {
    const sc = proj.scenes[si], dur = sc.dur;
    await p.goto('file://' + path.join(__dirname, 'tpl.html') + '?o=' + proj.o + '&d=' + encodeURIComponent(encodeURIComponent(JSON.stringify(sc))));
    await p.evaluate(async () => { await Promise.all(['700 50px HS','600 50px HS','800 50px NB'].map(f => document.fonts.load(f, 'বাংলা ১২৩'))); await document.fonts.ready; });
    await p.waitForTimeout(150);
    await p.evaluate(() => document.getAnimations().forEach(a => a.pause()));
    const seek = t => p.evaluate(ms => document.getAnimations().forEach(a => a.currentTime = ms), t * 1000);
    if (mode === 'preview') {
      await seek(dur - 0.5);
      await p.screenshot({ path: path.join(outDir, `prev_${si}.jpg`), type: 'jpeg', quality: 80 });
      continue;
    }
    const tmp = path.join(outDir, `tmp_${si}.mp4`), out = path.join(outDir, `s${si}.mp4`);
    list.push(`file '${out}'`);
    if (fs.existsSync(out)) continue;
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'mjpeg', '-i', '-',
      '-vf', `fade=in:st=0:d=0.25,fade=out:st=${dur - 0.25}:d=0.25,format=yuv420p`,
      '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-r', '30', '-pix_fmt', 'yuv420p', tmp]);
    const n = Math.round(dur * 30);
    for (let i = 0; i < n; i++) {
      await seek(i / 30);
      const buf = await p.screenshot({ type: 'jpeg', quality: 92 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end();
    const code = await new Promise(r => ff.on('close', r));
    if (code !== 0) throw new Error('ffmpeg failed ' + si);
    fs.renameSync(tmp, out);
    console.log('done', si);
  }
  if (mode !== 'preview') fs.writeFileSync(path.join(outDir, 'list.txt'), list.join('\n') + '\n');
  await b.close();
})();
