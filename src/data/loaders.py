"""Load local life table files from Excel or CSV."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.config.settings import COUNTRY_FILE_HINTS, RAW_DATA_DIR


AGE_ALIASES = ("IDADE", "Idade", "Age", "age", "x")
LX_ALIASES = ("lx", "LX", "Lx")
YEAR_ALIASES = ("Year", "year", "ANO", "Ano", "ano")


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def infer_country_from_filename(path: str | Path) -> str:
    """Infer a country/location code from a life-table filename."""
    filename = _strip_accents(Path(path).stem).lower()
    for code, hint in COUNTRY_FILE_HINTS.items():
        if hint.lower() in filename:
            return code
    match = re.search(r"hmd[_ -]?([a-z0-9]+)", filename)
    if match:
        return match.group(1).upper()
    return Path(path).stem.upper()


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


@dataclass(frozen=True)
class LifeTableRepository:
    """Repository for local life table files."""

    raw_dir: Path = RAW_DATA_DIR

    def resolve(self, filename: str | Path) -> Path:
        """Resolve a file path relative to the raw data directory."""
        path = Path(filename)
        return path if path.is_absolute() else self.raw_dir / path

    def load(
        self,
        filename: str | Path,
        *,
        country: str | None = None,
        year: int | None = None,
        sheet_name: str | int | None = 0,
    ) -> pd.DataFrame:
        """Load a single life table."""
        return load_life_table(
            self.resolve(filename), country=country, year=year, sheet_name=sheet_name
        )

    def load_many(self, files: Iterable[str | Path]) -> pd.DataFrame:
        """Load and concatenate multiple life table files."""
        frames = [self.load(file) for file in files]
        if not frames:
            return pd.DataFrame(columns=["country", "year", "age", "lx"])
        return pd.concat(frames, ignore_index=True)

