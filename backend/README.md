# Interviewer AI - Backend

Real-time AI interview platform with a LiveKit audio/video room, a multi-agent
LangGraph brain (planner, interviewer, evaluator, reporter), Pinecone RAG over
resume + job description, and a proctoring pipeline (insightface + mediapipe).

> **Just want to run it?** See [RUNBOOK.md](RUNBOOK.md) — that's the operational
> doc with URLs, ports, the interview lifecycle, and troubleshooting. This file
> is the architecture overview.

## Architecture

- **FastAPI** for the HTTP + WebSocket API.
- **LiveKit** for browser-side audio/video; a `livekit-agents` worker joins each
  interview room as the AI interviewer.
- **LangGraph** drives the multi-agent flow per session, checkpointed in memory
  (swap for Redis/Postgres-backed checkpointer in production).
- **Pinecone** stores resume + JD chunks under a per-interview namespace
  (`interview-{id}`) with `text-embedding-3-small`.
- **faster-whisper** for local STT, **OpenAI TTS** for voice out, **Groq llama
  3.3** for the live interviewer LLM and **OpenAI** for the evaluator/reporter.
- **SQLModel** persistence; defaults to MySQL but supports Snowflake + Databricks
  via `DB_PROVIDER` in `.env`.
- **Redis + RQ** for background ingest + report generation.
- **Langfuse** + **LangSmith** + **Sentry** for observability.

## Setup

1. Install dependencies (the project uses `uv` / `pyproject.toml`):

   ```bash
   cd backend
   uv sync   # or: pip install -e .
   ```

2. Configure `.env` at the project root (see existing keys). The recommended
   provider for live OLTP writes is MySQL — Snowflake is fine for analytics but
   chatty per-turn writes are slow:

   ```env
   DB_PROVIDER=mysql
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=password
   MYSQL_DB=interviewer_ai
   ```

3. Make sure these external services are reachable:

   - Redis (`REDIS_URL`)
   - Pinecone (`PINECONE_API_KEY`)
   - LiveKit Cloud (`LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`)
   - At least one LLM provider (`GROQ_API_KEY` or `OPENAI_API_KEY`)

## Running

You need three long-running processes for a full interview.

### 1. FastAPI

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/docs` for the OpenAPI UI. The startup banner shows
the current `DB_PROVIDER`, LLM, vector DB, and LiveKit URL. A second banner
reports live connectivity to each dependency a moment later.

### 2. RQ background worker

Handles resume / JD embedding into Pinecone, and post-session report
generation.

```bash
cd backend
python -m app.jobs.worker
```

### 3. LiveKit Agents worker

Joins each `interview-{id}` room as the AI interviewer (STT + LLM via the
LangGraph bridge + TTS):

```bash
cd backend
python -m app.livekit_agent.worker dev
```

The first run downloads the faster-whisper model and the silero VAD weights.

## Interview lifecycle (API)

1. `POST /api/v1/auth/signup` — register users (`candidate` / `recruiter`).
2. Recruiter `POST /api/v1/jds` — create a job description.
3. Candidate `POST /api/v1/resumes` — upload PDF/DOCX.
4. Recruiter `POST /api/v1/interviews` — creates the session; resume + JD ingest
   jobs are enqueued automatically.
5. Candidate `POST /api/v1/interviews/{id}/token` — returns a LiveKit JWT for
   the browser to join the room. The agent worker auto-joins and starts the
   interview.
6. Browser may also `POST /api/v1/proctoring/{id}/events` for client-side
   events (tab blur, network drops).
7. Recruiter dashboard connects to
   `ws://.../ws/interviews/{id}?token=<jwt>` for live transcript and
   proctoring alerts (relayed off Redis pub/sub `proctor:{id}` and
   `transcript:{id}`).
8. `POST /api/v1/interviews/{id}/end` — closes the session and enqueues report
   generation. Read it back at `GET /api/v1/reports/{id}`.

## Multi-agent graph

```
planner -> interviewer -> evaluator -> interviewer (probe or next Q)
                                            \-> reporter (when plan exhausted)
```

The graph is interrupted before `evaluator`; the LiveKit worker injects each
candidate transcript via `aupdate_state(..., {"last_answer": ...})` and resumes
the graph to get the next AI utterance.

## RAG

- `app/rag/ingest.py` chunks (1000 chars / 200 overlap), embeds, and upserts to
  `interview-{id}` namespace with `{kind, text, interview_id, ...}` metadata.
- `app/rag/retriever.InterviewRetriever` searches with a kind filter
  (resume / jd), `RAG_TOP_K`, and `RAG_SCORE_THRESHOLD`.
- Planner + interviewer pull context per turn; tools (`rag_search`,
  `read_resume`, `read_jd`) are exposed in `app/langgraph/tools` for any
  agent that wants explicit retrieval.

## Proctoring

`app/proctoring/pipeline.ProctorPipeline` consumes video frames sampled at
`PROCTOR_FRAME_SAMPLE_FPS` from the LiveKit worker and audio chunks for
silence / speaker drift detection. Events are written to `proctoring_events`
and broadcast on Redis channel `proctor:{interview_id}`.

Detected event kinds: `face_missing`, `multi_face`, `identity_mismatch`,
`gaze_away`, `speaker_mismatch`, `silence`, `tab_blur`, `network_drop`.

## Observability

- Every agent invocation is tagged for **Langfuse** (`callbacks=[handler]` via
  `app/langgraph/tracing.run_config`).
- If `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` is set, the LangSmith
  env vars are exported to `os.environ` at startup so LangChain auto-traces.
- **Sentry** is initialised when `SENTRY_DSN` is present.

## Notes / known gotchas

- The exact `livekit-agents` plugin imports vary between versions; the worker
  imports them defensively and degrades gracefully if a plugin is missing.
- Snowflake is supported but **not recommended** for per-turn writes; switch
  `DB_PROVIDER=mysql` for local dev and run analytics off Snowflake separately.
- `.env` contains live API keys — rotate them and add `.env` to `.gitignore`
  before pushing to a public remote.
