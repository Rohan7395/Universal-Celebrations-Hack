# BAND rooms are where agents coordinate

All coordination between agents (Flags, delegation from Coordinator to Specialists, Guardian's Escalation decisions) happens as messages and room tasks in BAND rooms, using BAND's Python SDK, with the On-call Human joining the same room to take over. We chose BAND over our own message bus or RocketRide because it already supports humans and agents in shared rooms with tasks, it supports Claude-based agents and Python (our team's strongest language), and it carries the event's only cash prize. Masky still provides the faces and voices of Companion and the Simulated Client; it is not the coordination layer.

## Considered Options

- **Our own in-process orchestration**: fastest to build, but coordination would be invisible to judges and earn no sponsor prize.
- **Maskord as the shared channel**: overlaps with BAND rooms, and with two builders we cannot make both the backbone.
