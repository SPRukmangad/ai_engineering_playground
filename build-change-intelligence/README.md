# Build Change Intelligence

A terminal-based **AI-assisted release analysis and change intelligence tool** built with
Python and OpenAI. Feed it a JSON or CSV file of engineering changes and get a structured
release report - categorized changes, deterministic risk scores, AI-generated summaries,
testing focus areas, and validation recommendations.

> Personal R&D project - exploring practical AI-assisted developer productivity and release
> intelligence workflows.

---

## Architecture
```
┌──────────────────────────────────────────────────────────────────┐
│ Input Layer                                                      │
│                                                                  │
│ --input release.json --format json --release v2.5.0              │
└─────────────────────────────┬────────────────────────────────────┘
                              |
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ analyzers/                                                       │
│                                                                  │
│ change_loader.py -> load JSON or CSV into raw change dicts       │
│ change_parser.py -> validate, normalize, fill defaults           │
│ categorizer.py -> classify each change by keyword scoring        │
└─────────────────────────────┬────────────────────────────────────┘
                              |
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ scoring/                                                         │
│                                                                  │
│ risk_scorer.py -> deterministic rule-based risk score 0-100      │
│ no AI involved - fully reproducible                              │
└─────────────────────────────┬────────────────────────────────────┘
                              |
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ prompts/                                                         │
│                                                                  │
│ system_release.txt -> release manager persona + JSON schema      │
│ user_release.txt -> structured context injected here             │
└─────────────────────────────┬────────────────────────────────────┘
                              |
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ analyzers/ai_analyzer.py                                         │
│                                                                  │
│ GPT-4o -> JSON response -> parsed release report dict            │
└─────────────────────────────┬────────────────────────────────────┘
                              |
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│ Terminal Output                                                  │
│                                                                  │
│ Categories | Risk Score | Release Summary | Testing Focus        │
│ Impacted Components | Risk Summary | Validation Areas            │
└──────────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| File                          | Responsibility                                                    |
|-------------------------------|-------------------------------------------------------------------|
| `app.py`                      | CLI entry point - arg parsing, orchestration, display             |
| `analyzers/change_loader.py`  | Loads JSON or CSV into raw change dicts                           |
| `analyzers/change_parser.py`  | Validates, normalizes, fills missing fields with defaults         |
| `analyzers/categorizer.py`    | Keyword-based change classification into 6 categories             |
| `analyzers/ai_analyzer.py`    | Builds context, calls GPT-4o, returns structured report           |
| `scoring/risk_scorer.py`      | Deterministic rule-based risk scoring - no AI, fully reproducible |
| `prompts/system_release.txt`  | Release manager persona + JSON schema + output guidelines         |
| `prompts/user_release.txt`    | User prompt template - injects change context                     |
| `prompts/loader.py`           | File-based prompt loader                                          |

---

## Workflow

1. Load -> read JSON or CSV input file
2. Parse -> validate required fields, normalize optional fields
3. Categorize -> keyword scoring classifies each change into:
   feature | bugfix | infrastructure | performance | risk | miscellaneous
4. Score -> rule-based risk engine assigns 0-100 score based on:
5. risk labels + categories + change volume + component spread
6. Analyze -> GPT-4o generates structured release report
(skippable with --no-ai flag)
7. Display -> formatted terminal report with all findings

---

## Project Structure
```
build-change-intelligence/
│
├── app.py # CLI entry point
├── requirements.txt # Dependencies
├── .env # OPENAI_API_KEY (git-ignored)
├── .env.example # Key template - safe to commit
├── .gitignore
├── README.md
│
├── analyzers/
│ ├── init.py
│ ├── change_loader.py # JSON + CSV file loader
│ ├── change_parser.py # Validation + normalization
│ ├── categorizer.py # Keyword-based classifier
│ └── ai_analyzer.py # GPT-4o release report generator
│
├── scoring/
│ ├── init.py
│ └── risk_scorer.py # Deterministic rule-based risk scorer
│
├── prompts/
│ ├── loader.py # Prompt file loader
│ ├── system_release.txt # Release manager system prompt
│ └── user_release.txt # User prompt template
│
└── sample_data/
├── release_v2_5_0.json # 10 changes - mixed risk, multiple components
└── release_v1_8_2.csv # 6 changes - CSV format example

```

---
## Setup Instructions

### 1. Clone and enter the project

```
git clone https://github.com/SPRukmangad/ai_engineering_playground.git
cd ai_engineering_playground/build-change-intelligence
```

### 2. Create a virtual environment

```
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

### 4. Set your OpenAI API key

```
cp .env.example .env
# Edit .env and add your key:
# OPENAI_API_KEY=sk-...your-key-here...
```

### 5. Run

JSON input - full AI analysis:

```
python app.py --input sample_data/release_v2_5_0.json --release "v2.5.0"
```

CSV input:
```
python app.py --input sample_data/release_v1_8_2.csv --format csv --release "v1.8.2"
```

Rule-based scoring only - no AI, no API key needed:
```
python app.py --input sample_data/release_v2_5_0.json --release "v2.5.0" --no-ai
```

## Sample Output

```
[INFO] Loading changes from: sample_data/release_v2_5_0.json
[INFO] Parsing 10 change(s)...
  -> 10 valid change(s) parsed.
[INFO] Categorizing changes...
  -> risk                 2 change(s)
  -> bugfix               2 change(s)
  -> infrastructure       3 change(s)
  -> performance          1 change(s)
  -> feature              2 change(s)
[INFO] Running rule-based risk scoring...
  -> Risk score: 72/100 (High)
     1 critical risk label(s) detected
     2 high risk label(s) detected
     3 infrastructure change(s) in this release
     Wide blast radius - 8 components affected
[INFO] Running AI release analysis...

═════════════════════════════════════════════════════════════════
  BUILD CHANGE INTELLIGENCE - Release Report
  Release : v2.5.0
═════════════════════════════════════════════════════════════════

 Total Changes   : 10
  Categories      :
      risk                 2 change(s)
      bugfix               2 change(s)
      infrastructure       3 change(s)
      performance          1 change(s)
      feature              2 change(s)

 Risk Score        : 72/100  (High)
   Risk Flags:
      • 1 critical risk label(s) detected
      • Wide blast radius - 8 components affected

 Release Summary
   This release delivers OAuth2 SSO support, payment retry logic, and a
   product search performance improvement alongside a critical database
   schema migration for multi-tenancy. Three infrastructure changes and
   a CVE patch increase the deployment risk profile for this release.

  Impacted Components
   • Auth Service
   • Order Service
   • Payment Service
   • Database
   • API Gateway
   • Search Service

 Testing Focus Areas
   • OAuth2 login flow end-to-end including token expiry and refresh
   • Order deduplication under concurrent load after race condition fix
   • Database migration rollback on staging before production window

  Engineering Risk Summary
   The critical-risk schema migration to support multi-tenancy is the
   highest risk item - it requires a maintenance window, backfills
   existing records, and impacts three downstream services.

 Suggested Validation Areas
   • Run schema migration on staging database clone and validate rollback
   • Confirm all external API consumers have migrated off deprecated v1 endpoints
   • Load test payment retry logic under simulated gateway failure conditions

═════════════════════════════════════════════════════════════════
```

## Future Improvements

- [ ] **Change diff ingestion** - parse actual Git diffs or PR descriptions alongside metadata

- [ ] **Historical baseline comparison** - compare current release risk score against rolling average of past releases

- [ ] **HTML / Markdown report export** - save the release report as a formatted file for Confluence or Notion

- [ ] **Jira API integration** - pull live ticket data directly instead of requiring a JSON export

- [ ] **Multi-release trend analysis** - track risk scores and change volumes across releases over time

- [ ] **Slack notification** - post release report summary to an engineering channel on run

- [ ] **Custom scoring rules** - allow teams to define their own risk weights via a YAML config file

- [ ] **LLM categorization fallback** - use GPT-4o to classify changes that score zero on all keyword rules

- [ ] **CI/CD integration** - run as a GitHub Actions step on every release branch merge

---
