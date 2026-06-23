from backend.app.core.security import sanitize_for_output
from backend.app.recommender.recommendation_engine import build_recommendation


def test_sanitize_masks_credentials():
    safe = sanitize_for_output({"headers": {"Authorization": "Bearer secret-token"}, "api_key": "123456789"})

    assert safe["headers"]["Authorization"] != "Bearer secret-token"
    assert safe["api_key"] != "123456789"


def test_recommender_handles_no_target():
    recommendation = build_recommendation(
        source={"type": "file"},
        summary={"row_count": 10, "column_count": 2, "null_pct": 0, "duplicate_pct": 0},
        schema={"type_counts": {"numeric": 2}, "columns": [{"name": "a", "null_pct": 0, "possible_sensitive": False}]},
        quality={"problems": []},
        statistics={},
        target={"detected": False},
    )

    assert "supervisionado" in " ".join(recommendation["not_recommended"]).lower()
    assert recommendation["recommended_approach"]

