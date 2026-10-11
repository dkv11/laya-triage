from pathlib import Path

import sqlite3
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator

from app.db import init_db, get_decision, list_decisions, save_feedback
from app.laya_model import get_router
from app.triage import triage

app = FastAPI(title="Laya", description="Maintenance triage copilot for IoT plants")
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


init_db()
get_router()  # load Laya once at startup, so the first request isn't slow



class TriageRequest(BaseModel):
    text: str = Field(min_length=2, examples=["motor se jalne ki smell aa rahi hai"])
    at_time: str = Field(examples=["2026-10-10 08:10:00"])
    operator_name: str | None = Field(default=None, examples=["Ramesh"])

class FeedbackRequest(BaseModel):
    is_correct: bool
    correct_team: Literal["mechanical", "electrical", "instrumentation", "unknown"] | None = None
    correct_issue_type: Literal["routine", "corrective", "emergency"] | None = None
    correct_priority: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = None
    corrected_by: str | None = Field(default=None, examples=["Suresh (electrical)"])

    @model_validator(mode="after")
    def wrong_needs_a_correction(self):
        if not self.is_correct and not (self.correct_team or self.correct_issue_type or self.correct_priority):
            raise ValueError("if the decision is wrong, give at least one correction")
        return self

@app.get("/", include_in_schema=False)
def home():
    """The chat page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    """Quick check that the server is running."""
    return {"status": "ok"}


@app.post("/triage")
def triage_endpoint(req: TriageRequest):
    """Send an operator message; get back Laya's decision."""
    try:
        return triage(req.text, req.at_time, req.operator_name)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"AI model gave an invalid answer: {e}")

@app.get("/decisions")
def decisions_endpoint(limit: int = Query(default=20, ge=1, le=100)):
    """Latest decisions, newest first, with feedback if given."""
    return list_decisions(limit)


@app.post("/decisions/{decision_id}/feedback")
def feedback_endpoint(decision_id: int, req: FeedbackRequest):
    """An engineer confirms or corrects a decision. This becomes training data."""
    if get_decision(decision_id) is None:
        raise HTTPException(status_code=404, detail=f"decision {decision_id} not found")
    try:
        feedback_id = save_feedback(decision_id, **req.model_dump())
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="feedback already given for this decision")
    return {"feedback_id": feedback_id, "decision_id": decision_id}
