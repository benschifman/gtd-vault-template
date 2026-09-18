---
name: project-create
description: Create a new GTD project note in 20-GTD/20-10-Projects/ from the project template, with an outcome-phrased name, an objective linked to its heading in priorities.md, and a first next action. Use this skill whenever Jordan says to make, start, add, or set up a new project, or when clarifying an inbox item or meeting commitment produces something that needs more than one action to finish.
---

# Project Create Skill

Creates one project note. The file is rendered from `90-System/templates/project.md` by
`90-System/scripts/new_from_template.py`, not hand-written, so the template stays the single
source of truth and this skill cannot drift from it.

A project is any outcome needing **more than one action** to finish. One action is a Tasknote —
use the `tasknotes` skill instead and stop here.

## Step 0 — Preconditions

None beyond the vault itself — the template script runs with Obsidian closed. Setting fields in
Step 4 uses `obsidian property:set`, which does need Obsidian open; if it is closed, edit the
frontmatter directly instead.

## Step 1 — Name it as an outcome

Project names are **the finished state, in past or perfect tense** — not a topic, not a task:

| Good | Bad |
|---|---|
| `Opt in Bill passed into law` | `Opt in zones bill` |
| `NHPA Heatmap article is published` | `Write NHPA heatmap piece` |
| `FERC 206 interconnection security standards adopted` | `FERC work` |

The name doubles as the wikilink target in every task's `projects:` array, so it is expensive to
change later. Propose the name and get Jordan's agreement before creating anything.

## Step 2 — Gather the fields

Ask as one numbered block, not one question at a time. Jordan answers by number.

| Field | Notes |
|---|---|
| `objective` | **Required.** A wikilink to the objective's heading in `20-GTD/20-05-Horizons/priorities.md`, aliased to a readable shorthand — see the table in Step 4. Read that file and propose the objective rather than asking cold. The weekly review scorecard and `gtd-coach` both key off this — a blank objective drops the project out of both silently. |
| `priority` | `high` / `medium` / `low`. Some legacy projects hold `"1"` or `"3"`; those are stale, do not copy them. |
| `desired_outcome` | One sentence: how you know it is done. If Jordan cannot state it, the project is not ready — say so. |
| `deadline` | Only if a real one exists. Never invent one. |
| `area`, `estimated_duration`, `contacts` | Optional. Leave blank rather than guessing; most existing projects leave `area` empty. |
| `status` | Defaults to `active`. Use `someday-maybe-inactive` if Jordan is parking it. |

## Step 3 — Create the note from the template

```bash
python3 90-System/scripts/new_from_template.py project "20-GTD/20-10-Projects/<PROJECT NAME>"
```

The script renders the template's `{{date:...}}` placeholders, refuses to overwrite an existing
file, and prints the path it wrote. Confirm it is under `20-GTD/20-10-Projects/` before
continuing.

## Step 4 — Fill the fields

Set frontmatter with the CLI, one property per call:

```bash
obsidian property:set name="priority" value="low" path="20-GTD/20-10-Projects/<NAME>.md"
```

### The `objective` value

Do **not** write a bare `O5`. Write a wikilink to the objective's heading in
`priorities.md`, aliased to a readable shorthand, so the field says what it means and
clicking it jumps to the objective itself. Copy the exact value from this table — the
heading text must match `priorities.md` character-for-character or the anchor silently
fails to resolve:

| | Value to set |
|---|---|
| O1 | `[[priorities#O1: Create policy change leading to counterfactually more secure compute in America via Opt in zones bill\|O1 - Opt-in Zones Bill]]` |
| O2 | `[[priorities#O2: Develop AI regulation / policy expertise and counterfactually improve AI regulation\|O2 - AI Regulation Expertise]]` |
| O3 | `[[priorities#O3: Increase counterfactual permitting reform quality or chance of passing\|O3 - Permitting Reform Quality]]` |
| O4 | `[[priorities#O4: Build Competency in Congressional Engagement / Build Strategic Network\|O4 - Congressional Engagement and Network]]` |
| O5 | `[[priorities#O5: Enhance Public Profile and Communication Skills\|O5 - Public Profile and Communication Skills]]` |
| O6 | `[[priorities#O6: Contribute to Broader Organizational Initiatives and Provide Mentorship\|O6 - Org Initiatives and Mentorship]]` |
| O7 | `[[priorities#O7: Improve the security of the grid serving American compute\|O7 - Grid Security for Compute]]` |

Pass it through the CLI in **single** quotes — the value contains `[`, `|` and `#`, and
double quotes will let the shell mangle it:

```bash
obsidian property:set name="objective" \
  value='[[priorities#O5: Enhance Public Profile and Communication Skills|O5 - Public Profile and Communication Skills]]' \
  path="20-GTD/20-10-Projects/<NAME>.md"
```

The CLI quotes the YAML for you — the colon in the heading needs it. Verify the anchor
resolved rather than assuming; a wrong heading produces a link that looks fine and goes
nowhere:

```bash
obsidian eval code="const p='20-GTD/20-10-Projects/<NAME>.md'; JSON.stringify({unresolved:Object.keys(app.metadataCache.unresolvedLinks[p]||{})})"
```

An empty `unresolved` array means the heading matched. If `priorities.md` is ever
re-worded, these anchors break — fix the table here, then the affected project files.

**If Jordan asks for a bare `O#` instead, that is fine** — nothing in the vault parses this
field programmatically. No script, no `.base` view, no query reads it; the only consumers
are `weekly-review` and `gtd-coach`, which are instructions read by Claude. The link
format is for Jordan's benefit, not a machine contract.

Then write the `## Description` section: what the outcome is and why it matters. Leave
`## Reference / Notes` and `## Notes` empty — they accumulate over the project's life.

## Step 5 — The first next action (hard gate)

**A project without an unblocked next action is the single failure this system is built to catch.**
The weekly review gates on it and `gtd-coach` audits for it. Two projects silently lost all their
actions during the 16-week review gap ending 2026-08-28.

So: propose a first next action and create it with the `tasknotes` skill, with
`projects: ["[[<project name>]]"]`.

**Propose it — do not create it silently.** Same rule as `meeting-capture`: Jordan approves task
creation. If he declines, the project is left deliberately actionless and you must **say so
explicitly** in the report, because the next weekly review will flag it.

If the project is `someday-maybe-inactive`, skip this step — parked projects are not supposed to
have live actions.

## Step 6 — Verify and report

```bash
obsidian property:read name="objective" path="20-GTD/20-10-Projects/<NAME>.md"
```

Report the project path, the objective it maps to, and the next action created (or the fact that
none was). Link the file so Jordan can open it.

## Notes

- **Never delete or rename a project file.** Renaming breaks the `projects:` wikilink in every
  task pointing at it. To retire one, set `status: someday-maybe-inactive`.
- If a template field drifts from what real project files hold, fix
  `90-System/templates/project.md` rather than compensating here.
