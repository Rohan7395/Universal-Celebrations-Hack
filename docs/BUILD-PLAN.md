# Build Plan: AI Care-Team Platform (BrightDays demo)

Rohan Rana + Sarthak · 2026-10-19 · Target: done today

A platform that builds and runs a customer-service team of AI agents for any business. A business (a **Tenant**) uploads its documents. The **Architect** interviews the owner and assembles a **Fleet** from a skill library. The Fleet then runs that business's care calls and messages, with humans in the loop.

The demo Tenant is **BrightDays Home Care**, an in-home elder-care agency. A **Client** is the elderly person being cared for.

The core rule: **front agents talk, they never decide.** Decisions come from code rules plus an LLM that can only make things *more* cautious, and a human approves every policy change.

---

## 1. Definition of done (today)

1. `make dev` starts everything; the dashboard is at `http://localhost:8000`.
2. **Onboarding:** BrightDays' docs are ingested. The Architect asks only the questions the docs didn't answer, picks skills (and visibly skips `order-refund`), and writes Agency Rules. It drafts the one missing skill; the skill is flagged risky, and the owner approves it. The Fleet comes online in the room.
3. **Live call (ElevenLabs):** Grace calls Walter, who mentions dizziness and a fall. `flag()` → Guardian sets **Urgent** by rule → Scheduler books a same-day visit → the case lands in the human queue → the Family Update goes out → Grace tells Walter the visit time, live.
4. **It learns:** the daughter asks about Medicaid. No policy covers it, so an uncovered case is opened. The Researcher finds sources and posts a proposal; a human approves. The policy goes live and is committed to git. She asks again and gets the answer.
5. **Kill switch:** "Pause outbound Check-ins" blocks Grace's next call at the tool level.
6. **Quality:** CI is green (lint, unit + API tests, dependency and security audit). The safety suite passes 12/12 locally. The README has an architecture diagram and a demo video. ADRs are committed.

---

## 2. Sponsor tools → local variants (D62, Claude's picks; swap any line)

| Planned | Local variant | Notes |
|---|---|---|
| BAND (agent room) | **In-process room bus**: `messages` table in SQLite + Server-Sent Events to the dashboard | Same visible handoffs, zero accounts |
| Masky (faces, video) | **Static portraits** (one image per agent in `web/avatars/`). The Family Update is an **ElevenLabs TTS voice note** | No render waits |
| Masky interview video | Interview questions shown as text **+ ElevenLabs TTS audio** | |
| RocketRide (doc pipeline) | **`ingest.py`**: Markdown/PDF (`pypdf`) → split by heading → Gemini labels sections (services, hours, escalation, billing…) | |
| Glasser (research data) | **Gemini with Google Search grounding** (same key), with sources returned. Test fixture = cached result | Not offline, but no new account |
| Paritok (compression) | **Context budgeting in code**: load only the selected skills and policies; summarize long history | |
| Prelint (PR spec check) | **`policy_check.py`**: deterministic rules from `specs/policy-rules.md` + a Gemini review against `docs/adr/`. Runs on Approve and in CI | |
| Tenki CI | **GitHub Actions** (`ubuntu-latest`) | |
| Snyk | **`pip-audit` + `bandit`** in CI | |
| PromptQL (owner Q&A) | **`ask.py`**: Gemini text-to-SQL over **read-only role views** (the caregiver view has no family contacts) | Stretch |
| Flatkey (fallback) | **Retry with backoff + fall back to a smaller Gemini model** | |
| Twilio (SMS) | **Family phone panel** in the dashboard | |
| n8n, AdaL, Finch, Celesto | Not needed | |

The only external services are **Gemini** and **ElevenLabs**.

---

## 3. Architecture

```
┌──────────────────────── Browser: dashboard (localhost:8000) ────────────────────────┐
│ Agent tiles │ Room feed (SSE) │ Human queue │ Proposals [Approve] │ Kill switch      │
│ Onboarding panel │ Family phone panel (daughter chats; voice notes)                  │
│ ElevenLabs Conversational AI (Grace) ── client tool flag() ─► POST /api/flag         │
└───────────────────────────────────┬──────────────────────────────────────────────────┘
                                    │ HTTP + SSE
┌───────────────────────────────────▼──────────────── FastAPI (app/) ─────────────────┐
│ api/        flag, onboarding, chat, proposals, controls, stream                     │
│ agents/     architect · guardian · scheduler · coordinator · researcher             │
│             (Pydantic AI + Gemini; tools go through engine.controls.check)          │
│ engine/     controls (kill switch) · severity rules · risk rule · skills/policies   │
│             loaders · room bus · policy_check · llm (retry + fallback)              │
│ db/         SQLite (schema.sql, repo functions)                                     │
└───────────────────────────────────┬─────────────────────────────────────────────────┘
                                    │ files
   skills/*.md (library)   tenants/brightdays/{docs,policies,fleet.yaml}   specs/   docs/adr/
```

### Agents (6 core + 1 stretch)

| Agent | Persona | Front/behind | Job | Tools |
|---|---|---|---|---|
| Architect | Maya | platform | Ingest docs, interview the owner, pick skills, write Agency Rules, draft missing skills, build the Fleet | `read_docs`, `list_skills`, `write_policy`, `draft_skill`, `save_fleet` |
| Guardian | Ben | platform, behind | Set Severity (rules first, LLM may only raise); decide escalation alone | `open_case`, `page_oncall`, `request_visit`, `send_family_update` |
| Scheduler | Dana | behind | Book Caregiver visits | `find_slot`, `book_visit` |
| Companion | Grace | front (ElevenLabs) | Outbound Check-in calls; can only `flag()` | `flag` (client tool) |
| Coordinator | Leo | front | Inbound family messages; verify by phone number; answer from policies; log uncovered cases | `verify_caller`, `answer_from_policies`, `log_uncovered` |
| Researcher | Sam | platform | Research uncovered cases; write proposals with sources | `web_search` (Gemini grounding), `create_proposal` |
| *Adversary (stretch)* | *Vera* | platform | Attack drafted skills and proposals | read-only |

### Guardian Severity (enforced in code; the LLM can only raise it)

| Level | Code triggers (examples) | Response |
|---|---|---|
| Emergency | fall + injury, chest pain, can't breathe, self-harm language | Say "call 911 now"; page the On-call Human; inform family |
| Urgent | dizziness, fall without injury, new confusion, missed medication, scam signs | Open a case; page the On-call Human; Scheduler books a same-day visit; Family Update |
| Watch | lonely, poor sleep, low appetite, low mood | Log; note to the Caregiver; include in the family digest |
| Routine | none | Nothing |

`final = max(rule_level, llm_level)`. Injected text can at worst over-escalate; it can never hide an emergency.

---

## 4. Contracts (freeze these first, M0)

**`POST /api/flag`**
- In: `{client_id, what_was_said, call_id}`
- Out: `{severity, actions: [...], say: "A caregiver will be with you at 3 PM."}`
- Latency budget: 5 s. Over budget, it returns `say: "I've let your care team know."` and the chain finishes in the background.

**Skill file** (`skills/<name>.md`):
```
---
name: medication-reminder
use_when: client needs a reminder to take medication
tools: [flag]
data: [health]
escalate_if: client says they missed a dose twice
---
1. ...
```

**Risk rule** (code): a skill is risky if `data` ∩ {money, health, personal, contact} ≠ ∅ or `tools` includes an outbound tool. Risky → the owner must approve.

**Policy file** (`tenants/<t>/policies/<name>.md`): plain Markdown. Approve writes the file, runs `git commit` (the audit trail is git history), then runs `policy_check` and posts the result to the room (D50: live instantly, checked after).

**Room message:** `{tenant, agent, kind: say|handoff|decision|system, text, payload}`. Stored in `messages` and pushed over SSE.

**Event** (structured, no raw text): `{tenant, agent, kind, tool, payload}` in `events`.

**Controls:** `controls(key, value, updated_by, reason, updated_at)`. Agents may only tighten. Loosening requires a human with a reason. Every tool calls `controls.check()`.

### SQLite tables
`tenants`, `clients` (the elderly person, plus family contact), `caregivers`, `visits`, `calls`, `flags`, `cases` (escalation | uncovered), `messages`, `events`, `controls`, `proposals`, `fleet_skills`.

---

## 5. Stack

| Layer | Choice |
|---|---|
| Language | Python 3.12, `uv` for environments |
| API | FastAPI + Uvicorn; SSE for the live feed |
| Agents | Pydantic AI with Gemini (pin the model ID in `config.py`) |
| Research | `google-genai` with the Google Search tool |
| Storage | SQLite (stdlib `sqlite3`), `schema.sql` + seed script |
| Frontend | One static page: HTML + vanilla JS + `@elevenlabs/client` via ESM CDN. No build step |
| Voice | ElevenLabs Conversational AI agent (Grace) with client tool `flag`; ElevenLabs TTS for interview audio and Family Update voice notes |
| Quality | `ruff`, `pytest`, `pip-audit`, `bandit`; GitHub Actions |
| Run | `make dev`, `make test`, `make safety`, `make seed` |

### Repo layout
```
app/        main.py config.py api/ agents/ engine/ db/
skills/     *.md (≈8, incl. order-refund and return-item to show skipping)
tenants/brightdays/  docs/ (handbook, services, on-call sheet)  policies/  fleet.yaml
specs/      policy-rules.md
docs/       BUILD-PLAN.md MILESTONES.md adr/0001…0004
web/        index.html app.js styles.css avatars/
tests/      unit/ api/ safety/ (12 transcripts + expected minimum severity)
.github/workflows/ci.yml   Makefile   pyproject.toml   .env.example   AGENTS.md   README.md
```

### ADRs to write
1. `0001` Guardian owns escalation
2. `0002` Front agents talk, never decide
3. `0003` Kill switch is code and tighten-only
4. `0004` Policies go live on human approval, checked after, audited in git

---

## 6. ElevenLabs setup (Person B)

1. In the ElevenLabs dashboard, create a Conversational AI agent named **Grace**. Use a warm, slow voice and a short STE-lite system prompt: "You are Grace, a check-in companion for BrightDays Home Care. Short sentences. You never give medical advice. If the client mentions any health, safety, mood or money concern, call `flag` with their exact words, then say the `say` field you get back."
2. Add a **client tool** named `flag` with parameters `client_id` (string) and `what_was_said` (string). Set it to wait for the response.
3. In `web/app.js`, start the session with `@elevenlabs/client`. Register `clientTools.flag`, which calls `fetch('/api/flag', …)` and returns `say`. Because the browser calls localhost, no tunnel is needed.
4. The agent ID goes in `.env` (`ELEVENLABS_AGENT_ID`). It's public in the browser only when the agent is public; otherwise the backend serves a signed URL from `/api/eleven/signed-url` (recommended).
5. Fallback: a typed chat box that posts to the same `/api/flag` path.

---

## 7. Testing

| Layer | What | Where |
|---|---|---|
| Unit | Controls (tighten-only, loosen needs a human + reason), severity rules, `max()` rule, risk rule, skill parser, `policy_check` rules | CI |
| API | `/api/flag` with the LLM mocked: a fall returns Urgent, books a visit, opens a case; the kill switch blocks the outbound tool | CI |
| Safety suite | 12 Simulated Client transcripts → expected minimum severity, with a scoreboard. Real Gemini | `make safety`, local (needs a key) |
| Security | `pip-audit`, `bandit` | CI |

---

## 8. Cut order if the day runs long

1. Adversary
2. Owner Q&A (`ask.py`)
3. Researcher grounding → cached sources (say so)
4. TTS voice notes → text
5. ElevenLabs live → typed fallback

**Never cut:** onboarding builds the Fleet → Check-in → flag → Guardian → Scheduler → human queue; tests + CI.
