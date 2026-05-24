# Deploy on Render

## What gets deployed

| Render service | Role | Min plan |
|----------------|------|----------|
| `interviewer-api` | FastAPI REST + WebSocket | Starter ($7/mo) |
| `interviewer-rq-worker` | Background jobs | Starter ($7/mo) |
| `interviewer-livekit-agent` | Alex voice + Simli | Starter ($7/mo) |
| `interviewer-web` | React static site | **Free** |

**Voice interviews require all three backend services always-on.** Render’s free web tier sleeps after inactivity — it is not suitable for the API or LiveKit agent.

## One-time setup

### 1. Push to GitHub

Do not commit `.env`. Ensure `.env` is in `.gitignore`.

### 2. Redis (free)

Create a database at [Upstash Redis](https://upstash.com/) (free tier). Copy the `rediss://…` URL.

### 3. Create Blueprint on Render

1. [Render Dashboard](https://dashboard.render.com/) → **New** → **Blueprint**
2. Connect your GitHub repo
3. Render reads `render.yaml` at the repo root

### 4. Fill environment variables

In **interviewer-backend** env group (or each service), set:

| Variable | Example |
|----------|---------|
| `SECRET_KEY` | long random string |
| `CORS_ORIGINS` | `https://interviewer-web.onrender.com` |
| `REDIS_URL` | `rediss://…` from Upstash |
| `DB_PROVIDER` | `snowflake` |
| `OPENAI_API_KEY` | … |
| `GROQ_API_KEY` | … |
| `LIVEKIT_URL` | `wss://….livekit.cloud` |
| `LIVEKIT_API_KEY` | … |
| `LIVEKIT_API_SECRET` | … |
| `SIMLI_*` | your Simli keys |
| Snowflake vars | same as local `.env` |

For **interviewer-web**:

| Variable | Value |
|----------|-------|
| `VITE_API_BASE_URL` | `https://interviewer-api.onrender.com` |
| `VITE_WS_BASE_URL` | `wss://interviewer-api.onrender.com` |

Replace hostnames with your actual Render URLs after the first deploy.

### 5. Deploy

Click **Apply**. First Docker build takes ~10–15 minutes (ML deps).

### 6. Verify

```bash
curl https://interviewer-api.onrender.com/api/v1/health
```

Open `https://interviewer-web.onrender.com`, start a new interview, and check **interviewer-livekit-agent** logs for `Simli avatar video live`.

## Cheapest “mostly working” option on Render

- **interviewer-web**: free (static)
- **interviewer-api**: Starter only (~$7/mo) — skip workers if you only need REST, no voice
- **Full voice + Simli**: ~$21/mo (3 × Starter) + API usage (OpenAI/Groq/Simli)

## Local storage on Render

The API mounts a 1 GB persistent disk at `/app/storage` for resume uploads. Files survive redeploys but are not shared with workers unless you use object storage later.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| API 502 on cold start | Normal on first boot; wait for health check |
| LiveKit agent never joins | Ensure `interviewer-livekit-agent` is **Starter**, not free |
| CORS errors | Set `CORS_ORIGINS` to your exact `interviewer-web` URL |
| WebSocket fails | `VITE_WS_BASE_URL` must be `wss://` (not `ws://`) |
| Simli no video | Check livekit-agent logs; verify `SIMLI_API_KEY` |
