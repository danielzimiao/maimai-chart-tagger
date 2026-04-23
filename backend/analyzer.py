"""
analyzer.py — Claude API integration for maimai Skill Gap Analyzer.

Provides analyze(features: dict) -> dict, which calls Claude to tag a
maimai chart with skill labels and estimate its difficulty on the maimai
scale (1.0 – 15.0).

Environment:
    ANTHROPIC_API_KEY  — must be set before importing this module.
"""

import anthropic
import json

# Module-level client — reads ANTHROPIC_API_KEY from environment.
client = anthropic.Anthropic()

# ---------------------------------------------------------------------------
# Tag taxonomy (used verbatim in the prompt)
# ---------------------------------------------------------------------------
TAGGING_PROMPT = """\
You are a maimai chart analyst. Given the raw simai chart text and note \
statistics below, identify the dominant skill patterns and estimate the chart \
difficulty.

TAG TAXONOMY — choose 1 to 3 tags from this list ONLY (no other tags allowed):
  - Trill          : rapid alternating single-finger hits between two positions
  - Stream         : long sequences of consecutive tap notes
  - Stamina        : high density charts requiring sustained energy throughout
  - Tech/Crossover : complex hand crossing patterns requiring technique
  - Slide-Heavy    : charts dominated by slide note patterns
  - Hand-Alternation: patterns requiring alternating between left and right hands
  - Balanced       : no single dominant pattern; well-rounded chart

DIFFICULTY SCALE: 1.0 (easiest) to 15.0 (hardest) on the maimai rating scale.

Return JSON ONLY — no markdown fences, no commentary — in exactly this format:
{"tags": ["Tag1", "Tag2"], "difficulty": 9.5}
"""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze(features: dict) -> dict:
    """Analyze a parsed maimai chart and return skill tags + difficulty.

    Args:
        features: dict as returned by parser.parse(), containing at minimum:
            raw_simai        (str)   — full simai chart text
            total_notes      (int)
            tap_count        (int)
            hold_count       (int)
            slide_count      (int)
            bpm              (float)
            duration_seconds (float)

    Returns:
        {"tags": list[str], "difficulty": float | None}
        Falls back to {"tags": ["Balanced"], "difficulty": None} on any
        JSON parse error from the model.
    """
    # Build the prompt manually (f-string) to avoid .format() choking on
    # the {N} divisor markers that appear in raw simai text.
    note_stats = (
        f"total_notes={features['total_notes']}, "
        f"tap_count={features['tap_count']}, "
        f"hold_count={features['hold_count']}, "
        f"slide_count={features['slide_count']}"
    )
    prompt = (
        TAGGING_PROMPT
        + "\n\n--- NOTE STATISTICS ---\n"
        + note_stats
        + f"\nbpm={features['bpm']}, duration_seconds={features['duration_seconds']}"
        + "\n\n--- RAW SIMAI CHART ---\n"
        + features["raw_simai"]
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text.strip()

    try:
        result = json.loads(raw_text)
        return {
            "tags": result["tags"],
            "difficulty": float(result["difficulty"]),
        }
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return {"tags": ["Balanced"], "difficulty": None}
