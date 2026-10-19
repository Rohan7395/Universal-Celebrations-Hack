"""Create the Fleet's Masky avatars and pre-render the demo videos.

Reads content/masky/media.json and writes everything the dashboard needs into web/media/:
  web/avatars/<agent>.jpeg        still faces
  web/media/<file>-<n>.mp4|.mp3     rendered parts, played in order
  web/media/masky.json              ids, urls and the part list for each video
  web/media/masky-voices.json       chosen voice per agent (edit it to override)

Usage (MASKY_API_KEY must be set; create one at https://masky.ai/developer):
  python3 tools/masky.py check          verify the key
  python3 tools/masky.py voices         list voices and pick one per agent
  python3 tools/masky.py avatars        generate faces and create avatars
  python3 tools/masky.py videos         render required videos (add --optional for the rest)
  python3 tools/masky.py videos --only maya-intro
Every step skips work already done, so it is safe to re-run.
"""

import argparse
import json
import os
import pathlib
import sys
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = ROOT / "content" / "masky" / "media.json"
MEDIA = ROOT / "web" / "media"
STATE = MEDIA / "masky.json"
VOICES = MEDIA / "masky-voices.json"
API = "https://masky.ai/api"


def load(path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def env_key():
    """MASKY_API_KEY from the environment, else from the repo's git-ignored .env file."""
    if os.environ.get("MASKY_API_KEY"):
        return os.environ["MASKY_API_KEY"]
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            name, _, value = line.strip().removeprefix("export ").partition("=")
            if name == "MASKY_API_KEY":
                return value.strip().strip("'\"")
    return None


def session():
    key = env_key()
    if not key:
        sys.exit("MASKY_API_KEY is not set. Create a key at https://masky.ai/developer, then: export MASKY_API_KEY=mky_...")
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    return s


def call(s, method, path, **kwargs):
    r = s.request(method, f"{API}{path}", timeout=60, **kwargs)
    if r.status_code == 401:
        sys.exit("Masky rejected the key (401). Create a new one at https://masky.ai/developer.")
    if r.status_code == 402:
        sys.exit("Masky says the account is out of credits (402). Add credits, then re-run; finished work is kept.")
    if r.status_code >= 400:
        sys.exit(f"Masky {method} {path} failed: {r.status_code} {r.text[:500]}")
    return r.json() if r.content else {}


def find(obj, key):
    """Return the first value for `key` anywhere in a nested JSON response."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            hit = find(v, key)
            if hit is not None:
                return hit
    elif isinstance(obj, list):
        for v in obj:
            hit = find(v, key)
            if hit is not None:
                return hit
    return None


def find_turn(obj, turn_id):
    """Find the turn dict with this id anywhere in a conversation response."""
    if isinstance(obj, dict):
        if obj.get("id") == turn_id:
            return obj
        obj = list(obj.values())
    if isinstance(obj, list):
        for v in obj:
            hit = find_turn(v, turn_id)
            if hit is not None:
                return hit
    return None


def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, timeout=120, stream=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)


def ext_of(url, default):
    suffix = pathlib.PurePosixPath(urllib.parse.urlparse(url).path).suffix
    return suffix if suffix in {".mp4", ".webm", ".mov", ".mp3", ".wav", ".ogg", ".m4a", ".png", ".jpg", ".jpeg", ".webp"} else default


# ---------------------------------------------------------------- commands

def cmd_check(_args):
    s = session()
    data = call(s, "GET", "/avatars")
    print(f"Key works. Avatars on this account: {len(find(data, 'avatars') or [])}")


def cmd_voices(_args):
    s = session()
    spec = load(SPEC, {})
    voices = find(call(s, "GET", "/voices"), "voices") or []
    if not voices:
        sys.exit("Masky returned no voices.")
    print(f"{len(voices)} voices:")
    for v in voices:
        print(f"  {v.get('id')}  {v.get('name')}  ({v.get('source')})")

    chosen = load(VOICES, {})
    used = {c["id"] for c in chosen.values()}
    for agent in spec["agents"]:
        if agent["key"] in chosen:
            continue
        def score(v):
            name = (v.get("name") or "").lower()
            return sum(k in name for k in agent["voice_keywords"]) - (5 if v.get("id") in used else 0)
        best = max(voices, key=score)
        chosen[agent["key"]] = {"id": best.get("id"), "name": best.get("name")}
        used.add(best.get("id"))
    save(VOICES, chosen)
    print("\nChosen voices (edit web/media/masky-voices.json to change, then run `avatars`):")
    for key, v in chosen.items():
        print(f"  {key:6} -> {v['name']}")


def cmd_avatars(_args):
    s = session()
    spec = load(SPEC, {})
    voices = load(VOICES, {})
    if not voices:
        sys.exit("Run `python3 tools/masky.py voices` first.")
    state = load(STATE, {"avatars": {}, "videos": {}})

    for agent in spec["agents"]:
        key = agent["key"]
        entry = state["avatars"].get(key, {})
        if "avatarId" in entry:
            print(f"{key}: already created")
            continue
        if "imageUrl" not in entry:
            prompt = f"{spec['style']}. Subject: {agent['look']}."
            img = call(s, "POST", "/images/generate", json={"prompt": prompt, "aspectRatio": "1:1"})
            entry["imageUrl"] = img["imageUrl"]
            local = ROOT / "web" / "avatars" / f"{key}{ext_of(img['imageUrl'], '.png')}"
            download(img["imageUrl"], local)
            entry["image"] = str(local.relative_to(ROOT / "web"))
            state["avatars"][key] = entry
            save(STATE, state)
            print(f"{key}: face generated -> {local.relative_to(ROOT)}")
        created = call(s, "POST", "/avatars", json={
            "displayName": agent["displayName"],
            "imageUrl": entry["imageUrl"],
            "personalityPrompt": agent["personality"],
            "voiceId": voices[key]["id"],
        })
        entry.update({
            "displayName": agent["displayName"],
            "avatarId": find(created, "avatarId"),
            "avatarOwnerUserId": find(created, "avatarOwnerUserId"),
            "voiceId": voices[key]["id"],
        })
        state["avatars"][key] = entry
        save(STATE, state)
        print(f"{key}: avatar created ({entry['avatarId']})")
    print("Done. Check the faces in web/avatars/. To redo one, delete its entry from web/media/masky.json.")


def render_video(s, state, video):
    """Render every part of one video in its own conversation, in order."""
    av = state["avatars"][video["agent"]]
    out = video.get("output", "video")
    url_key = "videoUrl" if out == "video" else "audioUrl"
    default_ext = ".mp4" if out == "video" else ".mp3"
    conv = call(s, "POST", "/conversations", json={"avatarOwnerUserId": av["avatarOwnerUserId"], "avatarId": av["avatarId"]})
    slug = find(conv, "shareSlug")
    parts = []
    for i, text in enumerate(video["parts"], 1):
        turn = call(s, "POST", f"/conversations/{find(conv, 'conversationId')}/turn",
                    json={"userText": text, "output": out, "mode": "speak"})
        turn_id = find(turn, "id")
        deadline = time.time() + 240
        url = None
        while time.time() < deadline:
            time.sleep(2)
            t = find_turn(call(s, "GET", f"/conversations/by-slug/{slug}"), turn_id) or {}
            if t.get("status") in {"failed", "error"}:
                raise RuntimeError(f"{video['file']} part {i} failed: {t}")
            url = t.get(url_key)
            if url:
                break
        if not url:
            raise RuntimeError(f"{video['file']} part {i} timed out after 4 minutes")
        local = MEDIA / f"{video['file']}-{i}{ext_of(url, default_ext)}"
        download(url, local)
        parts.append({"text": text, "url": url, "src": str(local.relative_to(ROOT / "web"))})
        print(f"  {video['file']} part {i}/{len(video['parts'])} ready")
    return {"agent": video["agent"], "output": out, "shareSlug": slug, "parts": parts}


def cmd_videos(args):
    s = session()
    spec = load(SPEC, {})
    state = load(STATE, {"avatars": {}, "videos": {}})
    todo = []
    for v in spec["videos"]:
        if args.only and v["file"] not in args.only:
            continue
        if v.get("optional") and not (args.optional or args.only):
            continue
        if v["file"] in state["videos"] and not args.force:
            print(f"{v['file']}: already rendered")
            continue
        if "avatarId" not in state["avatars"].get(v["agent"], {}):
            sys.exit(f"No avatar for {v['agent']}. Run `python3 tools/masky.py avatars` first.")
        todo.append(v)
    if not todo:
        return
    print(f"Rendering {len(todo)} item(s) in parallel; videos take ~30-60 s per part...")
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {v["file"]: pool.submit(render_video, s, state, v) for v in todo}
        for name, fut in futures.items():
            try:
                state["videos"][name] = fut.result()
                save(STATE, state)
            except Exception as e:  # keep the other renders
                print(f"{name}: FAILED: {e}")
    print("Done. Media is in web/media/; the list is in web/media/masky.json.")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check")
    sub.add_parser("voices")
    sub.add_parser("avatars")
    v = sub.add_parser("videos")
    v.add_argument("--only", nargs="+", help="render only these files (e.g. maya-intro)")
    v.add_argument("--optional", action="store_true", help="also render optional items")
    v.add_argument("--force", action="store_true", help="re-render even if already done")
    args = p.parse_args()
    {"check": cmd_check, "voices": cmd_voices, "avatars": cmd_avatars, "videos": cmd_videos}[args.cmd](args)


if __name__ == "__main__":
    main()
