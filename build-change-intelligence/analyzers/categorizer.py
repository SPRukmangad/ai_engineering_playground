from typing import Any

# Keyword Maps

# Each category maps to keywords checked against:
# title + description + change_type + risk_label (all lowercased)

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "feature": [
        "add", "new", "implement", "introduce", "feature",
        "support", "enable", "create", "build",
    ],
    "bugfix": [
        "fix", "bug", "patch", "resolve", "repair",
        "hotfix", "regression", "crash", "error", "incorrect",
    ],
    "infrastructure": [
        "infra", "infrastructure", "deploy", "pipeline", "ci",
        "cd", "docker", "kubernetes", "terraform", "helm",
        "config", "configuration", "environment", "setup",
    ],
    "performance": [
        "performance", "optimise", "optimize", "latency",
        "throughput", "memory", "cpu", "speed", "slow",
        "bottleneck", "cache", "efficient",
    ],
    "risk": [
        "risk", "breaking", "migration", "deprecat",
        "security", "vulnerability", "cve", "critical",
        "schema change", "data loss", "rollback",
    ],
}


# Public API
def categorize_changes(parsed: dict[str, Any]) -> dict[str, Any]:
    """
    Classify each change into one of:
        feature | bugfix | infrastructure | performance | risk | miscellaneous

    Classification priority order:
        risk > bugfix > infrastructure > performance > feature > miscellaneous

    Mutates parsed["by_category"] and adds a "category" key to each change.
    Returns the updated parsed dict.
    """
    by_category: dict[str, list] = {
        "feature":        [],
        "bugfix":         [],
        "infrastructure": [],
        "performance":    [],
        "risk":           [],
        "miscellaneous":  [],
    }

    for change in parsed["changes"]:
        category = _classify(change)
        change["category"] = category
        by_category[category].append(change)

    parsed["by_category"] = by_category

    # Print category summary
    for cat, items in by_category.items():
        if items:
            print(f"  -> {cat:<20} {len(items)} change(s)")

    return parsed


# Private Helpers
def _classify(change: dict) -> str:
    """
    Score each category by keyword hits across all relevant text fields.
    Priority order applied after scoring - risk checked first via label.
    Falls back to miscellaneous if no keyword hits found.
    """
    # Explicit high/critical risk label always wins - no scoring needed
    if change.get("risk_label") in {"high", "critical"}:
        return "risk"

    # Build combined text from all relevant fields
    text = " ".join([
        change.get("title",       ""),
        change.get("description", ""),
        change.get("change_type", ""),
        change.get("risk_label",  ""),
    ]).lower()

    # Score each category by keyword hit count
    scores: dict[str, int] = {cat: 0 for cat in CATEGORY_KEYWORDS}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[cat] += 1

    # Apply priority order - highest scoring category wins
    # Priority: risk > bugfix > infrastructure > performance > feature
    priority = ["risk", "bugfix", "infrastructure", "performance", "feature"]
    best_cat  = max(priority, key=lambda c: scores[c])

    # No keyword hits anywhere - miscellaneous
    if scores[best_cat] == 0:
        return "miscellaneous"

    return best_cat