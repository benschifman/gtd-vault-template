---
name: meeting-capture
description: Turn synced Granola meeting notes in 00-Inbox/granola/ into curated meeting notes in 10-Journal/10-10-Events/. Reconciles against notes Jordan already wrote by hand, fills in context and projects, proposes action items as Tasknotes for approval, and hands unknown attendees to the CRM Librarian. Use this skill when the user asks to process meeting notes, promote Granola notes, file meetings, or clear the Granola inbox.
---

# Meeting Capture Skill

The **Granola Meetings Simple Sync** plugin writes raw meeting notes to `00-Inbox/granola/` every 15 minutes, already in Jordan's meeting format. This skill does the judgment work the plugin can't: deciding which meetings deserve a curated note, reconciling against notes Jordan already wrote, and proposing action items and new contacts. Tasknotes are always proposed for Jordan's approval, never created silently.

The plugin handles all formatting. **Do not reformat notes** — if the output looks wrong, fix the template at `90-System/templates/granola-sync.md` rather than patching notes one by one.

## What gets processed at all — decide this first

These are Jordan's standing decisions. They determine which notes you touch, so read them before Step 1 rather than discovering them mid-run.

### Recurring series — 1:1s are promoted, standups are not

**A recurring title does not mean "skip."** Jordan's decision (2026-08-13) splits on *who is in the room*, not on whether the meeting repeats:

| Type | Treatment | Why |
|---|---|---|
| **Recurring 1:1s** — `Tim <> Jordan weekly`, `Hart <> Jordan` | **Promote, one note per occurrence** | A standing 1:1 is a relationship with accumulating substance. These carried org restructuring, Jordan's reporting line, project scoping, and FERC analysis. |
| **Team standups** — `Emerging tech weekly team update` | **Delete** | Status information, captured elsewhere, mostly not relevant. Jordan's explicit instruction for this series. |

Promote one note per occurrence, matching every other note in `10-10-Events` — do not consolidate a series into one rolling note.

Undecided as of 2026-08-13: `Weekly team stand-up` and `Infrastructure Team Weekly Meeting`. Ask Jordan rather than assuming they follow the emerging-tech rule.

Detect recurring series by counting duplicate titles rather than maintaining a list:

```bash
python3 - <<'PY'
import glob,os,re
from collections import Counter
t=[os.path.basename(f)[:-3][13:].strip() for f in glob.glob("00-Inbox/granola/*.md")
   if not re.search(r'^promoted:[ \t]*true',open(f,encoding='utf-8').read(),re.M)]
for title,n in Counter(t).most_common():
    if n>1: print(f"{n}x  {title}")
PY
```

Promote a single instance only when Jordan asks for it, or when one clearly carries a decision worth finding later.

### Personal notes — delete, don't archive

Granola captures Jordan's personal calls too — medical appointments, family logistics. These do not belong in a work vault. **Surface them and ask before deleting** (they may be the only convenient copy, though Granola retains the original), then delete without keeping a backup. Seen so far: doctor's calls, insurance/prior-authorization calls, family scheduling. Judge by content, not title — `consult call` turned out to be a family photographer booking.

The inverse also holds: **read before dismissing something as junk.** `CIA 4 Huddle` looked like noise and is Compute in America project work, including that Jordan drafted a bill for Will Hunt with Rep. Moolenaar as intended introducer. `New note` was a real project status update.

## Step 1 — Reconcile before touching anything

```bash
python3 90-System/scripts/granola_reconcile.py
```

This date-scopes and fuzzy-matches every inbox note against `10-Journal/10-10-Events/`. Titles differ a lot between the two — Jordan writes `Casey M <> Jordan re NHPA`, Granola writes `Casey Morgan and Jordan Lee` — so never match on title alone, and never assume one meeting per date.

Output has four groups:

| Group | Meaning | What to do |
|---|---|---|
| **CONFIDENT** (score ≥ 0.55) | Same meeting, already curated | Apply the merge rule below |
| **POSSIBLE** (0.30–0.55) | Might be the same meeting | **Ask Jordan** — this tier reliably contains both real and false matches |
| **NO MATCH** | Only exists in Granola | Candidate to promote |
| **CURATED WITHOUT SUMMARY** | Jordan's note has an empty `## Granola Notes` | Merge target |

Never auto-resolve the POSSIBLE tier. A wrong merge overwrites Jordan's own writing.

## Step 2 — The merge rule

For an inbox note that matches a curated note:

- **Curated note's `## Granola Notes` is empty** → merge the Granola summary into Jordan's note, then delete the inbox copy.
- **Curated note already has a summary** → keep Jordan's original untouched, delete the inbox copy.

Jordan's writing always wins. Merging means filling an empty section, never replacing prose he wrote.

### ⚠️ Deleting inside the sync window

The plugin's dedup only scans `00-Inbox/granola/` and keys on `granola_id`. **Deleting a note whose meeting is within the last 30 days makes the plugin re-create it on the next sync.** The reconcile script marks each row `safe_to_delete`.

If a note is inside the window and you'd otherwise delete it, leave a tombstone instead — strip the body, keep the frontmatter, and set `promoted: true`:

```yaml
---
granola_id: <unchanged>
promoted: true
superseded_by: "[[2026-07-13 - Chris <> Jordan NHPA]]"
---
```

Delete tombstones once they age past 30 days.

## Step 3 — Promote unmatched meetings

Only promote meetings worth a curated note. Most syncs contain recurring standups and one-off calls Jordan will never revisit; those stay in the inbox as a searchable archive. If more than ~10 are unmatched, show Jordan the list and ask which to promote rather than promoting all of them.

To promote:

1. **Copy** — do not move. Moving it out of the inbox breaks the plugin's dedup.
2. Filename: `YYYY-MM-DD - Title.md` in `10-Journal/10-10-Events/`. The plugin's sanitizer turns `<>` into `--`, so **restore `<>`** when Jordan's convention calls for it (`MPI -- NWF` → `MPI <> NWF`).
3. Drop `granola_id`, `promoted`, and `granola_url` from the promoted copy's frontmatter — keep the `granola_url` line in the body so the transcript link survives.
4. Fill `## Context` with one or two sentences on why the meeting mattered.
5. Set `related_projects` by checking `20-GTD/20-10-Projects/` for a match.
5b. **Append the full transcript** as a `## Transcript` section at the end of the promoted copy
   (after `## Action Items`). This is the default for every promoted note — see "Step 3b" below
   for the fetch and the exceptions.
6. **Tombstone the inbox original** — strip the body, keep the frontmatter, set `promoted: true` and
   `promoted_to: "[[<curated note>]]"`. Do **not** merely add the flag and leave the body in place.

   ```yaml
   ---
   granola_id: <unchanged>
   category: meeting
   date: <unchanged>
   promoted: true
   promoted_to: "[[2026-08-19 - Padilla team <> MPI re NHPA]]"
   ---
   ```

   A flag alone is invisible. A promoted note that keeps its body is byte-for-byte
   indistinguishable from unprocessed work in a file listing, and stays that way for up to 30
   days until the Step 6 sweep can delete it. That is exactly how the inbox reached 30 notes on
   2026-08-24 with **zero** of them actually unprocessed. Strip the body at promotion time and
   the inbox always shows the truth.

   Read the file fully, then write. Never inline a read inside a write call — `open(p,"w")`
   truncates before the read runs.

## Step 3b — Fetch the transcript

**Every promoted note carries its full transcript by default** (Jordan's decision, 2026-09-11). The
Granola summary is lossy in exactly the places that matter: on the 2026-09-11 Dana Whitfield
call the summary reduced a key idea to the two words "Hal Singer" and dropped her central
framing entirely. A transcript in the vault is searchable, quotable, and survives Granola. It
also lets the reader check the summary's claims — which are AI-generated and inherit the
transcription's garbled names (see Step 5).

Volume stays proportional to importance because only *promoted* notes get one. Standups and
notes left in the inbox never do.

**Exceptions — skip the transcript and say so in the report:**
- Anything with personal or medical content, even if the meeting is otherwise work. The
  transcript is verbatim and the vault is pushed to GitHub. When in doubt, ask.
- A meeting where a participant asked not to be recorded or quoted.
- Jordan says "summary only" for that meeting.

**The fetch.** The sync plugin's own MCP client exposes `getTranscript(id)` — no API key, no
`gws`. `obsidian eval` does not await promises, so park the result on a global and read it back:

```bash
obsidian eval code="window.__tr='pending'; const p=app.plugins.plugins['granola-meetings-simple-sync']; const rt=[...p.runtimes.values()][0]; rt.mcp.getTranscript('<granola_id>').then(r=>{window.__tr=typeof r==='string'?r:JSON.stringify(r)}).catch(e=>{window.__tr='ERR '+e.message}); 'fired'" >/dev/null 2>&1
sleep 6
obsidian eval code="window.__tr" > "$SCRATCH/tr_raw.txt" 2>&1
```

The result is a JSON object (`{id, title, transcript}`) wrapped in the CLI's `=> ` prefix; the
`transcript` string is one long line with speaker turns separated by two or more spaces and a
`Name:` label. Granola labels Jordan `Me` and any unattributed line `Them`; other speakers appear
by display name (`Dana Whitfield`) or handle (`rileywhitfield`). Reformat into one paragraph
per turn with bold labels:

```bash
python3 - "$SCRATCH" <<'PY'
import sys,json,re
S=sys.argv[1]
raw=open(S+'/tr_raw.txt').read(); raw=raw[raw.index('{'):raw.rindex('}')+1]
t=json.loads(raw)['transcript']
# Add every speaker label Granola used for this meeting; names with spaces must be listed
# explicitly or the generic two-word pattern will miss handles like "rileywhitfield".
speakers=['Me','Them','rileywhitfield','Dana Whitfield','Morgan Ellis']
t=re.sub(r'\s{2,}(?=(?:'+'|'.join(map(re.escape,speakers))+r'|[A-Z][a-z]+ [A-Z][a-z]+):\s)','\n',t).strip()
names={'Me':'**Jordan:**','Them':'**Unidentified:**','rileywhitfield':'**Riley Whitfield:**',
       'Dana Whitfield':'**Dana Whitfield:**','Morgan Ellis':'**Morgan Ellis:**'}
out=[]
for ln in t.split('\n'):
    m=re.match(r'^([^:]{1,30}):\s*(.*)$',ln)
    out.append(names[m.group(1).strip()]+' '+m.group(2) if m and m.group(1).strip() in names else ln)
open(S+'/transcript.md','w').write('\n\n'.join(out)+'\n')
PY
```

Check the speaker set before trusting the split — print the counter of labels and make sure
every attendee who spoke appears. A name missing from `speakers` shows up as text glued to the
previous turn, not as an error.

Then append to the promoted copy:

```markdown
## Transcript

Speaker labels from Granola; "Unidentified" is Granola's "Them" where it could not attribute the line.

**Jordan:** ...
```

Keep `## Context` and `## Granola Notes` above it — the transcript is the record, the summary is
what gets read. Note in `## Context` who was invited but does not appear in the transcript; an
attendee list is the calendar's claim, the transcript is the evidence.

## Step 4 — Action items

Read the summary for commitments Jordan made. Granola often has a "Next Steps" section, but commitments also appear inline.

**Never create a Tasknote from a meeting note without Jordan's explicit approval first.** This is a
hard gate, not a preference. Present the candidates as a numbered table and stop:

| # | Proposed task | Whose commitment | Project | Context | Due |
|---|---|---|---|---|---|

Then ask which to create. Jordan replies by number. Create only the rows he approves; the rest are
dropped, not filed as someday/maybe.

The gate applies **however this skill is running** — including inside a subagent, inside
`daily-start` or `weekly-review`, and inside a batch of many meetings. A subagent that cannot
reach Jordan does not thereby get permission: it returns the proposed table in its report and
creates nothing. If a batch produces candidates from several meetings, present one combined
table at the end rather than gating per meeting.

Use the `tasknotes` skill for the file format; set `projects` and `contexts`, and a `due` date if
the meeting implied one.

**Only Jordan's own commitments are candidates.** Something another attendee owes — their draft,
their paper, their intro — is not a next action. Do not convert it into a `status: waiting` task
to keep it visible; that is the same thing wearing a different status, and it still needs
approval. If a meeting produced no commitment from Jordan, the correct outcome is **zero tasks**,
and the report should say so plainly rather than manufacturing something to show for the run.

**Never invent a date.** A due or scheduled date comes from the meeting or it is absent. "End of
the year" is not 2026-12-15.

## Step 5 — Attendees

The plugin links attendees to person notes by matching a frontmatter `emails` array. Anything it can't match is left as a plain `[[Name]]` wikilink, which will be unresolved.

**Filter before treating an unresolved name as a new contact:**

| Pattern | Example | Action |
|---|---|---|
| Room or resource | `Conference`, `ARI-Floor 12-Lincoln (2)` | Remove from `attendees` — never a contact |
| Single-word handle | `Aidan`, `Mlove`, `Kcheuk` | Try to identify from the note body; if unclear, ask Jordan. Never create a file from a bare handle. |
| Full name | `Arthur Tellis` | Candidate for the CRM Librarian |

**Granola mis-transcribes names — check the CRM before trusting the transcript.** A note described a Will as "former staffer for Sen. Ryan Shots (Senate Committee on Indian Affairs)", which read as a different Will. It was Will Poff-Webster, and his CRM file already listed `[[Senator Brian Schatz]]` under prior organizations — Granola had garbled "Brian Schatz" into "Ryan Shots". **When a transcript detail seems to rule out the obvious person, check their CRM entry before concluding it is someone else.** Names, org names, and titles are the most frequently garbled parts of a transcript.

**"Contains a space" is NOT a test for a real name.** It admits `ARI-Floor 12-Lincoln (2)`, `Jack (OP)`, and `Heidi Lie.williams`. Before treating a name as real, reject anything that:

- contains a digit, parentheses, or `floor` / `room` / `conference` / `zoom`
- has a dot inside a word (`Lie.williams` — an email fragment, not a name)
- is a case-variant, substring, or first-name-only form of a name already in the list (`Arthur` when `Arthur Tellis` is present; `Jack (OP)` when `Jack Titus` is present)

### Preserving attendees before deleting an inbox copy

The inbox copy often lists attendees the curated note lacks. Deleting it outside the sync window loses them permanently. **Before deleting, merge real full names into the curated note's `attendees`** — additive only, never touching prose.

When comparing, **strip wikilink aliases first**: `[[Daniel Schory|Dan Schory]]` and `[[Daniel Schory]]` are the same person, and comparing raw link text creates duplicates.

To list everyone named in a meeting who has no CRM file:

```bash
python3 90-System/scripts/crm_unresolved_attendees.py
```

Hand full names to the **`crm-librarian`** agent, Enrich Person, 5–10 at a time — the script already ranks by meeting count and hides one-off bare handles.

**Capture emails whenever you see them.** Attendee emails appear in Granola's participant metadata. Every one added to a person file's `emails` array makes future meetings auto-link. This is the single highest-leverage thing this skill does — it compounds.

## Step 6 — Reconcile the inbox with reality

Filed notes leave a frontmatter-only tombstone in `00-Inbox/granola/` so the sync plugin does not
re-create them. This step enforces that invariant and clears anything aged out. **Run it at the end
of every pass** — and it is safe to run on its own, at any time, as a repair.

It does two things, in order:

1. **Tombstone any note flagged `promoted: true` that still has a body.** Step 3 should have done
   this at promotion time; this catches passes that didn't, including ones from older versions of
   this skill. Without it, filed notes masquerade as unprocessed work.
2. **Delete tombstones whose meeting is older than the sync window.** Past 30 days the plugin no
   longer looks for the `granola_id`, so the stub can go.

```bash
python3 - <<'PY'
import glob, os, re, datetime, io

CUT = datetime.date.today() - datetime.timedelta(days=30)   # match syncTimeRange
KEEP = ("granola_id", "category", "date", "promoted", "promoted_to",
        "superseded_by", "deleted_by_policy")
NOTE = "Tombstone. Body stripped after promotion; frontmatter kept only so the sync plugin does not re-create this note. Safe to delete after the 30-day sync window."

# A note is "still full" if it has a POPULATED `## Granola Notes` section — the
# same test granola_reconcile.py uses, so the two tools always agree. Raw body
# length is the wrong test: a correct tombstone often carries a sentence saying
# why it was filed, and that provenance is worth keeping.
SECTION = re.compile(r"^##\s*Granola Notes\s*$(.*?)(?=^##\s|\Z)", re.M | re.S)

tombstoned = deleted = 0
for f in sorted(glob.glob("00-Inbox/granola/*.md")):
    with io.open(f, encoding="utf-8") as fh:
        text = fh.read()                      # read fully BEFORE any write
    if not re.search(r"^promoted:[ \t]*true", text, re.M):
        continue                              # never touch unprocessed notes
    try:
        meeting_date = datetime.date.fromisoformat(os.path.basename(f)[:10])
    except ValueError:
        continue                              # unparseable date: leave it alone
    if meeting_date < CUT:
        os.remove(f); deleted += 1
        continue
    m = SECTION.search(text)
    if not m or len(m.group(1).strip()) <= 20:
        continue                              # already a tombstone
    parts = text.split("---")
    kept = [ln for ln in parts[1].strip("\n").split("\n")
            if ln.split(":")[0].strip() in KEEP]
    with io.open(f, "w", encoding="utf-8") as fh:
        fh.write("---\n" + "\n".join(kept) + "\n---\n\n" + NOTE + "\n")
    tombstoned += 1

print(f"tombstoned {tombstoned} filed-but-unstripped notes; deleted {deleted} aged-out tombstones")
PY
```

The `promoted: true` guard is what makes this safe — an unprocessed note is never touched. The
30-day check runs off the filename date, and anything unparseable is skipped rather than guessed at.

**A tombstone must keep `granola_id`.** That is the only field the plugin's dedup reads. Strip it and
the meeting re-syncs as a fresh note on the next run.

## Step 7 — Report

Summarize: merged, promoted, kept-as-is, tasks created, contacts handed off. Then say how many notes remain in the inbox unprocessed.

## Rules

- **Never overwrite Jordan's prose.** Merge into empty sections only.
- **Never move inbox files** — copy, then tombstone the original.
- **Never delete a note inside the 30-day sync window** — tombstone it.
- **A filed note is always a tombstone, never a flagged full copy.** `promoted: true` on a note that
  still has its body is a bug, not a state. It makes finished work indistinguishable from a backlog.
- **A tombstone must keep `granola_id`** — it is the only field the plugin's dedup reads.
- **Never create a person file from a room name or a bare handle.**
- Don't promote everything. The inbox is a fine permanent archive for meetings that don't warrant curation.
- **A promoted note carries its full transcript** unless it falls under a Step 3b exception. Summary-only promotion is the exception, and the report says why.
