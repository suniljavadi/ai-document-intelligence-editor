import difflib
import json
import logging
import uuid
from pathlib import Path
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.ai import MockLLMProvider, analyze_text
from app.core.config import settings
from app.core.db import Base, engine, get_db
from app.document_processing.parsers import DocumentParser, chunk_text
from app.models import Document, DocumentAnalysis, DocumentChunk, DocumentVersion
from app.schemas import DocumentAnalysisSchema, DocumentSummary, EditSuggestion, QuestionAnswer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(title=settings.app_name, version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
Base.metadata.create_all(bind=engine)
parser = DocumentParser()
llm = MockLLMProvider()


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class EditRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)
    operation: str = Field(pattern="^(improve|professional|shorten|expand|bullets|summarize|heading|explain)$")


class VersionRequest(BaseModel):
    content: str = Field(min_length=1)
    change_summary: str = Field(default="User edit", max_length=500)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.app_name, "llm_provider": settings.llm_provider}


@app.post("/api/v1/documents/upload", response_model=DocumentSummary)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    data = await file.read()
    limit = settings.max_upload_size_mb * 1024 * 1024
    if len(data) > limit:
        raise HTTPException(413, f"File exceeds {settings.max_upload_size_mb} MB limit")
    try:
        content = parser.parse(file.filename or "document.txt", data)
    except Exception as exc:
        raise HTTPException(400, f"Could not parse document: {exc}") from exc
    if not content.strip():
        raise HTTPException(400, "Document contains no extractable text")
    title = Path(file.filename or "document").stem
    document = Document(title=title, file_type=Path(file.filename or "").suffix.lower().lstrip(".") or "txt")
    db.add(document)
    db.flush()
    db.add(DocumentVersion(document_id=document.id, version_number=1, content=content))
    for index, text in enumerate(chunk_text(content)):
        db.add(DocumentChunk(document_id=document.id, chunk_index=index, text=text, section=None, page_number=None))
    db.commit()
    return DocumentSummary(id=document.id, title=document.title, file_type=document.file_type, version=1, updated_at=document.updated_at)


def get_document(document_id: int, db: Session) -> Document:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(404, "Document not found")
    return document


@app.get("/api/v1/documents", response_model=list[DocumentSummary])
def list_documents(db: Session = Depends(get_db)):
    documents = db.scalars(select(Document).order_by(Document.updated_at.desc())).all()
    return [DocumentSummary(id=d.id, title=d.title, file_type=d.file_type, version=len(d.versions), updated_at=d.updated_at) for d in documents]


@app.get("/api/v1/documents/{document_id}")
def document_detail(document_id: int, db: Session = Depends(get_db)):
    document = get_document(document_id, db)
    version = document.versions[-1]
    return {"id": document.id, "title": document.title, "file_type": document.file_type, "content": version.content, "version": version.version_number, "chunks": len(document.chunks)}


@app.post("/api/v1/documents/{document_id}/analyze", response_model=DocumentAnalysisSchema)
def analyze_document(document_id: int, db: Session = Depends(get_db)):
    document = get_document(document_id, db)
    result = analyze_text(document.versions[-1].content)
    existing = db.scalar(select(DocumentAnalysis).where(DocumentAnalysis.document_id == document_id))
    payload = result.model_dump_json()
    if existing:
        existing.payload = payload
    else:
        db.add(DocumentAnalysis(document_id=document_id, payload=payload))
    db.commit()
    return result


@app.get("/api/v1/documents/{document_id}/analysis", response_model=DocumentAnalysisSchema)
def get_analysis(document_id: int, db: Session = Depends(get_db)):
    get_document(document_id, db)
    analysis = db.scalar(select(DocumentAnalysis).where(DocumentAnalysis.document_id == document_id))
    if not analysis:
        raise HTTPException(404, "Document has not been analyzed")
    return DocumentAnalysisSchema.model_validate_json(analysis.payload)


@app.post("/api/v1/documents/{document_id}/ask", response_model=QuestionAnswer)
def ask_document(document_id: int, request: AskRequest, db: Session = Depends(get_db)):
    document = get_document(document_id, db)
    chunks = [(c.id, c.text, c.section, c.page_number) for c in document.chunks]
    return llm.answer(request.question, chunks)


@app.post("/api/v1/documents/{document_id}/edit", response_model=EditSuggestion)
def edit_document(document_id: int, request: EditRequest, db: Session = Depends(get_db)):
    get_document(document_id, db)
    return llm.edit(request.text, request.operation)


@app.get("/api/v1/documents/{document_id}/versions")
def versions(document_id: int, db: Session = Depends(get_db)):
    document = get_document(document_id, db)
    return [{"id": v.id, "version_number": v.version_number, "content": v.content, "change_summary": v.change_summary, "created_at": v.created_at} for v in document.versions]


@app.post("/api/v1/documents/{document_id}/versions")
def create_version(document_id: int, request: VersionRequest, db: Session = Depends(get_db)):
    document = get_document(document_id, db)
    version = DocumentVersion(document_id=document_id, version_number=len(document.versions) + 1, content=request.content, change_summary=request.change_summary)
    db.add(version)
    db.commit()
    return {"version_number": version.version_number, "change_summary": version.change_summary}


@app.post("/api/v1/documents/{document_id}/compare")
def compare_versions(document_id: int, from_version: int, to_version: int, db: Session = Depends(get_db)):
    document = get_document(document_id, db)
    versions_by_number = {v.version_number: v for v in document.versions}
    if from_version not in versions_by_number or to_version not in versions_by_number:
        raise HTTPException(404, "Version not found")
    old = versions_by_number[from_version].content.splitlines()
    new = versions_by_number[to_version].content.splitlines()
    diff = list(difflib.unified_diff(old, new, fromfile=f"version-{from_version}", tofile=f"version-{to_version}", lineterm=""))
    return {"from_version": from_version, "to_version": to_version, "added": [line[1:] for line in diff if line.startswith("+") and not line.startswith("+++")], "removed": [line[1:] for line in diff if line.startswith("-") and not line.startswith("---")], "diff": diff}
