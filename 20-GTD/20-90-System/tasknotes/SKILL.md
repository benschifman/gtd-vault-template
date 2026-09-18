---
name: tasknotes
description: Create, update, and manage GTD next-action tasks using the Tasknotes plugin in this Obsidian vault. Use this skill whenever the user asks to add a next action, create a task, update task status, mark something done, link a task to a project, or work with any files in 20-GTD/20-20-Next-Actions/. Also use when the user mentions contexts ([[@computer]], [[@email]], etc.), task priority, or scheduling work items. This skill should trigger even if the user doesn't say "Tasknotes" — phrases like "add that to my task list", "create a next action for", or "mark that as done" are all good triggers.
---

# Tasknotes Skill

Tasknotes (**v4.12.5**, checked 2026-08-31) manages GTD next actions as individual markdown files
identified by a frontmatter property. Views (kanban, agenda, calendar) are handled by the plugin's
native UI — don't create custom base files for tasks.

**Official docs: <https://tasknotes.dev/>** — the reference for anything this skill doesn't cover:
recurrence rules, dependencies and blocking, time tracking, pomodoro, field mapping, natural-language
task parsing, Bases integration, and the HTTP/MCP API. Consult it rather than guessing at plugin
behaviour, and re-check the version above before trusting anything version-specific here.

## Task File Location

All task files live in: `20-GTD/20-20-Next-Actions/`
Project folder: `20-GTD/20-10-Projects/`
Contexts folder: `20-GTD/20-30-Contexts/`
Archive folder: `20-GTD/20-60-Archive/`
Plugin views: `90-System/bases/Views/`

## Frontmatter Schema

```yaml
---
category: next-action        # REQUIRED — identifies the file as a task
status: open                 # open | in-progress | done | none
title: Human-readable action # REQUIRED — what the task actually says
priority: normal             # none | low | normal | high
projects:                    # wikilinks to project files
  - "[[project-file-name]]"
contexts:                    # @ context tags 
  - "[[@computer]]"
due: '2026-04-01'            # YYYY-MM-DD
scheduled: '2026-03-30'      # YYYY-MM-DD — when you plan to work on it
timeEstimate: 30             # minutes
created: '2026-03-29'        # YYYY-MM-DD
---
```

**Only include fields that are known or relevant** — `projects`, `contexts`, `due`, `scheduled`, `priority`, and `timeEstimate` are all optional.

## Key Conventions

- **Task identification**: `category: next-action` — this is what Tasknotes looks for (not `type`)
- **Contexts**: always `contexts` (plural), never `context`
- **Projects**: always an array of wikilinks — `["[[project-name]]"]` or YAML list format
- **Filename**: lowercase-hyphenated, derived from the action title (e.g., `call-senator-smith.md`)
- **No inline tasks in project files** — tasks live only in `20-GTD/20-20-Next-Actions/`

## Status Values

| Value | Meaning |
|-------|---------|
| `open` | Not started (default) |
| `in-progress` | Actively being worked |
| `done` | Completed |
| `waiting` | Blocked on someone/something else |
| `someday-maybe-inactive` | Deferred indefinitely — GTD someday/maybe list |
| `none` | No status assigned |

**Someday/maybe**: Tasks with `status: someday-maybe-inactive` live in `20-GTD/20-20-Next-Actions/` alongside active tasks. During weekly review, query for this status to surface the someday/maybe list.

## Priority Values

| Value | Meaning |
|-------|---------|
| `normal` | Default |
| `high` | Urgent/important |
| `low` | Can wait |
| `none` | Unset |

## Context Files

Context files live in `20-GTD/20-30-Contexts/`. Current contexts:
- `@computer` — requires computer
- `@deep-work` — requires focus block
- `@email` — email-based action
- `@agenda-Infra` — bring up at Infra team meeting

## Common Operations

### Create a new task

Write a new `.md` file in `20-GTD/20-20-Next-Actions/` with the required frontmatter. Always include `category`, `status`, `title`, and `created`. Add optional fields as known.

```yaml
---
category: next-action
status: open
title: Draft intro section of NHPA piece
projects:
  - "[[nhpa-articles]]"
contexts:
  - "@computer"
  - "@deep-work"
due: '2026-04-03'
priority: high
created: '2026-03-29'
---
```

### Mark a task done

Use `obsidian property:set` to update individual properties without rewriting the whole file:
```bash
obsidian property:set name="status" value="done" path="20-GTD/20-20-Next-Actions/task-name.md"
obsidian property:set name="completedDate" value="2026-03-29" path="20-GTD/20-20-Next-Actions/task-name.md"
```

### Update a task's due date or scheduled date

```bash
obsidian property:set name="due" value="2026-04-10" path="20-GTD/20-20-Next-Actions/task-name.md"
obsidian property:set name="scheduled" value="2026-04-07" path="20-GTD/20-20-Next-Actions/task-name.md"
```

### Update a task's project or context

Edit the `projects` or `contexts` arrays in the frontmatter directly using the Edit tool. Both are YAML lists (multi-value properties aren't supported by `property:set`).

### Link a task to multiple projects

```yaml
projects:
  - "[[nhpa-articles]]"
  - "[[national-priority-permitting-system]]"
```

### Archive a task

Move the file to `20-GTD/20-60-Archive/`. (Tasknotes can also auto-archive via its UI.)

## What Not to Do

- Don't use `type` instead of `category` — Tasknotes won't recognize the task
- Don't use `context` (singular) — use `contexts`
- Don't embed task views in project files — use Tasknotes' native kanban/agenda views
- Don't put task files anywhere other than `20-GTD/20-20-Next-Actions/`
- Don't add the `archived` tag manually — let Tasknotes handle archiving

## The HTTP API and MCP server — deliberately off

Tasknotes ships an HTTP API (and an MCP server riding on it) exposing ~25 typed tools. Both are
**disabled on purpose**. Evaluated 2026-08-31; see <https://tasknotes.dev/obsidian/HTTP_API/>.

**Do not turn them on to do ordinary task work.** Reading task files directly and writing
frontmatter is the supported path here, and it is the only one that works with Obsidian closed.
The API's real use is *external* automation — a phone shortcut, a cron job, another tool writing
into the vault. Jordan turns it on if and when he wants that.

Two findings worth keeping, so nobody re-derives them:

- **The in-process API silently ignores filters it doesn't understand.** `app.plugins.plugins
  .tasknotes.api.queryTasks(...)` returns *every* task — not an error — when the query shape is
  wrong, and two plausible shapes were both wrong. A filter that quietly returns everything (or
  nothing) would corrupt a `daily-start` plan invisibly. **Never filter tasks through
  `obsidian eval`.** Read the files and filter yourself.
- **The MCP query shape**, if the API is ever enabled, is
  `{conjunction:'and', children:[{type:'condition', id:'c1', property:'status', operator:'is', value:'open'}]}`
  — results come back grouped under an `all` key. This shape is **not** accepted by the
  in-process `queryTasks`; the MCP layer translates it first.

If the API is enabled, **set an auth token**. It is empty by default, and `tasknotes_delete_task`
permanently deletes task files — an unauthenticated local port that any process, including a web
page in the browser, can reach. That is flatly against the never-delete rule in CLAUDE.md.
