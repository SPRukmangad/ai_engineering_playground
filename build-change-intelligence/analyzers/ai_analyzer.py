import os
import json
from openai import OpenAI
from prompts.loader import load_prompt

# Config
CHAT_MODEL  = "gpt-4o"
TEMPERATURE = 0.3

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Public API
def run_ai_analysis(parsed: dict, scored: dict, release: str) -> dict:
    """
    Build the release analysis prompt and call GPT-4o.

    Returns a structured report dict with keys:
        release_summary     - 2-3 sentence plain English release overview
        impacted_components - list of affected components
        testing_focus       - list of suggested testing areas
        risk_summary        - 1-2 sentence engineering risk narrative
        validation_areas    - list of suggested pre-release validation steps
    """
    system_prompt = load_prompt("system_release.txt")
    user_prompt   = load_prompt("user_release.txt").format(
        release=release,
        context=_build_context(parsed, scored),
    )

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
    )

    raw = response.choices[0].message.content
    return _parse_response(raw)


# Private Helpers
def _build_context(parsed: dict, scored: dict) -> str:
    """
    Serialize parsed change data and risk scores into a structured
    plain-text context block for prompt injection.

    Organized by category so GPT-4o receives grouped, readable signal
    rather than a flat unsorted list of changes.
    """
    lines = []

    lines.append(f"Total changes : {parsed['total_changes']}")
    lines.append(f"Risk score    : {scored['overall_score']}/100 ({scored['risk_level']})")
    lines.append(f"Risk flags    : {', '.join(scored['risk_flags']) or 'none'}")
    lines.append(f"Components    : {', '.join(parsed['components']) or 'unknown'}")
    lines.append(f"Authors       : {', '.join(parsed['authors']) or 'unknown'}")
    lines.append("")

    # Category breakdown - highest signal categories first
    lines.append("=== Change Breakdown by Category ===")
    for cat, items in parsed["by_category"].items():
        if not items:
            continue
        lines.append(f"\n[{cat.upper()}] - {len(items)} change(s)")
        for ch in items:
            lines.append(f"  • [{ch['ticket']}] {ch['title']}")
            lines.append(f"    Component  : {ch['component']}")
            lines.append(f"    Risk label : {ch['risk_label']}")
            lines.append(f"    Description: {ch['description'][:200]}")

    return "\n".join(lines)


def _parse_response(raw: str) -> dict:
    """
    Parse GPT-4o JSON response into a report dict.
    Falls back gracefully on parse failure - app never crashes
    due to an unexpected model response.
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "release_summary":     raw,
            "impacted_components": [],
            "testing_focus":       [],
            "risk_summary":        "Could not parse structured response.",
            "validation_areas":    [],
        }