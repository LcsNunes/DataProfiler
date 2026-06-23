from backend.app.api.routes_reports import problem_catalog
from backend.app.profiler.issue_catalog import explain_problem, load_issue_catalog


def test_issue_catalog_contains_high_cardinality_guidance():
    catalog = load_issue_catalog()

    assert "high_cardinality" in catalog
    assert explain_problem("high_cardinality")["strategies"]


def test_problem_catalog_endpoint_is_available():
    assert "missing_values" in problem_catalog()
