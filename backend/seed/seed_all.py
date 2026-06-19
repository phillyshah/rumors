"""Idempotent seed script. Run: python -m seed.seed_all"""
import asyncio
import json
import os
import sys
from pathlib import Path

import asyncpg
import bcrypt as _bcrypt

DATA_DIR = Path(__file__).parent / "data"
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/rumors")


async def seed(conn: asyncpg.Connection) -> None:
    # Competitors
    competitors = json.loads((DATA_DIR / "competitors.json").read_text())
    for c in competitors:
        await conn.execute(
            """INSERT INTO competitors (canonical, aliases)
               VALUES ($1, $2)
               ON CONFLICT (canonical) DO UPDATE SET aliases = EXCLUDED.aliases""",
            c["canonical"], c["aliases"]
        )
    print(f"Seeded {len(competitors)} competitors")

    # Geo states
    states = json.loads((DATA_DIR / "geo_states.json").read_text())
    for s in states:
        await conn.execute(
            """INSERT INTO geo_states (code, name, region)
               VALUES ($1, $2, $3)
               ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, region = EXCLUDED.region""",
            s["code"], s["name"], s["region"]
        )
    print(f"Seeded {len(states)} states")

    # Geo regions
    regions = json.loads((DATA_DIR / "geo_regions.json").read_text())
    for r in regions:
        await conn.execute(
            """INSERT INTO geo_regions (canonical, aliases)
               VALUES ($1, $2)
               ON CONFLICT (canonical) DO UPDATE SET aliases = EXCLUDED.aliases""",
            r["canonical"], r["aliases"]
        )
    print(f"Seeded {len(regions)} regions")

    # Geo metros
    metros = json.loads((DATA_DIR / "geo_metros.json").read_text())
    for m in metros:
        await conn.execute(
            """INSERT INTO geo_metros (alias, state_code)
               VALUES ($1, $2)
               ON CONFLICT (alias) DO UPDATE SET state_code = EXCLUDED.state_code""",
            m["alias"], m["state_code"]
        )
    print(f"Seeded {len(metros)} metros")

    # Topic keywords
    topics = json.loads((DATA_DIR / "topic_keywords.json").read_text())
    for t in topics:
        for kw in t["keywords"]:
            await conn.execute(
                """INSERT INTO topic_keywords (topic, keyword)
                   VALUES ($1, $2)
                   ON CONFLICT (topic, keyword) DO NOTHING""",
                t["topic"], kw
            )
    total_kw = sum(len(t["keywords"]) for t in topics)
    print(f"Seeded {total_kw} topic keywords across {len(topics)} topics")

    # Test users
    test_users = [
        {
            "email": "admin@fieldintel.internal",
            "display_name": "Admin User",
            "password": "admin123",
            "is_admin": True,
        },
        {
            "email": "rep1@fieldintel.internal",
            "display_name": "Alex Johnson",
            "password": "rep123",
            "is_admin": False,
        },
        {
            "email": "rep2@fieldintel.internal",
            "display_name": "Sam Rivera",
            "password": "rep123",
            "is_admin": False,
        },
    ]
    for u in test_users:
        hashed = _bcrypt.hashpw(u["password"].encode(), _bcrypt.gensalt()).decode()
        await conn.execute(
            """INSERT INTO users (email, display_name, hashed_password, is_admin)
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (email) DO UPDATE SET display_name = EXCLUDED.display_name""",
            u["email"], u["display_name"], hashed, u["is_admin"]
        )
    print(f"Seeded {len(test_users)} test users")
    print("\nTest credentials:")
    for u in test_users:
        role = "ADMIN" if u["is_admin"] else "rep"
        print(f"  [{role}] {u['email']} / {u['password']}")


async def main() -> None:
    print(f"Connecting to {DATABASE_URL}")
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await seed(conn)
        print("\nSeed complete.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
