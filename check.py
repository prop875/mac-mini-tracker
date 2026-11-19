import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

RSS_URL = os.environ["RSS_URL"].strip()
NTFY_TOPIC = os.environ["NTFY_TOPIC"].strip()
SEEN_FILE = Path("seen.json")

# Matches Mac mini with 24GB memory and 512GB storage
REQUIRED_PATTERNS = [
    r"mac\s*mini",
    r"\b24\s*gb\b",
    r"\b512\s*gb\b",
]

seen = json.loads(SEEN_FILE.read_text()) if SEEN_FILE.exists() else []
seen_set = set(seen)

req = urllib.request.Request(RSS_URL, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=20) as resp:
    root = ET.fromstring(resp.read())

new_items = []
for item in root.findall(".//item"):
    title = (item.findtext("title") or "Refurbished Mac mini").strip()
    desc = (item.findtext("description") or "").strip()
    link = (item.findtext("link") or "").strip()
    item_id = (item.findtext("guid") or link or title).strip()

    full_text = f"{title} {desc}"
    if item_id in seen_set:
        continue
    if all(re.search(p, full_text, re.IGNORECASE) for p in REQUIRED_PATTERNS):
        new_items.append((item_id, title, link))

for item_id, title, link in new_items:
    headers = {
        "Title": "CA Refurb Mac mini (24GB/512GB)",
        "Priority": "high",
        "Tags": "computer",
    }
    if link:
        headers["Click"] = link
    push = urllib.request.Request(
        f"https://ntfy.sh/{NTFY_TOPIC}",
        data=title.encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(push, timeout=15):
        pass
    seen.append(item_id)

if new_items:
    SEEN_FILE.write_text(json.dumps(seen[-200:], indent=2))
    print(f"Sent {len(new_items)} alert(s).")
else:
    print("No new 24GB/512GB Mac mini listings.")
