import json
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from app.auth import get_current_user_id
from app.extractor.pipeline import extract
from app.models.note import NoteCreate, NoteDetailResponse, NoteResponse

router = APIRouter(tags=["notes"])


def _row_to_note(row) -> dict:
    d = dict(row)
    if isinstance(d.get("entities"), str):
        d["entities"] = json.loads(d["entities"])
    return d


@router.post("/notes", response_model=NoteResponse, status_code=201)
async def create_note(
    body: NoteCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    user_id: int = Depends(get_current_user_id),
):
    pool = request.app.state.db
    gz = request.app.state.gazetteers

    result = extract(body.raw_text, gz)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO notes (
                 author_id, raw_text, competitors, distributors, regions, states,
                 geo_scope, topics, source_confidence, extraction_method
               ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
               RETURNING id, raw_text, created_at, competitors, distributors,
                         regions, states, geo_scope, topics, entities,
                         source_confidence, summary, extraction_method, enriched_at""",
            user_id,
            body.raw_text,
            result.competitors,
            result.distributors,
            result.regions,
            result.states,
            result.geo_scope,
            result.topics,
            result.source_confidence,
            "deterministic",
        )

    note = _row_to_note(row)

    if result.coverage_thin:
        topic_list = list(gz.topics.keys())
        from app.claude.client import enrich_note_background
        background_tasks.add_task(
            enrich_note_background, note["id"], body.raw_text, topic_list, pool
        )

    return NoteResponse(**note)


@router.get("/feed", response_model=list[NoteResponse])
async def feed(request: Request, limit: int = 20, offset: int = 0):
    pool = request.app.state.db
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT id, raw_text, created_at, competitors, distributors, regions,
                      states, geo_scope, topics, entities, source_confidence,
                      summary, extraction_method, enriched_at
               FROM notes
               ORDER BY created_at DESC
               LIMIT $1 OFFSET $2""",
            limit, offset,
        )
    return [NoteResponse(**_row_to_note(r)) for r in rows]


@router.get("/notes/{note_id}", response_model=NoteDetailResponse)
async def get_note(note_id: int, request: Request, user_id: int = Depends(get_current_user_id)):
    pool = request.app.state.db
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT n.id, n.raw_text, n.created_at, n.competitors, n.distributors,
                      n.regions, n.states, n.geo_scope, n.topics, n.entities,
                      n.source_confidence, n.summary, n.extraction_method, n.enriched_at,
                      u.display_name AS author_display_name
               FROM notes n
               JOIN users u ON u.id = n.author_id
               WHERE n.id = $1""",
            note_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail="Note not found")
    d = _row_to_note(row)
    return NoteDetailResponse(**d)
