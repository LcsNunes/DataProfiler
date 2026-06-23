from pathlib import Path

from backend.app.loaders.file_loader import load_file
from backend.app.loaders.json_normalizer import normalize_json_payload


def test_load_csv_detects_separator_and_rows(tmp_path: Path):
    path = tmp_path / "sample.csv"
    path.write_text("id;status\n1;ok\n2;fail\n", encoding="utf-8")

    loaded = load_file(str(path))

    assert loaded.dataframe.height == 2
    assert loaded.metadata["separator"] == ";"
    assert loaded.source["type"] == "file"


def test_normalize_nested_json():
    payload = {"response": {"items": [{"id": 1, "user": {"name": "Ana"}}]}}

    df = normalize_json_payload(payload)

    assert df.columns == ["id", "user.name"]
    assert df.height == 1

