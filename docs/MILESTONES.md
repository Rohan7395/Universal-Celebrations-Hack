# Milestones: done today

From [BUILD-PLAN.md](BUILD-PLAN.md).
- **Person A** = agents + backend (`app/agents`, `app/engine`, `app/api`, `tests/safety`)
- **Person B** = voice, dashboard, repo (`web/`, `.github/`, docs, ElevenLabs)

Pick who is who. Stay in your own folders to avoid merge conflicts; pull before each milestone, push after.

Times are targets starting ~16:40. Each milestone ends with both people's parts working together.

---

## M0 Contracts + scaffold: both, 16:40–17:10
- **A:**
  - [ ] `pyproject.toml` (uv): fastapi, uvicorn, pydantic-ai, google-genai, pypdf, pytest, ruff, pip-audit, bandit
  - [ ] `app/db/schema.sql` with all 12 tables + `make seed` (BrightDays, Walter, his daughter, 2 caregivers, open visit slots)
  - [ ] `app/engine/llm.py`: Gemini client with retry/backoff + smaller-model fallback
  - [ ] Stub `/api/flag` returning a fixed Urgent decision
- **B:**
  - [ ] `Makefile` (`dev`, `test`, `safety`, `seed`), `.github/workflows/ci.yml` (ruff, pytest, pip-audit, bandit)
  - [ ] `web/index.html` shell with the panels as empty boxes
  - [ ] SSE client in `app.js`
  - [ ] Create the ElevenLabs Grace agent + `flag` client tool (BUILD-PLAN §6)
- **Both:**
  - [ ] Agree the contracts in BUILD-PLAN §4 and commit them as Pydantic models in `app/api/models.py`
- **Done when:** `make dev` serves the dashboard, `make test` runs, and CI is green on push.

## M1 The call works: 17:10–18:40 · NEVER CUT
- **A:**
  - [ ] `engine/controls.py`: tighten-only, human loosen with reason, logged; `check()` on every tool + unit tests
  - [ ] `engine/severity.py`: rule table + `max(rule, llm)` + unit tests
  - [ ] Room bus: `messages` + SSE `/api/stream`
  - [ ] Agents Guardian (Ben) + Scheduler (Dana) in Pydantic AI; tools `open_case`, `page_oncall`, `find_slot`, `book_visit`, `send_family_update`
  - [ ] Real `/api/flag` with the 5 s budget + background completion
  - [ ] API test with the LLM mocked
- **B:**
  - [ ] Grace live in the browser via `@elevenlabs/client`, `flag` client tool → `/api/flag`; signed-URL endpoint
  - [ ] Typed fallback
  - [ ] Agent tiles with avatars; live room feed; human queue panel (accept / resolve)
- **Done when:** Walter says "I felt dizzy and fell this morning" live. The room shows Ben → Urgent → Dana books 3 PM → a case in the human queue. Grace says the time.

## M2 Onboarding builds the Fleet: 18:40–20:10 · NEVER CUT
- **A:**
  - [ ] `skills/`: ~8 Markdown skills, including `order-refund` and `return-item`
  - [ ] `tenants/brightdays/docs/`: handbook, services, on-call sheet (synthetic, and labeled so)
  - [ ] `ingest.py`
  - [ ] Architect (Maya): 4 fixed questions, skipping those the docs answered; skill picks with reasons; writes `policies/*.md` + Guardian thresholds + on-call contact + `fleet.yaml`
  - [ ] `draft_skill` (Gemini) for the missing `medication-reminder`
  - [ ] Risk rule + unit test
- **B:**
  - [ ] Onboarding panel: upload/select docs; questions as text + ElevenLabs TTS audio; owner types answers; picked vs skipped skills; risky skill → Approve button
  - [ ] Fleet joins the room with an animation
- **Done when:** from a clean `make seed`, onboarding produces `fleet.yaml`, the owner approves the drafted skill, and M1's call runs on the generated Fleet.

## M3 It learns + kill switch: 20:10–21:20
- **A:**
  - [ ] Coordinator (Leo): verify by phone number; answer from policies; `log_uncovered`
  - [ ] Researcher (Sam): Gemini grounding → proposal with sources (+ cached fixture)
  - [ ] Approve → write policy → `git commit` → `policy_check` → result posted in the room
  - [ ] `specs/policy-rules.md`
- **B:**
  - [ ] Family phone panel (the daughter chats with Leo); Family Update voice note (TTS)
  - [ ] Proposals panel with sources + Approve / Reject
  - [ ] Kill switch panel: "Pause outbound Check-ins", reason required to loosen
- **Done when:**
  - The Medicaid question → uncovered → proposal → Approve → the same question is answered, and git log shows the policy commit.
  - The kill switch blocks the next Check-in.

## M4 Proof + polish: 21:20–22:30
- **A:**
  - [ ] `tests/safety/`: 12 transcripts + scoreboard (`make safety`), target 12/12
  - [ ] Bandit/pip-audit findings fixed
- **B:**
  - [ ] ADRs 0001–0004
  - [ ] README: pitch, architecture diagram, how to run, screenshots
  - [ ] AGENTS.md
  - [ ] Record the demo video (onboarding → call → learning → kill switch)
- **Done when:** the BUILD-PLAN §1 definition of done holds, all six points.

## Stretch (only after M4)
- [ ] Owner Q&A (`ask.py`) with role views
- [ ] Adversary (Vera) attacks drafted skills
