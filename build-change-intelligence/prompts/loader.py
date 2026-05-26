import os

# Config

# Resolve the prompts/ directory relative to this file
# so the loader works regardless of where app.py is invoked from
PROMPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# Public API
def load_prompt(filename: str) -> str:
    """
    Load a prompt template from the prompts/ directory.

    Args:
        filename: name of the prompt file e.g. "system_release.txt"

    Returns:
        Full contents of the prompt file as a string.

    Raises:
        FileNotFoundError: if the prompt file does not exist.
    """
    path = os.path.join(PROMPTS_DIR, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"[ERROR] Prompt template not found: {path}\n"
            f"        Expected location: prompts/{filename}"
        )

    with open(path, "r", encoding="utf-8") as f:
        return f.read()
