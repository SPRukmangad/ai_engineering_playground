from typing import Any

# Token Budget Constants
MAX_ERROR_LINES   = 30
MAX_STACK_LINES   = 50
MAX_WARNING_LINES = 10
MAX_CRASH_LINES   = 10


# Public API
def preprocess(
    log_data:   dict,
    stack_data: dict,
    metadata:   dict,
) -> dict[str, Any]:
    """
    Combine log signals, stack trace, and metadata into a single
    structured context object ready for prompt injection.

    Applies token-budget trimming so prompts stay within model limits.

    Returns:
        full_context   - the complete context string to inject into the prompt
        has_log        - whether log data was provided
        has_stack      - whether stack trace data was provided
        has_metadata   - whether metadata was provided
        exception_type - exception class name if detected
        crash_detected - True if any crash indicator lines were found
        error_count    - total number of error lines found
        warning_count  - total number of warning lines found
    """
    sections = []

    # Metadata block
    if metadata:
        section = _build_metadata_section(metadata)
        sections.append(section)

    # Log signals
    if log_data:
        section = _build_log_section(log_data)
        sections.append(section)

    # Stack trace
    if stack_data:
        section = _build_stack_section(stack_data)
        sections.append(section)

    full_context = "\n".join(sections)

    return {
        "full_context":    full_context,
        "has_log":         bool(log_data),
        "has_stack":       bool(stack_data),
        "has_metadata":    bool(metadata),
        "exception_type":  stack_data.get("exception_type")  if stack_data else None,
        "crash_detected":  bool(log_data.get("crash_lines")) if log_data   else False,
        "error_count":     len(log_data.get("error_lines",   [])) if log_data else 0,
        "warning_count":   len(log_data.get("warning_lines", [])) if log_data else 0,
    }


# Private Section Builders
def _build_metadata_section(metadata: dict) -> str:
    """Format the optional metadata JSON into a readable block."""
    lines = ["=== System Metadata ==="]
    for k, v in metadata.items():
        if isinstance(v, list):
            lines.append(f"  {k}:")
            for item in v:
                lines.append(f"    - {item}")
        else:
            lines.append(f"  {k}: {v}")
    return "\n".join(lines)


def _build_log_section(log_data: dict) -> str:
    """
    Build the log analysis block.
    Priority order: crash indicators -> errors -> warnings.
    Each group is trimmed to its token budget constant.
    """
    lines = ["=== Log Analysis ==="]
    lines.append(f"Source     : {log_data.get('source', 'unknown')}")
    lines.append(f"Total lines: {log_data.get('total_lines', 0)}")

    first_ts = log_data.get("first_timestamp")
    last_ts  = log_data.get("last_timestamp")
    if first_ts:
        lines.append(f"Time range : {first_ts} -> {last_ts}")

    # Crash indicators - highest signal value
    crash_lines = log_data.get("crash_lines", [])
    if crash_lines:
        lines.append("\n[Crash Indicators]")
        lines.extend(crash_lines[:MAX_CRASH_LINES])

    # Error lines
    error_lines = log_data.get("error_lines", [])
    if error_lines:
        lines.append("\n[Error Lines]")
        lines.extend(error_lines[:MAX_ERROR_LINES])
        if len(error_lines) > MAX_ERROR_LINES:
            lines.append(
                f"  ... ({len(error_lines) - MAX_ERROR_LINES} more error lines truncated)"
            )

    # Warning lines - summary only
    warning_lines = log_data.get("warning_lines", [])
    if warning_lines:
        lines.append(f"\n[Warnings - {len(warning_lines)} total, showing first {MAX_WARNING_LINES}]")
        lines.extend(warning_lines[:MAX_WARNING_LINES])

    return "\n".join(lines)


def _build_stack_section(stack_data: dict) -> str:
    """
    Build the stack trace block.
    Includes exception header, root frame summary, and trimmed raw trace.
    """
    lines = ["=== Stack Trace ==="]
    lines.append(f"Exception  : {stack_data.get('exception_type',    'unknown')}")
    lines.append(f"Message    : {stack_data.get('exception_message', 'unknown')}")
    lines.append(f"Frames     : {stack_data.get('frame_count', 0)}")

    root = stack_data.get("root_frame")
    if root:
        lines.append(
            f"Root frame : {root.get('function')} "
            f"in {root.get('file')} "
            f"line {root.get('line')}"
        )

    raw_lines = stack_data.get("raw", "").splitlines()
    lines.append("\n[Raw Stack Trace]")
    lines.extend(raw_lines[:MAX_STACK_LINES])
    if len(raw_lines) > MAX_STACK_LINES:
        lines.append(
            f"  ... ({len(raw_lines) - MAX_STACK_LINES} lines truncated)"
        )

    return "\n".join(lines)