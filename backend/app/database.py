import asyncpg
from app.config import settings
from app.extractor.pipeline import Gazetteers


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(settings.database_url, min_size=2, max_size=10)


async def close_pool(pool: asyncpg.Pool) -> None:
    await pool.close()


async def load_gazetteers(pool: asyncpg.Pool) -> Gazetteers:
    """Load all gazetteer tables into memory for use by extract()."""
    async with pool.acquire() as conn:
        # Competitors: alias -> canonical
        comp_rows = await conn.fetch(
            "SELECT canonical, aliases FROM competitors WHERE active = true"
        )
        competitors: dict[str, str] = {}
        for row in comp_rows:
            for alias in row["aliases"]:
                competitors[alias.lower()] = row["canonical"]

        # Distributors: alias -> canonical
        dist_rows = await conn.fetch(
            "SELECT canonical, aliases FROM distributors WHERE active = true"
        )
        distributors: dict[str, str] = {}
        for row in dist_rows:
            for alias in row["aliases"]:
                distributors[alias.lower()] = row["canonical"]

        # States: code -> region
        state_rows = await conn.fetch("SELECT code, name, region FROM geo_states")
        states: dict[str, str] = {}
        state_names: dict[str, str] = {}
        for row in state_rows:
            states[row["code"].strip()] = row["region"]
            state_names[row["name"].lower()] = row["code"].strip()

        # Metro aliases: alias -> state code
        metro_rows = await conn.fetch("SELECT alias, state_code FROM geo_metros")
        metros: dict[str, str] = {row["alias"].lower(): row["state_code"].strip() for row in metro_rows}

        # Regions: alias -> canonical
        region_rows = await conn.fetch("SELECT canonical, aliases FROM geo_regions")
        regions: dict[str, str] = {}
        for row in region_rows:
            regions[row["canonical"].lower()] = row["canonical"]
            for alias in row["aliases"]:
                regions[alias.lower()] = row["canonical"]

        # Topics: topic -> set of keywords
        topic_rows = await conn.fetch("SELECT topic, keyword FROM topic_keywords")
        topics: dict[str, set[str]] = {}
        for row in topic_rows:
            topics.setdefault(row["topic"], set()).add(row["keyword"].lower())

    return Gazetteers(
        competitors=competitors,
        distributors=distributors,
        states=states,
        state_names=state_names,
        metros=metros,
        regions=regions,
        topics=topics,
    )
