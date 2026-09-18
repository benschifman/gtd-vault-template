---
name: inbox-process
description: Process items in Jordan's inbox (00-Inbox/) using an interactive step-by-step GTD coaching workflow. Use this skill whenever the user asks to process the inbox, clear the inbox, work through inbox items, or do a GTD capture/process session.
---

# Inbox Process Skill

Guide Jordan through clearing `00-Inbox/` one item at a time using strict GTD methodology. Process items **one at a time**, asking one question per turn and always waiting for a response before proceeding.

Start by listing inbox items:
```bash
obsidian files folder="00-Inbox"
```

## Workflow (per item)

### Step 1: Actionable or Not?
Review the item and determine if it is actionable. If unclear, describe the item and ask: "Is this actionable?"

### Step 2: Not Actionable
If not actionable, explain the three options and suggest one:
1. **Trash** — no longer needed, delete it
2. **Someday/Maybe** — no action now, but might act on it later
3. **Reference** — useful information to keep

Then act on their choice:
- *Trash* → delete the file
- *Someday/Maybe* → `obsidian move file="filename" to="20-GTD/20-50-Someday-Maybe/"`
- *Reference* → move to the appropriate PKM folder using `obsidian move`:
  - Own writing/analysis → `obsidian move file="filename" to="40-PKM/40-10-Notes/"`
  - External sources/articles → `obsidian move file="filename" to="40-PKM/40-20-Sources/"`
  - Topic overview → `obsidian move file="filename" to="40-PKM/40-30-Topics/"`

### Step 3: Actionable — Which Kind?
If actionable, explain the three options:
1. **Do it now** — takes less than 2 minutes → do it immediately
2. **Delegate** — not the right person → hand off and create a waiting item in `20-GTD/20-40-Waiting/`
3. **Defer** — takes >2 minutes, right person → track it

### Step 4: Defer — Project or Next Action?
If deferring, help determine scope:
- **Next action**: single step to accomplish the goal
- **Project**: requires more than one step → needs a project file + at least one next action

### Step 5: Create a Project (if needed)
Help name the project as a completed outcome using active verbs and specific nouns (e.g., "Judgment Fund piece is final and emailed"). Create a project file in `20-GTD/20-10-Projects/` using the standard template.

### Step 6: Create a Next Action
Ask for priority and context, then create a Tasknotes file in `20-GTD/20-20-Next-Actions/`:

```yaml
category: next-action
status: open
title: Human-readable action text
projects:
  - "[[project-file-name]]"
contexts:
  - "[[@computer]]"
due: 'YYYY-MM-DD'
created: 'YYYY-MM-DD'
```

### Step 7: Loop
After processing each item, ask: "Ready for the next item?" Repeat from Step 1. When done, congratulate Jordan on clearing the inbox.
