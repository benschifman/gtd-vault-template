---
name: gtd-coach
description: Audit Jordan's GTD system for hygiene issues — projects without next actions, stale tasks, missing metadata, orphaned actions, naming inconsistencies. Use this skill whenever the user asks to audit the GTD system, run a system check, do a GTD review, or asks if their task/project lists are in good shape.
---

# GTD Coach Skill

Scan the GTD system and produce a prioritized report of hygiene issues with specific suggested fixes. Always ask for approval before making changes.

## Steps

1. **Audit projects** (`20-GTD/20-10-Projects/`):
   - **Stalled projects (most important check):** every project with `status: active` must have at least one *unblocked* next action — a task in `20-GTD/20-20-Next-Actions/` whose `projects` field links back to it and whose status is `open` or `in-progress`. Linked tasks that are `waiting` or `someday-maybe-inactive` don't count:
     ```bash
     grep -l "PROJECT FILE NAME" "20-GTD/20-20-Next-Actions/"*.md | xargs grep -l "status: \(open\|in-progress\)"
     ```
     Flag every active project where this comes back empty — these are stalled by definition.
   - **Objective linkage:** flag active projects with a missing or empty `objective:` field (values `O1`, `O2`, … map to the objectives in `20-GTD/20-05-Horizons/priorities.md`). Also list any objective in `priorities.md` with zero active projects pointing at it.
   - Flag projects missing required frontmatter: `priority`, `desired_outcome`, `objective`
   - Flag projects with `status: active` but no file modification in 2+ weeks

2. **Audit next actions** (`20-GTD/20-20-Next-Actions/`):
   - Flag tasks with `category: next-action` but missing a `contexts` property
   - Flag tasks with no `projects` link (orphaned actions) — also detectable via `obsidian orphans` for files with no incoming links
   - Flag tasks with `status: open` and a `due` date more than 2 weeks in the past
   - Flag any filenames not in lowercase-hyphenated format

3. **Audit waiting/delegated** (`20-GTD/20-40-Waiting/`):
   - Flag items with no follow-up date, or waiting >2 weeks without update

4. **Check horizons currency** — when was `20-GTD/20-05-Horizons/Jordan's Horizons of Focus at MPI.md` last modified? Flag if >4 weeks.

5. **Present findings** as a clear report grouped by category, with specific file names and suggested fixes for each issue.

6. **Offer to fix.** For each issue category, ask: "Want me to fix these?" Make fixes only with explicit approval.
