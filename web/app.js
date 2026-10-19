// BrightDays Fleet dashboard. No build step: plain ES module served by FastAPI.
//
// Live feed: Server-Sent Events from GET /api/stream. Each event's `data` is one
// room message (BUILD-PLAN §4):
//   {tenant, agent, kind: "say"|"handoff"|"decision"|"system", text, payload}
// Optional `id` and `created_at` (app/api/models.py RoomMessage) are used when present. The browser
// reconnects on its own and resends Last-Event-ID, so the server can replay.
//
// Open with ?mock=1 to play a scripted feed without a backend.

import { initCall } from "./call.js";

const API = ""; // same origin as FastAPI (http://localhost:8000)

export const AGENTS = [
  { key: "maya", name: "Maya", role: "Architect" },
  { key: "grace", name: "Grace", role: "Companion" },
  { key: "leo", name: "Leo", role: "Coordinator" },
  { key: "ben", name: "Ben", role: "Guardian" },
  { key: "dana", name: "Dana", role: "Scheduler" },
  { key: "sam", name: "Sam", role: "Researcher" },
];

const $ = (sel) => document.querySelector(sel);
let messageCount = 0;

// ---------------------------------------------------------------- agents

// Match "ben", "Ben", "guardian" or "Ben · Guardian" to one of our agents.
function findAgent(name) {
  const n = String(name || "").toLowerCase();
  return AGENTS.find((a) => n === a.key || n.includes(a.key) || n.includes(a.role.toLowerCase()));
}

function avatarSrc(agent) {
  return agent ? `avatars/${agent.key}.jpeg` : "";
}

function renderAgents() {
  $("#agents").replaceChildren(
    ...AGENTS.map((a) => {
      const el = document.createElement("article");
      el.className = "agent";
      el.id = `agent-${a.key}`;
      el.innerHTML = `
        <img src="${avatarSrc(a)}" alt="">
        <div class="who">
          <div class="name"></div>
          <div class="role"></div>
          <div class="status">Idle</div>
        </div>`;
      el.querySelector(".name").textContent = a.name;
      el.querySelector(".role").textContent = a.role;
      return el;
    }),
  );
}

const activeTimers = {};
function markActive(agent, status) {
  if (!agent) return;
  const el = $(`#agent-${agent.key}`);
  if (!el) return;
  el.classList.add("active");
  el.querySelector(".status").textContent = status;
  clearTimeout(activeTimers[agent.key]);
  activeTimers[agent.key] = setTimeout(() => {
    el.classList.remove("active");
    el.querySelector(".status").textContent = "Idle";
  }, 4000);
}

// ---------------------------------------------------------------- feed

// SQLite stores UTC as "2026-10-19T16:05:00" with no zone; treat zone-less times as UTC.
function parseTime(value) {
  if (!value) return new Date();
  return new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(value) ? value : `${value}Z`);
}

function appendMessage(msg) {
  const agent = findAgent(msg.agent);
  const li = document.createElement("li");
  li.className = `msg kind-${msg.kind || "say"}`;

  const img = document.createElement("img");
  img.alt = "";
  if (agent) img.src = avatarSrc(agent);

  const body = document.createElement("div");
  const meta = document.createElement("div");
  meta.className = "meta";
  const who = document.createElement("b");
  who.textContent = agent ? `${agent.name} · ${agent.role}` : msg.agent || "System";
  const kind = document.createElement("span");
  kind.className = `kind kind-${msg.kind || "say"}`;
  kind.textContent = msg.kind || "say";
  const time = document.createElement("span");
  time.textContent = parseTime(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  meta.append(who, kind, time);

  const severity = String(msg.payload?.severity || "").toLowerCase();
  if (severity) {
    const sev = document.createElement("span");
    sev.className = `sev sev-${severity}`;
    sev.textContent = severity[0].toUpperCase() + severity.slice(1);
    meta.append(sev);
  }

  const text = document.createElement("div");
  text.className = "text";
  text.textContent = msg.text || "";

  body.append(meta, text);
  li.append(img, body);

  const feed = $("#feed");
  const nearBottom = feed.scrollHeight - feed.scrollTop - feed.clientHeight < 60;
  feed.append(li);
  if (nearBottom) feed.scrollTop = feed.scrollHeight;

  messageCount += 1;
  $("#feed-count").textContent = `${messageCount} message${messageCount === 1 ? "" : "s"}`;
  markActive(agent, msg.kind === "decision" ? "Deciding" : msg.kind === "handoff" ? "Handing off" : "Speaking");
  document.dispatchEvent(new CustomEvent("room-message", { detail: msg }));
}

// ---------------------------------------------------------------- connection

function setConn(state, text) {
  const el = $("#conn");
  el.dataset.state = state;
  el.querySelector(".conn-text").textContent = text;
}

function connectStream() {
  const es = new EventSource(`${API}/api/stream`);
  const onData = (e) => {
    try {
      appendMessage(JSON.parse(e.data));
    } catch (err) {
      console.warn("Bad room message", e.data, err);
    }
  };
  es.onopen = () => setConn("live", "Live");
  es.onerror = () => setConn("reconnecting", "Reconnecting…");
  es.onmessage = onData; // unnamed events
  es.addEventListener("room", onData); // or `event: room`
  return es;
}

// Small JSON helper for the panels built in later milestones.
export async function api(path, { method = "GET", body } = {}) {
  const res = await fetch(`${API}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${method} ${path}: ${res.status} ${await res.text()}`);
  return res.status === 204 ? null : res.json();
}

// ---------------------------------------------------------------- mock

const MOCK = [
  { agent: "grace", kind: "say", text: "Good morning, Walter. This is Grace from BrightDays. How are you feeling today?" },
  { agent: "grace", kind: "handoff", text: "Flag: Walter says he got dizzy and fell in the kitchen this morning. He thinks he is not hurt." },
  { agent: "ben", kind: "decision", text: "Severity Urgent by rule: fall + dizziness. Opening a case and paging Priya.", payload: { severity: "urgent" } },
  { agent: "dana", kind: "decision", text: "Booked Rosa for Walter at 3:00 PM today. Rosa is his usual caregiver." },
  { agent: "ben", kind: "system", text: "Family Update sent to Linda Brooks (daughter)." },
  { agent: "grace", kind: "say", text: "Walter, Rosa will visit you at three o'clock today. Priya will call you soon." },
];

function playMock() {
  setConn("mock", "Mock feed");
  MOCK.forEach((m, i) => setTimeout(() => appendMessage({ tenant: "brightdays", ...m }), 700 * (i + 1)));
}

// ---------------------------------------------------------------- start

renderAgents();
initCall();
if (new URLSearchParams(location.search).has("mock")) playMock();
else connectStream();
