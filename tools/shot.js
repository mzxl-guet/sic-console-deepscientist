// 用 CDP 驱动无头 Edge：设置视口 -> 打开页面 -> 可选点击 -> 整页截图
// 用法: node shot.js <url> <outFile> [--w=1600] [--h=1000] [--full] [--click=文本]
const http = require('http');
const fs = require('fs');

const args = process.argv.slice(2);
const url = args[0];
const out = args[1];
const opt = (k, d) => {
  const a = args.find((x) => x.startsWith(`--${k}=`));
  return a ? a.split('=').slice(1).join('=') : d;
};
const W = parseInt(opt('w', '1600'), 10);
const H = parseInt(opt('h', '1000'), 10);
const FULL = args.includes('--full');
const CLICKS = args.filter((x) => x.startsWith('--click=')).map((x) => x.slice(8));
const SELECTORS = args.filter((x) => x.startsWith('--sel=')).map((x) => x.slice(6));
const SCROLL = opt('scroll', null);
const PORT = 9222;

function getJSON(path) {
  return new Promise((res, rej) => {
    http.get({ host: '127.0.0.1', port: PORT, path }, (r) => {
      let b = '';
      r.on('data', (c) => (b += c));
      r.on('end', () => { try { res(JSON.parse(b)); } catch (e) { rej(e); } });
    }).on('error', rej);
  });
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  const targets = await getJSON('/json');
  const page = targets.find((t) => t.type === 'page');
  if (!page) throw new Error('no page target');
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0;
  const pending = new Map();
  ws.addEventListener('message', (ev) => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  });
  const send = (method, params = {}) => new Promise((res) => {
    const i = ++id;
    pending.set(i, res);
    ws.send(JSON.stringify({ id: i, method, params }));
  });
  await new Promise((r) => ws.addEventListener('open', r));

  await send('Page.enable');
  await send('Runtime.enable');
  await send('Emulation.setDeviceMetricsOverride', {
    width: W, height: H, deviceScaleFactor: 1, mobile: false,
  });
  await send('Page.navigate', { url });
  await sleep(6500);

  for (const text of CLICKS) {
    const expr = `(() => {
      const pick = (sel) => [...document.querySelectorAll(sel)]
        .find(n => n.textContent && n.textContent.trim() === ${JSON.stringify(text)});
      const hit = pick('button') || pick('a') || pick('[role=button]') || pick('div, span');
      if (hit) { hit.click(); return 'clicked:' + ${JSON.stringify(text)}; }
      return 'notfound:' + ${JSON.stringify(text)};
    })()`;
    const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true });
    console.log(r.result?.result?.value);
    await sleep(2200);
  }

  for (const sel of SELECTORS) {
    const expr = `(() => {
      const el = document.querySelector(${JSON.stringify(sel)});
      if (!el) return 'notfound:' + ${JSON.stringify(sel)};
      el.click();
      return 'clicked:' + ${JSON.stringify(sel)};
    })()`;
    const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true });
    console.log(r.result?.result?.value);
    await sleep(2500);
  }

  if (SCROLL !== null) {
    await send('Runtime.evaluate', { expression: `window.scrollTo(0, ${parseInt(SCROLL, 10)})` });
    await sleep(900);
  }
  await sleep(1200);

  const params = { format: 'png', captureBeyondViewport: FULL };
  if (FULL) {
    const m = await send('Page.getLayoutMetrics');
    const h = Math.min(Math.ceil(m.result.cssContentSize.height), 8000);
    await send('Emulation.setDeviceMetricsOverride', { width: W, height: h, deviceScaleFactor: 1, mobile: false });
    await sleep(1200);
  }
  const shot = await send('Page.captureScreenshot', params);
  fs.writeFileSync(out, Buffer.from(shot.result.data, 'base64'));
  const dom = await send('Runtime.evaluate', {
    expression: 'document.title + " | body-h=" + document.body.scrollHeight',
    returnByValue: true,
  });
  console.log('title:', dom.result?.result?.value);
  console.log('saved', out);
  ws.close();
  process.exit(0);
})().catch((e) => { console.error('ERR', e.message); process.exit(1); });
