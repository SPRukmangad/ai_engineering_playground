from typing import Any


# Scoring Weights

# Each rule contributes a fixed number of points to the overall score.
# Score is capped at 100. Risk level thresholds applied after scoring.

WEIGHTS = {
    # Per-change risk label contributions
    "risk_label_critical":     25,
    "risk_label_high":         15,
    "risk_label_medium":        8,

    # Category contributions (per change)
    "category_risk":           12,
    "category_infrastructure":  8,
    "category_bugfix":          4,
    "category_performance":     3,
    "category_feature":         2,

    # Volume contributions
    "volume_large":            10,   # > 15 changes
    "volume_medium":            5,   # > 7 changes

    # Component spread
    "component_spread_high":   10,   # > 5 unique components
    "component_spread_medium":  5,   # > 2 unique components
}

RISK_THRESHOLDS = {
    "Critical": 75,
    "High":     50,
    "Medium":   25,
    "Low":       0,
}


# Public API
def score_changes(parsed: dict[str, Any]) -> dict[str, Any]:
    """
    Apply deterministic rule-based risk scoring to the parsed change set.

    No AI involved - scores are fully reproducible and explainable.

    Returns:
        overall_score   - integer 0-100
        risk_level      - Critical | High | Medium | Low
        risk_flags      - list of human-readable strings explaining the score
        score_breakdown - dict showing each rule's point contribution
    """
    changes     = parsed["changes"]
    by_category = parsed["by_category"]
    components  = parsed["components"]

    score     = 0
    flags     = []
    breakdown = {}

    # Risk label scoring
    critical_count = sum(1 for c in changes if c["risk_label"] == "critical")
    high_count     = sum(1 for c in changes if c["risk_label"] == "high")
    medium_count   = sum(1 for c in changes if c["risk_label"] == "medium")

    if critical_count:
        pts = min(critical_count * WEIGHTS["risk_label_critical"], 40)
        score += pts
        breakdown["critical_labels"] = pts
        flags.append(f"{critical_count} critical risk label(s) detected")

    if high_count:
        pts = min(high_count * WEIGHTS["risk_label_high"], 30)
        score += pts
        breakdown["high_labels"] = pts
        flags.append(f"{high_count} high risk label(s) detected")

    if medium_count:
        pts = min(medium_count * WEIGHTS["risk_label_medium"], 16)
        score += pts
        breakdown["medium_labels"] = pts

    # Category scoring
    cat_map = {
        "risk":           "category_risk",
        "infrastructure": "category_infrastructure",
        "bugfix":         "category_bugfix",
        "performance":    "category_performance",
        "feature":        "category_feature",
    }
    for cat, weight_key in cat_map.items():
        count = len(by_category.get(cat, []))
        if count:
            pts = min(count * WEIGHTS[weight_key], 20)
            score += pts
            breakdown[f"category_{cat}"] = pts
            if cat in {"risk", "infrastructure"} and count >= 3:
                flags.append(f"{count} {cat} change(s) in this release")

    # Volume scoring
    total = parsed["total_changes"]
    if total > 15:
        score += WEIGHTS["volume_large"]
        breakdown["volume"] = WEIGHTS["volume_large"]
        flags.append(f"Large release - {total} changes total")
    elif total > 7:
        score += WEIGHTS["volume_medium"]
        breakdown["volume"] = WEIGHTS["volume_medium"]

    # Component spread scoring
    spread = len(components)
    if spread > 5:
        score += WEIGHTS["component_spread_high"]
        breakdown["component_spread"] = WEIGHTS["component_spread_high"]
        flags.append(f"Wide blast radius - {spread} components affected")
    elif spread > 2:
        score += WEIGHTS["component_spread_medium"]
        breakdown["component_spread"] = WEIGHTS["component_spread_medium"]

    # Cap and level
    score = min(score, 100)
    level = _get_risk_level(score)

    print(f"  -> Risk score: {score}/100 ({level})")
    if flags:
        for flag in flags:
            print(f"     ⚑ {flag}")

    return {
        "overall_score":   score,
        "risk_level":      level,
        "risk_flags":      flags,
        "score_breakdown": breakdown,
    }


# Private Helpers
def _get_risk_level(score: int) -> str:
    """Map a numeric score to a named risk level."""
    for level, threshold in RISK_THRESHOLDS.items():
        if score >= threshold:
            return level
    return "Low"