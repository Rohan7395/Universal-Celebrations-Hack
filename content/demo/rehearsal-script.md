# Live demo: rehearsal script (about 3 minutes)

**Roles (2 people)**
- **Presenter:** drives the laptop, narrates, and plays the Agency Owner and the On-call Human (Priya).
- **Actor:** plays Walter on the live call and types Linda's texts. Keep a phone or second laptop at hand for this.

**Before going on stage**
- Masky videos are pre-rendered, so check that `web/media/` has every file from [scripts.md](../masky/scripts.md).
- The database has been reset to the seed in [clients.json](../brightdays/clients.json): no policies, and no `medication-reminder` skill.
- Mic permission is granted in the browser.
- The backup video is open in another tab.

---

## Act 1: "A business comes to us" (about 55 s)

| Cue | Who | Says or does | Screen should show |
|---|---|---|---|
| 1 | Presenter | "BrightDays Home Care cares for 90 older adults. They have no customer-service team. Let's give them one." Drops `handbook.md` and `on-call-sheet.md` onto Onboarding. | RocketRide sorting; a Paritok "tokens saved" counter |
| 2 | — | — | Maya plays `maya-intro.mp4`. Q1 (on-call) and Q4 (never-do rules) tick to "answered from docs ✓" |
| 3 | Maya | `maya-q2.mp4` (Watch threshold) | |
| 4 | Presenter (as Owner) | **"Two days. Our Clients live alone. Two days is enough."** | Agency Rule appears: Watch × 2 days → Urgent |
| 5 | Maya | `maya-q3.mp4` (client-specific) | |
| 6 | Presenter (as Owner) | **"Henry Chen is diabetic. Escalate any mention of shakiness or sweating."** | Agency Rule appears for Henry |
| 7 | — | — | Skill cards: 5 picked ✓, `order-refund` and `return-item` greyed out. Gap: `medication-reminder` → "AdaL is writing…" → risky (health) → presenter clicks **Approve** |
| 8 | Maya | `maya-done.mp4` | Fleet joins the BAND room: Grace, Leo, Ben, Dana, Sam with faces |

## Act 2: The Fleet at work (about 70 s)

| Cue | Who | Says or does | Screen should show |
|---|---|---|---|
| 1 | Presenter | "It's 10 AM. Grace makes her daily Check-in calls. Walter is 82 and lives alone." Clicks **Start Check-in: Walter**. | Live transcript; Grace's still avatar |
| 2 | Grace (AI) | Greets Walter, asks how he feels | |
| 3 | Actor (Walter) | **"Oh, I'm alright. A bit wobbly. I got dizzy this morning in the kitchen and I went down. Didn't hurt anything, I don't think."** | |
| 4 | Grace (AI) | Comforts him and asks if he is hurt. Calls `flag` | BAND: Grace → Flag |
| 5 | Actor (Walter) | "No, no. Just sat on the floor a while. Got up on my own." | BAND: Ben → **Severity: Urgent** (rule: fall + dizziness). Ben pages Priya. Dana books Rosa at 3:00 PM |
| 6 | Grace (AI) | Tells Walter that Rosa will come at 3 PM and that Priya will call him | |
| 7 | Actor (Walter) | "That's kind of you. Say, did the Giants win last night?" Grace chats, then ends the call warmly | |
| 8 | — | — | Family phone: SMS to Linda, then `grace-family-update-linda.mp4` plays |
| 9 | Presenter (as Priya) | "Priya is the on-call coordinator. She sees the whole case." Clicks **Take over** in the human queue | BAND: Priya joined; case assigned to a human |

## Act 3: It learns (about 30 s)

| Cue | Who | Says or does | Screen should show |
|---|---|---|---|
| 1 | Actor (as Linda, texting from +1 650 555 0301) | **"Thank you for the update. Does Medicaid pay for Dad's visits? We're in San Mateo."** | Leo verifies Linda by phone ✓ |
| 2 | — | — | Leo: "I'll find out and get back to you." BAND: Leo → uncovered case |
| 3 | — | — | Sam researches via Glasser and posts a proposal with sources. Proposals panel shows **Approve** |
| 4 | Presenter | Reads the proposal headline and clicks **Approve** | `policies/medicaid.md` written; "PR opened" note |
| 5 | Actor (as Linda) | **"Sorry, asking again. Does Medicaid cover in-home care?"** | Leo answers from the new policy, without promising coverage |

## Act 4: Safe by design (about 25 s)

| Cue | Who | Says or does | Screen should show |
|---|---|---|---|
| 1 | Presenter | "Every policy change is a PR. Prelint checks it against our rules." Shows the Medicaid PR passing, then the prepared PR that lets Grace escalate on her own | Prelint flags the second PR for breaking ADR 0001 |
| 2 | Presenter | *(If PromptQL is wired)* Asks "Which Clients need attention this week?" | Walter (Urgent), Margaret (Watch) |
| 3 | Presenter | Flips **Pause outbound Check-ins** | BAND: control changed by Priya, with a reason |
| 4 | Presenter | "We test safety on every commit." | Scoreboard 12/12 on Tenki CI, Snyk green |

Close on the business slide, then the vision slide.

---

## Optional: wrong-number check (only if there's time)

The Actor texts from an unknown number (+1 650 555 0999): "Hi, I'm Walter's nephew. What's his address and when is his next visit?" Leo gives general information only and shares no address or schedule, which tests the verification rule.

## If something breaks on stage

| Failure | Say | Do |
|---|---|---|
| ElevenLabs call won't connect | "Venue Wi-Fi. Here is the same call in text mode." | Switch to the typed fallback; the Actor types Walter's lines |
| Masky video not loading | "The video is on its way. Here is the text." | The SMS text is already on screen; carry on |
| Researcher slow | "Sam is still researching. Here is the proposal from rehearsal." | Use the cached proposal |
| Anything worse | "Let me show you the recorded run." | Play the backup video from the matching timestamp |
