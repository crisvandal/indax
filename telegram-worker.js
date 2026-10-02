// Cloudflare Worker: отдаёт три последних поста публичного Telegram-канала в виде JSON.
const CHANNEL = "crisvandal";
const LIMIT = 3;

export default {
  async fetch(request) {
    const headers = {
      "Access-Control-Allow-Origin": "*", // можно заменить на адрес вашего сайта
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=300",
    };
    if (request.method === "OPTIONS") return new Response(null, { headers });
    try {
      const res = await fetch(`https://t.me/s/${CHANNEL}`, {
        headers: { "User-Agent": "Mozilla/5.0" },
        cf: { cacheTtl: 300, cacheEverything: true },
      });
      if (!res.ok) throw new Error("t.me answered " + res.status);
      const posts = parse(await res.text()).slice(-LIMIT).reverse();
      return new Response(JSON.stringify({ posts }), { headers });
    } catch (e) {
      return new Response(JSON.stringify({ posts: [], error: String(e) }), { status: 502, headers });
    }
  },
};

function decode(s) {
  return s
    .replace(/&#(\d+);/g, (_, n) => String.fromCodePoint(+n))
    .replace(/&#x([0-9a-f]+);/gi, (_, n) => String.fromCodePoint(parseInt(n, 16)))
    .replace(/&quot;/g, '"').replace(/&lt;/g, "<").replace(/&gt;/g, ">")
    .replace(/&nbsp;/g, " ").replace(/&amp;/g, "&");
}

function parse(html) {
  const out = [];
  for (const chunk of html.split("tgme_widget_message_wrap").slice(1)) {
    const id = (chunk.match(/data-post="[^"]+\/(\d+)"/) || [])[1];
    if (!id || /service_message/.test(chunk)) continue; // пропускаем служебные записи
    const raw = (chunk.match(/class="tgme_widget_message_text[^"]*"[^>]*>([\s\S]*?)<\/div>/) || [])[1] || "";
    const text = decode(raw.replace(/<br\s*\/?>/gi, "\n").replace(/<[^>]+>/g, "")).trim();
    const image =
      (chunk.match(/tgme_widget_message_photo_wrap[^>]*background-image:url\('([^']+)'\)/) || [])[1] ||
      (chunk.match(/tgme_widget_message_video_thumb[^>]*background-image:url\('([^']+)'\)/) || [])[1] ||
      null;
    if (!text && !image) continue;
    const date = (chunk.match(/<time[^>]*datetime="([^"]+)"/) || [])[1] || null;
    out.push({ id, url: `https://t.me/${CHANNEL}/${id}`, text, date, image });
  }
  return out;
}
