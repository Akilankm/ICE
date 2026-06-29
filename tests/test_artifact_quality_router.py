import pandas as pd

from ice.config import IntegratedConfig
from ice.routers.artifact_quality_router import ArtifactQualityRouter


def test_low_quality_routes_to_repair():
    df = pd.DataFrame([
        {"input_id": "ROW_1", "quality_score": 0.1, "requires_manual_review": "false"}
    ])
    coding_ready, repair, review = ArtifactQualityRouter(IntegratedConfig()).route(df)
    assert coding_ready.empty
    assert len(repair) == 1
    assert review.empty
