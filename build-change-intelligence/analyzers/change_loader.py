import json
import csv
from typing import Any

# Public API
def load_changes(filepath: str, fmt: str) -> list[dict[str, Any]]:
    """
    Load raw change records from a JSON or CSV file.

    Args:
        filepath : path to the input file
        fmt      : "json" or "csv"

    Returns:
        List of raw change dicts - one per change record.
    """
    if fmt == "json":
        return _load_json(filepath)
    elif fmt == "csv":
        return _load_csv(filepath)
    else:
        raise ValueError(
            f"[ERROR] Unsupported format: {fmt}. Use 'json' or 'csv'."
        )


# Private Helpers
def _load_json(filepath: str) -> list[dict[str, Any]]:
    """Load changes from a JSON file. Supports both list and wrapped formats."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Support both raw list and {"changes": [...]} wrapper
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "changes" in data:
        return data["changes"]

    raise ValueError(
        "[ERROR] JSON file must be a list of changes or "
        "a dict with a 'changes' key."
    )


def _load_csv(filepath: str) -> list[dict[str, Any]]:
    """Load changes from a CSV file. First row must be headers."""
    changes = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            changes.append(dict(row))

    print(f"  -> Loaded {len(changes)} record(s) from CSV.")
    return changes