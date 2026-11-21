// Cloudflare Worker: the always-on receiver for Telegram button presses (GitHub Actions is not a server).
// It does as little as possible: authenticate the webhook, accept only the owner's presses with a valid
// signature, acknowledge the press, and forward it to GitHub as repository_dispatch "telegram_decision".
// All real checks (known request, expiry, single use) are repeated in telegram-decision.yml.
//
// Secrets (wrangler secret put ...): TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_CALLBACK_SECRET,
//   TELEGRAM_WEBHOOK_SECRET (random, also passed to setWebhook as secret_token),
//   GITHUB_TOKEN (fine-grained PAT: only this repo, Contents: Read and write - required for repository_dispatch).
// Vars (wrangler.toml): GITHUB_REPO = "skychwdkh5-design/YouTube-Agent"

const enc = new TextEncoder();

function b64url(buf) {
  let s = btoa(String.fromCharCode(...new Uint8Array(buf)));
  return s.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function safeEqual(a, b) {
  if (a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}

async function sign(secret, action, rid, chat) {
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const mac = await crypto.subtle.sign("HMAC", key, enc.encode(`v1|${action}|${rid}|${chat}`));
  return b64url(mac).slice(0, 22);
}

async function tg(env, method, params) {
  return fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/${method}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(params),
  });
}

export default {
  async fetch(request, env) {
    if (request.method !== "POST") return new Response("ok");
    const hdr = request.headers.get("X-Telegram-Bot-Api-Secret-Token") || "";
    if (!env.TELEGRAM_WEBHOOK_SECRET || !safeEqual(hdr, env.TELEGRAM_WEBHOOK_SECRET)) return new Response("forbidden", { status: 403 });

    let update;
    try { update = await request.json(); } catch { return new Response("ok"); }
    const cq = update.callback_query;
    if (!cq) return new Response("ok");                       // ignore everything except button presses

    const fromId = String(cq.from && cq.from.id);
    const data = String(cq.data || "");
    const m = /^([yn]):([a-z0-9]{6,16}):([A-Za-z0-9_-]{22})$/.exec(data);
    let verdict = "Не принято";
    if (fromId === String(env.TELEGRAM_CHAT_ID) && m) {
      const expect = await sign(env.TELEGRAM_CALLBACK_SECRET, m[1], m[2], env.TELEGRAM_CHAT_ID);
      if (safeEqual(m[3], expect)) {
        const r = await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/dispatches`, {
          method: "POST",
          headers: {
            "Authorization": `Bearer ${env.GITHUB_TOKEN}`, "Accept": "application/vnd.github+json",
            "User-Agent": "telegram-decision-worker", "X-GitHub-Api-Version": "2022-11-28",
          },
          body: JSON.stringify({ event_type: "telegram_decision", client_payload: { data, from_id: fromId } }),
        });
        verdict = r.status === 204 ? "Принято, записываю…" : "GitHub недоступен, попробуй позже";
      }
    }
    await tg(env, "answerCallbackQuery", { callback_query_id: cq.id, text: verdict });
    return new Response("ok");
  },
};
