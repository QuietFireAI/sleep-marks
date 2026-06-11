"""
sleep-marks - basic demonstration

Shows the core workflow in minimal code.
A session ends. The next session picks up where the reasoning left off.
"""

from sleep_marks import SleepMarker

# Simulate: session A ended. These are the traces from that session.
# In real use, SleepMarker reads these from the transcript.jsonl file.
# Here we patch them in directly for demonstration.

marker = SleepMarker()
marker._extract_traces = lambda cid, n: [
    {
        "step_index": 5,
        "created_at": "2026-06-11T10:00:00Z",
        "thinking": (
            "I am not certain whether approach X handles edge case Z. "
            "The user leaned toward X but I was still evaluating Y. "
            "Need to resolve this before committing."
        ),
        "content": "Evaluating both approaches.",
    }
]

mark = marker.capture(
    conversation_id="session-a-id",
    context_summary="Choosing between approach X and Y for task T",
    open_questions=[
        "Does constraint Z hold in edge cases?",
        "Is approach Y still viable if Z fails?",
    ],
)

mark.save("marks/demo_mark.json")

print("Sleep mark created.")
print(f"Reasoning traces captured: {len(mark.reasoning_traces)}")
print(f"Open questions: {len(mark.open_questions)}")
print()
print("--- Reflection text (prepend to next session) ---")
print(mark.reflection_text)

# Session B begins. Load the mark and restore context.
restored = SleepMarker.restore("marks/demo_mark.json")

print("--- Restored reasoning state ---")
print(restored.reasoning_state)
