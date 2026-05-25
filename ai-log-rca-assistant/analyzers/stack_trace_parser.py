import re
from typing import Any

# Compiled Patterns

# Python:  File "/app/routes/orders.py", line 47, in get_order_summary
PYTHON_FRAME = re.compile(r'File "(.+)", line (\d+), in (\S+)')

# Java:    at com.example.service.OrderService.process(OrderService.java:142)
JAVA_FRAME = re.compile(r'at ([\w\.$]+)\(([\w]+\.java):(\d+)\)')

# Node.js: at processOrder (/app/services/order.js:88:14)
NODE_FRAME = re.compile(r'at (.+) \((.+):(\d+):(\d+)\)')

# Exception header - works for Python, Java, Node
EXCEPTION_LINE = re.compile(
    r'^(\w+(?:\.\w+)*(?:Error|Exception|Fault|Panic)):\s*(.*)',
    re.MULTILINE
)


# Public API
def parse_stack_trace(filepath: str) -> dict[str, Any]:
    """
    Parse a stack trace file and extract structured signals.

    Supports Python, Java, and Node.js stack trace formats.

    Returns:
        source            - original file path
        raw               - full raw text of the stack trace
        exception_type    - e.g. TimeoutError, NullPointerException
        exception_message - the message that accompanied the exception
        frames            - list of dicts: {file, line, function, raw}
        root_frame        - deepest non-library application frame
        frame_count       - total number of frames detected
    """
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read()

    lines = raw.splitlines()

    # Exception header
    exception_type    = None
    exception_message = None
    match = EXCEPTION_LINE.search(raw)
    if match:
        exception_type    = match.group(1)
        exception_message = match.group(2)

    # Frame extraction
    # Try all three patterns per line - first match wins
    frames = []
    for line in lines:
        frame = (
            _try_python_frame(line) or
            _try_java_frame(line)   or
            _try_node_frame(line)
        )
        if frame:
            frames.append(frame)

    # Root frame heuristic
    # Strip library internals - surface the application frame
    # that actually caused the crash
    app_frames = [
        f for f in frames
        if "site-packages"  not in f["file"]
        and "node_modules"  not in f["file"]
        and "<frozen"       not in f["file"]
        and "lib/python"    not in f["file"]
    ]
    root_frame = app_frames[-1] if app_frames else (frames[-1] if frames else None)

    print(
        f"  -> Exception: {exception_type or 'unknown'} | "
        f"{len(frames)} frames detected | "
        f"Root frame: {root_frame['function'] if root_frame else 'N/A'}"
    )

    return {
        "source":            filepath,
        "raw":               raw,
        "exception_type":    exception_type,
        "exception_message": exception_message,
        "frames":            frames,
        "root_frame":        root_frame,
        "frame_count":       len(frames),
    }


# Private Helpers
def _try_python_frame(line: str) -> dict | None:
    m = PYTHON_FRAME.search(line)
    if not m:
        return None
    return {
        "file":     m.group(1),
        "line":     m.group(2),
        "function": m.group(3),
        "raw":      line.strip(),
    }


def _try_java_frame(line: str) -> dict | None:
    m = JAVA_FRAME.search(line)
    if not m:
        return None
    return {
        "file":     m.group(2),
        "line":     m.group(3),
        "function": m.group(1),
        "raw":      line.strip(),
    }


def _try_node_frame(line: str) -> dict | None:
    m = NODE_FRAME.search(line)
    if not m:
        return None
    return {
        "file":     m.group(2),
        "line":     m.group(3),
        "function": m.group(1),
        "raw":      line.strip(),
    }