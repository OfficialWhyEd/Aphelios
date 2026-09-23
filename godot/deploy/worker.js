// Aphi sul web: file statici di Godot; il .wasm (40 MB) sta compresso come .wasm.gz e viene
// servito con Content-Encoding gzip (limite di 25 MB per file degli asset dei Worker).
export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    if (url.pathname.endsWith('.wasm')) {
      const r = await env.ASSETS.fetch(new Request(url.origin + url.pathname + '.gz', req));
      if (r.status !== 200) return r;
      return new Response(r.body, { status: 200, encodeBody: 'manual', headers: {
        'Content-Type': 'application/wasm', 'Content-Encoding': 'gzip', 'Cache-Control': 'public, max-age=86400' } });
    }
    return env.ASSETS.fetch(req);
  }
};
