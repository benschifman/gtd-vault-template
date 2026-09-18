# Setup

## 1. Get the vault

```bash
git clone <this repo> my-vault
cd my-vault
```

Open the folder as a vault in Obsidian and turn on community plugins (Settings →
Community plugins). The plugin *settings* are in the repo; the plugin *code* is not.
Install each of these from **Browse** — the settings already in the folder are picked up
when the plugin loads:

| Plugin | Role |
|---|---|
| Tasknotes | Next actions as files; kanban, agenda, and calendar views in `90-System/bases/Views/` |
| Notebook Navigator | File navigation, calendar, folder templates, and the "New person / New project / …" commands |
| Omnisearch | Full-text search |
| PDF++ | Reading and annotating source PDFs |
| Image Converter | Compresses pasted images |
| Granola Meetings Simple Sync | Syncs Granola meeting notes into `00-Inbox/granola/` (optional) |

Two plugins keep credentials in their settings file once configured — Granola (OAuth
tokens) and Tasknotes (your private calendar ICS URL) — so those `data.json` files are
git-ignored. The repo ships scrubbed copies as `data.example.json`. **Before enabling the
plugins**, copy them into place so Tasknotes picks up the task schema this vault depends on:

```bash
cp .obsidian/plugins/tasknotes/data.example.json .obsidian/plugins/tasknotes/data.json
cp .obsidian/plugins/granola-meetings-simple-sync/data.example.json .obsidian/plugins/granola-meetings-simple-sync/data.json
```

The vault opens with the layout it was built with: Notebook Navigator in the left
sidebar, its calendar and the backlinks/outline panes on the right, `Dashboard.md` in the
main pane, and a trimmed ribbon. That layout is `.obsidian/workspace.json`, tracked once as
a seed. Obsidian rewrites the file constantly, so after your first open run
`git update-index --skip-worktree .obsidian/workspace.json` to keep it out of your diffs.

## 2. Tools

- **Claude Code** — `CLAUDE.md` at the vault root is its briefing. Skills load from
  `.claude/skills` (a symlink to `90-System/skills/`). Run
  `bash 90-System/scripts/check_skill_registry.sh` once to confirm every symlink resolves.
- **Obsidian CLI** — `obsidian` on your PATH, with Obsidian open. The skills use it for
  moves, property edits, and `eval`. `CLAUDE.md` lists the caveats.
- **Python 3.11+** with `pypdf`. The scripts in `90-System/scripts/` have no other
  dependencies. `marker_single` is an optional fallback for scanned PDFs.
- **MCP connectors** (optional, but `daily-start`, `daily-close`, and `email-triage` are
  built around them): Gmail, Google Calendar, Google Drive. Connect them in Claude Code;
  the skills call `search_threads`, `list_events`, and friends by name.
- **Granola** (optional) — sign in through the plugin's settings. `meeting-capture`
  expects notes to land in `00-Inbox/granola/` in the `granola-sync.md` template format.

## 3. Make it yours

Everything below is fictional placeholder content. Replace it in this order — each step
is what `CLAUDE.md` or a skill reads to understand who it is working for.

1. **`CLAUDE.md`** — the Overview paragraph (name, role, employer) and the Gmail address
   under "Google Workspace Access". Delete the "Template note" callout when you're done.
2. **`20-GTD/20-05-Horizons/`** — `About Jordan.md` (rename it), `priorities.md`
   (your objectives; keep the `## O1: …` heading form because projects link to those
   headings), and the Horizons file.
3. **`20-GTD/20-30-Contexts/`** — rename `@agenda-Sam` to your manager, add
   `@agenda-<person>` files for anyone you meet regularly.
4. **Gmail labels** — `email-triage` maps threads onto labels named `1-Next-Action`,
   `2-Project/*`, `3-Delgated-Waiting`, `4-Scheduled`, `5-Someday-Maybe`, `6-Reference`,
   `7-Agendas/*`. Create them, then replace every `Label_<YOUR_LABEL_ID>` in
   `20-GTD/20-90-System/email-triage/SKILL.md` and `daily-start/SKILL.md` with the ids
   Gmail's API reports (`list_labels`).
5. **`90-System/reference/drafting-guides/`** — the writing skills expect
   `writing style.md`, `Editorial Pass.md`, and `email style.md` here. The template
   ships the folder empty; the skills describe what each file should contain.
6. **Delete the sample data**: everything in `30-CRM/30-10-People/`,
   `30-CRM/30-20-Organizations/`, `40-PKM/40-20-Sources/`, `40-PKM/40-30-Topics/`,
   `40-PKM/40-10-Notes/`, `20-GTD/20-10-Projects/`, `20-GTD/20-20-Next-Actions/`,
   `20-GTD/20-50-Someday-Maybe/`, `10-Journal/`, and `00-Inbox/`. Then rebuild the
   catalog: `python3 90-System/scripts/score_pkm.py --build-only`.
7. **Backups** — create a private GitHub repo and point `origin` at it. `daily-close`,
   `weekly-review`, and `.claude/hooks/auto-commit.sh` push to `origin main`. Keep the
   vault inside a synced folder (Drive, iCloud, Dropbox) for the binaries git ignores.
   Read the Backups section of `CLAUDE.md` before relying on any of it.

## 4. First run

```bash
bash 90-System/scripts/check_skill_registry.sh
python3 90-System/scripts/crm_lint.py
python3 90-System/scripts/score_pkm.py --build-only
```

Then, in Claude Code inside the vault: `/daily-start`. If it finds your calendar and
writes today's note into `10-Journal/YYYY/MM/`, the wiring is right.
