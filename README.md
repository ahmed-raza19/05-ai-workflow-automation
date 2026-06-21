# AI Workflow Automation System

An end-to-end automated workflow for **customer support ticket triage and
routing**: incoming tickets are classified, prioritized, routed to the right
department, and given a draft reply — automatically.

## Workflow

```
Input: customer ticket (name, subject, message)
        │
        ▼
LLM-based decision making (Groq / Llama 3.3)
  → category, priority, summary, suggested reply, human-review flag
        │
        ├── LLM call fails / times out / returns invalid JSON
        │         │
        │         ▼
        │   Rule-based fallback decision system (keyword heuristics)
        │
        ▼
Structured JSON output + routed department + full audit log
```

## Project Structure

```
05-ai-workflow-automation/
├── models.py            # Pydantic request/response schemas
├── workflow.py            # LLM decision logic + rule-based fallback
├── logger_config.py       # structured logging setup
├── app.py                 # FastAPI application
├── logs/                  # workflow.log generated at runtime
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Get a **free** Groq API key at [console.groq.com](https://console.groq.com) and
add it to `.env`. (The workflow still runs without a key — it automatically
uses the rule-based fallback, so the project is demoable with zero setup cost.)

## Usage

### 1. Run the API

```bash
uvicorn app:app --reload
```

Visit `http://127.0.0.1:8000/docs` for interactive Swagger documentation.

### 2. Submit a ticket

```bash
curl -X POST http://127.0.0.1:8000/submit-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Ali Raza",
    "subject": "Refund not received",
    "message": "I was charged twice for my subscription and need a refund immediately."
  }'
```

Response:

```json
{
  "ticket_id": "af1798c9",
  "category": "Billing",
  "priority": "Medium",
  "department": "Billing Department",
  "summary": "Customer was double-charged and is requesting a refund.",
  "suggested_reply": "Thanks for flagging this, Ali — I'm sorry for the inconvenience...",
  "requires_human_review": false
}
```

### 3. Check the logs

Every ticket is logged with its routing decision, decision source
(`llm` or `rule_based_fallback`), and timestamp:

```
2026-06-20 16:26:09 | INFO | Ticket af1798c9 received from Ali Raza: 'Refund not received'
2026-06-20 16:26:09 | INFO | Ticket af1798c9 routed to Billing Department | priority=Medium | source=llm | human_review=False
```

## Design Notes

- **Hybrid decision system**: the LLM handles nuanced classification and
  drafts replies; a keyword-based fallback guarantees the workflow never
  goes down even if the LLM API is unavailable, rate-limited, or returns
  malformed output.
- **Validation**: LLM output is validated against allowed category/priority
  values before being trusted — invalid responses automatically trigger the
  fallback path instead of propagating bad data.
- **Error handling & logging**: every stage (receipt, decision, routing,
  failures) is logged to both console and `logs/workflow.log` for auditability.
- **Adapting this template**: the same input → LLM-decision → fallback →
  structured-output → logging pattern can be repointed at other workflows
  (invoice processing, lead qualification, content moderation, etc.) by
  swapping out the prompt and category set in `workflow.py`.
