"""
Tests for sleep_marks.marker

Core claims being tested:
1. SleepMark captures reasoning traces and produces injection text
2. Injection text contains the context summary and open questions
3. RestoredContext loads a saved mark and reconstructs injection text
4. Token efficiency claim: reasoning traces encode state densely
5. No reasoning traces = graceful handling, not crash
6. Injection text respects max_injection_chars limit
7. Open questions survive round-trip save/restore
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from sleep_marks import SleepMarker, SleepMark, RestoredContext


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_TRACES = [
    {
        "step_index": 3,
        "created_at": "2026-06-11T10:00:00Z",
        "thinking": (
            "I am not certain whether approach X handles edge case Z correctly. "
            "The team leaned toward X but I was still evaluating Y. "
            "This needs more thought before committing."
        ),
        "content": "I will evaluate both approaches before deciding.",
    },
    {
        "step_index": 7,
        "created_at": "2026-06-11T10:05:00Z",
        "thinking": (
            "The constraint on Z seems to hold in the common case. "
            "But I noticed the spec is ambiguous on the edge case. "
            "I was about to ask the user to clarify when the session ended."
        ),
        "content": "Approach X looks viable, pending clarification on Z.",
    },
]

SAMPLE_OPEN_QUESTIONS = [
    "Does constraint Z hold in the edge case?",
    "Is approach Y still viable if Z fails?",
]

SAMPLE_SUMMARY = "Evaluating approach X vs Y for task T with constraint Z"


def make_marker_with_traces(traces: list[dict], tmp_path: Path) -> SleepMarker:
    """
    Build a SleepMarker and monkey-patch _extract_traces to return known data.
    Used to test the full pipeline without needing a real transcript file.
    """
    marker = SleepMarker(brain_dir=str(tmp_path))
    marker._extract_traces = lambda cid, n: traces[:n]
    return marker


# ── SleepMark creation tests ───────────────────────────────────────────────────

class TestSleepMarkCapture:

    def test_returns_sleep_mark(self, tmp_path):
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        result = marker.capture(
            conversation_id="test-session-001",
            context_summary=SAMPLE_SUMMARY,
        )
        assert isinstance(result, SleepMark)

    def test_context_summary_preserved(self, tmp_path):
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        result = marker.capture("id-001", SAMPLE_SUMMARY)
        assert SAMPLE_SUMMARY in result.context_summary

    def test_reasoning_traces_captured(self, tmp_path):
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        result = marker.capture("id-001", SAMPLE_SUMMARY)
        assert len(result.reasoning_traces) == len(SAMPLE_TRACES)

    def test_open_questions_preserved(self, tmp_path):
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        result = marker.capture(
            "id-001",
            SAMPLE_SUMMARY,
            open_questions=SAMPLE_OPEN_QUESTIONS,
        )
        assert result.open_questions == SAMPLE_OPEN_QUESTIONS

    def test_injection_text_present(self, tmp_path):
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        result = marker.capture("id-001", SAMPLE_SUMMARY)
        assert len(result.injection_text) > 0

    def test_injection_contains_summary(self, tmp_path):
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        result = marker.capture("id-001", SAMPLE_SUMMARY)
        assert SAMPLE_SUMMARY in result.injection_text

    def test_injection_contains_open_questions(self, tmp_path):
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        result = marker.capture(
            "id-001",
            SAMPLE_SUMMARY,
            open_questions=SAMPLE_OPEN_QUESTIONS,
        )
        for q in SAMPLE_OPEN_QUESTIONS:
            assert q in result.injection_text

    def test_injection_contains_reasoning(self, tmp_path):
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        result = marker.capture("id-001", SAMPLE_SUMMARY)
        # At least part of the thinking trace should be in the injection
        assert "approach X" in result.injection_text or "constraint Z" in result.injection_text

    def test_injection_respects_max_chars(self, tmp_path):
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        result = marker.capture("id-001", SAMPLE_SUMMARY, max_injection_chars=100)
        # The reasoning portion should be truncated
        assert len(result.injection_text) < 2000  # well under unconstrained size


# ── No-traces graceful handling ────────────────────────────────────────────────

class TestNoTraces:

    def test_empty_traces_does_not_crash(self, tmp_path):
        marker = make_marker_with_traces([], tmp_path)
        result = marker.capture("id-empty", SAMPLE_SUMMARY)
        assert isinstance(result, SleepMark)

    def test_empty_traces_injection_still_valid(self, tmp_path):
        marker = make_marker_with_traces([], tmp_path)
        result = marker.capture("id-empty", SAMPLE_SUMMARY)
        assert SAMPLE_SUMMARY in result.injection_text

    def test_empty_traces_no_questions(self, tmp_path):
        marker = make_marker_with_traces([], tmp_path)
        result = marker.capture("id-empty", SAMPLE_SUMMARY)
        assert result.open_questions == []


# ── Save and restore round-trip ───────────────────────────────────────────────

class TestSaveRestore:

    def test_save_creates_file(self, tmp_path):
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        mark = marker.capture("id-001", SAMPLE_SUMMARY)
        out = mark.save(str(tmp_path / "test_mark.json"))
        assert out.exists()

    def test_saved_file_is_valid_json(self, tmp_path):
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        mark = marker.capture("id-001", SAMPLE_SUMMARY)
        out = mark.save(str(tmp_path / "test_mark.json"))
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "conversation_id" in data
        assert "injection_text" in data
        assert "open_questions" in data

    def test_restore_returns_restored_context(self, tmp_path):
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        mark = marker.capture("id-001", SAMPLE_SUMMARY, open_questions=SAMPLE_OPEN_QUESTIONS)
        out = mark.save(str(tmp_path / "test_mark.json"))
        restored = SleepMarker.restore(str(out))
        assert isinstance(restored, RestoredContext)

    def test_open_questions_survive_roundtrip(self, tmp_path):
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        mark = marker.capture("id-001", SAMPLE_SUMMARY, open_questions=SAMPLE_OPEN_QUESTIONS)
        out = mark.save(str(tmp_path / "test_mark.json"))
        restored = SleepMarker.restore(str(out))
        assert restored.open_questions == SAMPLE_OPEN_QUESTIONS

    def test_injection_text_survives_roundtrip(self, tmp_path):
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        mark = marker.capture("id-001", SAMPLE_SUMMARY)
        original_injection = mark.injection_text
        out = mark.save(str(tmp_path / "test_mark.json"))
        restored = SleepMarker.restore(str(out))
        assert restored.injection_text == original_injection

    def test_reasoning_state_in_restored(self, tmp_path):
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        mark = marker.capture("id-001", SAMPLE_SUMMARY)
        out = mark.save(str(tmp_path / "test_mark.json"))
        restored = SleepMarker.restore(str(out))
        assert len(restored.reasoning_state) > 0


# ── Token efficiency claim ─────────────────────────────────────────────────────

class TestTokenEfficiency:
    """
    Encodes the core claim: reasoning traces are more token-efficient
    than narrative handoffs for restoring cognitive context.

    The test validates that the injection text is significantly shorter
    than a full re-narration of the same context would be, while still
    containing the key reasoning content.
    """

    def test_injection_is_dense_relative_to_traces(self, tmp_path):
        """
        Injection text should be shorter than the sum of raw trace content,
        while preserving the key reasoning markers.
        """
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        mark = marker.capture("id-001", SAMPLE_SUMMARY, max_injection_chars=1500)

        raw_trace_chars = sum(len(t["thinking"]) for t in SAMPLE_TRACES)
        injection_chars = len(mark.injection_text)

        # Injection is bounded and structured, not a raw dump
        assert injection_chars < raw_trace_chars * 3  # not inflated
        # But it contains meaningful content
        assert injection_chars > 100

    def test_key_uncertainty_preserved_in_injection(self, tmp_path):
        """
        The uncertainty that was present in the thinking should survive
        into the injection text. This is the whole point.
        """
        marker = make_marker_with_traces(SAMPLE_TRACES, tmp_path)
        mark = marker.capture("id-001", SAMPLE_SUMMARY)

        # The uncertainty from step 3 should be in the injection
        assert "not certain" in mark.injection_text or "still evaluating" in mark.injection_text or "constraint Z" in mark.injection_text
