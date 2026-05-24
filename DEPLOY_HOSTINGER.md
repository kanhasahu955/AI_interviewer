# Deploy on Hostinger VPS

Your AI interview app needs **always-on Python**, **WebSockets**, and a **LiveKit agent**.
That requires **Hostinger VPS** (or Cloud VPS) — **not** shared/cPanel web hosting.

| Hostinger plan | Works? |
|----------------|--------|
| **VPS / Cloud VPS** (KVM) | Yes — use this guide |
| Shared / WordPress hosting | No — no Docker, no long-running agents |

**Recommended VPS:** at least **4 GB RAM** (ML deps + LiveKit agent). KVM 2 (8 GB) is safer.

---

## What runs on the VPS

```
https://iweb.bakerywala.cloud     → React frontend (nginx static)
https://intapi.bakerywala.cloud    → FastAPI + WebSocket (nginx → api:8000)

bakerywala.cloud                   → your existing app (unchanged)

Docker on VPS:
  redis · api · rq-worker · livekit-agent · nginx
        │
        ├── Snowflake
        ├── LiveKit Cloud
        └── OpenAI / Groq / Simli / Pinecone
```

### DNS (Hostinger hPanel)

Add **A records** pointing to your **interview app VPS IP** (same IP is fine):

| Host | Type | Value |
|------|------|--------|
| `iweb` | A | `YOUR_VPS_IP` |
| `intapi` | A | `YOUR_VPS_IP` |

Do **not** change the existing `bakerywala.cloud` / `@` record if another service uses it.

---

## 1. Prepare the VPS (Hostinger hPanel)

1. Buy / open **Hostinger VPS** → choose **Ubuntu 24.04**.
2. Note the **SSH IP** and **root password** (or SSH key).
3. Add DNS A records for `iweb` and `intapi` (see table above).
4. Open firewall ports **80** and **443** (Hostinger firewall or `ufw`).

```bash
ssh root@YOUR_VPS_IP
```

Install Docker:

```bash
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
apt install -y git
```

---

## 2. Clone the app

```bash
cd /opt
git clone https://github.com/kanhasahu955/AI_interviewer.git
cd AI_interviewer
```

---

## 3. Production `.env`

```bash
nano backend/.env
```

Use your real keys. Template: `backend/deploy/hostinger/env.production.example`

```env
APP_ENV=production
APP_DEBUG=false
SECRET_KEY=<long-random-string>
CORS_ORIGINS=https://iweb.bakerywala.cloud

DB_PROVIDER=snowflake
# ... your SNOWFLAKE_* vars ...

REDIS_URL=redis://redis:6379/0
USE_REDIS_QUEUE=true

LIVEKIT_URL=wss://...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...

OPENAI_API_KEY=...
GROQ_API_KEY=...
SIMLI_ENABLED=true
SIMLI_API_KEY=...
SIMLI_FACE_ID=...

LIVEPORTRAIT_ENABLED=false
PINECONE_API_KEY=...
```

Do **not** commit this file.

---

## 4. Build frontend (points to intapi)

Nginx config already uses `iweb.bakerywala.cloud` and `intapi.bakerywala.cloud`
(see `backend/deploy/hostinger/nginx.conf`).

Build the React app with API URLs baked in:

```bash
chmod +x backend/deploy/hostinger/build-frontend.sh
./backend/deploy/hostinger/build-frontend.sh
```

This sets:
- `VITE_API_BASE_URL=https://intapi.bakerywala.cloud`
- `VITE_WS_BASE_URL=wss://intapi.bakerywala.cloud`

Requires Node 20+ on the VPS. If missing:

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs
npm install -g pnpm
./backend/deploy/hostinger/build-frontend.sh
```

After you enable HTTPS, rebuild with `https` / `wss` URLs (defaults already use them).

---

## 5. Start everything

```bash
cd backend
docker compose -f docker-compose.hostinger.yml up -d --build
```

First build takes **10–20 minutes** (large Python image).

Check status:

```bash
docker compose -f docker-compose.hostinger.yml ps
docker compose -f docker-compose.hostinger.yml logs -f livekit-agent
curl -s http://localhost/api/v1/health
# (via nginx — or curl http://127.0.0.1:8000 from inside if api exposed internally only)
```

Health checks:

```bash
curl -s http://intapi.bakerywala.cloud/api/v1/health
curl -sI http://iweb.bakerywala.cloud
```

Open **https://iweb.bakerywala.cloud** in the browser after SSL is enabled.

---

## 6. HTTPS (SSL)

**Option A — Hostinger hPanel:** VPS → SSL → install free certificate for your domain.

**Option B — Certbot on the VPS:**

```bash
apt install -y certbot
docker compose -f docker-compose.hostinger.yml stop nginx
certbot certonly --standalone -d iweb.bakerywala.cloud -d intapi.bakerywala.cloud
```

Then add SSL server blocks to nginx or use Hostinger hPanel SSL for each subdomain.

Restart:

```bash
docker compose -f docker-compose.hostinger.yml up -d nginx
```

Keep `CORS_ORIGINS=https://iweb.bakerywala.cloud` (use `https` after SSL).

---

## 7. Updates after code changes

```bash
cd /opt/AI_interviewer
git pull
./backend/deploy/hostinger/build-frontend.sh
cd backend
docker compose -f docker-compose.hostinger.yml up -d --build
```

---

## Makefile shortcut (on the VPS)

From `backend/`:

```bash
make hostinger-up      # build + start
make hostinger-logs    # tail logs
make hostinger-ps      # status
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `pull access denied for interviewer-ai` | Image is **local only** — run `docker compose -f docker-compose.hostinger.yml build` then `up -d --build` (never `docker pull interviewer-ai`) |
| 502 from nginx | `docker compose ... logs api` — wait for health check |
| Agent not speaking | `logs livekit-agent` — look for `Simli avatar video live` |
| Out of memory | Upgrade to 8 GB VPS or set `SIMLI_ENABLED=false` |
| WebSocket fails | nginx `/ws/` block must have `Upgrade` headers (included) |
| Shared hosting | Upgrade to VPS — this stack cannot run on cPanel PHP hosting |

---

## Optional: lighter VPS (LiveKit agent in cloud)

If the VPS is too small for the LiveKit container, run only API + worker on Hostinger and deploy the agent to LiveKit Cloud:

```bash
# On your laptop (once)
cd backend
lk cloud auth
lk agent deploy --secrets-file .env.agent
```

Then remove the `livekit-agent` service from `docker-compose.hostinger.yml` on the VPS.

See also: [DEPLOY_FREE.md](../DEPLOY_FREE.md)
