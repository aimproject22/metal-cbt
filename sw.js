const C="metal-cbt-v7.1-20260813-1";
const A=["./","index.html","app.js","manifest.webmanifest","icon-192.png","icon-512.png","data/manifest.json","data/subject1.json","data/subject2.json","data/subject3.json","data/subject4.json","data/subject5.json"];
self.addEventListener("install",e=>{self.skipWaiting();e.waitUntil(caches.open(C).then(c=>c.addAll(A)))});
self.addEventListener("activate",e=>{e.waitUntil(Promise.all([self.clients.claim(),caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==C).map(k=>caches.delete(k))))]))});
self.addEventListener("fetch",e=>e.respondWith(fetch(e.request).then(r=>{const cp=r.clone();caches.open(C).then(c=>c.put(e.request,cp));return r}).catch(()=>caches.match(e.request))));
