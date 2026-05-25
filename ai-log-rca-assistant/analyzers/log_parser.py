import re
from typing import Any

# Compiled Patterns
ERROR_PATTERN   = re.compile(r"(ERROR|FATAL|CRITICAL|EXCEPTION)", re.IGNORECASE)
WARNING_PATTERN = re.compile(r"(WARN|WARNING)", re.IGNORECASE)
CRASH_PATTERN   = re.compile(
    r"(segfault|core dumped|killed|out of memory|oom killer|abort|crash)",
    re.IGNORECASE
)
TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")



# Public API
def parse_log_file(filepath: str) -> dict[str, Any]:
    """
    Read a log file and extract structured signals.

    Returns:
        source        - original file path
        total_lines   - total line count
        all_lines     - every line stripped of trailing whitespace
        error_lines   - lines matching ERROR / FATAL / CRITICAL / EXCEPTION
        warning_lines - lines matching WARN / WARNING
        crash_lines   - lines matching crash / OOM / segfault indicators
        first_timestamp - earliest timestamp seen in the file
        last_timestamp  - latest timestamp seen in the file
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    all_lines     = [line.rstrip() for line in lines]
    error_lines   = [l for l in all_lines if ERROR_PATTERN.search(l)]
    warning_lines = [l for l in all_lines if WARNING_PATTERN.search(l)]
    crash_lines   = [l for l in all_lines if CRASH_PATTERN.search(l)]

    timestamps = [
        TIMESTAMP_PATTERN.search(l).group()
        for l in all_lines
        if TIMESTAMP_PATTERN.search(l)
    ]

    print(
        f"  -> {len(all_lines)} total lines | "
        f"{len(error_lines)} errors | "
        f"{len(warning_lines)} warnings | "
        f"{len(crash_lines)} crash indicators"
    )

    return {
        "source":          filepath,
        "total_lines":     len(all_lines),
        "all_lines":       all_lines,
        "error_lines":     error_lines,
        "warning_lines":   warning_lines,
        "crash_lines":     crash_lines,
        "first_timestamp": timestamps[0]  if timestamps else None,
        "last_timestamp":  timestamps[-1] if timestamps else None,
    }
