import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Gazetteers:
    competitors: dict[str, str]    # alias (lower) -> canonical
    distributors: dict[str, str]   # alias (lower) -> canonical
    states: dict[str, str]         # state code (upper) -> region
    state_names: dict[str, str]    # state name (lower) -> state code
    metros: dict[str, str]         # metro alias (lower) -> state code
    regions: dict[str, str]        # region alias (lower) -> canonical
    topics: dict[str, set[str]]    # topic -> set of keywords (lower)


@dataclass
class ExtractionResult:
    competitors: list[str] = field(default_factory=list)
    distributors: list[str] = field(default_factory=list)
    states: list[str] = field(default_factory=list)
    regions: list[str] = field(default_factory=list)
    geo_scope: str = "national"
    topics: list[str] = field(default_factory=list)
    entities: list[dict] = field(default_factory=list)
    source_confidence: str = "medium"
    coverage_thin: bool = False


def _word_boundary_search(pattern: str, text: str) -> bool:
    return bool(re.search(r"\b" + re.escape(pattern) + r"\b", text))


def extract(raw_text: str, gz: Gazetteers) -> ExtractionResult:
    """Pure extraction function. No DB calls — gazetteers are passed in."""
    result = ExtractionResult()
    norm = raw_text.lower()
    tokens = re.findall(r"\b\w+\b", norm)

    # --- 1. Competitor exact matching ---
    found_competitors: set[str] = set()
    for alias, canonical in gz.competitors.items():
        if _word_boundary_search(alias, norm):
            found_competitors.add(canonical)

    # --- 2. Competitor fuzzy/phonetic fallback ---
    if not found_competitors:
        from app.extractor.fuzzy import fuzzy_match_gazetteer
        fuzzy_hits = fuzzy_match_gazetteer(tokens, gz.competitors)
        found_competitors.update(fuzzy_hits)

    result.competitors = sorted(found_competitors)

    # --- 3. Distributor exact matching (+ fuzzy if empty) ---
    found_distributors: set[str] = set()
    for alias, canonical in gz.distributors.items():
        if _word_boundary_search(alias, norm):
            found_distributors.add(canonical)

    if not found_distributors and gz.distributors:
        from app.extractor.fuzzy import fuzzy_match_gazetteer
        found_distributors.update(fuzzy_match_gazetteer(tokens, gz.distributors))

    result.distributors = sorted(found_distributors)

    # --- 4. Geography ---
    found_states: set[str] = set()
    found_regions: set[str] = set()

    # 4a. State codes: require bare uppercase 2-letter token in ORIGINAL text
    for code in gz.states:
        if re.search(r"\b" + re.escape(code) + r"\b", raw_text):
            found_states.add(code)

    # 4b. State full names (lowercase)
    for name, code in gz.state_names.items():
        if _word_boundary_search(name, norm):
            found_states.add(code)

    # 4c. Metro aliases -> state
    for metro_alias, state_code in gz.metros.items():
        if _word_boundary_search(metro_alias, norm):
            found_states.add(state_code)

    # 4d. Direct region name/alias match
    for region_alias, canonical_region in gz.regions.items():
        if _word_boundary_search(region_alias, norm):
            found_regions.add(canonical_region)

    # 4e. Roll up states to regions
    for code in found_states:
        region = gz.states.get(code)
        if region:
            found_regions.add(region)

    result.states = sorted(found_states)
    result.regions = sorted(found_regions)

    # Set geo_scope (most-specific wins)
    if found_states:
        result.geo_scope = "state"
    elif found_regions:
        result.geo_scope = "region"
    else:
        result.geo_scope = "national"

    # --- 5. Topic classification ---
    found_topics: set[str] = set()
    for topic, keywords in gz.topics.items():
        for kw in keywords:
            # For keywords >= 5 chars, allow common inflections (plural, past tense, etc.)
            # For short keywords, require exact word boundaries to avoid false positives
            if len(kw) >= 5:
                pattern = r"\b" + re.escape(kw)
            else:
                pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, norm):
                found_topics.add(topic)
                break

    if not found_topics:
        found_topics.add("other")
    result.topics = sorted(found_topics)

    # --- 6. Source confidence ---
    hedge_phrases = [
        "heard", "rumor", "supposedly", "maybe", "i think",
        "someone said", "apparently", "allegedly", "not sure",
    ]
    firm_phrases = [
        "confirmed", "saw", "signed", "official", "i was there",
        "verified", "directly told",
    ]
    has_hedge = any(_word_boundary_search(w, norm) for w in hedge_phrases)
    has_firm = any(_word_boundary_search(w, norm) for w in firm_phrases)

    if has_hedge and not has_firm:
        result.source_confidence = "low"
    elif has_firm and not has_hedge:
        result.source_confidence = "high"
    else:
        result.source_confidence = "medium"

    # --- 7. Coverage thin flag ---
    only_other = result.topics == ["other"]
    no_entities = not result.competitors and not result.distributors
    long_note = len(raw_text) > 280
    matched_field_count = sum([
        bool(result.competitors),
        bool(result.distributors),
        not only_other,
    ])
    result.coverage_thin = (no_entities and only_other) or (long_note and matched_field_count <= 1)

    return result
