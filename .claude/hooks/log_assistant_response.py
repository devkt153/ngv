import json
import sys
import datetime
import pathlib

data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
transcript_path = data.get("transcript_path") or ""
text = ""

if transcript_path and pathlib.Path(transcript_path).exists():
    with open(transcript_path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("type") != "assistant":
            continue
        content = entry.get("message", {}).get("content")
        if not isinstance(content, list):
            continue
        texts = [c.get("text", "") for c in content if c.get("type") == "text"]
        if texts:
            text = "\n".join(texts).strip()
            break

if text:
    root = pathlib.Path(__file__).resolve().parents[2]
    path = root / "PROMPT.md"
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n## {ts} — Claude\n\n{text}\n")
