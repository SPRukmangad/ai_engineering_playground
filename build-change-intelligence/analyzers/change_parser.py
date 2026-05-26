from typing import Any

# Field Definitions

# Every change record must have these fields
REQUIRED_FIELDS = {"id", "title", "description"}

# Optional fields with safe defaults applied if missing
OPTIONAL_DEFAULTS = {
    "ticket":           "N/A",
    "author":           "unknown",
    "component":        "unknown",
    "risk_label":       "none",
    "change_type":      "miscellaneous",
    "commit_hash":      "N/A",
    "impacted_systems": [],
}

# Public API
def parse_changes(raw_changes: list[dict]) -> dict[str, Any]:
    """
    Validate and normalize raw change records.

    - Fills in missing optional fields with safe defaults
    - Skips malformed records with a warning
    - Returns a structured dict ready for categorization and scoring

    Returns:
        total_changes  - count of valid records
        changes        - list of normalized change dicts
        by_category    - placeholder dict (populated by categorizer)
        components     - sorted list of unique impacted components
        authors        - sorted list of contributing authors
        risk_labels    - sorted list of risk labels present in dataset
    """
    valid   = []
    skipped = 0

    for raw in raw_changes:
        # Check required fields
        missing = REQUIRED_FIELDS - set(raw.keys())
        if missing:
            print(
                f"  [WARN] Skipping record missing fields "
                f"{missing}: {raw.get('id', '?')}"
            )
            skipped += 1
            continue

        # Merge defaults then override with actual values
        change = {**OPTIONAL_DEFAULTS, **raw}

        # Normalize impacted_systems - always a list
        if isinstance(change["impacted_systems"], str):
            change["impacted_systems"] = [
                s.strip()
                for s in change["impacted_systems"].split(",")
                if s.strip()
            ]

        # Normalize string fields
        change["risk_label"]  = str(change["risk_label"]).strip().lower()
        change["change_type"] = str(change["change_type"]).strip().lower()
        change["component"]   = str(change["component"]).strip()

        valid.append(change)

    if skipped:
        print(f"  -> {skipped} record(s) skipped due to missing required fields.")

    print(f"  -> {len(valid)} valid change(s) parsed.")

    # Aggregate metadata across all valid changes
    components  = sorted({c["component"]  for c in valid if c["component"]  != "unknown"})
    authors     = sorted({c["author"]     for c in valid if c["author"]     != "unknown"})
    risk_labels = sorted({c["risk_label"] for c in valid if c["risk_label"] != "none"})

    return {
        "total_changes": len(valid),
        "changes":       valid,
        "by_category":   {},         # populated by categorizer.py
        "components":    components,
        "authors":       authors,
        "risk_labels":   risk_labels,
    }