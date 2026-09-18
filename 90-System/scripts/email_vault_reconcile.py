#!/usr/bin/env python3
"""Reconcile GTD-labeled Gmail threads against their vault counterparts.

The Gmail side comes from the MCP connector, which this script cannot reach.
Feed it a JSON file written by the calling skill:

    [
      {"threadId": "1a01caca4f4c960e",
       "subject": "Flex Bill comments",
       "from": "andrew@example.org",
       "labels": ["1-Next-Action"]},
      ...
    ]

Then:  python3 90-System/scripts/email_vault_reconcile.py threads.json [--json]

Reports, per thread, whether the vault object its label implies actually exists,
and flags mismatches (labeled Someday-Maybe but the task is open, labeled
Next-Action but the task is already done, etc.). Dependency-free; works with
Obsidian closed.
"""

import json
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parents[2]

NEXT_ACTIONS = VAULT / "20-GTD/20-20-Next-Actions"
ARCHIVE = VAULT / "20-GTD/20-60-Archive"
PROJECTS = VAULT / "20-GTD/20-10-Projects"
CONTEXTS = VAULT / "20-GTD/20-30-Contexts"

# label prefix -> (what the vault must hold, acceptable task statuses)
EXPECT = {
    "1-Next-Action": ("task", {"open", "in-progress"}),
    # 2-Project/* is a FILING label: it says which project a thread belongs to,
    # not that Jordan owes an action. Outcomes and next actions live in the vault.
    "2-Project": ("project-ref", set()),
    "3-Delgated-Waiting": ("task", {"waiting"}),
    "4-Scheduled": ("calendar", set()),
    "5-Someday-Maybe": ("task", {"someday-maybe-inactive"}),
    "6-Reference": ("none", set()),
    "7-Agendas": ("agenda", set()),
}

STOPWORDS = {
    "the", "and", "for", "with", "from", "your", "you", "our", "this", "that",
    "are", "was", "has", "have", "will", "can", "not", "but", "all", "any",
    "re", "fwd", "fw", "about", "into", "out", "new", "get", "how", "what",
}


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return m.group(1) if m else ""


def prop(fm, name):
    m = re.search(rf"^{name}:\s*(.+?)\s*$", fm, re.M)
    if not m:
        return None
    return m.group(1).strip().strip("\"'")


def load_notes():
    notes = []
    for folder, kind in ((NEXT_ACTIONS, "task"), (ARCHIVE, "archived"),
                         (PROJECTS, "project")):
        if not folder.is_dir():
            continue
        for f in sorted(folder.glob("*.md")):
            try:
                text = f.read_text(encoding="utf-8")
            except OSError:
                continue
            fm = frontmatter(text)
            notes.append({
                "path": f.relative_to(VAULT).as_posix(),
                "name": f.stem,
                "kind": kind,
                "status": prop(fm, "status"),
                "title": prop(fm, "title") or f.stem,
                "projects": re.findall(r"\[\[([^\]]+)\]\]",
                                       re.search(r"^projects:.*?(?=^\S|\Z)", fm,
                                                 re.M | re.S).group(0))
                            if re.search(r"^projects:", fm, re.M) else [],
                "text": text,
            })
    return notes


def agenda_text():
    blobs = {}
    if CONTEXTS.is_dir():
        for f in sorted(CONTEXTS.glob("@agenda-*.md")):
            try:
                blobs[f.stem] = f.read_text(encoding="utf-8")
            except OSError:
                pass
    return blobs


def keywords(subject):
    words = re.findall(r"[A-Za-z0-9']{3,}", (subject or "").lower())
    return [w for w in words if w not in STOPWORDS]


def gtd_label(labels):
    """Return the first GTD label on the thread, or None."""
    for lab in labels or []:
        head = lab.split("/")[0]
        if head in EXPECT:
            return lab
    return None


def reconcile(threads, notes, agendas):
    rows = []
    project_names = {n["name"] for n in notes if n["kind"] == "project"}

    for t in threads:
        tid = (t.get("threadId") or "").strip()
        label = gtd_label(t.get("labels"))
        row = {
            "threadId": tid,
            "subject": t.get("subject", ""),
            "from": t.get("from", ""),
            "label": label,
            "expects": None,
            "matches": [],
            "fuzzy": [],
            "verdict": "",
            "detail": "",
        }

        if label is None:
            row["verdict"] = "UNLABELED"
            row["detail"] = "no GTD label — classify it first"
            # Still look for a vault object: an unlabeled thread that already
            # has a task needs a label, not a second task.
            if tid:
                row["matches"] = [n for n in notes if tid in n["text"]]
            if row["matches"]:
                row["detail"] += (" — already has " +
                                  ", ".join(f"{n['path']} [{n['status']}]"
                                            for n in row["matches"]))
            rows.append(row)
            continue

        kind, ok_status = EXPECT[label.split("/")[0]]
        row["expects"] = kind

        # exact match: the thread id appears in a note body
        if tid:
            row["matches"] = [n for n in notes if tid in n["text"]]

        # fuzzy fallback — vault sometimes holds a Gmail UI permalink
        # (#inbox/FMfcgz...) rather than the API thread id, so ids won't match.
        if not row["matches"]:
            kws = set(keywords(row["subject"]))
            if kws:
                for n in notes:
                    if n["kind"] == "project":
                        continue
                    hit = kws & set(keywords(n["title"]))
                    if len(hit) >= 2:
                        row["fuzzy"].append((n, sorted(hit)))

        live = [n for n in row["matches"] if n["kind"] in ("task", "project")]
        archived = [n for n in row["matches"] if n["kind"] == "archived"]

        if kind == "none":
            row["verdict"] = "OK"
            row["detail"] = "reference — no vault object required"

        elif kind == "project-ref":
            row["verdict"] = "OK"
            linked = [n for n in row["matches"] if n["kind"] == "project"]
            row["detail"] = ("project filing label — linked from " +
                             ", ".join(n["path"] for n in linked)) if linked else (
                             "project filing label — reference only, no task expected")

        elif kind == "calendar":
            row["verdict"] = "CHECK"
            row["detail"] = "scheduled — confirm a calendar event exists; no task expected"
            if live:
                row["verdict"] = "MISMATCH"
                row["detail"] = ("labeled 4-Scheduled but has a task: "
                                 + ", ".join(n["path"] for n in live))

        elif kind == "agenda":
            person = label.split("/", 1)[1] if "/" in label else ""
            key = next((k for k in agendas
                        if person and person.lower() in k.lower()), None)
            if key is None:
                row["verdict"] = "MISSING"
                row["detail"] = f"no agenda context file for '{person}' in 20-GTD/20-30-Contexts/"
            elif tid and tid in agendas[key]:
                row["verdict"] = "OK"
                row["detail"] = f"listed in {key}.md"
            else:
                row["verdict"] = "MISSING"
                row["detail"] = f"not yet listed in {key}.md"

        elif live:
            statuses = {n["status"] for n in live}
            paths = ", ".join(n["path"] for n in live)
            if ok_status and not (statuses & ok_status):
                row["verdict"] = "MISMATCH"
                row["detail"] = (f"task status {sorted(s for s in statuses if s)} "
                                 f"≠ expected {sorted(ok_status)} — {paths}")
            else:
                row["verdict"] = "OK"
                row["detail"] = paths
            if kind == "task+project":
                linked = {p for n in live for p in n["projects"]}
                if not linked:
                    row["verdict"] = "MISMATCH"
                    row["detail"] += " — task has no projects: link"
                else:
                    missing = [p for p in linked if p not in project_names]
                    if missing:
                        row["verdict"] = "MISMATCH"
                        row["detail"] += f" — project file missing for {missing}"

        elif archived:
            row["verdict"] = "STALE"
            row["detail"] = ("task is done/archived (" +
                             ", ".join(n["path"] for n in archived) +
                             ") — thread can probably lose its label and be archived")

        else:
            row["verdict"] = "MISSING"
            want = {"task": "a Tasknote", "task+project": "a Tasknote linked to a project"}
            row["detail"] = f"no vault object — needs {want.get(kind, kind)}"
            if row["fuzzy"]:
                row["detail"] += (" (possible existing match: " +
                                  "; ".join(f"{n['path']} [{'+'.join(h)}]"
                                            for n, h in row["fuzzy"][:3]) + ")")

        rows.append(row)
    return rows


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if not args:
        print(__doc__)
        return 2
    threads = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    if isinstance(threads, dict):
        threads = threads.get("threads", [])

    rows = reconcile(threads, load_notes(), agenda_text())

    if as_json:
        print(json.dumps(rows, indent=2, default=lambda o: o.get("path", str(o))))
        return 0

    order = ["UNLABELED", "MISSING", "MISMATCH", "STALE", "CHECK", "OK"]
    rows.sort(key=lambda r: (order.index(r["verdict"]), r["subject"]))
    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1

    print(f"{len(rows)} labeled threads — " +
          ", ".join(f"{k} {v}" for k, v in
                    sorted(counts.items(), key=lambda kv: order.index(kv[0]))))
    print()
    for i, r in enumerate(rows, 1):
        if r["verdict"] == "OK":
            continue
        print(f"{i:>3}. [{r['verdict']}] {r['subject'][:64]}")
        print(f"     label: {r['label'] or '—'}   from: {r['from'][:40]}")
        print(f"     {r['detail']}")
        print(f"     https://mail.google.com/mail/u/0/#all/{r['threadId']}")
        print()
    ok = [r for r in rows if r["verdict"] == "OK"]
    filed = [r for r in ok if r["expects"] == "project-ref"]
    if ok:
        note = f"({len(ok)} threads already reconciled — not listed"
        if filed:
            note += f"; {len(filed)} of them 2-Project/* filings, reference only"
        print(note + ")")
    return 0


if __name__ == "__main__":
    sys.exit(main())
