"""
End-to-end ticket triage workflow:

  Input (customer ticket)
        │
        ▼
  LLM-based decision making (Groq / Llama 3.3) — classifies category,
  priority, department, drafts a reply, and flags tickets needing a human
        │
        ▼  (on any failure: timeout, bad JSON, missing API key)
  Rule-based fallback decision system — keeps the workflow operational
        │
        ▼
  Structured output + logging
"""

import json
import os
import re
import uuid

from groq import Groq

from logger_config import logger
from models import TicketDecision

GROQ_MODEL = "llama-3.3-70b-versatile"

VALID_CATEGORIES = {"Billing", "Technical", "General", "Urgent Escalation"}
VALID_PRIORITIES = {"Low", "Medium", "High", "Critical"}
DEPARTMENT_MAP = {
    "Billing": "Billing Department",
    "Technical": "Technical Support",
    "General": "General Support",
    "Urgent Escalation": "Management",
}

URGENT_KEYWORDS = [
    "legal action",
    "lawsuit",
    "fraud",
    "unauthorized charge",
    "data breach",
]
BILLING_KEYWORDS = ["refund", "charge", "invoice", "payment", "billing", "subscription"]
TECHNICAL_KEYWORDS = [
    "error",
    "bug",
    "crash",
    "not working",
    "broken",
    "login",
    "password",
]


def _build_prompt(subject: str, message: str) -> str:
    return f"""You are a support ticket triage assistant. Analyze the ticket below and
respond with ONLY a valid JSON object (no markdown, no extra text) with these exact keys:

- "category": one of "Billing", "Technical", "General", "Urgent Escalation"
- "priority": one of "Low", "Medium", "High", "Critical"
- "summary": a one-sentence summary of the issue
- "suggested_reply": a short, polite draft reply to the customer (2-3 sentences)
- "requires_human_review": true or false (true for legal/security/critical issues)

Ticket subject: {subject}
Ticket message: {message}

JSON:"""


def _call_llm(subject: str, message: str) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set")

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": _build_prompt(subject, message)}],
        temperature=0.2,
        max_tokens=300,
    )
    raw_content = response.choices[0].message.content.strip()
    raw_content = re.sub(r"^```json|```$", "", raw_content, flags=re.MULTILINE).strip()
    parsed = json.loads(raw_content)

    if parsed.get("category") not in VALID_CATEGORIES:
        raise ValueError(f"LLM returned invalid category: {parsed.get('category')}")
    if parsed.get("priority") not in VALID_PRIORITIES:
        raise ValueError(f"LLM returned invalid priority: {parsed.get('priority')}")

    return parsed


def _rule_based_fallback(subject: str, message: str) -> dict:
    text = f"{subject} {message}".lower()

    if any(keyword in text for keyword in URGENT_KEYWORDS):
        category, priority, requires_review = "Urgent Escalation", "Critical", True
    elif any(keyword in text for keyword in BILLING_KEYWORDS):
        category, priority, requires_review = "Billing", "Medium", False
    elif any(keyword in text for keyword in TECHNICAL_KEYWORDS):
        category, priority, requires_review = "Technical", "Medium", False
    else:
        category, priority, requires_review = "General", "Low", False

    return {
        "category": category,
        "priority": priority,
        "summary": subject or message[:80],
        "suggested_reply": (
            "Thank you for reaching out. We've received your message and a member "
            "of our team will follow up with you shortly."
        ),
        "requires_human_review": requires_review,
    }


def process_ticket(customer_name: str, subject: str, message: str) -> TicketDecision:
    ticket_id = str(uuid.uuid4())[:8]
    logger.info(f"Ticket {ticket_id} received from {customer_name}: '{subject}'")

    try:
        decision_data = _call_llm(subject, message)
        decision_source = "llm"
    except Exception as error:
        logger.warning(
            f"Ticket {ticket_id}: LLM decision failed ({error}), using rule-based fallback"
        )
        decision_data = _rule_based_fallback(subject, message)
        decision_source = "rule_based_fallback"

    department = DEPARTMENT_MAP.get(decision_data["category"], "General Support")

    decision = TicketDecision(
        ticket_id=ticket_id,
        category=decision_data["category"],
        priority=decision_data["priority"],
        department=department,
        summary=decision_data["summary"],
        suggested_reply=decision_data["suggested_reply"],
        requires_human_review=decision_data["requires_human_review"],
        decision_source=decision_source,
    )

    logger.info(
        f"Ticket {ticket_id} routed to {department} | priority={decision.priority} "
        f"| source={decision_source} | human_review={decision.requires_human_review}"
    )

    return decision
