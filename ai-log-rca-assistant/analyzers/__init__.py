# This package contains all log analysis and RCA modules:
#
#   log_parser.py         - extracts error/warning/crash signals from log files
#   stack_trace_parser.py - parses Python, Java, and Node.js stack traces
#   preprocessor.py       - combines parsed signals into a structured prompt context
#   rca_engine.py         - calls GPT-4o and returns a structured RCA report