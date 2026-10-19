# Masky scripts

Every line is written in STE-lite (W09): short sentences, one instruction each, active voice, no idioms.

**Pre-render all videos (marked 🎬) before going on stage.** Masky takes 30–60 s per video. Save them as `web/media/<file>.mp4`, using the file names below.

---

## Avatars to create (one per agent)

Persona names, personalities and voices come from D43. Every agent gets a still image; the videos are listed further down.

| Agent | Persona | Look | Voice | Media |
|---|---|---|---|---|
| Architect | Maya | Woman, 40s, warm smile, cardigan, bright home office | Warm alto | Still + 🎬 videos |
| Companion | Grace | Woman, 60s, kind eyes, soft sweater, cozy living room | Soft, warm | Still + 🎬 Family Update |
| Coordinator | Leo | Man, 30s, friendly, headset, front desk | Bright | Still |
| Guardian | Ben | Man, 50s, calm, plain shirt, quiet office | Slow, kind | Still (+ optional audio clip) |
| Scheduler | Dana | Woman, 40s, focused, calendar on the wall | Firm | Still |
| Researcher | Sam | Person, 30s, glasses, bookshelves | Quick | Still |
| *Adversary (stretch)* | *Vera* | *Woman, 50s, sharp blazer* | *Crisp* | *Still* |

The Companion live call uses the **ElevenLabs** voice, not Masky. Pick an ElevenLabs voice that sounds close to Grace's Masky voice so she sounds like one person.

---

## Act 1: Onboarding (Maya, Architect)

The documents already answer interview Q1 (who is on call: the on-call sheet) and Q4 (things to never do: the handbook). So Maya asks only Q2 and Q3. The dashboard shows Q1 and Q4 as "answered from docs ✓".

🎬 **`maya-intro.mp4`**
> Hello. I am Maya. I build customer service teams. I read your handbook and your on-call sheet. Your documents answer most of my questions. I have two more questions for you.

🎬 **`maya-q2.mp4`**
> Question one. Sometimes a Client feels lonely, sleeps badly, or does not eat well. We call this a Watch sign. After how many days in a row should we treat a Watch sign as urgent? The usual answer is three days.

🎬 **`maya-q3.mp4`**
> Question two. Is there anything about a specific Client that we must always escalate? For example, a health condition or a known risk.

🎬 **`maya-done.mp4`**
> Thank you. I have your answers. I chose five skills for your team. Your handbook offers medication reminder calls. We do not have that skill yet, so we are writing it now. Your team is ready. Meet Grace, Leo, Ben, Dana and Sam.

---

## Act 2: Family Update after Walter's fall (Grace, Companion)

🎬 **`grace-family-update-linda.mp4`**
> Hello Linda. This is Grace from BrightDays. I spoke with your father, Walter, at ten this morning. He felt dizzy, and he fell in the kitchen. He says he is not hurt. Rosa, his caregiver, will visit him at three o'clock today. Priya, our on-call coordinator, will call you soon. Your father was calm. He asked me about the Giants game. We will send you another update after Rosa's visit.

**SMS sent first** (text only, appears on the family-phone panel):
> BrightDays: Walter had a fall this morning. He says he is not hurt. Rosa will visit him at 3:00 PM today. Priya, our on-call coordinator, will call you in the next 10 minutes. A short video update from Grace follows.

---

## Optional audio clips (still avatar + voice in the BAND feed, D29)

These play when the agent posts its key message in the room. They are not needed if time is short.

| File | Agent | Line |
|---|---|---|
| `ben-urgent.mp3` | Ben | Walter Brooks has an urgent flag. He fell, and he feels dizzy. I am paging Priya now. |
| `dana-booked.mp3` | Dana | I booked Rosa for Walter at three o'clock today. Rosa is his usual caregiver. |
| `sam-proposal.mp3` | Sam | I found an answer about Medi-Cal and in-home care. I wrote a proposal with three sources. A human must approve it. |
| `leo-followup.mp3` | Leo | I do not have a policy for this question. I told Linda we will follow up. I logged it for Sam. |

---

## Deck closing line (Masky, optional)

🎬 **`maya-closing.mp4`**
> We set up BrightDays on this stage in one minute. Any business can do the same. Upload your documents. Answer two questions. Meet your team.
