import pytest
from app.extractor.pipeline import Gazetteers


@pytest.fixture
def gz() -> Gazetteers:
    return Gazetteers(
        competitors={
            "stryker": "Stryker",
            "stryk": "Stryker",
            "zimmer": "Zimmer Biomet",
            "biomet": "Zimmer Biomet",
            "zb": "Zimmer Biomet",
            "zimmer biomet": "Zimmer Biomet",
            "depuy": "DePuy Synthes",
            "synthes": "DePuy Synthes",
            "smith nephew": "Smith+Nephew",
            "smith and nephew": "Smith+Nephew",
            "s&n": "Smith+Nephew",
            "arthrex": "Arthrex",
            "medtronic": "Medtronic",
            "globus": "Globus Medical",
            "nuvasive": "Globus Medical",
        },
        distributors={},
        states={
            "FL": "Southeast", "TX": "Southwest", "GA": "Southeast",
            "OH": "Midwest", "CA": "West", "NY": "Northeast", "IL": "Midwest",
            "TN": "Southeast", "NC": "Southeast",
        },
        state_names={
            "florida": "FL", "texas": "TX", "georgia": "GA", "ohio": "OH",
            "california": "CA", "new york": "NY", "illinois": "IL",
            "tennessee": "TN", "north carolina": "NC",
        },
        metros={
            "tampa": "FL", "dallas": "TX", "atlanta": "GA",
            "houston": "TX", "orlando": "FL", "chicago": "IL",
            "nashville": "TN", "charlotte": "NC",
        },
        regions={
            "southeast": "Southeast",
            "the southeast": "Southeast",
            "the south": "Southeast",
            "dixie": "Southeast",
            "southwest": "Southwest",
            "the southwest": "Southwest",
            "midwest": "Midwest",
            "the midwest": "Midwest",
            "west": "West",
            "west coast": "West",
            "the west coast": "West",
            "northeast": "Northeast",
            "the northeast": "Northeast",
        },
        topics={
            "personnel": {"hired", "poached", "quit", "left", "joined", "rep", "recruiter", "defected", "new hire"},
            "pricing": {"price", "pricing", "discount", "rebate", "gpo", "contract", "capitated", "bundle"},
            "account_movement": {"lost", "won", "switched", "converted", "flipped", "signed", "dropped"},
            "distributor_health": {"distributor", "layoffs", "struggling", "expanding", "closing", "restructuring"},
            "product": {"510k", "launch", "recall", "clearance", "pipeline", "fda", "new system", "instrument"},
            "regulatory": {"recall", "warning letter", "audit", "pma"},
            "m&a": {"acquired", "acquisition", "merger", "buying", "bought", "takeover"},
        },
    )
