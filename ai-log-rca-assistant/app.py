import os
import sys
import json
import argparse
from dotenv import load_dotenv

from analyzers.log_parser import parse_log_file
from analyzers.stack_trace_parser import parse_stack_trace
from analyzers.preprocessor import preprocess
from analyzers.rca_engine import run_rca

# Config
load_dotenv()

SUPPORTED_LOG_EXTENSIONS = {".txt", ".log"}

# Argument Parser

def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Log RCA Assistant - Root Cause Analysis for logs and stack traces"
    )
    parser.add_argument(
        "--log",
        type=str,
        help="Path to a log file (.txt or .log)",
    )
    parser.add_argument(
        "--stack",
        type=str,
        help="Path to a stack trace file (.txt)",
    )
    parser.add_argument(
        "--meta",
        type=str,
        help="Path to optional metadata JSON file",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive terminal mode (ask follow-up questions)",
    )
    return parser.parse_args()


# Input Validation
def validate_inputs(args):
    if not args.log and not args.stack:
        print("[ERROR] Provide at least one input: --log or --stack")
        sys.exit(1)

    if args.log and not os.path.exists(args.log):
        print(f"[ERROR] Log file not found: {args.log}")
        sys.exit(1)

    if args.stack and not os.path.exists(args.stack):
        print(f"[ERROR] Stack trace file not found: {args.stack}")
        sys.exit(1)

    if args.meta and not os.path.exists(args.meta):
        print(f"[ERROR] Metadata file not found: {args.meta}")
        sys.exit(1)


# Load Metadata
def load_metadata(meta_path):
    if not meta_path:
        return {}
    with open(meta_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Display RCA Report
def display_report(report: dict):
    print("\n" + "═" * 60)
    print("  AI LOG RCA ASSISTANT - Analysis Report")
    print("═" * 60)

    print(f"\n Severity       : {report.get('severity', 'Unknown')}")
    print(f" Subsystem      : {report.get('subsystem', 'Unknown')}")
    print(f"\n Issue Summary\n   {report.get('summary', 'N/A')}")
    print(f"\n Probable Root Cause\n   {report.get('root_cause', 'N/A')}")
    print(f"\n  Debugging Recommendations")

    recommendations = report.get("recommendations", [])
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("   N/A")

    print("\n" + "═" * 60 + "\n")


# Interactive Follow-up Loop
def run_interactive_loop(context: str):
    from analyzers.rca_engine import ask_followup

    print("\n Interactive mode - ask follow-up questions about this log.")
    print("   Type 'exit' to quit.\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[INFO] Session ended.")
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            print("[INFO] Goodbye.")
            break

        answer = ask_followup(context, question)
        print(f"\nAssistant: {answer}\n")


# Entry Point
def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not set. Add it to a .env file or export it.")
        sys.exit(1)

    args = parse_args()
    validate_inputs(args)

    log_data = {}
    stack_data = {}
    metadata = load_metadata(args.meta)

    # Parse inputs
    if args.log:
        print(f"[INFO] Parsing log file: {args.log}")
        log_data = parse_log_file(args.log)

    if args.stack:
        print(f"[INFO] Parsing stack trace: {args.stack}")
        stack_data = parse_stack_trace(args.stack)

    # Preprocess and structure
    print("[INFO] Preprocessing and extracting error signals...")
    structured = preprocess(log_data, stack_data, metadata)

    # Run RCA via OpenAI
    print("[INFO] Running AI root cause analysis...")
    report = run_rca(structured)

    # Display report
    display_report(report)

    # Optional interactive mode
    if args.interactive:
        run_interactive_loop(structured.get("full_context", ""))


if __name__ == "__main__":
    main()
