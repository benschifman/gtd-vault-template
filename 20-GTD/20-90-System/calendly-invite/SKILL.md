---
name: calendly-invite
description: Create a one-off Calendly meeting for a specific date and time window, then hand Jordan a Gmail-ready block of clickable time-slot buttons to paste into an email. Use this whenever Jordan wants to offer someone times to book — "make a Calendly for X", "send them some times", "set up a 30 min next Tuesday morning", "give me the buttons to paste" — or when a reply he is drafting needs scheduling options.
---

# Calendly Invite Skill

Produces two things: a booking link scoped to the window Jordan names, and an HTML block of
per-slot buttons he can paste into Gmail. Jordan sends the email; this skill never does.

Reverse-engineered 2026-09-10 from a working invite Jordan sent to Dana Whitfield.
The URL format in Step 4 is copied from that message — do not improvise it.

## Step 0 — What Jordan has to decide

Ask as one block if any is missing. Do not guess a date.

| Field | Notes |
|---|---|
| Duration | 30 min unless he says otherwise |
| Date | A specific date. "Next week" is not a date. |
| Window | Start and end in ET, e.g. 9:00–11:00 |
| Who | Only matters for the covering email, not the link |
| Name | Shows as the heading in the pasted block, e.g. "AI & Antitrust Meeting" |

## Step 1 — Resolve the account

```
users-get_current_user
```

Keep `resource.uri` and `timezone`. Jordan is `America/New_York`.

## Step 2 — Pick the base event type

```
event_types-list_event_types  (user=<uri>, active=true)
```

Use a **one-on-one** type — `kind: "solo"` with `pooling_type: null`. `shares-create_share`
rejects group and collective types. Jordan's usual base is **30 Minute Meeting (virtual)**,
Zoom, `https://api.calendly.com/event_types/8eb1955d-9203-4235-b272-dad01c57dab2`. Re-list
rather than trusting that URI — it can change.

## Step 3 — Create the share link

```
shares-create_share
  event_type: <uri>
  name: "<meeting name>"           # max 55 chars, shows in the email block
  duration: 30
  period_type: "fixed"
  start_date: "YYYY-MM-DD"
  end_date:   "YYYY-MM-DD"         # same day for a one-off
  availability_rule:
    timezone: "America/New_York"
    rules:
      - type: "date"
        date: "YYYY-MM-DD"
        intervals: [{ from: "09:00", to: "11:00" }]
```

Keep `resource.scheduling_links[0].booking_url` — e.g. `https://calendly.com/d/<EVENT-ID>/<event-slug>`.
Everything in Step 4 is built from it.

> [!important] The override beats Jordan's working hours
> Jordan's standing availability ("Working hours") is **10:00–16:00, Mon–Fri**. A date-specific
> `availability_rule` on the share **replaces** it, so a 9:00 window really does produce 9:00
> and 9:30 slots. Confirmed 2026-09-10 — a sent invite offered 9:00am and Becca could book it.
> Do not tell Jordan the early slots are unavailable.

## Step 4 — Build the slot URLs

One button per slot, stepping by the duration across the window.

```
<booking_url>/<slug>/<YYYYMMDD>T<HHMM>Z?source=email&timezone=America%2FNew_York
```

> [!warning] The `<slug>` segment is mandatory and the API does not give it to you
> `shares-create_share` returns a bare `booking_url` — `https://calendly.com/d/<EVENT-ID>`,
> no slug. Appending the timestamp straight onto that produces a link that **silently opens the
> day view instead of the chosen time**. It returns HTTP 200 and looks fine; only clicking it
> reveals the problem. Verified broken 2026-09-10.
>
> Derive the slug by kebab-casing the `name` you passed in Step 3 — lowercase, spaces to
> hyphens. `"Meeting with Jordan Lee"` -> `meeting-with-jordan-lee`, confirmed working.
> **So keep Step 3 names to plain letters, digits and spaces** — punctuation makes the
> kebab-cased guess unreliable, and there is no API call to read the real slug back.

The timestamp is **UTC**. Both compact (`20260914T1400Z`) and extended
(`2026-09-14T14:00:00Z`) formats work — Jordan confirmed both, so this is not the thing to worry
about. Calendly's own emails use compact, so prefer it for consistency. EDT is UTC−4, EST is
UTC−5, so 9:00am ET in September is `20260914T1300Z`.

```
9:00am  -> https://calendly.com/d/<EVENT-ID>/meeting-with-jordan-lee/20260914T1300Z?source=email&timezone=America%2FNew_York
9:30am  -> https://calendly.com/d/<EVENT-ID>/meeting-with-jordan-lee/20260914T1330Z?source=email&timezone=America%2FNew_York
10:00am -> https://calendly.com/d/<EVENT-ID>/meeting-with-jordan-lee/20260914T1400Z?source=email&timezone=America%2FNew_York
```

The "Change" link beside the timezone line is the bare booking URL — **no slug, no timestamp** —
plus `?source=email&timezone=America%2FNew_York&timezone_picker=true`.

**Ask Jordan to click one button before he sends.** A wrong slug degrades to the day view rather
than erroring, so nothing upstream will catch it. This is the single failure mode of this skill.

## Step 5 — Write the HTML

Gmail strips `<style>` blocks and class selectors, so everything is inline and table-based.
Write to the scratchpad, then send it with `SendUserFile`.

```html
<div style="font-family:'Proxima Nova',-apple-system,BlinkMacSystemFont,Helvetica,Arial,sans-serif;color:#1a1a1a;">
  <div style="font-weight:bold;font-size:16px;line-height:19px;margin-top:15px;">MEETING NAME</div>
  <div style="font-size:14px;line-height:17px;color:#333;">30 mins</div>
  <div style="font-size:14px;line-height:17px;color:#333;">Time zone: Eastern Time - US &amp; Canada
    <a href="BOOKING_URL?source=email&amp;timezone=America%2FNew_York&amp;timezone_picker=true"
       style="margin-left:3px;">Change</a></div>

  <div style="font-size:14px;line-height:16px;font-weight:bold;margin-top:16px;">Friday, September 11</div>

  <table cellpadding="0" cellspacing="0" border="0" style="border-spacing:0 4px;margin-top:8px;">
    <tr>
      <!-- repeat this cell per slot; SLOT_URL = booking_url/slug/timestamp -->
      <td style="width:64px;height:22px;border:1px solid #0069ff;border-radius:3px;text-align:center;">
        <a href="SLOT_URL"
           style="text-decoration:none;color:#0069ff;font-size:12px;line-height:16px;display:block;padding:3px 0;">9:00am</a>
      </td>
      <td style="width:8px;"></td>
    </tr>
  </table>
</div>
```

Keep the real Calendly look: 1px `#0069ff` border, 3px radius, blue text, no fill.

## Step 6 — Hand it over

`SendUserFile` the HTML with `display: "render"`, and tell Jordan: **open it in a browser,
Select All, Copy, paste into Gmail.** Pasting rendered HTML preserves the links and styling;
pasting source does not.

Also give him the plain-text fallback — times with bare URLs — for anyone whose client
strips HTML.

## Constraints — read before promising anything

- **One-off meetings Jordan creates in the Calendly UI are invisible to the API.** They are not
  event types and do not come back from `event_types-list_event_types`, so their slots cannot be
  enumerated. If he already made one himself, tell him to use Calendly's own **"Copy times"**
  button — one click, always correct. This skill only works end-to-end when *it* creates the link.
- **`event_types-list_event_type_available_times` does not see share overrides.** It reports the
  base event type's availability, which is bounded by working hours. Use it to spot real calendar
  conflicts, never to decide which slots the share offers.
- **The booking page will not load in the in-app browser** — it redirects to the Calendly root,
  apparently bot protection. Do not try to verify slots by rendering the page.
- **A share link is single-use by default.** The first person to book consumes it. On a thread
  with several recipients, say so.
- **One-on-one event types have one host.** Colleagues are not on the invite; whoever books can
  add guests, or Jordan adds them to the calendar event afterward. Flag this whenever he mentions
  a colleague joining.
- **Never send the email.** Produce the draft and the HTML; Jordan sends. See the email rules in
  `email-triage`.

## Checking for conflicts -- do this BEFORE creating the share

Use the Google Calendar MCP connector, which is authoritative -- not the Tasknotes ICS cache,
which hides events a guest declined (that is exactly how a 4-hour convening was invisible when
a Monday-morning link was generated on 2026-09-10).

```
list_events(startTime: "YYYY-MM-DDT00:00:00-04:00", endTime: "YYYY-MM-DDT23:59:59-04:00",
            timeZone: "America/New_York", orderBy: "startTime")
```

Skip events Jordan declined (`"self": true` with `responseStatus: "declined"`). Anything else
that overlaps the requested window is a conflict: **narrow the window or ask before creating
the share link.** A share that offers a slot inside an existing meeting is worse than no share.
