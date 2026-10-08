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
