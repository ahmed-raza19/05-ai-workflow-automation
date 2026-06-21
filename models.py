from typing import List, Optional

from pydantic import BaseModel, Field


class TicketRequest(BaseModel):
    customer_name: str
    subject: str
    message: str = Field(..., min_length=1)


class TicketDecision(BaseModel):
    ticket_id: str
    category: str
    priority: str
    department: str
    summary: str
    suggested_reply: str
    requires_human_review: bool
    decision_source: str


class WorkflowError(BaseModel):
    ticket_id: str
    error: str
