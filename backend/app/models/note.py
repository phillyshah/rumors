from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NoteCreate(BaseModel):
    raw_text: str


class NoteResponse(BaseModel):
    id: int
    raw_text: str
    created_at: datetime
    competitors: list[str]
    distributors: list[str]
    regions: list[str]
    states: list[str]
    geo_scope: str
    topics: list[str]
    entities: list[dict]
    source_confidence: Optional[str]
    summary: Optional[str]
    extraction_method: str
    enriched_at: Optional[datetime]


class NoteDetailResponse(NoteResponse):
    author_display_name: str


class SearchResponse(BaseModel):
    notes: list[NoteResponse]
    synthesis: Optional[str] = None
    total: int
