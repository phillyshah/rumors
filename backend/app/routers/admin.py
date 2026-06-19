from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from typing import Optional
from app.auth import get_current_user_id

router = APIRouter(tags=["admin"])


async def require_admin(request: Request, user_id: int = Depends(get_current_user_id)) -> int:
    pool = request.app.state.db
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT is_admin FROM users WHERE id = $1", user_id)
    if not row or not row["is_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user_id


class CompetitorCreate(BaseModel):
    canonical: str
    aliases: list[str] = []


class CompetitorUpdate(BaseModel):
    canonical: Optional[str] = None
    aliases: Optional[list[str]] = None
    active: Optional[bool] = None


class DistributorCreate(BaseModel):
    canonical: str
    aliases: list[str] = []
    region: Optional[str] = None


class TopicKeywordCreate(BaseModel):
    topic: str
    keyword: str


def _invalidate_gazetteer(request: Request):
    """Force reload of gazetteers on next request."""
    request.app.state.gazetteers_dirty = True


# ── Competitors ───────────────────────────────────────────────────────────────

@router.get("/competitors")
async def list_competitors(request: Request, _=Depends(require_admin)):
    pool = request.app.state.db
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, canonical, aliases, active FROM competitors ORDER BY canonical")
    return [dict(r) for r in rows]


@router.post("/competitors", status_code=201)
async def create_competitor(body: CompetitorCreate, request: Request, _=Depends(require_admin)):
    pool = request.app.state.db
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO competitors (canonical, aliases) VALUES ($1, $2) RETURNING id, canonical, aliases, active",
            body.canonical, [a.lower() for a in body.aliases],
        )
    _invalidate_gazetteer(request)
    return dict(row)


@router.patch("/competitors/{comp_id}")
async def update_competitor(comp_id: int, body: CompetitorUpdate, request: Request, _=Depends(require_admin)):
    pool = request.app.state.db
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM competitors WHERE id = $1", comp_id)
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        canonical = body.canonical if body.canonical is not None else row["canonical"]
        aliases = [a.lower() for a in body.aliases] if body.aliases is not None else list(row["aliases"])
        active = body.active if body.active is not None else row["active"]
        updated = await conn.fetchrow(
            "UPDATE competitors SET canonical=$1, aliases=$2, active=$3 WHERE id=$4 RETURNING id, canonical, aliases, active",
            canonical, aliases, active, comp_id,
        )
    _invalidate_gazetteer(request)
    return dict(updated)


@router.delete("/competitors/{comp_id}", status_code=204)
async def delete_competitor(comp_id: int, request: Request, _=Depends(require_admin)):
    pool = request.app.state.db
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM competitors WHERE id = $1", comp_id)
    _invalidate_gazetteer(request)


# ── Distributors ──────────────────────────────────────────────────────────────

@router.get("/distributors")
async def list_distributors(request: Request, _=Depends(require_admin)):
    pool = request.app.state.db
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, canonical, aliases, region, active FROM distributors ORDER BY canonical")
    return [dict(r) for r in rows]


@router.post("/distributors", status_code=201)
async def create_distributor(body: DistributorCreate, request: Request, _=Depends(require_admin)):
    pool = request.app.state.db
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO distributors (canonical, aliases, region) VALUES ($1, $2, $3) RETURNING id, canonical, aliases, region, active",
            body.canonical, [a.lower() for a in body.aliases], body.region,
        )
    _invalidate_gazetteer(request)
    return dict(row)


@router.delete("/distributors/{dist_id}", status_code=204)
async def delete_distributor(dist_id: int, request: Request, _=Depends(require_admin)):
    pool = request.app.state.db
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM distributors WHERE id = $1", dist_id)
    _invalidate_gazetteer(request)


# ── Topics ────────────────────────────────────────────────────────────────────

@router.get("/topics")
async def list_topics(request: Request, _=Depends(require_admin)):
    pool = request.app.state.db
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT topic, keyword FROM topic_keywords ORDER BY topic, keyword")
    return [dict(r) for r in rows]


@router.post("/topics", status_code=201)
async def create_topic_keyword(body: TopicKeywordCreate, request: Request, _=Depends(require_admin)):
    pool = request.app.state.db
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO topic_keywords (topic, keyword) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            body.topic, body.keyword.lower(),
        )
    _invalidate_gazetteer(request)
    return {"topic": body.topic, "keyword": body.keyword.lower()}


@router.delete("/topics/{topic}/{keyword}", status_code=204)
async def delete_topic_keyword(topic: str, keyword: str, request: Request, _=Depends(require_admin)):
    pool = request.app.state.db
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM topic_keywords WHERE topic = $1 AND keyword = $2", topic, keyword)
    _invalidate_gazetteer(request)
