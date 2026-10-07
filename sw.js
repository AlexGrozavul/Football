/* ------------------------------------------------------------------
   Service worker for the installable app. CLAUDE.md, "The installable
   app", says what this caches, what it deliberately does not, and how
   to force-refresh a phone.

   Everything here is relative to this file, which sits at the root of
   the site: on GitHub Pages that is /Football/, so './' is /Football/
   and never '/'. A root-relative path would point outside the site.

   Three kinds of request, three rules:

   - The app shell (the page, the manifest, the icons, the Leaflet
     copy in vendor/): NETWORK FIRST. Online, the phone always gets what
     GitHub Pages serves now, and the copy in the cache is refreshed;
     the cache answers only when the network fails. So a new deploy
     reaches the phone on its next online open, whether or not anybody
     remembered to change SHELL_VERSION.
   - Data (everything under data/): NETWORK FIRST, and the cache answers
     ONLY when the network fails. A copy served from the cache carries
     two headers, x-served-from: cache and x-saved-at, and the page
     shows a banner with that date. Cached data is never served while
     the network works.
   - Anything else, above all map tiles, routing and place search
     (Stadia Maps, another origin): not touched at all. Not cached.

   SHELL_VERSION names the shell cache. Change it whenever this file
   changes: a changed sw.js is installed as a new worker, and the new
   name makes it drop the old shell cache instead of keeping it forever.
------------------------------------------------------------------- */

const SHELL_VERSION = 'v8';
const SHELL_CACHE = 'football-shell-' + SHELL_VERSION;
/* The data cache keeps its own name across shell versions, so a new
   deploy does not throw away the data a phone needs to open offline. */
const DATA_CACHE = 'football-data-v1';

const SCOPE = new URL('./', self.location).href;          // .../Football/
const DATA_ROOT = new URL('data/', SCOPE).href;
const INDEX = new URL('index.html', SCOPE).href;

const SHELL_FILES = [
  './',
  'index.html',
  'manifest.webmanifest',
  'icons/icon-192.png',
  'icons/icon-512.png',
  'icons/icon-maskable-192.png',
  'icons/icon-maskable-512.png',
  'icons/apple-touch-icon.png',
  'vendor/leaflet-1.9.4/leaflet.js',
  'vendor/leaflet-1.9.4/leaflet.css'
].map(p => new URL(p, SCOPE).href);
const SHELL_SET = new Set(SHELL_FILES);

const MATCH = {ignoreSearch: true, ignoreVary: true};

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(SHELL_CACHE);
    /* cache:'reload' so the new shell is today's files, not whatever
       the phone's HTTP cache still holds. */
    await cache.addAll(SHELL_FILES.map(u => new Request(u, {cache: 'reload'})));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    for(const name of await caches.keys()){
      if(name !== SHELL_CACHE && name !== DATA_CACHE) await caches.delete(name);
    }
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if(req.method !== 'GET') return;
  const url = req.url.split('#')[0];
  if(!url.startsWith(SCOPE)) return;        // tiles, routing, search, other sites
  if(url.startsWith(DATA_ROOT)) { event.respondWith(dataFirst(req, event)); return; }
  if(req.mode === 'navigate' || SHELL_SET.has(url.split('?')[0])){
    event.respondWith(shellFirst(req, event));
  }
  /* Anything else in the site (calendars/*.ics, docs) passes straight
     to the network, untouched and uncached. */
});

/* -------------------------------------------------------------- shell */

async function shellFirst(req, event){
  const nav = req.mode === 'navigate';
  const plain = req.url.split('#')[0].split('?')[0];
  try{
    /* no-cache: revalidate with GitHub Pages rather than take a copy
       the phone's HTTP cache may hold for ten minutes. A navigation
       keeps redirect:'manual' so GitHub's /Football -> /Football/
       redirect reaches the browser as a redirect. */
    const res = await fetch(new Request(req.url, {
      cache: 'no-cache', credentials: 'same-origin', redirect: nav ? 'manual' : 'follow'}));
    if(res.ok && res.type === 'basic' && (SHELL_SET.has(plain) || plain === SCOPE || plain === INDEX)){
      const copy = res.clone();
      event.waitUntil(caches.open(SHELL_CACHE).then(c => c.put(plain, copy)));
    }
    return res;
  }catch(err){
    const cache = await caches.open(SHELL_CACHE);
    let hit = await cache.match(plain, MATCH);
    /* Offline, the site root and index.html are the same page. Any other
       address in the site has no offline copy and fails as it would. */
    if(!hit && nav && (plain === SCOPE || plain === INDEX)){
      hit = await cache.match(INDEX, MATCH) || await cache.match(SCOPE, MATCH);
    }
    if(hit) return hit;
    throw err;
  }
}

/* --------------------------------------------------------------- data */

async function stamp(res){
  const headers = new Headers(res.headers);
  headers.set('x-saved-at', new Date().toISOString());
  return new Response(await res.blob(), {status: res.status, statusText: res.statusText, headers});
}

async function save(url, res){
  const cache = await caches.open(DATA_CACHE);
  await cache.put(url, await stamp(res));
}

async function dataFirst(req, event){
  const plain = req.url.split('#')[0].split('?')[0];
  let res;
  try{
    res = await fetch(req);
  }catch(err){
    /* The network failed - not a 404, not a 500, a failure to reach the
       server at all. Only now does the saved copy answer, marked so the
       page can say it is old. */
    const cache = await caches.open(DATA_CACHE);
    const hit = await cache.match(plain, MATCH);
    if(!hit){
      return new Response('', {status: 503, statusText: 'Offline, and this file was never saved on this device',
                               headers: {'x-served-from': 'none'}});
    }
    const headers = new Headers(hit.headers);
    headers.set('x-served-from', 'cache');
    return new Response(hit.body, {status: hit.status, statusText: hit.statusText, headers});
  }
  /* Online: the network's answer goes to the page whatever it is. A
     good one also replaces the saved copy. */
  if(res.ok && res.type === 'basic') event.waitUntil(save(plain, res.clone()));
  return res;
}

/* The page loads its data before this worker controls it on the very
   first visit, so those requests never passed through here. It then
   sends the list, and the files not yet saved are fetched once now so
   the next visit can open offline. */
self.addEventListener('message', event => {
  const msg = event.data || {};
  if(msg.type !== 'save-data' || !Array.isArray(msg.urls)) return;
  event.waitUntil((async () => {
    const cache = await caches.open(DATA_CACHE);
    for(const u of msg.urls){
      const plain = String(u).split('#')[0].split('?')[0];
      if(!plain.startsWith(DATA_ROOT) || await cache.match(plain, MATCH)) continue;
      try{
        const res = await fetch(plain, {cache: 'no-cache'});
        if(res.ok) await save(plain, res);
      }catch(err){ /* offline again: nothing to save, nothing lost */ }
    }
  })());
});
