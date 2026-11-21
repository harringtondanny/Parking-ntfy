#!/usr/bin/env python3
"""Alert via ntfy when a new parking listing matching MATCH appears on ikwilhuren.nu."""
import json, os, re, sys, urllib.request
from pathlib import Path

URL = "https://ikwilhuren.nu/parkeerplaatsen/"
MATCH = os.environ.get("MATCH", "heathrowstraat").lower()
TOPIC = os.environ.get("NTFY_TOPIC", "")
STATE = Path(__file__).with_name("seen.json")
LINK_RE = re.compile(r'https://ikwilhuren\.nu/object/[^"\s)<>\']+')

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (parking-ntfy)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")

def listing_links(html):
    return set(LINK_RE.findall(html))

def matches(links, needle=MATCH):
    return sorted(l for l in links if needle in l.lower())

def notify(link):
    slug = link.rstrip("/").rsplit("/", 1)[-1].rsplit("-", 1)[0].replace("-", " ")
    req = urllib.request.Request(
        f"https://ntfy.sh/{TOPIC}",
        data=f"New listing: {slug}".encode(),
        headers={"Title": "Parking spot posted", "Click": link, "Priority": "high", "Tags": "car"},
    )
    urllib.request.urlopen(req, timeout=30).read()

def main():
    html = fetch(URL)
    links = listing_links(html)
    if len(links) < 50:  # page layout probably changed; fail loudly
        sys.exit(f"Only {len(links)} listings parsed, aborting")
    seen = set(json.loads(STATE.read_text())) if STATE.exists() else set()
    new = [l for l in matches(links) if l not in seen]
    for l in new:
        print("NEW:", l)
        if TOPIC:
            notify(l)
    STATE.write_text(json.dumps(sorted(seen | set(new)), indent=1))
    print(f"{len(links)} listings, {len(new)} new match(es)")

if __name__ == "__main__":
    main()
