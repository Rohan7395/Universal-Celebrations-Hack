# Customer Service Fleet

A B2B platform that turns a business's documents and systems into a ready-to-run team of AI customer-service agents.

## Language

### Parties

**Tenant**:
A business that registers with the platform and gets its own Fleet.
_Avoid_: Client, merchant, account, business (when ambiguous)

**End Customer**:
A person who contacts a Tenant for support.
_Avoid_: User, client, caller

**Agency Owner**:
The person at a Tenant who sets up its Fleet and decides its Agency Rules.
_Avoid_: Admin, operator

**On-call Human**:
A Tenant staff member who receives Escalations and takes over from the Fleet.
_Avoid_: Agent (reserved for AI agents), supervisor

### Agents

**Fleet**:
The set of Fleet Agents configured for one Tenant.
_Avoid_: Swarm, team, bot

**Platform Agent**:
An AI agent that belongs to the platform and serves every Tenant: Architect, Guardian, Analyst.

**Fleet Agent**:
An AI agent configured for a single Tenant: Coordinator, Companion and the Specialists.

**Specialist**:
A Fleet Agent that handles one domain of requests (e.g. Scheduler, Billing & Benefits).
_Avoid_: Spoke, sub-agent, worker

**Architect**:
The Platform Agent that runs Onboarding and configures a Tenant's Fleet.

**Coordinator**:
The Fleet Agent that receives every Inbound Request, verifies who is asking, and routes it to a Specialist.
_Avoid_: Router, dispatcher, hub

**Companion**:
The Fleet Agent that holds Check-ins with Clients.

**Guardian**:
The Platform Agent that judges every conversation against Safety Rules and alone decides on Escalation.

**Analyst**:
The Platform Agent that writes the Agency Owner a regular digest of trends across conversations.

### Onboarding and safety

**Onboarding**:
The process that turns a new Tenant's documents and Onboarding Interview into a working Fleet.

**Onboarding Interview**:
A short, focused conversation in which Architect asks the Agency Owner questions to set the Agency Rules.

**Safety Rule**:
A condition that, when Guardian detects it in a conversation, requires a defined response.

**Baseline Rule**:
A Safety Rule that every Tenant gets automatically and cannot remove.

**Agency Rule**:
A Safety Rule that an Agency Owner adds or tunes for their own Tenant.

**Severity**:
Guardian's rating of a conversation: Emergency, Urgent, Watch or Routine. Each level has a fixed response.

**Emergency**:
Immediate danger to a Client (e.g. a fall with injury, chest pain, self-harm language); the On-call Human is paged at once.

**Urgent**:
A risk that needs a human today (e.g. dizziness, a fall without injury, new confusion, a scam attempt); leads to Escalation and a same-day Caregiver visit.

**Watch**:
A wellbeing concern that needs attention but no Escalation (e.g. loneliness, poor sleep); logged and passed to the Caregiver.

**Routine**:
Nothing of concern.

**Family Update**:
A message from Companion to a Family Contact after a Check-in, as text and a Masky video. Families are always informed; this is not optional per Tenant.

**Flag**:
A signal from a Fleet Agent to Guardian that something might be serious; not itself an Escalation.

**Escalation**:
Guardian's decision to hand a conversation to an On-call Human.
_Avoid_: Handoff (when meaning the safety decision), alert

### Testing

**Simulated Client**:
An AI persona that plays a Client in a Check-in, with a hidden scenario (e.g. a fall, loneliness, a scam call), used to demo and test the Fleet.
_Avoid_: Fake client, bot user

### Demo Tenants

**Evergreen Home Care** (working name):
A fictional in-home elder-care agency and the main demo Tenant.

**Second Tenant** (stretch goal):
A different kind of business onboarded live in the demo to show the platform works for any Tenant.
_Avoid_: Foot Locker or any real brand name

### Evergreen people

**Client**:
An older adult who receives in-home care from Evergreen.
_Avoid_: Patient, resident, senior (in formal use)

**Family Contact**:
A relative or guardian authorized to speak with Evergreen about a Client.
_Avoid_: Caller, relative (when authorization matters)

**Caregiver**:
A human Evergreen employee who visits Clients in their homes.
_Avoid_: Aide, nurse (unless licensed)

### Interactions

**Inbound Request**:
A conversation started by a Client or Family Contact asking for help.
_Avoid_: Ticket (when meaning the conversation itself), call

**Check-in**:
A short wellbeing conversation that the Fleet starts with a Client on a schedule, without being asked.
_Avoid_: Outreach, wellness call, ping
