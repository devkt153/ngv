import json
import sys
import datetime
import pathlib

data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
prompt = data.get("prompt") or ""

if prompt.strip():
    root = pathlib.Path(__file__).resolve().parents[2]
    path = root / "PROMPT.md"
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n## {ts} — User\n\n{prompt}\n")
