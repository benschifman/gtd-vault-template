# GTD vault template

An Obsidian vault, run by Claude Code, for a policy researcher: a GTD task system, a
contact database, a personal knowledge base, and a set of skills that keep them all
current — daily start and close, weekly review, email triage, meeting capture, CRM
and knowledge-base librarians.

Everything structural here is real and in daily use. Everything *in* it is fictional:
Jordan Lee, the Meridian Policy Institute, every contact, source, project, and note.
Swap them for your own (see [SETUP.md](SETUP.md)) and the system works as documented.

## The idea

Obsidian holds the files. Claude Code, working from `CLAUDE.md` and the skills in
`90-System/skills/`, does the upkeep that people never actually do by hand: filing
inbox items, keeping contacts current from meeting notes, turning sources into topic
pages, checking that every project has a next action, backing up. The human's job is
to capture, decide, and write.

```
you  ──capture──▶  00-Inbox  ──inbox-process──▶  20-GTD (projects, next actions)
                                              ▶  30-CRM (people, organizations)
                                              ▶  40-PKM (sources → topics)
Granola ──sync──▶  00-Inbox/granola ──meeting-capture──▶ 10-Journal/10-10-Events
Gmail  ──email-triage──▶  labels + next actions
                   daily-start / daily-close  ──▶  10-Journal/YYYY/MM/YYYY-MM-DD
                   weekly-review              ──▶  10-Journal/YYYY/MM/W##  + backup
```

## Folder map

| Folder | What lives there | Maintained by |
|---|---|---|
| `00-Inbox/` | Everything captured and not yet decided. `granola/` is where meeting notes sync in. | `inbox-process`, `meeting-capture` |
| `10-Journal/` | Daily notes (`YYYY/MM/YYYY-MM-DD.md`), weekly reviews (`YYYY/MM/W##.md`), curated meeting notes (`10-10-Events/`) | `daily-start`, `daily-close`, `weekly-review`, `meeting-capture` |
| `20-GTD/` | Horizons and `priorities.md`, projects, next actions (Tasknotes), contexts, waiting, someday/maybe, archive | `project-create`, `tasknotes`, `gtd-coach` |
| `30-CRM/` | One file per person and per organization, plus `log.md` | `crm-update`, `crm-lint`, the CRM Librarian agent |
| `40-PKM/` | Sources, topic pages, your own notes, `catalog.jsonl`, `log.md` | `source-processing`, `topic-writing`, `pkm-lint`, the PKM Librarian agent |
| `50-Work/` | Drafts: articles, legislation, short-form | `article-drafting`, `legislation-drafting`, `tweet-review`, `doc-coauthoring` |
| `90-System/` | Templates, Bases views, scripts, the skill and agent registries, reference material | you |

Each domain keeps its own skills in an `NN-90-System/` subfolder (for example
`30-CRM/30-90-System/crm-update/`). `90-System/skills/` and `90-System/agents/` are
symlink registries pointing at those folders — Claude Code discovers skills there via
`.claude/skills` and `.claude/agents`. `CLAUDE.md` explains the convention.

## How a day runs

1. **`daily-start`** — sweeps Gmail for anything that changes the day, pulls the
   calendar, proposes three priorities and a time-blocked plan, and writes today's note.
2. Work. Capture anything new into `00-Inbox/` or straight into a Tasknote.
3. **`daily-close`** — records what happened, reconciles the Gmail inbox against its
   GTD labels, carries forward what slipped, commits and pushes the vault.

Weekly, **`weekly-review`** walks the full GTD review: inbox to zero, every project
checked for an unblocked next action, objectives scorecard, calendar look-ahead,
CRM and PKM health checks, zip snapshot, commit.

## Conventions that matter

- **Tasks are files.** Each next action is a markdown file in `20-GTD/20-20-Next-Actions/`
  with `category: next-action` frontmatter, managed by the
  [Tasknotes](https://github.com/callumalpass/tasknotes) plugin. Done tasks auto-archive.
- **Projects link to objectives.** `objective:` in a project's frontmatter is a wikilink
  to a heading in `20-GTD/20-05-Horizons/priorities.md`. The weekly review scores
  objectives by their projects; `gtd-coach` flags projects that link nowhere.
- **Templates are the source of truth.** `90-System/templates/` uses Notebook
  Navigator's `{{date:…}}` / `{{title}}` placeholders. In Obsidian, folder templates and
  the "New person / New project / …" commands apply them; from the command line,
  `python3 90-System/scripts/new_from_template.py <template> <path>` renders the same file.
- **Meeting notes feed the CRM.** Attendees are wikilinks to person files; a person
  file's `## Meetings` section is a live Bases query of every meeting they appear in.
- **Sources become topics.** A source file's `topics:` list names topic pages; the PKM
  Librarian creates missing ones and keeps `catalog.jsonl` — a one-line-per-file index
  you can grep with Obsidian closed.
- **Git tracks text, your file sync holds binaries.** PDFs and images are git-ignored.
  Plugin files that hold OAuth tokens or private calendar URLs are git-ignored too.

## What's in the sample data

Enough to see every part working: five people across four organizations, three
projects mapped to objectives, six next actions in five contexts, two sources feeding
three topic pages, one meeting note, one daily note, one weekly review, one inbox item.
Open `Dashboard.md` first.

## Requirements

Obsidian with the plugins listed in `.obsidian/community-plugins.json`; Claude Code;
Python 3.11+ (`pypdf` for PDF extraction); the `obsidian` CLI; optionally the Gmail,
Google Calendar, and Drive MCP connectors and a Granola account. [SETUP.md](SETUP.md)
walks through it.
