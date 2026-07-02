"""Data loading interfaces."""

from src.data.loaders import (
    load_life_table,
    load_life_tables,
    load_life_tables_from_metadata,
    load_metadata,
)

__all__ = [
    "load_life_table",
    "load_life_tables",
    "load_life_tables_from_metadata",
    "load_metadata",
]
