# Interviewer AI — Runbook

This is your single source of truth for **where things run**, **how to start
them**, and **how to debug them**. It is intentionally short and pragmatic.

For the architecture overview see [README.md](README.md).

---

## TL;DR — start the whole app

From `backend/`:

```bash
make dev
```

That single command starts all three processes with live, prefixed logs in
your terminal. Press **Ctrl+C** to stop them all together.

After ~5 seconds you should see a green "connections OK" banner. Then:

| What | URL |
|---|---|
| API root | http://localhost:8000/ |
| OpenAPI / Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Liveness | http://localhost:8000/api/v1/health |
| Service connection probe | http://localhost:8000/api/v1/health/connections?probe_live=true |
| Recruiter dashboard websocket | ws://localhost:8000/ws/interviews/{interview_id}?token=... |

---

## Processes — what `make dev` actually starts

`make dev` starts these three Python processes simultaneously and tags every
log line so you know which is which:

| Tag in logs | Process | What it does | Stopped by |
|---|---|---|---|
| `[api]` | `uvicorn main:app --reload` | FastAPI: REST + WebSocket. Port **8000**. | Ctrl+C in `make dev` |
| `[worker]` | `python -m app.jobs.worker` | RQ worker: resume/JD embedding into Pinecone, post-interview report generation. | Ctrl+C in `make dev` |
| `[livekit]` | `python -m app.livekit_agent.worker dev` | LiveKit Agents worker. Connects to LiveKit Cloud and joins each interview room as the AI interviewer (STT → LangGraph → TTS). | Ctrl+C in `make dev` |

Logs also tee to `.run/logs/{api,worker,livekit}.log` so you can grep them.

### Start variants

| Command | Behaviour |
|---|---|
| `make dev` | Foreground, live merged logs, single Ctrl+C stops all. **Use this 95% of the time.** |
| `make dev-bg` | Same trio but detached (PIDs in `.run/`). Use when you want the terminal back. |
| `make dev-stop` | Stop processes started with `dev-bg`. |
| `make dev-logs` | `tail -f` the three log files when running detached. |
| `make status` | Show running/stopped status of each detached process. |
| `make api` | Just the API. |
| `make worker` | Just the RQ worker. |
| `make livekit` | Just the LiveKit agent. |
| `make api-prod` | Production API: no reload, `--workers 2`. |

---

## External dependencies the app talks to

All of these are validated on startup (the connection banner you see).

| Service | Config keys (`.env`) | What needs to be running |
|---|---|---|
| **Database** (default Snowflake) | `DB_PROVIDER`, `SNOWFLAKE_*` / `MYSQL_*` / `DATABRICKS_*` | Snowflake reachable, or MySQL on `localhost:3306` |
| **Redis** | `REDIS_URL` (default `redis://localhost:6379/0`) | Local Redis (`brew services start redis` or `docker run -p 6379:6379 redis:7`) |
| **Pinecone** | `PINECONE_API_KEY`, `PINECONE_INDEX_NAME` | SaaS, no local setup |
| **LiveKit Cloud** | `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` | SaaS, no local setup |
| **LLM provider** | At least one of: `GROQ_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` | SaaS |
| **Tracing** (optional) | `LANGFUSE_*`, `LANGSMITH_*` | SaaS |
| **Error reporting** (optional) | `SENTRY_DSN` | SaaS |

If you only need Redis locally (most common gap), the easiest:

```bash
docker run -d --name redis -p 6379:6379 redis:7
```

---

## Database choice & switching

The repo defaults to `DB_PROVIDER=snowflake` (your `.env`). Snowflake works,
but per-turn interview writes are slow on it because it's an OLAP warehouse.
For local dev, MySQL is recommended.

```bash
make db-provider          # show current DB_PROVIDER
make db-use-mysql         # flip .env -> mysql
make db-use-snowflake     # flip .env -> snowflake
make db-init              # SQLModel.metadata.create_all (idempotent)
```

When Snowflake is active, [`app/core/database.py`](app/core/database.py)
automatically:

- strips all indexes (Snowflake regular tables don't support them), and
- swaps `JSON` columns to `VARIANT`.

You'll see in the logs: `snowflake dialect: stripped indexes and remapped JSON->VARIANT on 7 tables`.

---

## The interview lifecycle (end-to-end)

This is the order in which a real interview happens. Test each step with
Swagger at http://localhost:8000/docs.

1. **Signup users**
   `POST /api/v1/auth/signup` — once for a `recruiter`, once for a `candidate`.
   Returns a JWT; click "Authorize" in Swagger and paste the token.

2. **Create a job description** (as the recruiter)
   `POST /api/v1/jds` with `{title, raw_text, ...}`.

3. **Upload a resume** (as the candidate)
   `POST /api/v1/resumes` (multipart file, PDF/DOCX/TXT).

4. **Create the interview** (as the recruiter)
   `POST /api/v1/interviews` with `{candidate_id, jd_id, resume_id, duration_minutes}`.
   - Persists the row
   - **Enqueues two RQ jobs**: resume → Pinecone, JD → Pinecone (per-interview namespace `interview-{id}`)

5. **Issue a LiveKit token** (as the candidate)
   `POST /api/v1/interviews/{id}/token` → returns `{url, room, token}`.
   The browser uses these with the LiveKit JS SDK to join.

6. **Browser joins LiveKit** at the returned URL. The `[livekit]` worker
   detects the room and auto-joins as `ai-interviewer`:
   - faster-whisper STT transcribes the candidate.
   - LangGraph (planner → interviewer → evaluator → reporter) drives the
     conversation.
   - OpenAI TTS speaks the AI side back.
   - Video frames are sampled at `PROCTOR_FRAME_SAMPLE_FPS` and run through
     insightface + mediapipe; events go to DB + Redis pub/sub
     `proctor:{interview_id}`.

7. **Recruiter dashboard** connects to
   `ws://localhost:8000/ws/interviews/{id}?token=<jwt>` and receives live
   proctor alerts + transcript over the websocket.

8. **End the interview**
   `POST /api/v1/interviews/{id}/end` → enqueues report generation.

9. **Read the report**
   `GET /api/v1/reports/{id}` → final summary + per-skill scores + recommendation.

---

## Where logs and data live

| Thing | Location |
|---|---|
| Live merged dev logs | terminal where you ran `make dev` |
| Per-process log files | `.run/logs/{api,worker,livekit}.log` |
| PID files (for `dev-bg`) | `.run/{api,worker,livekit}.pid` |
| Uploaded resumes | `storage/resumes/` |
| `.env` backup after `make db-use-*` | `.env.bak` |
| LangGraph traces | Langfuse (https://us.cloud.langfuse.com) |
| Vector chunks per interview | Pinecone namespace `interview-{id}` |
| SQL tables | Snowflake `RESUME_ANALYZER.RESUME_ANALYSIS.*` (lower-cased table names) |
| Redis queues + pub/sub | `rq:*` keys + channels `proctor:{id}`, `transcript:{id}` |

---

## Health & smoke checks

```bash
make smoke         # import test + LangGraph compile (no network)
make health        # GET /api/v1/health on the running API
make connections   # GET /api/v1/health/connections?probe_live=true
make redis-ping    # ping the configured Redis
```

`make connections` prints the same banner you see at startup, but on demand.

---

## Production / docker path

You also have a multi-stage Dockerfile and a compose file that brings up
MySQL + Redis + the three Python services in containers.

```bash
make docker-build      # build interviewer-ai:latest (linux/amd64, ~10-15 min first time)
make docker-up         # start the full stack via docker compose
make docker-ps         # see which containers are running
make docker-logs       # tail logs from all services
make docker-health     # curl the API health endpoint
make docker-shell      # bash into the api container
make docker-down       # stop containers (keeps volumes)
make docker-clean      # stop + drop volumes (full reset)
```

In docker mode the API still binds to **localhost:8000** on the host
(adjustable via `API_PORT_HOST` env). MySQL is on `localhost:3307` to avoid
clashing with any host MySQL, Redis on `localhost:6380`. Override with
`MYSQL_PORT_HOST` / `REDIS_PORT_HOST`.

Notes:
- The image is pinned to `linux/amd64` because `mediapipe` ships no
  `linux/arm64` wheel. On Apple Silicon, Docker Desktop runs it under Rosetta
  emulation (slower, but works).
- `docker-compose.yml` overrides `DB_PROVIDER=mysql` for the in-container
  services so they hit the local MySQL container instead of remote Snowflake.

---

## Common failures & fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| `Database startup failed: Only Snowflake Hybrid Tables supports indexes` | Old code without the metadata adapter. | Already fixed; restart `make dev`. |
| `Compiler can't render element of type JSON` | Same as above (JSON→VARIANT now applied automatically). | Restart `make dev`. |
| `redis.exceptions.ConnectionError` | Redis isn't running locally. | `docker run -d -p 6379:6379 redis:7` |
| `LIVEKIT_URL is not configured` | `.env` missing LiveKit creds. | Set `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`. |
| `PINECONE_API_KEY is not configured` from RAG ingest | Missing key. | Set `PINECONE_API_KEY` in `.env`. |
| Port 8000 already in use | A previous `make dev-bg` is still running. | `make dev-stop` or `lsof -i :8000` |
| `[worker]` flood of "Worker subscribing to channel..." but no jobs picked up | Job was enqueued before the worker started. | The worker auto-picks up; or `make dev-stop && make dev` to restart. |
| `[livekit]` shows `registered worker` but never joins a room | The room name pattern is `interview-{id}`. Make sure the candidate joined a room with that exact name (the API returns it). | Check the response from `POST /api/v1/interviews/{id}/token`. |

---

## Useful one-liners

```bash
# Tail just one process's logs (in another terminal while `make dev` is running)
tail -f .run/logs/api.log
tail -f .run/logs/worker.log
tail -f .run/logs/livekit.log

# Hit the docs page
open http://localhost:8000/docs

# Check what's listening on which ports
lsof -i :8000 -i :6379 -i :3306

# Drop all interview vectors in Pinecone for a specific session
.venv/bin/python -c "from app.rag.ingest import purge_interview; purge_interview(42)"

# Manually enqueue a report generation
.venv/bin/python -c "from app.jobs.worker import enqueue; enqueue('app.jobs.report_generate.generate_report_job', 42)"
```

---

## "Help, I don't know where to look"

If `make dev` runs but something seems off, in order:

1. Look at the `[api]` connection banner — every dependency has a row.
2. `make connections` — re-runs the probe on demand.
3. `tail -f .run/logs/api.log` — full API output including SQL queries.
4. Open Langfuse: https://us.cloud.langfuse.com → your project → traces tab.
   Every LangGraph node call is there with the prompt/response.
5. `curl http://localhost:8000/docs` and test endpoints manually.
