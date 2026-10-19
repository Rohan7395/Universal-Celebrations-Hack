"""Save one secret into .env without echoing it: python3 tools/set_env_key.py MASKY_API_KEY"""

import getpass
import pathlib
import re
import sys

name = sys.argv[1]
env = pathlib.Path(__file__).resolve().parent.parent / ".env"
value = getpass.getpass(f"Paste {name} (input hidden), then press Enter: ").strip()
if not value:
    sys.exit("Nothing pasted; .env unchanged.")
text = env.read_text() if env.exists() else ""
line = f"{name}={value}"
if re.search(rf"(?m)^{name}=.*$", text):
    text = re.sub(rf"(?m)^{name}=.*$", lambda _: line, text)
else:
    text += f"\n{line}\n"
env.write_text(text)
print(f"Saved {name} to {env} ({len(value)} characters).")
