# Free deployment (no credit card, no Blueprint)

This app needs **4 pieces**. You cannot run everything on one Render free service reliably,
but you **can** do it for **$0** with this split:

| Piece | Free host | Card? |
|-------|-----------|-------|
| React UI | **Cloudflare Pages** | No |
| Voice agent + Simli | **LiveKit Cloud** (`lk agent deploy`) | No (uses your LK project) |
| API + background jobs | **Render free Web Service** (manual) OR **Cloudflare Tunnel** + your Mac | Render: often no card for free web |
| Redis | **Upstash** free tier | No |
| Database | **Snowflake** (you already use) | Your account |

Render **Blueprint** and **Background Workers** need paid plans — skip those.

---

## Architecture

```
Cloudflare Pages (interviewer-web)
        │  HTTPS / WSS
        ▼
Render free Web Service  ──or──  Cloudflare Tunnel → localhost:8000
  (API + RQ worker in one container)
        │
        ├── Upstash Redis
        ├── Snowflake
        └── LiveKit Cloud ← agent runs here (lk agent deploy), not on Render
```

---

## Step 1 — Upstash Redis (2 min, free)

1. Go to [upstash.com](https://upstash.com) → sign up (GitHub, no card).
2. **Create database** → Redis → pick a region near you.
3. Copy the **Redis URL** (`rediss://default:...@....upstash.io:6379`).

You will paste this as `REDIS_URL` later.

---

## Step 2 — Deploy LiveKit agent to LiveKit Cloud (voice + Simli)

This replaces the paid Render `livekit-agent` worker. The agent runs on LiveKit’s servers.

```bash
# Install CLI (Mac)
brew install livekit-cli

# Login to your LiveKit Cloud project
lk cloud auth
```

Edit `backend/livekit.toml` — set `subdomain` from your `LIVEKIT_URL`:

```toml
# wss://agenticai-sbtpkmom.livekit.cloud  →  subdomain = agenticai-sbtpkmom
[project]
  subdomain = "agenticai-sbtpkmom"

[agent]
  id = "interviewer-ai"
```

Create a secrets file **on your machine only** (do not commit):

```bash
cd backend
cat > .env.agent <<'EOF'
OPENAI_API_KEY=...
GROQ_API_KEY=...
LIVEKIT_URL=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
SIMLI_ENABLED=true
SIMLI_API_KEY=...
SIMLI_FACE_ID=...
DB_PROVIDER=snowflake
SNOWFLAKE_ACCOUNT=...
SNOWFLAKE_USER=...
SNOWFLAKE_PASSWORD=...
SNOWFLAKE_DATABASE=...
SNOWFLAKE_SCHEMA=...
SNOWFLAKE_WAREHOUSE=...
SNOWFLAKE_ROLE=...
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=...
EOF
```

Deploy:

```bash
cd backend
lk agent create --region us-east    # first time only
lk agent deploy --secrets-file .env.agent
lk agent status
lk agent logs
```

Verify: start a new interview locally or on prod — agent should join the room without `make dev` livekit process.

---

## Step 3 — Frontend on Cloudflare Pages (free, no Blueprint)

1. [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.
2. Select repo `AI_interviewer`.
3. Build settings:

| Setting | Value |
|---------|--------|
| Production branch | `master` |
| Root directory | `web` |
| Build command | `corepack enable && pnpm install && pnpm build` |
| Build output | `dist` |

4. **Environment variables** (Production):

```
VITE_API_BASE_URL=https://YOUR-API-URL.onrender.com
VITE_WS_BASE_URL=wss://YOUR-API-URL.onrender.com
```

(Use your Render URL from Step 4, or your Cloudflare Tunnel URL from Step 5.)

5. Deploy. Your site will be `https://interviewer-web.pages.dev` (or custom domain).

---

## Step 4 — API on Render (manual, free tier, no Blueprint)

1. [dashboard.render.com](https://dashboard.render.com) → **New +** → **Web Service** (not Blueprint).
2. Connect GitHub repo `AI_interviewer`.
3. Settings:

| Setting | Value |
|---------|--------|
| Name | `interviewer-api` |
| Region | Oregon (or nearest) |
| Root directory | `backend` |
| Runtime | **Docker** |
| Instance type | **Free** |
| Docker command | `/app/scripts/start-api-and-worker.sh` |
| Health check path | `/api/v1/health` |

4. **Environment** — add all keys from your local `.env`, plus:

```
APP_ENV=production
APP_DEBUG=false
USE_REDIS_QUEUE=true
REDIS_URL=rediss://...   (Upstash)
CORS_ORIGINS=https://interviewer-web.pages.dev
LIVEPORTRAIT_ENABLED=false
SECRET_KEY=<long-random-string>
```

5. Create Web Service. First Docker build takes ~10–15 min.

6. Copy the service URL, e.g. `https://interviewer-api.onrender.com`.

7. Go back to **Cloudflare Pages** → Settings → Environment variables → set `VITE_API_BASE_URL` and `VITE_WS_BASE_URL` to that URL → **Redeploy**.

### Render free limitations (important)

- Service **sleeps after ~15 min** with no traffic → first request takes ~30–60 s (cold start).
- **512 MB RAM** — heavy ML deps may be tight; if build fails, use Step 5 (tunnel) instead.
- For interviews: open the app once, wait for API to wake, then start interview.

Optional: free [UptimeRobot](https://uptimerobot.com) ping every 5 min on `/api/v1/health` to reduce sleep (against Render ToS for always-on — use for demos only).

---

## Step 5 — Alternative API: Cloudflare Tunnel (100% free, no Render)

If Render asks for a card or the free tier is too small:

```bash
# Terminal 1 — run backend locally
cd backend && make dev

# Terminal 2 — expose HTTPS (no account needed for quick tunnel)
brew install cloudflared
cloudflared tunnel --url http://localhost:8000
```

Copy the `https://....trycloudflare.com` URL → use as `VITE_API_BASE_URL` and `VITE_WS_BASE_URL` in Cloudflare Pages.

**Catch:** Your Mac must stay on and `make dev` running during interviews. Good for demos; not 24/7 production.

For a stable URL without Render: create a free Cloudflare account → named tunnel (still no card).

---

## Step 6 — Test end-to-end

1. Open your Cloudflare Pages URL.
2. Sign up / log in.
3. Upload resume → start interview → join room.
4. Check:
   - API: `curl https://YOUR-API/api/v1/health`
   - LiveKit agent: `lk agent logs`
   - Simli face in the interview panel.

---

## Cost summary

| Item | Cost |
|------|------|
| Cloudflare Pages | $0 |
| Upstash Redis | $0 (free tier limits) |
| Render free API | $0 (sleeps when idle) |
| LiveKit Cloud agent | $0 tier + usage |
| OpenAI / Groq / Simli | Pay per use (API keys) |
| Snowflake | Your warehouse usage |

**No Render Blueprint. No paid workers. No card** for Cloudflare + Upstash + LiveKit Cloud deploy.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Render asks for card | Use Step 5 (Cloudflare Tunnel) instead |
| API 502 / slow first load | Render waking from sleep — wait 60 s, retry |
| Agent never joins room | Run `lk agent logs`; redeploy with `lk agent deploy` |
| CORS error | Set `CORS_ORIGINS` to exact Pages URL (no trailing slash) |
| WebSocket fails | `VITE_WS_BASE_URL` must be `wss://` not `ws://` |
| Resume jobs stuck | Check `REDIS_URL` and that `start-api-and-worker.sh` is the Docker command |

---

## Do not use for this free path

- `render.yaml` Blueprint (creates 3 paid Starter services)
- Render **Background Worker** (paid)
- Committing `.env` to GitHub
