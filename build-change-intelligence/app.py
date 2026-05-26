import os
import sys
import argparse
from dotenv import load_dotenv

from analyzers.change_loader import load_changes
from analyzers.change_parser import parse_changes
from analyzers.categorizer import categorize_changes
from scoring.risk_scorer import score_changes
from analyzers.ai_analyzer import run_ai_analysis

# Config
load_dotenv()

# Argument Parser
def parse_args():
    parser = argparse.ArgumentParser(
        description="Build Change Intelligence - AI-assisted release analysis tool"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to input file (.json or .csv)",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "csv"],
        default="json",
        help="Input file format (default: json)",
    )
    parser.add_argument(
        "--release",
        type=str,
        default="Unnamed Release",
        help="Release name or version label (e.g. v2.5.0)",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip AI analysis and only run rule-based scoring",
    )
    return parser.parse_args()

# Input Validation
def validate_inputs(args):
    if not os.path.exists(args.input):
        print(f"[ERROR] Input file not found: {args.input}")
        sys.exit(1)

# Display Report
def display_report(release: str, parsed: dict, scored: dict, ai_report: dict):
    print("\n" + "═" * 65)
    print(f"  BUILD CHANGE INTELLIGENCE - Release Report")
    print(f"  Release : {release}")
    print("═" * 65)

    # Change summary
    print(f"\n Total Changes   : {parsed['total_changes']}")
    print(f" Categories      :")
    for cat, items in parsed["by_category"].items():
        if items:
            print(f"      {cat:<20} {len(items)} change(s)")

    # Risk score
    score = scored["overall_score"]
    level = scored["risk_level"]
    print(f"\n Risk Score        : {score}/100  ({level})")

    if scored["risk_flags"]:
        print(f"   Risk Flags:")
        for flag in scored["risk_flags"]:
            print(f"      • {flag}")

    # AI analysis
    if ai_report:
        print(f"\n Release Summary")
        print(f"   {ai_report.get('release_summary', 'N/A')}")

        print(f"\n Impacted Components")
        for c in ai_report.get("impacted_components", []):
            print(f"   • {c}")

        print(f"\n Testing Focus Areas")
        for t in ai_report.get("testing_focus", []):
            print(f"   • {t}")

        print(f"\n Engineering Risk Summary")
        print(f"   {ai_report.get('risk_summary', 'N/A')}")

        print(f"\n Suggested Validation Areas")
        for v in ai_report.get("validation_areas", []):
            print(f"   • {v}")

    print("\n" + "═" * 65 + "\n")


# Entry Point
def main():
    api_key = os.getenv("OPENAI_API_KEY")

    args = parse_args()
    validate_inputs(args)

    if not args.no_ai and not api_key:
        print("[ERROR] OPENAI_API_KEY not set. Add it to .env or use --no-ai flag.")
        sys.exit(1)

    # Load raw data
    print(f"[INFO] Loading changes from: {args.input}")
    raw_changes = load_changes(args.input, args.format)

    # Parse and structure
    print(f"[INFO] Parsing {len(raw_changes)} change(s)...")
    parsed = parse_changes(raw_changes)

    # Categorize
    print("[INFO] Categorizing changes...")
    parsed = categorize_changes(parsed)

    # Rule-based risk scoring
    print("[INFO] Running rule-based risk scoring...")
    scored = score_changes(parsed)

    # AI analysis
    ai_report = {}
    if not args.no_ai:
        print("[INFO] Running AI release analysis...")
        ai_report = run_ai_analysis(parsed, scored, args.release)

    # Display
    display_report(args.release, parsed, scored, ai_report)


if __name__ == "__main__":
    main()
