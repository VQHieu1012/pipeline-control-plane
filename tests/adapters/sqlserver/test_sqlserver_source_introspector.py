from control_plane.adapters.sqlserver.source_introspector import (
    SqlServerIntrospector,
    SqlServerTableMetadata,
)
from control_plane.domain.schema import SourceSystem
from control_plane.ports.source_introspector import SourceIntrospector


def accepts_source_introspector(
    introspector: SourceIntrospector,
) -> None:
    pass


class FakeSqlServerQueryExecutor:
    def __init__(
        self,
        rows: tuple[tuple[object, ...], ...],
    ) -> None:
        self._rows = rows

    def fetch_all(
        self,
        query: str,
        params: tuple[object, ...] = (),
    ) -> tuple[tuple[object, ...], ...]:
        return self._rows


def test_sqlserver_introspector_satisfies_protocol() -> None:
    executor = FakeSqlServerQueryExecutor(
        rows=(
            ("dbo", "users"),
            ("dbo", "orders"),
        )
    )
    introspector = SqlServerIntrospector(executor, catalog="sales")

    accepts_source_introspector(introspector)


def test_maps_sqlserver_table_metadata_to_table_identity() -> None:
    metadata = SqlServerTableMetadata(
        catalog="SalesDB",
        schema_name="dbo",
        table_name="UserInfo",
    )

    identity = SqlServerIntrospector._map_table_metadata(metadata)

    assert identity.system == SourceSystem.SQLSERVER
    assert identity.catalog == "SalesDB"
    assert identity.schema_name == "dbo"
    assert identity.table == "UserInfo"


def test_sqlserver_list_tables_maps_metadata_rows() -> None:
    executor = FakeSqlServerQueryExecutor(
        rows=(
            ("dbo", "users"),
            ("dbo", "orders"),
        )
    )

    introspector = SqlServerIntrospector(executor, catalog="sales")

    result = introspector.list_tables(
        catalog="sales",
        schema_name="dbo",
    )
    print(result)

    assert tuple(table.table for table in result) == (
        "orders",
        "users",
    )
