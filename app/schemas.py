from datetime import datetime
from pydantic import BaseModel, Field


class Citation(BaseModel):
    chunk_id: int
    source: str
    section: str | None = None
    page_number: int | None = None
    quote: str


class ActionItem(BaseModel):
    action: str
    owner: str | None = None
    deadline: str | None = None
    priority: str | None = None
    evidence: str
    source: str


class Risk(BaseModel):
    category: str
    description: str
    evidence: str
    source: str


class MissingInformation(BaseModel):
    missing: str
    why_it_matters: str
    evidence: str


class Contradiction(BaseModel):
    statement_a: str
    statement_b: str
    assessment: str
    explanation: str


class DocumentAnalysisSchema(BaseModel):
    executive_summary: str
    key_points: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    missing_information: list[MissingInformation] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)


class EditSuggestion(BaseModel):
    original_text: str
    suggested_text: str
    operation: str
    explanation: str


class QuestionAnswer(BaseModel):
    answer: str
    evidence: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    confidence: str


class DocumentSummary(BaseModel):
    id: int
    title: str
    file_type: str
    version: int
    updated_at: datetime
