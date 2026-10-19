"""Create (or update) Grace, the ElevenLabs Conversational AI agent, from content/elevenlabs/grace.json.

Reads ELEVENLABS_API_KEY from the environment or .env. Writes ELEVENLABS_AGENT_ID back into .env.

  python3 tools/eleven_grace.py voices     list candidate voices for Grace
  python3 tools/eleven_grace.py create     create the flag tool + agent (or update the existing agent)
  python3 tools/eleven_grace.py create --voice <voice_id>
"""

import argparse
import json
import os
import pathlib
import re
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = ROOT / "content" / "elevenlabs" / "grace.json"
ENV = ROOT / ".env"
API = "https://api.elevenlabs.io"


def env(name):
    if os.environ.get(name):
        return os.environ[name]
    if ENV.exists():
        for line in ENV.read_text().splitlines():
            key, _, value = line.strip().removeprefix("export ").partition("=")
            if key == name:
                return value.strip().strip("'\"") or None
    return None


def set_env(name, value):
    text = ENV.read_text() if ENV.exists() else ""
    line = f"{name}={value}"
    if re.search(rf"(?m)^{name}=.*$", text):
        text = re.sub(rf"(?m)^{name}=.*$", lambda _: line, text)
    else:
        text += f"\n{line}\n"
    ENV.write_text(text)


def session():
    key = env("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY is missing. Save it with: python3 tools/set_env_key.py ELEVENLABS_API_KEY")
    s = requests.Session()
    s.headers.update({"xi-api-key": key, "Content-Type": "application/json"})
    return s


def call(s, method, path, **kwargs):
    r = s.request(method, f"{API}{path}", timeout=60, **kwargs)
    if r.status_code >= 400:
        sys.exit(f"ElevenLabs {method} {path} failed: {r.status_code} {r.text[:800]}")
    return r.json() if r.content else {}


def candidate_voices(s, spec):
    vs = spec["voice_search"]
    for age in (vs["age"], vs["fallback_age"]):
        data = call(s, "GET", "/v2/voices", params={"gender": vs["gender"], "age": age, "page_size": 20})
        if data.get("voices"):
            return data["voices"]
    return call(s, "GET", "/v2/voices", params={"gender": vs["gender"], "page_size": 20}).get("voices", [])


def cmd_voices(_args):
    s = session()
    for v in candidate_voices(s, json.loads(SPEC.read_text())):
        labels = ", ".join(f"{k}={val}" for k, val in (v.get("labels") or {}).items())
        print(f"{v['voice_id']}  {v['name']}  [{labels}]")


def cmd_create(args):
    s = session()
    spec = json.loads(SPEC.read_text())

    voice_id = args.voice
    if not voice_id:
        voices = candidate_voices(s, spec)
        if not voices:
            sys.exit("No voices found; pass --voice <voice_id>.")
        voice_id = voices[0]["voice_id"]
        print(f"Voice: {voices[0]['name']} ({voice_id})")

    tool = call(s, "POST", "/v1/convai/tools", json={"tool_config": spec["tool"]})
    tool_id = tool["id"]
    print(f"Tool `flag` created: {tool_id}")

    conversation_config = {
        "agent": {
            "first_message": spec["first_message"],
            "language": "en",
            "dynamic_variables": {"dynamic_variable_placeholders": spec["dynamic_variable_placeholders"]},
            "prompt": {"prompt": spec["prompt"], "tool_ids": [tool_id]},
        },
        "tts": {"voice_id": voice_id},
    }
    body = {
        "name": spec["name"],
        "conversation_config": conversation_config,
        "platform_settings": {"auth": spec["auth"]},
    }

    existing = env("ELEVENLABS_AGENT_ID")
    if existing:
        call(s, "PATCH", f"/v1/convai/agents/{existing}", json=body)
        print(f"Updated agent {existing}")
        return
    agent = call(s, "POST", "/v1/convai/agents/create", json=body)
    set_env("ELEVENLABS_AGENT_ID", agent["agent_id"])
    print(f"Created agent {agent['agent_id']} and saved ELEVENLABS_AGENT_ID in .env")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("voices")
    c = sub.add_parser("create")
    c.add_argument("--voice", help="ElevenLabs voice_id (default: first warm older female voice)")
    args = p.parse_args()
    {"voices": cmd_voices, "create": cmd_create}[args.cmd](args)


if __name__ == "__main__":
    main()
