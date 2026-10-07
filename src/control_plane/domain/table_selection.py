from __future__ import annotations

import re
from enum import Enum

from pydantic import Field, model_validator

from control_plane.domain.schema import DomainModel, SourceSystem, TableIdentity


class TableSelectorMode(str, Enum):
    EXACT = "exact"
    REGEX = "regex"


class TableSelector(DomainModel):
    system: SourceSystem
    catalog: str | None = None
    schema_name: str | None = Field(default=None, alias="schema")
    mode: TableSelectorMode
    table_expression: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_selector(self) -> TableSelector:
        if self.mode == TableSelectorMode.REGEX:
            try:
                re.compile(self.table_expression)
            except re.error as exc:
                raise ValueError(f"Invalid table regex: {exc}") from exc

        return self


class ResolvedTable(DomainModel):
    identity: TableIdentity
