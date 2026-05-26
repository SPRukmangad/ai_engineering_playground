# This package contains all change data processing modules:
#
#   change_loader.py  - loads JSON or CSV input files into raw change dicts
#   change_parser.py  - validates and structures raw change records
#   categorizer.py    - classifies each change into feature/bugfix/infra/etc.
#   ai_analyzer.py    - calls GPT-4o to generate the AI release report
