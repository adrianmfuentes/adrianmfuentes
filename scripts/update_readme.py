"""Fills the 'Latest' block of README.md with the most recent commits across public repos."""
import json, os, re, urllib.request
from pathlib import Path

USER = os.environ.get("GITHUB_REPOSITORY_OWNER", "adrianmfuentes")
TOKEN = os.environ.get("GITHUB_TOKEN")
README = Path(__file__).resolve().parent.parent / "README.md"
LIMIT = 5


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json", **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def latest():
    rows, seen = [], set()
    for ev in api(f"/users/{USER}/events/public?per_page=100"):
        if ev["type"] != "PushEvent":
            continue
        repo = ev["repo"]["name"]
        if repo in seen or repo == f"{USER}/{USER}":
            continue
        commits = ev["payload"].get("commits") or []
        if not commits:
            continue
        seen.add(repo)
        msg = commits[-1]["message"].splitlines()[0][:60]
        day = ev["created_at"][:10]
        rows.append(f"• [{repo.split('/')[1]}](https://github.com/{repo}) {msg} - {day}")
        if len(rows) == LIMIT:
            break
    return "<br>".join(rows) or "Nothing public yet."


if __name__ == "__main__":
    text = README.read_text(encoding="utf-8")
    block = f"<!-- latest:start -->\n{latest()}\n<!-- latest:end -->"
    new = re.sub(r"<!-- latest:start -->.*?<!-- latest:end -->", lambda _: block, text, flags=re.S)
    if new != text:
        README.write_text(new, encoding="utf-8")
