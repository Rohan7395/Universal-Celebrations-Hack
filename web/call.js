// Grace's live Check-in call (BUILD-PLAN §6).
//
// 1. GET /api/eleven/signed-url  -> short-lived session URL (the API key stays on the server)
// 2. Start an ElevenLabs Conversational AI session with Grace in the browser.
// 3. Grace's only tool, `flag`, is a client tool: we POST it to /api/flag on our own
//    backend and hand the returned `say` line back to Grace, who speaks it.

import { api } from "./app.js";

// Pinned, at least two weeks old. Loaded only when a call starts, so the dashboard works offline.
const ELEVENLABS_CLIENT = "https://cdn.jsdelivr.net/npm/@elevenlabs/client@1.26.0/+esm";

const CLIENT = { id: "walter", name: "Walter Brooks", firstName: "Walter" };

const $ = (sel) => document.querySelector(sel);
let conversation = null;

function setStatus(state, text) {
  const el = $("#call-status");
  el.dataset.state = state;
  el.textContent = text;
  $("#call-face").classList.toggle("speaking", state === "speaking");
}

function addLine(who, text, kind = "say") {
  const li = document.createElement("li");
  li.className = `line line-${kind} from-${who}`;
  const label = document.createElement("span");
  label.className = "line-who";
  label.textContent = who === "grace" ? "Grace" : who === "client" ? CLIENT.firstName : "Tool";
  const body = document.createElement("span");
  body.className = "line-text";
  body.textContent = text;
  li.append(label, body);
  const list = $("#transcript");
  list.append(li);
  list.scrollTop = list.scrollHeight;
}

function setButtons(inCall) {
  $("#call-start").hidden = inCall;
  $("#call-end").hidden = !inCall;
  $("#call-start").disabled = false;
}

// The `flag` client tool. Whatever we return is what Grace reads back to the client.
async function flag(params) {
  const whatWasSaid = String(params?.what_was_said || "").trim();
  addLine("tool", `flag → "${whatWasSaid}"`, "tool");
  try {
    const decision = await api("/api/flag", {
      method: "POST",
      body: {
        client_id: params?.client_id || CLIENT.id,
        what_was_said: whatWasSaid || "(no words captured)",
        call_id: conversation?.getId?.() ?? null,
      },
    });
    addLine("tool", `${decision.severity} · ${decision.actions.join(", ") || "no actions"} · say: "${decision.say}"`, "tool");
    return decision.say;
  } catch (err) {
    console.error("flag failed", err);
    addLine("tool", "flag failed; Grace tells Walter the care team will call.", "error");
    return "I've let your care team know. Someone will call you soon.";
  }
}

async function startCall() {
  $("#call-start").disabled = true;
  $("#transcript").replaceChildren();
  setStatus("connecting", "Connecting…");
  try {
    await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    setStatus("error", "Microphone blocked. Allow it in the browser, then try again.");
    setButtons(false);
    return;
  }
  try {
    const [{ Conversation }, { signed_url: signedUrl }] = await Promise.all([
      import(ELEVENLABS_CLIENT),
      api("/api/eleven/signed-url"),
    ]);
    conversation = await Conversation.startSession({
      signedUrl,
      dynamicVariables: { client_name: CLIENT.firstName, client_id: CLIENT.id },
      clientTools: { flag },
      onConnect: () => {
        setStatus("listening", "Connected");
        setButtons(true);
      },
      onDisconnect: () => {
        setStatus("idle", "Call ended");
        setButtons(false);
        conversation = null;
      },
      onError: (message) => {
        console.error("ElevenLabs error", message);
        setStatus("error", `Error: ${message}`);
      },
      onModeChange: ({ mode }) =>
        setStatus(mode === "speaking" ? "speaking" : "listening", mode === "speaking" ? "Grace is speaking" : "Listening…"),
      onMessage: ({ message, source, role }) => {
        const who = (role || source) === "user" ? "client" : "grace";
        if (message) addLine(who, message);
      },
    });
  } catch (err) {
    console.error(err);
    setStatus("error", `Could not start the call: ${err.message}`);
    setButtons(false);
  }
}

async function endCall() {
  $("#call-end").disabled = true;
  try {
    await conversation?.endSession();
  } finally {
    $("#call-end").disabled = false;
    setButtons(false);
    setStatus("idle", "Call ended");
  }
}

// ---------------------------------------------------------------- typed fallback
// If voice or ElevenLabs fails on stage: Walter's words go straight to /api/flag and
// Grace's reply is the `say` line the backend returns. No ElevenLabs involved.

let typedMode = false;

function setTypedMode(on) {
  typedMode = on;
  $("#typed").hidden = !on;
  $("#call-start").hidden = on || !!conversation;
  $("#call-hint").textContent = on
    ? "Typed mode: no voice. Grace's replies come from the care team (/api/flag)."
    : "Uses your microphone. Speak as Walter.";
  $("#typed-toggle").textContent = on ? "Use voice" : "Type instead";
  if (on) {
    $("#transcript").replaceChildren();
    setStatus("listening", "Typed check-in");
    addLine("grace", `Good morning, ${CLIENT.firstName}. This is Grace from BrightDays. How are you feeling today?`);
    $("#typed-input").focus();
  } else {
    setStatus("idle", "Ready");
  }
}

async function sendTyped(event) {
  event.preventDefault();
  const input = $("#typed-input");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  $("#typed-send").disabled = true;
  addLine("client", text);
  try {
    addLine("grace", "Thank you for telling me.");
    addLine("grace", await flag({ client_id: CLIENT.id, what_was_said: text }));
  } finally {
    $("#typed-send").disabled = false;
    input.focus();
  }
}

export function initCall() {
  $("#call-start").addEventListener("click", startCall);
  $("#call-end").addEventListener("click", endCall);
  $("#typed").addEventListener("submit", sendTyped);
  $("#typed-toggle").addEventListener("click", async () => {
    if (conversation) await endCall();
    setTypedMode(!typedMode);
  });
}
