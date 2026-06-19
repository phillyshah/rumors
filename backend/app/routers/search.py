import json
import re
from typing import Optional

from fastapi import APIRouter, Request

from app.models.note import NoteResponse, SearchResponse

router = APIRouter(tags=["search"])


def _row_to_note(row) -> dict:
    d = dict(row)
    if isinstance(d.get("entities"), str):
        d["entities"] = json.loads(d["entities"])
    return d


def _parse_query_for_filters(q: str, gz) -> dict:
    """Detect gazetteer matches in a free-text query and return structured filters."""
    filters = {"competitors": [], "states": [], "regions": []}
    if not q:
        return filters
    norm = q.lower()
    tokens = re.findall(r"\b\w+\b", norm)
    norm_q = norm

    for alias, canonical in gz.competitors.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", norm_q):
            filters["competitors"].append(canonical)

    for code in gz.states:
        if re.search(r"\b" + re.escape(code) + r"\b", q):
            filters["states"].append(code)

    for name, code in gz.state_names.items():
        if re.search(r"\b" + re.escape(name) + r"\b", norm_q):
            if code not in filters["states"]:
                filters["states"].append(code)

    for metro_alias, state_code in gz.metros.items():
        if re.search(r"\b" + re.escape(metro_alias) + r"\b", norm_q):
            if state_code not in filters["states"]:
                filters["states"].append(state_code)

    for region_alias, canonical_region in gz.regions.items():
        if re.search(r"\b" + re.escape(region_alias) + r"\b", norm_q):
            filters["regions"].append(canonical_region)

    # Roll up states to regions
    for code in filters["states"]:
        region = gz.states.get(code)
        if region and region not in filters["regions"]:
            filters["regions"].append(region)

    return filters


@router.get("/search", response_model=SearchResponse)
async def search(
    request: Request,
    q: Optional[str] = None,
    state: Optional[str] = None,
    region: Optional[str] = None,
    scope: Optional[str] = None,
    competitor: Optional[str] = None,
    topic: Optional[str] = None,
    synthesize: bool = False,
    limit: int = 20,
    offset: int = 0,
):
    pool = request.app.state.db
    gz = request.app.state.gazetteers

    # Parse q for implicit filters
    q_filters = _parse_query_for_filters(q or "", gz)

    # Merge explicit params with q-derived filters
    competitor_filter = [competitor] if competitor else q_filters["competitors"]
    state_filter = [state.upper()] if state else q_filters["states"]
    region_filter = [region] if region else q_filters["regions"]

    # Separate WHERE params from the ORDER BY q param to keep count query clean.
    where_conditions = []
    where_params: list = []
    widx = 1

    has_structured = bool(competitor_filter or state_filter or region_filter or scope or topic)

    if q and not has_structured:
        # Use FTS as a WHERE filter only when there are no structured filters
        where_conditions.append(f"search_vector @@ plainto_tsquery('english', ${widx})")
        where_params.append(q)
        widx += 1

    if competitor_filter:
        where_conditions.append(f"competitors && ${widx}::text[]")
        where_params.append(competitor_filter)
        widx += 1

    if topic:
        where_conditions.append(f"topics @> ${widx}::text[]")
        where_params.append([topic])
        widx += 1

    if state_filter:
        where_conditions.append(f"states && ${widx}::text[]")
        where_params.append(state_filter)
        widx += 1

    if region_filter:
        # Include region-tagged notes AND national notes (relevant everywhere)
        where_conditions.append(
            f"(regions && ${widx}::text[] OR geo_scope = 'national')"
        )
        where_params.append(region_filter)
        widx += 1

    if scope:
        where_conditions.append(f"geo_scope = ${widx}")
        where_params.append(scope)
        widx += 1

    where = ("WHERE " + " AND ".join(where_conditions)) if where_conditions else ""

    # ORDER BY: use FTS ranking when q provided (embed literal tsquery to avoid param type issues)
    if q:
        safe_q = q.replace("'", "''")
        order = f"ts_rank_cd(search_vector, plainto_tsquery('english', '{safe_q}')) DESC, created_at DESC"
    else:
        order = "created_at DESC"

    # Pagination params appended after WHERE params
    paginate_params = list(where_params) + [limit, offset]

    query = f"""
        SELECT id, raw_text, created_at, competitors, distributors, regions,
               states, geo_scope, topics, entities, source_confidence,
               summary, extraction_method, enriched_at
        FROM notes
        {where}
        ORDER BY {order}
        LIMIT ${widx} OFFSET ${widx + 1}
    """
    count_query = f"SELECT count(*) FROM notes {where}"

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *paginate_params)
        total = await conn.fetchval(count_query, *where_params)

    notes = [NoteResponse(**_row_to_note(r)) for r in rows]

    synthesis = None
    if synthesize and notes:
        from app.claude.client import claude_synthesize
        synthesis = await claude_synthesize(
            [{"raw_text": n.raw_text, "created_at": str(n.created_at)} for n in notes],
            q or (competitor or "") + " " + (region or ""),
        )

    return SearchResponse(notes=notes, synthesis=synthesis, total=total)
