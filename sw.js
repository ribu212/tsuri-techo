/* 釣り手帳のサービスワーカー（スマホの中でアプリを支える小さなプログラム）
   ・アプリ本体をスマホに保存しておき、電波が弱い釣り場でもすぐ開けるようにする
   ・アプリ本体と天気は「ネット優先」：つながれば最新、つながらなければ前回の内容を出す
   ・ライブラリや潮位表など変わらないファイルは「保存したもの優先」で速く開く
   ・ログインや記録の送受信（Firebase）、地図の画像には手を出さない */
const CACHE = 'tsuri-techo-v1';
const SHELL = ['./', './index.html', './firebase-config.js', './manifest.webmanifest', './data/muni.json', './tide/stations.json', './icons/icon-192.png'];
const CDN = ['https://cdnjs.cloudflare.com/', 'https://www.gstatic.com/firebasejs/', 'https://fonts.googleapis.com/', 'https://fonts.gstatic.com/'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

const save = (req, res) => { if (res.ok || res.type === 'opaque'){ const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); } return res; };

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const same = url.origin === self.location.origin;
  const cdn = CDN.some(p => req.url.startsWith(p));
  const weather = url.hostname.endsWith('open-meteo.com');
  if (!same && !cdn && !weather) return;

  // 変わらないファイル：保存したもの優先
  if (cdn || /\/tide\/\d{4}\//.test(url.pathname) || url.pathname.includes('/icons/')){
    e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => save(req, res))));
    return;
  }
  // アプリ本体・天気：ネット優先、だめなら前回の内容
  e.respondWith(fetch(req).then(res => save(req, res)).catch(async () => {
    const hit = await caches.match(req, {ignoreSearch: req.mode === 'navigate'});
    if (hit) return hit;
    if (req.mode === 'navigate') return caches.match('./index.html');
    return Response.error();
  }));
});
