import pandas as pd

from ice.config import IntegratedConfig
from ice.routers.candidate_router import CandidateRouter


def test_high_confidence_exact_uses_one_candidate():
    canonical_df = pd.DataFrame([
        {"input_id": "ROW_1", "main_text": "Toy", "country_code": "CZ", "PG_name": "Figures"}
    ])
    search_df = pd.DataFrame([
        {
            "input_id": "ROW_1",
            "verified_exact_url": "https://retailer.example/p/1",
            "best_available_url": "https://other.example/p/1",
            "confidence": 0.95,
        }
    ])
    candidates = CandidateRouter(IntegratedConfig()).build_scrape_candidates(canonical_df, search_df)
    assert len(candidates) == 1
    assert candidates[0].source_url_role == "verified_exact_url"
