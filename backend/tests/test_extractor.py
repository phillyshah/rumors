"""Unit tests for the deterministic extraction pipeline."""
import pytest
from app.extractor.pipeline import Gazetteers, extract


# ── Competitor exact matching ──────────────────────────────────────────────────

def test_exact_competitor_stryker(gz):
    r = extract("Stryker is cutting prices in FL", gz)
    assert "Stryker" in r.competitors


def test_case_insensitive_competitor(gz):
    r = extract("STRYKER is cutting prices", gz)
    assert "Stryker" in r.competitors


def test_exact_competitor_alias(gz):
    r = extract("heard ZB is losing accounts", gz)
    assert "Zimmer Biomet" in r.competitors


def test_multi_competitor(gz):
    r = extract("Both Stryker and Zimmer Biomet were at the conference", gz)
    assert "Stryker" in r.competitors
    assert "Zimmer Biomet" in r.competitors


def test_no_partial_match(gz):
    # "striker" as part of another word should not match "stryker"
    r = extract("the goalkeeper was a real strikerrr", gz)
    assert "Stryker" not in r.competitors


# ── Fuzzy / phonetic matching ─────────────────────────────────────────────────

def test_typo_stryker(gz):
    r = extract("Striker is poaching our reps in FL", gz)
    assert "Stryker" in r.competitors


def test_typo_depuy(gz):
    r = extract("Depew is dropping prices in Ohio", gz)
    assert "DePuy Synthes" in r.competitors


def test_typo_smith_nephew(gz):
    r = extract("Smith and Nephue is expanding in the Southeast", gz)
    assert "Smith+Nephew" in r.competitors


def test_phonetic_medtronic(gz):
    r = extract("Medtronix is launching a new system", gz)
    assert "Medtronic" in r.competitors


# ── State matching ────────────────────────────────────────────────────────────

def test_state_code_uppercase(gz):
    r = extract("heard something in FL about Stryker", gz)
    assert "FL" in r.states
    assert r.geo_scope == "state"


def test_state_full_name(gz):
    r = extract("this is happening in Florida", gz)
    assert "FL" in r.states


def test_state_rollup_to_region(gz):
    r = extract("Florida account switched to Zimmer", gz)
    assert "FL" in r.states
    assert "Southeast" in r.regions


def test_two_states(gz):
    r = extract("accounts in FL and TX are both switching", gz)
    assert "FL" in r.states
    assert "TX" in r.states
    assert "Southeast" in r.regions
    assert "Southwest" in r.regions


def test_state_code_lowercase_no_match(gz):
    # "in" is lowercase Indiana — should NOT match IN state code
    r = extract("i heard this in a meeting", gz)
    # "in" should not fire as Indiana state code
    assert "IN" not in r.states


# ── Metro matching ────────────────────────────────────────────────────────────

def test_metro_tampa(gz):
    r = extract("Tampa rep quit last week", gz)
    assert "FL" in r.states
    assert "Southeast" in r.regions


def test_metro_dallas(gz):
    r = extract("Dallas account lost to Stryker", gz)
    assert "TX" in r.states
    assert "Southwest" in r.regions


def test_metro_atlanta(gz):
    r = extract("Atlanta hospital flipped to Arthrex", gz)
    assert "GA" in r.states


# ── Region direct matching ────────────────────────────────────────────────────

def test_region_direct_southeast(gz):
    r = extract("the Southeast is heating up with Stryker", gz)
    assert "Southeast" in r.regions
    assert r.geo_scope in ("state", "region")


def test_region_alias_the_south(gz):
    r = extract("the South is dominated by Zimmer", gz)
    assert "Southeast" in r.regions


def test_region_alias_west_coast(gz):
    r = extract("west coast is dominated by Arthrex", gz)
    assert "West" in r.regions


def test_region_direct_no_states(gz):
    r = extract("the Southeast is heating up with no state named", gz)
    # regions populated, states empty (no specific state named)
    assert "Southeast" in r.regions
    assert r.states == []


# ── National default ──────────────────────────────────────────────────────────

def test_national_default_no_geo(gz):
    r = extract("heard Stryker is launching a new system nationwide", gz)
    assert r.geo_scope == "national"
    assert r.states == []
    assert r.regions == []


def test_national_scope_no_location(gz):
    r = extract("Zimmer just acquired a small company", gz)
    assert r.geo_scope == "national"


# ── Topic classification ──────────────────────────────────────────────────────

def test_topic_personnel_poached(gz):
    r = extract("Stryker poached our best rep", gz)
    assert "personnel" in r.topics


def test_topic_pricing_discount(gz):
    r = extract("they are offering deep discounts on their implants", gz)
    assert "pricing" in r.topics


def test_topic_account_movement_signed(gz):
    r = extract("Tampa General signed with Arthrex", gz)
    assert "account_movement" in r.topics


def test_topic_multi(gz):
    r = extract("they signed a new contract and poached our rep", gz)
    assert "account_movement" in r.topics
    assert "personnel" in r.topics
    assert "pricing" in r.topics


def test_topic_ma(gz):
    r = extract("Globus just acquired a smaller spine company", gz)
    assert "m&a" in r.topics


def test_topic_fallback_other(gz):
    r = extract("something weird is happening out there", gz)
    assert "other" in r.topics


def test_topic_product_launch(gz):
    r = extract("Stryker has a new system launching next quarter", gz)
    assert "product" in r.topics


# ── Source confidence ─────────────────────────────────────────────────────────

def test_confidence_low_heard(gz):
    r = extract("heard that Stryker is poaching reps", gz)
    assert r.source_confidence == "low"


def test_confidence_low_rumor(gz):
    r = extract("rumor has it Zimmer lost a big account", gz)
    assert r.source_confidence == "low"


def test_confidence_low_apparently(gz):
    r = extract("apparently Arthrex is expanding in FL", gz)
    assert r.source_confidence == "low"


def test_confidence_high_confirmed(gz):
    r = extract("confirmed: Stryker signed Tampa General", gz)
    assert r.source_confidence == "high"


def test_confidence_high_saw(gz):
    r = extract("I saw the contract myself — Zimmer is out", gz)
    assert r.source_confidence == "high"


def test_confidence_medium_default(gz):
    r = extract("Stryker is cutting prices in FL", gz)
    assert r.source_confidence == "medium"


# ── Coverage thin flag ────────────────────────────────────────────────────────

def test_coverage_thin_no_entities_no_topics(gz):
    r = extract("something weird is happening somewhere", gz)
    assert r.coverage_thin is True


def test_coverage_not_thin_with_competitor_and_topic(gz):
    r = extract("Stryker is poaching reps in FL", gz)
    assert r.coverage_thin is False


def test_coverage_not_thin_competitor_only(gz):
    r = extract("Stryker is doing something in FL", gz)
    # has competitor, so not thin even without clear topic
    assert r.coverage_thin is False
