"""
substack_sync.py — creates a Substack DRAFT for every new essay.

Runs inside the GitHub Action after the site is rebuilt. It never publishes:
you review each draft on Substack and hit Publish yourself.

How it decides what's "new":
    substack_sent.json lists every essay that already has a draft.
    Anything in essays/ that isn't on that list gets a draft, then is added
    to the list so later edits don't create duplicate drafts.

Needs one GitHub secret:
    SUBSTACK_COOKIE  — the value of your "substack.sid" cookie
Optional:
    SUBSTACK_PUBLICATION_URL — e.g. https://yourname.substack.com
                               (only needed if you have more than one publication)
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
ESSAYS_DIR = ROOT / "essays"
STATE_FILE = ROOT / "substack_sent.json"


def parse_essay(path: Path):
    """Same title/body rules as build.py, but keeps the body as plain text."""
    lines = path.read_text(encoding="utf-8").splitlines()
    title, body_start = "Untitled", 0
    for i, line in enumerate(lines):
        if line.lower().startswith("title:"):
            title = line.split(":", 1)[1].strip()
        elif line.lower().startswith("date:"):
            continue
        elif line.strip() == "" and title != "Untitled":
            body_start = i + 1
            break
    body = "\n".join(lines[body_start:]).strip()
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return {"title": title, "body": body, "slug": slug}


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return []


def save_state(sent):
    STATE_FILE.write_text(json.dumps(sorted(sent), indent=2) + "\n", encoding="utf-8")


def main():
    sent = load_state()
    new_essays = [
        e for e in (parse_essay(p) for p in sorted(ESSAYS_DIR.glob("*.md")))
        if e["slug"] not in sent and e["body"]
    ]

    if not new_essays:
        print("No new essays — nothing to send to Substack.")
        return

    cookie = os.environ.get("SUBSTACK_COOKIE", "").strip()
    if not cookie:
        print("SUBSTACK_COOKIE secret isn't set — skipping Substack drafts.")
        return
    if "=" not in cookie:  # allow pasting just the value
        cookie = f"substack.sid={cookie}"

    from substack import Api  # imported here so the script runs without it when there's nothing to do

    api = Api(
        cookies_string=cookie,
        publication_url=os.environ.get("SUBSTACK_PUBLICATION_URL") or None,
    )

    for essay in new_essays:
        result = api.create_draft_from_markdown(
            title=essay["title"],
            markdown=essay["body"],
            publish=False,  # drafts only — you publish by hand
        )
        draft_id = result["draft"].get("id")
        print(f"Created Substack draft for '{essay['title']}' (draft id {draft_id})")
        sent.append(essay["slug"])
        save_state(sent)  # save after each one so a later failure can't cause duplicates


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Substack sync failed: {exc}")
        print("If this says 401/403 or 'not logged in', your cookie probably expired —"
              " grab a fresh substack.sid and update the SUBSTACK_COOKIE secret.")
        sys.exit(1)
