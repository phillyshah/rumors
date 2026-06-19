import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _get_client():
    from app.config import settings
    if not settings.anthropic_api_key:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=settings.anthropic_api_key)
    except ImportError:
        logger.warning("anthropic package not installed")
        return None


async def claude_extract(raw_text: str, topic_list: list[str]) -> dict:
    """Async-compatible wrapper — runs sync Anthropic call in a thread pool in production.
    Returns empty dict if API key not set or on any error."""
    from app.config import settings
    client = _get_client()
    if not client:
        logger.debug("Skipping Claude extraction: no API key configured")
        return {}
    try:
        msg = client.messages.create(
            model=settings.extraction_model,
            max_tokens=1024,
            system=(
                "Extract structured field-intel tags from a sales rep's note about the "
                "orthopedic device industry. Return ONLY a JSON object, no prose, no markdown. "
                f"`topics` must be a subset of: {topic_list}. "
                "Keys: competitors[], distributors[], states[] (2-letter codes), regions[] "
                "(only from: Northeast, Southeast, Midwest, Southwest, West), "
                "geo_scope ('state'|'region'|'national' — use 'national' if no location implied), "
                "topics[], entities[] (list of strings: people or account names), "
                "source_confidence ('high'|'medium'|'low'), summary (1 sentence, max 120 chars)."
            ),
            messages=[{"role": "user", "content": raw_text}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"Claude extraction failed: {e}")
        return {}


async def claude_synthesize(notes: list[dict], query: str) -> str:
    """Generate a 2-3 sentence narrative summary of matching notes."""
    from app.config import settings
    client = _get_client()
    if not client:
        return ""
    try:
        notes_text = "\n\n".join(
            f"[{n.get('created_at', '')}] {n.get('raw_text', '')}"
            for n in notes[:10]
        )
        msg = client.messages.create(
            model=settings.synthesis_model,
            max_tokens=512,
            system=(
                "You are summarizing field intelligence for an orthopedic sales rep. "
                "Write a 2-3 sentence narrative summary of what the team has heard, "
                "based only on the notes provided. Be factual and neutral. "
                "Do not invent details not present in the notes."
            ),
            messages=[{
                "role": "user",
                "content": f"Query: {query}\n\nNotes:\n{notes_text}\n\nSummarize what the team has heard.",
            }],
        )
        return "".join(b.text for b in msg.content if b.type == "text")
    except Exception as e:
        logger.error(f"Claude synthesis failed: {e}")
        return ""


async def enrich_note_background(
    note_id: int,
    raw_text: str,
    topic_list: list[str],
    pool,
) -> None:
    """Background task: run Claude extraction and merge results into the note row."""
    result = await claude_extract(raw_text, topic_list)
    if not result:
        return

    entities_json = json.dumps(result.get("entities", []))
    competitors = result.get("competitors", [])
    distributors = result.get("distributors", [])
    topics = result.get("topics", [])
    summary = result.get("summary")

    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE notes SET
              competitors = (
                SELECT array_agg(DISTINCT e ORDER BY e)
                FROM unnest(competitors || $2::text[]) AS t(e)
              ),
              distributors = (
                SELECT array_agg(DISTINCT e ORDER BY e)
                FROM unnest(distributors || $3::text[]) AS t(e)
              ),
              topics = (
                SELECT array_agg(DISTINCT e ORDER BY e)
                FROM unnest(topics || $4::text[]) AS t(e)
              ),
              entities = $5::jsonb,
              summary = COALESCE($6, summary),
              extraction_method = 'hybrid',
              enriched_at = now()
            WHERE id = $1
            """,
            note_id,
            competitors,
            distributors,
            topics,
            entities_json,
            summary,
        )
