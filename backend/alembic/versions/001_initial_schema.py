"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-19
"""

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op


def upgrade() -> None:
    op.execute("""
    CREATE TABLE users (
      id              BIGSERIAL PRIMARY KEY,
      email           TEXT UNIQUE NOT NULL,
      display_name    TEXT NOT NULL,
      hashed_password TEXT NOT NULL,
      region          TEXT,
      is_admin        BOOLEAN NOT NULL DEFAULT false,
      created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """)

    op.execute("""
    CREATE TABLE competitors (
      id        BIGSERIAL PRIMARY KEY,
      canonical TEXT UNIQUE NOT NULL,
      aliases   TEXT[] NOT NULL DEFAULT '{}',
      active    BOOLEAN NOT NULL DEFAULT true
    )
    """)

    op.execute("""
    CREATE TABLE distributors (
      id        BIGSERIAL PRIMARY KEY,
      canonical TEXT UNIQUE NOT NULL,
      aliases   TEXT[] NOT NULL DEFAULT '{}',
      region    TEXT,
      active    BOOLEAN NOT NULL DEFAULT true
    )
    """)

    op.execute("""
    CREATE TABLE geo_states (
      code   CHAR(2) PRIMARY KEY,
      name   TEXT NOT NULL,
      region TEXT NOT NULL
    )
    """)

    op.execute("""
    CREATE TABLE geo_regions (
      canonical TEXT PRIMARY KEY,
      aliases   TEXT[] NOT NULL DEFAULT '{}'
    )
    """)

    op.execute("""
    CREATE TABLE geo_metros (
      alias      TEXT PRIMARY KEY,
      state_code CHAR(2) NOT NULL REFERENCES geo_states(code)
    )
    """)

    op.execute("""
    CREATE TABLE topic_keywords (
      topic   TEXT NOT NULL,
      keyword TEXT NOT NULL,
      PRIMARY KEY (topic, keyword)
    )
    """)

    op.execute("""
    CREATE TABLE notes (
      id                BIGSERIAL PRIMARY KEY,
      author_id         BIGINT NOT NULL REFERENCES users(id),
      raw_text          TEXT NOT NULL,
      created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
      competitors       TEXT[] DEFAULT '{}',
      distributors      TEXT[] DEFAULT '{}',
      regions           TEXT[] DEFAULT '{}',
      states            TEXT[] DEFAULT '{}',
      geo_scope         TEXT NOT NULL DEFAULT 'national',
      topics            TEXT[] DEFAULT '{}',
      entities          JSONB DEFAULT '[]',
      source_confidence TEXT,
      summary           TEXT,
      extraction_method TEXT NOT NULL DEFAULT 'deterministic',
      enriched_at       TIMESTAMPTZ,
      search_vector     tsvector
    )
    """)

    # Trigger function to maintain search_vector (array_to_string is STABLE, not IMMUTABLE,
    # so it cannot be used in a GENERATED ALWAYS column — trigger is the correct approach)
    op.execute("""
    CREATE OR REPLACE FUNCTION notes_search_vector_update() RETURNS trigger AS $$
    BEGIN
      NEW.search_vector :=
        setweight(to_tsvector('pg_catalog.english', coalesce(NEW.raw_text, '')), 'A') ||
        setweight(to_tsvector('pg_catalog.english', coalesce(array_to_string(NEW.competitors, ' '), '')), 'B') ||
        setweight(to_tsvector('pg_catalog.english', coalesce(array_to_string(NEW.distributors, ' '), '')), 'B') ||
        setweight(to_tsvector('pg_catalog.english', coalesce(array_to_string(NEW.topics, ' '), '')), 'C') ||
        setweight(to_tsvector('pg_catalog.english', coalesce(array_to_string(NEW.regions, ' '), '')), 'C');
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """)

    op.execute("""
    CREATE TRIGGER notes_search_vector_trigger
    BEFORE INSERT OR UPDATE ON notes
    FOR EACH ROW EXECUTE FUNCTION notes_search_vector_update();
    """)

    op.execute("CREATE INDEX idx_notes_search ON notes USING GIN (search_vector)")
    op.execute("CREATE INDEX idx_notes_competitors ON notes USING GIN (competitors)")
    op.execute("CREATE INDEX idx_notes_states ON notes USING GIN (states)")
    op.execute("CREATE INDEX idx_notes_regions ON notes USING GIN (regions)")
    op.execute("CREATE INDEX idx_notes_scope ON notes (geo_scope)")
    op.execute("CREATE INDEX idx_notes_topics ON notes USING GIN (topics)")
    op.execute("CREATE INDEX idx_notes_created ON notes (created_at DESC)")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS notes_search_vector_trigger ON notes")
    op.execute("DROP FUNCTION IF EXISTS notes_search_vector_update")
    op.execute("DROP TABLE IF EXISTS notes CASCADE")
    op.execute("DROP TABLE IF EXISTS topic_keywords CASCADE")
    op.execute("DROP TABLE IF EXISTS geo_metros CASCADE")
    op.execute("DROP TABLE IF EXISTS geo_regions CASCADE")
    op.execute("DROP TABLE IF EXISTS geo_states CASCADE")
    op.execute("DROP TABLE IF EXISTS distributors CASCADE")
    op.execute("DROP TABLE IF EXISTS competitors CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
