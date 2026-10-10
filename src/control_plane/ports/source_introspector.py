from typing import Protocol

from control_plane.domain.schema import (
    CanonicalSchema,
    TableIdentity,
)


class SourceIntrospector(Protocol):
    def list_tables(
        self, *, catalog: str | None, schema_name: str | None
    ) -> tuple[TableIdentity, ...]: ...

    def introspect_table(
        self,
        table: TableIdentity,
    ) -> CanonicalSchema: ...


class SourceIntrospectionError(Exception):
    """Base error for source metadata introspection."""


class SourceUnavailableError(SourceIntrospectionError):
    """The source database cannot be reached."""


class SourceTableNotFoundError(SourceIntrospectionError):
    """The requested table does not exist."""


class UnsupportedSourceMetadataError(SourceIntrospectionError):
    """Source metadata cannot be represented by the current contract."""
