#!/usr/bin/env python3
"""Reconcile synced Granola notes against Jordan's curated meeting notes.

Synced notes land in 00-Inbox/granola/; curated ones live in
10-Journal/10-10-Events/. The same meeting often exists in both under
different titles ("Casey M <> Jordan re NHPA" vs "Casey Morgan and Jordan Lee"),
so matching is date-scoped and fuzzy, and anything uncertain is reported for
a human decision rather than guessed.

Read-only. Never writes or deletes.

KNOWN LIMITATION — acronyms. Matching is token-overlap based, so an acronym
and its expansion share nothing and score zero: "HNRC O&I -- Jordan S." did not
match the curated "MPI <> House natural resources investigations" on the same
date, and landed in NO MATCH rather than even POSSIBLE. When a NO MATCH note
shares a date with a curated note, eyeball the pair before promoting it.

Usage:
    python3 90-System/scripts/granola_reconcile.py [--json]
"""

import os
import re
import sys
import json
import glob
import difflib
import datetime

VAULT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INBOX = os.path.join(VAULT, "00-Inbox", "granola")
EVENTS = os.path.join(VAULT, "10-Journal", "10-10-Events")

SYNC_WINDOW_DAYS = 30          # must match the plugin's syncTimeRange
CONFIDENT = 0.55               # auto-matchable similarity
POSSIBLE = 0.30                # worth showing for confirmation

# Words that carry no signal when comparing a meeting title.
NOISE = {
    "jordan", "lee", "and", "the", "re", "with", "call", "meeting", "sync",
    "chat", "weekly", "catch", "up", "intro", "vs", "x", "a", "of", "on",
}


def norm(title):
    """Comparable token set for a meeting title."""
    t = title.lower()
    t = t.replace("--", " ").replace("<>", " ").replace("-", " ")
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return {w for w in t.split() if w and w not in NOISE and len(w) > 1}


def similarity(a, b):
    ta, tb = norm(a), norm(b)
    if not ta or not tb:
        return 0.0
    overlap = len(ta & tb) / min(len(ta), len(tb))
    ratio = difflib.SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()
    return max(overlap, ratio)


def parse(path):
    name = os.path.basename(path)[:-3]
    m = re.match(r"(\d{4}-\d{2}-\d{2})\s*-\s*(.+)", name)
    date, title = (m.group(1), m.group(2)) if m else ("", name)
    text = open(path, encoding="utf-8").read()
    gid = re.search(r"^granola_id:\s*(\S+)", text, re.M)
    section = re.search(r"## Granola Notes(.*?)(?=^## |\Z)", text, re.S | re.M)
    body = re.sub(r"<!--.*?-->", "", section.group(1), flags=re.S).strip() if section else ""
    return {
        "path": os.path.relpath(path, VAULT), "name": name, "date": date,
        "title": title, "granola_id": gid.group(1) if gid else None,
        # No `## Granola Notes` heading at all means the note predates the
        # template — that is not the same as having the section but leaving it
        # empty, which is the actual merge target.
        "has_section": section is not None,
        "has_summary": len(body) > 20,
        # Already-filed notes keep their frontmatter as a tombstone so the sync
        # plugin does not re-create them. Without this the reconciler matches
        # its own past work and reports dozens of phantom matches.
        "promoted": bool(re.search(r"^promoted:[ \t]*true", text, re.M)),
    }


def reconcile():
    all_inbox = [parse(x) for x in sorted(glob.glob(os.path.join(INBOX, "*.md")))]
    inbox = [p for p in all_inbox if not p["promoted"]]
    # Notes already filed. These are excluded from matching, which is correct —
    # but they must be REPORTED, or an inbox where everything is already done
    # prints four zeroes and reads as a broken script. A filed note is supposed
    # to be a frontmatter-only tombstone; one that still has a body is an
    # invariant violation (Step 3 promoted it but never stripped it) and is why
    # a cleared inbox can still look like a pile of unprocessed work.
    filed = [p for p in all_inbox if p["promoted"]]
    untombstoned = [p for p in filed if p["has_summary"]]
    events = [parse(p) for p in sorted(glob.glob(os.path.join(EVENTS, "*.md")))]
    by_date = {}
    for e in events:
        by_date.setdefault(e["date"], []).append(e)

    cutoff = datetime.date.today() - datetime.timedelta(days=SYNC_WINDOW_DAYS)
    confident, possible, promote = [], [], []

    for g in inbox:
        cands = by_date.get(g["date"], [])
        scored = sorted(((similarity(g["title"], c["title"]), c) for c in cands),
                        key=lambda x: -x[0])
        best, cand = (scored[0] if scored else (0.0, None))
        try:
            safe = datetime.date.fromisoformat(g["date"]) < cutoff
        except ValueError:
            safe = False
        row = {
            "granola": g["path"], "granola_title": g["title"], "date": g["date"],
            "match": cand["path"] if cand else None,
            "match_title": cand["title"] if cand else None,
            "score": round(best, 2),
            # merge only when Jordan's note has no summary of its own
            "action": None,
            "safe_to_delete": safe,
        }
        if best >= CONFIDENT:
            row["action"] = "merge" if not cand["has_summary"] else "keep-original"
            confident.append(row)
        elif best >= POSSIBLE:
            possible.append(row)
        else:
            promote.append(row)

    # Merge targets are notes that HAVE the section but left it empty.
    orphan = [e for e in events if e["has_section"] and not e["has_summary"]]
    return confident, possible, promote, orphan, filed, untombstoned


def main():
    confident, possible, promote, orphan, filed, untombstoned = reconcile()

    if "--json" in sys.argv:
        print(json.dumps({"confident": confident, "possible": possible,
                          "promote": promote,
                          "curated_without_summary": [o["path"] for o in orphan],
                          "already_filed": [f["path"] for f in filed],
                          "filed_but_not_tombstoned": [u["path"] for u in untombstoned]}, indent=2))
        return

    print(f"ALREADY FILED ({len(filed)}) — excluded from matching below, nothing to do")
    if untombstoned:
        print(f"  ⚠️  {len(untombstoned)} of them still have a body and should be tombstones.")
        print(f"      They look like unprocessed work in the inbox. Run Step 6 of meeting-capture.")
        for u in untombstoned[:10]:
            print(f"        {u['date']}  {u['title']}")
        if len(untombstoned) > 10:
            print(f"        … +{len(untombstoned) - 10} more")
    print()

    print(f"CONFIDENT MATCHES ({len(confident)}) — same meeting, already curated")
    for r in confident:
        flag = "" if r["safe_to_delete"] else "  ⚠️ inside sync window, deleting re-syncs it"
        print(f"  [{r['score']}] {r['date']}  {r['granola_title']}")
        print(f"        -> {r['match_title']}   ACTION: {r['action']}{flag}")

    print(f"\nPOSSIBLE MATCHES ({len(possible)}) — confirm before acting")
    for r in possible:
        print(f"  [{r['score']}] {r['date']}  {r['granola_title']}")
        print(f"        -> {r['match_title']}")

    print(f"\nNO MATCH ({len(promote)}) — candidates to promote")
    for r in promote[:20]:
        print(f"  {r['date']}  {r['granola_title']}")
    if len(promote) > 20:
        print(f"  … +{len(promote) - 20} more")

    print(f"\nCURATED NOTES WITH NO SUMMARY ({len(orphan)}) — merge targets")
    for o in orphan:
        print(f"  {o['name']}")


if __name__ == "__main__":
    main()
