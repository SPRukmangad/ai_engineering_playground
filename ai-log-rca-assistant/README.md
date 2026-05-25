# AI Log RCA Assistant

A terminal-based AI-powered **Root Cause Analysis (RCA)** tool for production logs and stack traces. Feed it a log file, a stack trace, or both - and get a structured diagnosis: root cause, affected subsystem, severity, and concrete debugging recommendations.

> Personal R&D project - exploring practical AI-assisted debugging workflows and prompt engineering for engineering operations.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Input Layer                                                     │
│                                                                 │
│ --log app.log --stack trace.txt --meta metadata.json            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│ analyzers/                                                      │
│                                                                 │
│ log_parser.py -> extract errors, warnings, crashes               │
│ stack_trace_parser.py -> parse frames, exception type            │
│ preprocessor.py -> combine + trim -> structured context           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│ prompts/                                                        │
│                                                                 │
│ system_rca.txt -> expert SRE system persona + JSON schema        │
│ user_rca.txt -> structured context injected here                 │
│ system_followup.txt -> interactive Q&A persona                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│ analyzers/rca_engine.py                                         │
│                                                                 │
│ GPT-4o -> JSON response -> parsed report dict                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│ Terminal Output                                                 │
│                                                                 │
│ Severity | Subsystem | Summary | Root Cause | Recommendations   │
│                                                                 │
│ Optional: --interactive -> follow-up Q&A loop                    │
└─────────────────────────────────────────────────────────────────┘

```


### Component Breakdown

| File                              | Responsibility                                                        |
|-----------------------------------|-----------------------------------------------------------------------|
| `app.py`                          | CLI entry point - arg parsing, orchestration, display                 |
| `analyzers/log_parser.py`         | Regex-based log signal extraction (errors, warnings, crashes)         |
| `analyzers/stack_trace_parser.py` | Multi-language stack trace parser (Python, Java, Node.js)             |
| `analyzers/preprocessor.py`       | Combines all inputs into a trimmed, structured context string         |
| `analyzers/rca_engine.py`         | Builds prompts, calls GPT-4o, parses JSON response                    |
| `prompts/system_rca.txt`          | System prompt - SRE persona, JSON output schema, severity definitions |
| `prompts/user_rca.txt`            | User prompt template - injects structured context                     |
| `prompts/system_followup.txt`     | Follow-up Q&A system prompt for interactive mode                      |
| `prompts/loader.py`               | Simple file-based prompt loader                                       |

---

## Workflow

1. Parse inputs -> read log / stack trace files, load metadata JSON
2. Extract signals -> regex scan for ERROR, WARN, CRITICAL, crash keywords
3. Parse stack trace -> identify exception type, frames, root application frame
4. Preprocess -> merge all signals into a structured context block
(token-budget trimming - max 30 error lines, 50 stack lines)
Build prompt -> system_rca.txt + user_rca.txt with context injected
5. GPT-4o analysis -> response_format: json_object enforced, temperature=0.2
6. Parse & display -> severity, subsystem, summary, root cause, recommendations
7. Interactive loop -> (optional) follow-up questions answered using same context


---

## Project Structure

```
ai-log-rca-assistant/
│
├── app.py # CLI entry point
├── requirements.txt # Dependencies
├── .env # OPENAI_API_KEY (git-ignored)
├── .env.example # Key template - safe to commit
├── .gitignore
├── README.md
│
├── analyzers/
│ ├── __init__.py
│ ├── log_parser.py # Log file signal extractor
│ ├── stack_trace_parser.py # Stack trace frame parser
│ ├── preprocessor.py # Context builder + trimmer
│ └── rca_engine.py # GPT-4o RCA + follow-up calls
│
├── prompts/
│ ├── loader.py # Prompt file loader
│ ├── system_rca.txt # RCA system prompt (SRE persona + JSON schema)
│ ├── user_rca.txt # RCA user prompt template
│ └── system_followup.txt # Interactive follow-up system prompt
│
└── sample_logs/
├── app_crash.log # DB connection pool exhaustion scenario
├── memory_oom.log # OOM killer batch job failure scenario
├── db_timeout_stack.txt # SQLAlchemy connection timeout stack trace
└── metadata.json # Optional system metadata example
```


---

## Setup Instructions

### 1. Clone and enter the project

```
git clone https://github.com/SPRukmangad/ai_engineering_playground.git
cd ai_engineering_playground/ai-log-rca-assistant
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
Analyze a log file:

```
python app.py --log sample_logs/app_crash.log
```

Analyze a stack trace:
```
python app.py --stack sample_logs/db_timeout_stack.txt
```

Analyze both with metadata:
```
python app.py --log sample_logs/app_crash.log --stack sample_logs/db_timeout_stack.txt --meta sample_logs/metadata.json
```

Interactive follow-up mode:
```
python app.py --log sample_logs/app_crash.log --interactive
```

### Sample Output

```
[INFO] Parsing log file: sample_logs/app_crash.log
  -> 22 total lines | 8 errors | 4 warnings | 2 crash indicators
[INFO] Preprocessing and extracting error signals...
[INFO] Running AI root cause analysis...

════════════════════════════════════════════════════════════
  AI LOG RCA ASSISTANT - Analysis Report
════════════════════════════════════════════════════════════

 Severity       : Critical
 Subsystem      : Database Connection Pool

 Issue Summary
   The application crashed due to complete exhaustion of the SQLAlchemy
   connection pool (size 10), triggered by a slow query cascade that held
   connections open beyond the timeout threshold.

 Probable Root Cause
   A slow query on the orders table (4821ms) caused connections to be held
   longer than expected, exhausting the pool of 10. Subsequent requests
   queued and timed out, triggering the circuit breaker and ultimately
   a fatal shutdown.

  Debugging Recommendations
   1. Investigate the slow query on orders table - add an index on
      user_id if missing.
   2. Increase connection pool size temporarily (pool_size=20) to reduce
      exhaustion risk while the query is optimized.
   3. Review connection leak patterns - check if connections are being
      properly released after slow queries complete.

════════════════════════════════════════════════════════════
```

### Future Improvements

PDF and structured log support - parse JSON logs (Datadog, CloudWatch format) and PDF incident reports

Multi-file ingestion - pass a directory of logs and correlate events across services

Timeline reconstruction - extract and sort all timestamped events across log files into a single incident timeline

Severity trend detection - plot error frequency over time to identify exact degradation onset

RCA report export - save structured output as a Markdown or JSON incident report file

LangChain agent mode - replace single-shot prompt with a ReAct agent that reasons over logs iteratively

Slack / PagerDuty integration - post RCA summary to an incident channel automatically

Fine-tuned model - evaluate whether a domain-specific fine-tuned model outperforms GPT-4o on log RCA tasks

Local model support - swap OpenAI for a local Ollama model for air-gapped or sensitive environments


---
