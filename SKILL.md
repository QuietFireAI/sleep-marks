---
name: sleep-marks
description: >
  Run at the END of a session or before a context break (capture) and at the
  START of a new session (restore). Carry the reasoning STATE across the break - 
  the uncertainty that was live, the options still open, the questions left
  unanswered - not just the decisions that were reached. This is the CONTINUITY
  layer of the DispatcherAgents stack.
---

# sleep-marks

## What it is
A normal handoff carries what was decided. sleep-marks carries *how the agent was
reasoning when it decided*: the live uncertainty, the open alternatives, the soft
ground. The next session resumes knowing where the doubt was, instead of
re-covering ground it already questioned without knowing it did.

## When to trigger
- **Capture:** at the end of a session, before a context-window reset, or before
  any deliberate break in a long task.
- **Restore:** at the start of the next session, before resuming the work.

## The protocol
Capture not just the conclusion but the reasoning state:
> "The team chose X" → "The team was choosing between X and Y. X won on constraint
> Z - but whether Z holds in edge cases was still open at the break."
Restore that state first thing next session so the next turn knows where the soft
ground is.

## Invoke the engine
```bash
pip install -e .            # from the sleep-marks repo
```
```python
from sleep_marks import SleepMarker, RestoredContext

# end of session - capture and save
mark = SleepMarker(brain_dir).capture(conversation_id, last_n=5)
path = mark.save("sleep_mark.json")

# start of next session - restore
ctx = SleepMarker.restore("sleep_mark.json")   # -> RestoredContext
```

## Works with
- **before-turn** reads reasoning *within* a session; sleep-marks spans *across*
  sessions - together they keep an agent self-aware end to end.
- **agent-open-mind** traces and **open-mind** drift reports are exactly the kind
  of reasoning state worth carrying over a break.

## Honest scope
This captures reasoning state as structured reflection text; it is not a full
memory system and does not guarantee perfect resumption. Restore gives the next
session *context*, not certainty - treat carried-over reasoning as prior state to
re-examine, not settled fact.

## Output convention
End a triggering turn with one line, e.g.:
`sleep-marks: captured reasoning state → sleep_mark.json` - or - `sleep-marks: restored from sleep_mark.json (3 open questions carried).`
