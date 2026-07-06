import pandas as pd

from src.data.loaders import (
    infer_country_from_filename,
    load_life_table,
    load_life_tables,
    load_life_tables_from_metadata,
    load_metadata,
)


def test_infer_country_from_filename_returns_readable_label():
    assert infer_country_from_filename("female_life_table_chile_2023.xlsx") == (
        "Female Life Table Chile 2023"
    )


def test_load_life_table_standardizes_columns_from_csv(tmp_path):
    path = tmp_path / "life_table.csv"
    pd.DataFrame({"age": [0, 1], "lx": [100000, 99000]}).to_csv(path, index=False)

    out = load_life_table(path, country="Test", year=2025)

    assert list(out.columns) == ["country", "year", "age", "lx"]
    assert out["country"].tolist() == ["Test", "Test"]
    assert out["year"].tolist() == [2025, 2025]
    assert out["age"].tolist() == [0, 1]


def test_load_life_tables_concatenates_mapping_items(tmp_path):
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    pd.DataFrame({"age": [0], "lx": [100000]}).to_csv(first, index=False)
    pd.DataFrame({"age": [0], "lx": [95000]}).to_csv(second, index=False)

    out = load_life_tables(
        [
            {"filename": first, "country": "A", "year": 2024},
            {"filename": second, "country": "B", "year": 2025},
        ]
    )

    assert out["country"].tolist() == ["A", "B"]
    assert out["year"].tolist() == [2024, 2025]


def test_load_life_tables_from_metadata(tmp_path):
    life_table = tmp_path / "table.csv"
    metadata = tmp_path / "metadata.csv"
    pd.DataFrame({"age": [0], "lx": [100000]}).to_csv(life_table, index=False)
    pd.DataFrame(
        {"filename": [str(life_table)], "country": ["Test"], "year": [2026]}
    ).to_csv(metadata, index=False)

    loaded_metadata = load_metadata(metadata)
    out = load_life_tables_from_metadata(metadata)

    assert loaded_metadata["country"].tolist() == ["Test"]
    assert out["country"].tolist() == ["Test"]
    assert out["year"].tolist() == [2026]
