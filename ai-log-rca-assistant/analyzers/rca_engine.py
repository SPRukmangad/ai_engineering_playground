import os
import json
from openai import OpenAI
from prompts.loader import load_prompt

# Config
CHAT_MODEL   = "gpt-4o"
TEMPERATURE  = 0.2

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Public API
def run_rca(structured: dict) -> dict:
    """
    Build the RCA prompt from the structured context and call GPT-4o.

    Uses response_format: json_object to guarantee a parseable response.
    Falls back gracefully if JSON parsing fails for any reason.

    Returns a report dict with keys:
        severity, subsystem, summary, root_cause, recommendations
    """
    system_prompt = load_prompt("system_rca.txt")
    user_prompt   = load_prompt("user_rca.txt").format(
        context=structured["full_context"]
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


def ask_followup(context: str, question: str) -> str:
    """
    Answer a follow-up question about the log in interactive mode.

    Reuses the same context window from the original RCA -
    no re-parsing or additional API calls to rebuild context.

    Returns a plain string answer.
    """
    system_prompt = load_prompt("system_followup.txt")

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role":    "user",
                "content": f"Log context:\n{context}\n\nQuestion: {question}",
            },
        ],
    )

    return response.choices[0].message.content.strip()


# Private Helpers
def _parse_response(raw: str) -> dict:
    """
    Parse the raw JSON string from GPT-4o into a report dict.

    Falls back to a safe default structure if parsing fails -
    the app never crashes due to an unexpected model response.
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "severity":        "Unknown",
            "subsystem":       "Unknown",
            "summary":         raw,
            "root_cause":      "Could not parse structured response from model.",
            "recommendations": [],
        }