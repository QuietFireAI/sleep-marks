# sleep-marks

> *"We don't always remember what we did. We remember the formation of why we thought things. sleep-marks gives agents the same thing."*

---

## What This Is

`sleep-marks` restores cognitive continuity after a session break.

Standard handoffs inject what was decided. sleep-marks injects how the agent was reasoning when it decided - the uncertainty that was present, the options that were considered, the reasoning that was in motion.

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
Standard context injection:
  "The team decided to use approach X."

sleep-marks injection:
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
  sleep-marks injects the previous reasoning trace
  into the new context before the agent begins
         |
         v
  Agent begins with cognitive continuity, not just factual continuity
```

The injected content is not a summary of decisions.
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

---

## Token Efficiency

Standard context restoration is expensive. Handoff documents are long.
They repeat conclusions, re-explain background, restate decisions.

sleep-marks is different. Reasoning traces are dense.
A single thinking step of 200 tokens can encode the cognitive state
that would take 2000 tokens of narrative to reconstruct.

The claim: **injecting compressed reasoning traces restores more
cognitive context per token than any narrative handoff can.**

This is testable. It is one of the core claims this project exists to validate.

---

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
print(restoration.injection_text)   # Prepend this to the next session's context
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
