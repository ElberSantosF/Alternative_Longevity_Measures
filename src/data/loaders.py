"""Load local life table files from Excel or CSV."""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd

from src.config.settings import DATA_DIR, RAW_DATA_DIR


AGE_ALIASES = ("age", "Age", "x")
LX_ALIASES = ("lx", "LX", "Lx")
YEAR_ALIASES = ("year", "Year")


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def infer_country_from_filename(path: str | Path) -> str:
    """Infer a readable location label from a local filename."""
    filename = _strip_accents(Path(path).stem).lower()
    return filename.replace("_", " ").replace("-", " ").title()


def _first_existing(columns: Iterable[str], aliases: Iterable[str]) -> str | None:
    existing = {str(col): str(col) for col in columns}
    lowered = {str(col).lower(): str(col) for col in columns}
    for alias in aliases:
        if alias in existing:
            return existing[alias]
        if alias.lower() in lowered:
            return lowered[alias.lower()]
    return None


def _read_table(path: Path, sheet_name: str | int | None = 0) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm", ".xls"}:
        return pd.read_excel(path, sheet_name=sheet_name)
    if suffix == ".csv":
        return pd.read_csv(path)
    raise ValueError(f"Unsupported file extension: {path.suffix}")


def load_life_table(
    path: str | Path,
    *,
    country: str | None = None,
    year: int | None = None,
    sheet_name: str | int | None = 0,
) -> pd.DataFrame:
    """Load one local life table and standardize columns.

    The returned data frame contains ``country``, ``year``, ``age`` and ``lx``.
    If the file already has a year column, it is preserved unless ``year`` is
    supplied explicitly.
    """
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = RAW_DATA_DIR / file_path
    if not file_path.exists():
        raise FileNotFoundError(file_path)

    df = _read_table(file_path, sheet_name=sheet_name)
    age_col = _first_existing(df.columns, AGE_ALIASES)
    lx_col = _first_existing(df.columns, LX_ALIASES)
    year_col = _first_existing(df.columns, YEAR_ALIASES)

    if age_col is None or lx_col is None:
        raise ValueError(
            f"{file_path.name} must contain age and lx columns. "
            f"Accepted age aliases: {AGE_ALIASES}; lx aliases: {LX_ALIASES}."
        )

    out = pd.DataFrame(
        {
            "country": country or infer_country_from_filename(file_path),
            "age": pd.to_numeric(df[age_col], errors="coerce"),
            "lx": pd.to_numeric(df[lx_col], errors="coerce"),
        }
    )

    if year is not None:
        out["year"] = int(year)
    elif year_col is not None:
        out["year"] = pd.to_numeric(df[year_col], errors="coerce").astype("Int64")
    else:
        out["year"] = pd.NA

    out = out.dropna(subset=["age", "lx"]).copy()
    if out.empty:
        raise ValueError(f"{file_path.name} has no valid age/lx rows.")
    if (out["lx"] <= 0).any():
        raise ValueError(f"{file_path.name} contains non-positive lx values.")

    return out[["country", "year", "age", "lx"]].sort_values(
        ["country", "year", "age"], na_position="last"
    )


def load_life_tables(files: Iterable[str | Path | Mapping[str, object]]) -> pd.DataFrame:
    """Load and concatenate multiple local life table files.

    Each item can be a filename/path or a mapping with ``filename``, ``country``,
    ``year`` and ``sheet_name`` keys.
    """
    frames = []
    for item in files:
        if isinstance(item, Mapping):
            filename = item.get("filename") or item.get("path")
            if filename is None:
                raise ValueError("Each file mapping must contain 'filename' or 'path'.")
            frames.append(
                load_life_table(
                    filename,
                    country=item.get("label") or item.get("country"),
                    year=item.get("year"),
                    sheet_name=item.get("sheet_name", 0),
                )
            )
        else:
            frames.append(load_life_table(item))

    if not frames:
        return pd.DataFrame(columns=["country", "year", "age", "lx"])
    return pd.concat(frames, ignore_index=True)


def load_metadata(path: str | Path | None = None) -> pd.DataFrame:
    """Load the spreadsheet catalog used by the notebook.

    The metadata file must contain ``filename`` and can optionally contain
    ``country``, ``year`` and ``sheet_name``.
    """
    metadata_path = Path(path) if path is not None else DATA_DIR / "metadata.csv"
    if not metadata_path.is_absolute():
        metadata_path = DATA_DIR / metadata_path
    if not metadata_path.exists():
        raise FileNotFoundError(metadata_path)

    metadata = pd.read_csv(metadata_path)
    if "filename" not in metadata.columns:
        raise ValueError("metadata.csv must contain a 'filename' column.")
    return metadata


def load_life_tables_from_metadata(path: str | Path | None = None) -> pd.DataFrame:
    """Load all life tables listed in ``data/metadata.csv``."""
    metadata = load_metadata(path)
    files = metadata.where(pd.notna(metadata), None).to_dict("records")
    return load_life_tables(files)
