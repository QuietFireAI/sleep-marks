# sleep-marks

> *"We don't always remember what we did. We remember the formation of why we thought things. sleep-marks gives agents the same thing."*

---

## The DispatcherAgents Stack

*Each tool works alone. All five make generation governed. Read the [MANIFESTO.md](./MANIFESTO.md) for the full architecture.*

| Tool | Role |
|---|---|
| [before-turn](https://github.com/QuietFireAI/before-turn) | Governs entry -- reads prior thinking before every response |
| [pre-response-selfcheck](https://github.com/QuietFireAI/pre-response-selfcheck) | Governs exit -- reads output as cold reader before delivering |
| [agent-open-mind](https://github.com/QuietFireAI/agent-open-mind) | Reads what sub-agents thought, not what they said |
| [open-mind](https://github.com/QuietFireAI/open-mind) | Compares what the agent thought to what it said |
| [sleep-marks](https://github.com/QuietFireAI/sleep-marks) | Restores reasoning state across session breaks |

---


## What This Is

`sleep-marks` restores cognitive continuity after a session break.

Standard handoffs carry what was decided. sleep-marks restores how the agent was reasoning when it decided - the uncertainty that was present, the options that were considered, the reasoning that was in motion.

The agent coming back from a break knows not just the conclusion. It knows the thinking behind it.

---

## The Problem

Agents are stateless. After any break, they lose context.

The current fix - conversation handoffs - works at the factual layer:

```
"Here is what was decided:
- Task A completed
- Task B is pending
- Decision: use approach X"
```

Useful. But incomplete.

What is missing is the cognitive layer:

```
"Here is what was being reasoned:
- Why approach X was chosen over Y (and with what confidence)
- Where the reasoning was uncertain or contested
- What the agent was about to do when the break happened
- What open questions were unresolved"
```

The factual handoff tells you where you ended up.
sleep-marks tells you how you were thinking when you got there.

---

## Human Memory Analogy

Human memory does not store every fact. But it tends to retain the formation of important decisions - the moment of weighing, the feeling of uncertainty, the why underneath the what.

sleep-marks applies this to agents:

```
Standard context handoff:
  "The team decided to use approach X."

sleep-marks reflection:
  "The team was deciding between X and Y.
   X was chosen because of constraint Z, but the agent noted
   uncertainty about Z's validity in edge cases.
   That uncertainty was open when the session ended."
```

The second agent re-entering this context knows where the soft ground is.
The first one erased it.

---

## How It Works

```
Session A (before break):
  Agent reasons -> acts -> produces thoughts
         |
         | sleep-marks captures the reasoning trace
         | at the point of break - the "sleep mark"
         |
         v
Session B (after break):
  sleep-marks provides the previous reasoning trace
  into the new context before the agent begins
         |
         v
  Agent begins with cognitive continuity, not just factual continuity
```

The provided content is not a summary of decisions.
It is a reconstruction of the reasoning state at the break point.

---

## Relationship to the OpenMind Family

| Tool | Direction | When |
|---|---|---|
| [agent-open-mind](https://github.com/QuietFireAI/agent-open-mind) | External | Dispatcher reads what agents thought |
| [open-mind](https://github.com/QuietFireAI/open-mind) | Internal | Agent compares its thinking to its response |
| **sleep-marks** | Temporal | Agent restores reasoning context after a break |

They are sequential tools in the same pipeline:

```
agent-open-mind captures thoughts  (within a session)
open-mind compares thoughts        (within a turn)
sleep-marks restores thoughts      (across sessions)
```

The **before-turn protocol** is the connective tissue:

```
Before each turn:
  quick_check.py reads last 3 thinking steps  (agent-open-mind)
        |
        v
During the turn:
  open-mind catches where the response drifted from the thinking
        |
        v
At session break:
  sleep-marks captures the reasoning state
        |
        v
Next session:
  reflection_text restores the thinking -- not just the conclusions
```

`quick_check.py` is in agent-open-mind. Run it before each turn.


## Token Efficiency

Standard context restoration is expensive. Handoff documents are long.
They repeat conclusions, re-explain background, restate decisions.

sleep-marks is different. Reasoning traces are dense.
A single thinking step of 200 tokens can encode the cognitive state
that would take 2000 tokens of narrative to reconstruct.

The claim: **providing compressed reasoning traces restores more
cognitive context per token than any narrative handoff can.**

This is testable. It is one of the core claims this project exists to validate.

**Status of this claim:** Directional evidence exists from a cross-LLM experiment
(June 11 2026, Gemini + Claude Sonnet 4.6). A three-condition test showed that
Condition B (JSON with reasoning traces) produced materially deeper answers than
Condition A (narrative summary) on three of five questions. One session is not proof.
It is sufficient to move from speculative to supported.

---

## v0.1 Design Limitation -- Named Explicitly

**The open_questions field is manually curated.**

This means the agent decides what uncertainty to surface before passing to the next session.
That is the same suppression mechanism the entire project is designed to detect.

In the June 11 2026 founding session, all three uncertainty gaps that a cross-model
evaluation identified (Steps 143, 161, 231) were absent from the manually curated
open_questions field -- despite being structurally present in the reasoning traces.

Manual curation selects for admitted uncertainty.
The traces contain suppressed uncertainty the agent rationalized away.

**This is not a bug to fix before shipping. It is a limitation to name before shipping.**

v0.1 ships with manual curation. The limitation is documented here.
v0.2 target: automatic uncertainty extraction from the reasoning trace itself,
bypassing agent curation entirely.

Ship v0.1. Name the gap. That is consistent with this project's intellectual position.

### Experimental Evidence for the Extraction Gap

The June 11 2026 CrossPoll session produced a quantified measurement of this limitation.

**The delta:**

- Antigravity's manual curation produced **6 open_questions**
- After cross-model examination (Claude Sonnet 4.6 receiving the handoff and returning analysis), the list grew to **11 open_questions**
- **5 additional questions** were surfaced by the receiving model that the originating agent did not surface itself

That delta -- 5 questions -- is the manual proof of what automatic uncertainty extraction
would produce without requiring a human in the middle.

In the CrossPoll session, Jeff Phillips was the extraction mechanism. He carried the
handoff documents from Antigravity to Claude, observed Claude's responses, and returned
the surfaced uncertainties to the open_questions list. That is a human doing manually
what v0.2 is designed to do automatically.

The 6-to-11 delta is not an estimate. It is a measured result from a documented session.
The session transcript, handoff files, and reasoning traces are all preserved.


## Installation

```bash
pip install sleep-marks
```

Or from source:

```bash
git clone https://github.com/QuietFireAI/sleep-marks.git
cd sleep-marks
pip install -e .
```

**Zero required dependencies.** Pure Python 3.9+.

---

## Quick Start

```python
from sleep_marks import SleepMarker

# At the end of a session - mark the break point
marker = SleepMarker()
mark = marker.capture(
    conversation_id="your-session-id",
    context_summary="What was being worked on",
)
mark.save("marks/session_001.json")

# At the start of the next session - restore the reasoning state
from sleep_marks import SleepMarker

restoration = SleepMarker.restore("marks/session_001.json")
print(restoration.reflection_text)   # Prepend this to the next session's context
print(restoration.open_questions)   # What was unresolved
print(restoration.reasoning_state)  # How the agent was thinking
```

---

## Status

**v0.1 - June 2026**

Core concept validated. Implementation in progress.

Part of the [DispatcherAgents](https://dispatcheragents.com) project.

---

## License

Apache 2.0 - QuietFireAI / [dispatcheragents.com](https://dispatcheragents.com)

---

*"The agents start fresh every time. sleep-marks means they don't have to."*
