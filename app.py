import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from logger_config import logger
from models import TicketDecision, TicketRequest
from workflow import process_ticket

load_dotenv()

app = FastAPI(
    title="AI Workflow Automation System",
    description="End-to-end customer support ticket triage and routing automation.",
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    return FileResponse("templates/index.html")


@app.get("/status")
def status():
    return {
        "status": "ok",
        "workflow": "support_ticket_triage",
        "llm_available": bool(os.getenv("GROQ_API_KEY")),
    }


@app.post("/submit-ticket", response_model=TicketDecision)
def submit_ticket(ticket: TicketRequest):
    try:
        return process_ticket(ticket.customer_name, ticket.subject, ticket.message)
    except Exception as error:
        logger.error(f"Unhandled error while processing ticket: {error}")
        raise HTTPException(status_code=500, detail="Failed to process ticket.")
