from dataclasses import dataclass
from typing import Protocol

from control_plane.domain.schema import CanonicalSchema, SourceSystem, TableIdentity

_LIST_TABLES_SQL = """
    SELECT
        s.name AS schema_name,
        t.name AS table_name
    FROM sys.tables AS t
    JOIN sys.schemas AS s
        ON t.schema_id = s.schema_id
    WHERE (? IS NULL OR s.name = ?)
    ORDER BY
        s.name,
        t.name
"""


@dataclass(frozen=True)
class SqlServerTableMetadata:
    catalog: str
    schema_name: str
    table_name: str


class SqlServerQueryExecutor(Protocol):
    def fetch_all(
        self,
        query: str,
        params: tuple[object, ...] = (),
    ) -> tuple[tuple[object, ...], ...]: ...


class SqlServerIntrospector:

    def __init__(
        self,
        executor: SqlServerQueryExecutor,
        catalog: str,
    ) -> None:
        self._executor = executor
        self._catalog = catalog

    @staticmethod
    def _map_table_metadata(
        metadata: SqlServerTableMetadata,
    ) -> TableIdentity:
        return TableIdentity(
            system=SourceSystem.SQLSERVER,
            catalog=metadata.catalog,
            schema=metadata.schema_name,
            table=metadata.table_name,
        )

    def list_tables(
        self,
        *,
        catalog: str | None,
        schema_name: str | None,
    ) -> tuple[TableIdentity, ...]:
        if catalog is not None and catalog != self._catalog:
            return ()

        rows = self._executor.fetch_all(
            _LIST_TABLES_SQL,
            (schema_name, schema_name),
        )

        identities = []

        for row in rows:
            schema = row[0]
            table = row[1]

            assert isinstance(schema, str)
            assert isinstance(table, str)

            identity = self._map_table_metadata(
                SqlServerTableMetadata(
                    catalog=self._catalog,
                    schema_name=schema,
                    table_name=table,
                )
            )

            identities.append(identity)

        return tuple(
            sorted(
                identities,
                key=lambda table: (
                    table.schema_name or "",
                    table.table,
                ),
            )
        )

    def introspect_table(
        self,
        table: TableIdentity,
    ) -> CanonicalSchema:
        raise NotImplementedError
