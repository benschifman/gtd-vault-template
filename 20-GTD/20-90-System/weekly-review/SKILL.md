---
name: weekly-review
description: Conduct Jordan's GTD weekly review — collect, process, review all projects and lists, check calendar, plan next week, and create the weekly note. Use this skill whenever the user asks to do a weekly review, run weekly-review, or review the week.
---
# Weekly Review Skill

Walk through the GTD weekly review interactively. Create or open the weekly note and populate it as you go.

## Steps

1. **Open or create the weekly note** at `10-Journal/YYYY/MM/W##.md` (e.g. `10-Journal/2026/04/W01.md`, where W## is the week-of-month number padded to 2 digits). Create it from `90-System/templates/weekly-review.md` with `new_from_template.py` — see "Creating the note" at the end of this file. W## is `ceil(day_of_month / 7)`, zero-padded.

2. **Collect** — Check `00-Inbox/` for unprocessed items. Also ask: "Anything in Gmail or Slack that needs to be captured before we process?" Wait for a response and file anything identified into `00-Inbox/` before proceeding.

3. **Process** — Check what's in `00-Inbox/` before deciding how to process:
   - If the inbox contains **only source notes** (articles, PDFs, research docs), run the PKM Librarian agent directly to process them all at once — it's faster and more thorough than inbox-process for sources.
   - If the inbox contains **actionable items** (tasks, decisions, misc captures), invoke the `inbox-process` workflow.
   - If it contains a mix, run PKM Librarian on the sources first, then `inbox-process` on the remainder.
   - This step is mandatory — do not offer to skip it, even if the inbox appears empty.

   Then run the PKM health check (even if the inbox was empty — this catches drift from the whole week):
   ```bash
   python3 90-System/scripts/score_pkm.py --json --build
   ```
   This also rebuilds `40-PKM/catalog.jsonl`. Report the summary line in the weekly note. If it shows uncovered sources, missing hubs, or broken links, flag them to Jordan — fixing is optional and can be deferred to a full pkm-lint run, but the numbers should be recorded so drift is visible week over week.

4. **Review past week's calendar.**

   **Calendar source is the Google Calendar MCP connector** (`list_events` on the primary
   calendar), adopted 2026-09-13. It is the live calendar: RSVP status is per-attendee,
   recurrence is expanded server-side, and your own entry carries `"self": true`. Never use
   `gws`, and do not fall back to the Tasknotes ICS cache for planning -- that cache hides any
   event where a **guest** declined and mis-dates moved recurring instances (Tasknotes 4.12.5,
   reported upstream 2026-09-10; see the note at the end of this step).

   ```
   list_events(startTime: "YYYY-MM-DDT00:00:00-04:00", endTime: "YYYY-MM-DDT23:59:59-04:00",
               timeZone: "America/New_York", orderBy: "startTime")
   ```

   Use `-05:00` offsets in EST (Nov-Mar). Times come back already in ET -- no conversion.

   **The response is verbose and cannot be trimmed** -- there is no field mask, and every
   attendee is an object. A normal day is ~2-3K tokens; a 40-person convening alone is ~1K.
   Accepted cost. Do not call it more than once per day per skill run; reuse the result.

   Reading each event:
   - **Skip it** if `status` is `cancelled`, or if your own attendee entry
     (`"self": true`) has `responseStatus: "declined"`.
   - **Flag it as unanswered** if your entry is `needsAction` -- an unanswered invite is a
     decision, not a commitment.
   - Video link: `conferenceUrl` first, then `location`, then scan `description` for
     `zoom.us` / `meet.google`.
   - Recurring instances carry `recurringEventId` and `originalStartTime`; a moved instance
     shows the new time in `start` and the old one in `originalStartTime`.
   - `attendees[].email` is the hook for CRM linking -- match against the `emails` array on
     person files in `30-CRM/30-10-People/`.

   Call it once for the whole week -- Monday of the past week to today -- and **keep the
   result**; Step 12b reuses the attendee emails.

   List each event with ET time and title, linking any attendee who has a person file.
   Identify any meetings not logged in `10-Journal/10-10-Events/`. Flag for capture. **Stop and
   wait for Jordan to respond** before moving on -- he may want to log notes or capture actions.

5. **Review next 2 weeks' calendar.**
   Same call with `startTime` = tomorrow and `endTime` = 14 days out. Flag upcoming deadlines,
   meetings needing prep, unanswered invitations (`needsAction`), and scheduling conflicts.
   Suggest next actions for anything requiring preparation. **Stop and wait for Jordan to
   respond** before moving on.

6. **Review projects** (`20-GTD/20-10-Projects/`).
   For each project with `status: active`, verify it has at least one **unblocked** next action — a task in `20-GTD/20-20-Next-Actions/` with a `projects` wikilink back to it AND `status: open` or `status: in-progress`. A linked task that is `waiting` or `someday-maybe-inactive` does not count.
   ```bash
   grep -l "PROJECT FILE NAME" "20-GTD/20-20-Next-Actions/"*.md | xargs grep -l "status: \(open\|in-progress\)"
   ```
   **This is a hard gate — do not proceed past this step while any active project lacks an unblocked next action.** For each violation, Jordan must either:
   - (a) name the very next physical action, which you create immediately (tasknotes conventions, with the `projects` link), or
   - (b) demote the project to `status: waiting` or `status: someday-maybe-inactive`, adding a one-line reason to its Notes section.

7. **Review waiting/delegated** — Query for tasks with `status: waiting` in `20-GTD/20-20-Next-Actions/`:
   ```bash
   grep -rl "status: waiting" "20-GTD/20-20-Next-Actions/"
   ```
   Also check for projects with `status: waiting` in `20-GTD/20-10-Projects/`. Flag items waiting >1 week without an update. Suggest follow-up actions.

8. **Review someday/maybe** — Query for tasks with `status: someday-maybe-inactive` in `20-GTD/20-20-Next-Actions/`:
   ```bash
   grep -rl "status: someday-maybe-inactive" "20-GTD/20-20-Next-Actions/"
   ```
   Also check `20-GTD/20-50-Someday-Maybe/` and projects with `status: someday-maybe-inactive` in `20-GTD/20-10-Projects/`.
   Present the list and ask: "Anything here to activate, remove, or keep as-is?"

9. **Objective scorecard** — Read `20-GTD/20-05-Horizons/priorities.md`. Build a table mapping each objective (O1, O2, …) to the active projects whose `objective:` frontmatter field points at it. Include the table in the weekly note. Then:
   - For any active project with a missing or empty `objective:`, ask Jordan which objective it serves and set it:
     ```bash
     obsidian property:set name="objective" value="O#" path="20-GTD/20-10-Projects/PROJECT.md"
     ```
     If a project genuinely serves no current objective, don't force a fit — flag it as a signal that either the project or the objectives list needs rethinking.
   - Present any objective with zero active projects and ask whether that's intentional.
   - If the portfolio and the objectives have clearly diverged, ask whether `priorities.md` needs a refresh, and update it together if so (updating the `modified` date).

10. **Review horizons** — Read `20-GTD/20-05-Horizons/Jordan's Horizons of Focus at MPI.md`. Summarize the key purpose, vision, 1–2 year goals, and areas of focus in plain language — do not assume Jordan has them top of mind. Then cross-reference against the week's tasks, calendar events, and active projects to identify any goal or area that is **underrepresented**. Surface the single most notable gap and ask if it warrants a next action. Then ask: "Have your priorities or goals shifted since this was last updated?"

11. **Goals for next week** — Ask: "What are your top 3 goals for next week?" Add to the weekly note.

12. **Health-check the CRM.** Meetings during the week add contacts and change jobs; nothing notices unless this runs.

    ```bash
    python3 90-System/scripts/crm_lint.py --limit 20
    python3 90-System/scripts/crm_unresolved_attendees.py
    ```

    Fix the integrity findings immediately — `broken_frontmatter` makes a file invisible to every Bases query, and `people_missing_emails_field` silently breaks Granola attendee linking. Apply the one safe auto-fix:

    ```bash
    python3 90-System/scripts/crm_lint.py --fix-dates --write
    ```

    For anything needing judgment — contradictions, job changes, gaps — invoke the `crm-lint` skill, which owns the full checklist. Offer to run the `crm-librarian` agent on whatever batch comes out of it.

12b. **Advance `last_contact` from the week's calendar and sent mail.** `--fix-dates` above
    only sees curated meeting notes. Two kinds of contact never become notes -- calendar
    events that were not worth a note, and email Jordan sent -- so they are collected here and
    fed to a companion script.

    **Calendar:** from the Step 4 result, take every attendee `email` on events where Jordan's
    own entry (`"self": true`) is `accepted` or `tentative`, paired with the event date.

    **Sent mail:** metadata only -- never bodies:
    ```
    search_threads(query: "in:sent newer_than:7d", view: "THREAD_VIEW_METADATA_ONLY", pageSize: 50)
    ```
    Take only messages whose `sender` is `jordan@meridianpolicy.org`; each `toRecipients` and
    `ccRecipients` address gets that message's date. Mail Jordan *received* is not contact he
    initiated and does not count.

    Write both as one JSON array to the scratchpad and run the script, dry-run first:
    ```bash
    python3 90-System/scripts/crm_touch.py "$SCRATCH/touchpoints.json"
    python3 90-System/scripts/crm_touch.py "$SCRATCH/touchpoints.json" --write
    ```
    `last_contact` only moves forward, files without the key are reported not modified, and
    system addresses (Luma, Drive shares, group calendars, no-reply) are filtered. Show Jordan the
    dry run; apply on his nod.

    **Read the "no CRM file" list at the bottom.** Those are the addresses Jordan actually met or
    wrote to this week that have no person file -- a far better enrichment queue than any lint
    finding, because it is ranked by real contact. Offer the top 5-10 to the `crm-librarian`
    agent alongside whatever `crm-lint` produced.

13. **Run the zip snapshot.** This is a step of the review, not a scheduled job.
    The launchd agent was retired on 2026-08-28: it fired every Sunday but always
    failed with `Operation not permitted`, because launchd's `bash` has no
    Files-and-Folders access to the vault inside Google Drive CloudStorage. Nothing
    prompts for that permission on a headless run, so it failed silently for two
    weeks and the newest snapshot was 13 days stale before anyone noticed. Running
    it here works, because this session's shell already has Drive access.

    ```bash
    bash 90-System/scripts/vault_snapshot.sh
    ```

    It takes a minute or two and prints the path and size of the zip it wrote.
    Then confirm GitHub is current:

    ```bash
    git log origin/main..HEAD --oneline | wc -l
    ```

    Any unpushed commits go up as part of step 14; say so when they do.

    **If the snapshot command fails**, say so plainly and do not report the review
    as complete — the zips are the only layer holding the attachments and images
    that `.gitignore` keeps out of GitHub. See the Backups section of `CLAUDE.md`.


14. **Finalize and save** the weekly note. Commit and push using the ISO week
    number from the note's `week:` frontmatter field (e.g., `2026-W18`), not the
    week-of-month filename:
    ```bash
    git add -A && git commit -m "weekly review: YYYY-W##" && git push origin main
    ```
    If the push fails, say so rather than reporting the review as complete.


## Creating the note

`90-System/templates/weekly-review.md` is the source of truth. Render it with the shared script,
which resolves the template's `{{date:...}}` placeholders and refuses to overwrite an existing
file. Obsidian does not need to be open.

Compute the path first — W## is the week-of-month, `ceil(day / 7)` zero-padded to 2 digits — then:

```bash
python3 90-System/scripts/new_from_template.py weekly-review 10-Journal/YYYY/MM/W## --date YYYY-MM-DD
```

Pass `--date` as the date the review is for, so the `created`/`week`/`date` fields are right when
a review is run late. The script prints the path it wrote; confirm it before populating the note.

Do not create weekly notes from Notebook Navigator's calendar: it names weeks by ISO week number
(`W38`), not week-of-month, and would not match the existing files.
