import pytest

from control_plane.domain.schema import (
    CanonicalSchema,
    CanonicalType,
    CanonicalTypeKind,
    Column,
    NativeTypeMetadata,
    SourceSystem,
    TableIdentity,
)
from control_plane.ports.source_introspector import (
    SourceIntrospector,
    SourceTableNotFoundError,
    SourceUnavailableError,
    UnsupportedSourceMetadataError,
)


class FakeSourceIntrospector:
    def __init__(
        self,
        tables: tuple[TableIdentity, ...],
        schemas: tuple[CanonicalSchema, ...],
        *,
        available: bool = True,
        unsupported_tables: tuple[TableIdentity, ...] = (),
    ) -> None:
        self._tables = tables
        self._schemas = schemas
        self._available = available
        self._unsupported_tables = unsupported_tables

    def _ensure_available(self) -> None:
        if not self._available:
            raise SourceUnavailableError("Source is unavailable")

    def list_tables(
        self,
        *,
        catalog: str | None,
        schema_name: str | None,
    ) -> tuple[TableIdentity, ...]:
        self._ensure_available()

        filtered_table = tuple(
            table
            for table in self._tables
            if (catalog is None or table.catalog == catalog)
            and (schema_name is None or table.schema_name == schema_name)
        )

        return tuple(
            sorted(
                filtered_table,
                key=lambda table: (
                    table.catalog or "",
                    table.schema_name or "",
                    table.table,
                ),
            )
        )

    def introspect_table(
        self,
        table: TableIdentity,
    ) -> CanonicalSchema:
        self._ensure_available()

        if table in self._unsupported_tables:
            raise UnsupportedSourceMetadataError(
                f"Unsupported metadata for table: "
                f"{table.catalog}.{table.schema_name}.{table.table}"
            )

        for schema in self._schemas:
            if schema.table == table:
                return schema

        raise SourceTableNotFoundError(
            f"Table not found: " f"{table.catalog}.{table.schema_name}.{table.table}"
        )


def test_source_introspector_lists_concrete_tables() -> None:
    table = TableIdentity(
        system=SourceSystem.SQLSERVER, catalog="sales", schema="dbo", table="users"
    )

    introspector: SourceIntrospector = FakeSourceIntrospector(
        tables=(table,),
        schemas=(),
    )

    result = introspector.list_tables(
        catalog="sales",
        schema_name="dbo",
    )

    assert result == (table,)


def test_source_introspector_returns_canonical_schema() -> None:
    table = TableIdentity(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema="dbo",
        table="users",
    )

    schema = CanonicalSchema(
        schema_version=1,
        table=table,
        columns=(
            Column(
                name="id",
                ordinal=1,
                data_type=CanonicalType(kind=CanonicalTypeKind.BIGINT),
                nullable=False,
                native=NativeTypeMetadata(
                    type_name="numeric",
                    full_type="NUMBERIC(18,0)",
                    precision=18,
                    scale=0,
                ),
            ),
            Column(
                name="age",
                ordinal=2,
                data_type=CanonicalType(kind=CanonicalTypeKind.BIGINT),
                nullable=False,
                native=NativeTypeMetadata(
                    type_name="INT",
                    full_type="INT",
                ),
            ),
        ),
    )

    introspector: SourceIntrospector = FakeSourceIntrospector(
        tables=(table,),
        schemas=(schema,),
    )

    schema_result = introspector.introspect_table(table)

    assert schema_result == schema


def test_source_introspector_raises_table_not_found_for_unknown_table() -> None:
    known_table = TableIdentity(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema_name="dbo",  # type: ignore
        table="users",
    )

    unknown_table = TableIdentity(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema_name="dbo",  # type: ignore
        table="orders",
    )

    introspector: SourceIntrospector = FakeSourceIntrospector(
        tables=(known_table,),
        schemas=(),
    )

    with pytest.raises(SourceTableNotFoundError):
        introspector.introspect_table(unknown_table)


def test_source_introspector_lists_tables_within_requested_scope() -> None:
    table_1 = TableIdentity(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema_name="dbo",  # type: ignore
        table="users",
    )

    table_2 = TableIdentity(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema_name="dbo",  # type: ignore
        table="orders",
    )

    table_3 = TableIdentity(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema_name="audit",  # type: ignore
        table="events",
    )

    table_4 = TableIdentity(
        system=SourceSystem.SQLSERVER,
        catalog="hr",
        schema_name="dbo",  # type: ignore
        table="employees",
    )

    introspector: SourceIntrospector = FakeSourceIntrospector(
        tables=(table_1, table_2, table_3, table_4),
        schemas=(),
    )

    tables = introspector.list_tables(catalog="sales", schema_name="dbo")
    assert tables == (table_2, table_1)

    tables = introspector.list_tables(catalog=None, schema_name="dbo")
    assert tables == (table_4, table_2, table_1)

    tables = introspector.list_tables(catalog="hr", schema_name=None)
    assert tables == (table_4,)

    tables = introspector.list_tables(
        catalog=None,
        schema_name=None,
    )

    assert tables == (
        table_4,
        table_3,
        table_2,
        table_1,
    )


def test_source_introspector_list_deterministic_tables() -> None:

    table_1 = TableIdentity(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema_name="dbo",  # type: ignore
        table="users",
    )

    table_2 = TableIdentity(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema_name="dbo",  # type: ignore
        table="orders",
    )

    table_3 = TableIdentity(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema_name="audit",  # type: ignore
        table="events",
    )

    introspector: SourceIntrospector = FakeSourceIntrospector(
        tables=(table_2, table_1, table_3), schemas=()
    )

    result = introspector.list_tables(catalog="sales", schema_name="dbo")

    assert result == (table_2, table_1)


def test_source_introspector_rejects_unknown_table() -> None:
    known_table = TableIdentity(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema="dbo",
        table="users",
    )

    unknown_table = TableIdentity(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema="dbo",
        table="orders",
    )

    introspector: SourceIntrospector = FakeSourceIntrospector(
        tables=(known_table,),
        schemas=(),
    )

    with pytest.raises(SourceTableNotFoundError):
        introspector.introspect_table(unknown_table)


def test_source_introspector_rejects_list_when_source_unavailable() -> None:
    introspector: SourceIntrospector = FakeSourceIntrospector(
        tables=(),
        schemas=(),
        available=False,
    )

    with pytest.raises(SourceUnavailableError):
        introspector.list_tables(
            catalog="sales",
            schema_name="dbo",
        )


def test_source_introspector_rejects_introspection_when_source_unavailable() -> None:
    table = TableIdentity(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema="dbo",
        table="users",
    )

    introspector: SourceIntrospector = FakeSourceIntrospector(
        tables=(table,),
        schemas=(),
        available=False,
    )

    with pytest.raises(SourceUnavailableError):
        introspector.introspect_table(table)


def test_source_introspector_rejects_unsupported_metadata() -> None:
    """
    1. source available?
    2. table unsupported metadata?
    3. schema exists?
    4. return CanonicalSchema
    """

    table = TableIdentity(
        system=SourceSystem.SQLSERVER, catalog="sales", schema="dbo", table="users"
    )

    introspector: SourceIntrospector = FakeSourceIntrospector(
        tables=(table,),
        schemas=(),
        unsupported_tables=(table,),
    )

    with pytest.raises(UnsupportedSourceMetadataError):
        introspector.introspect_table(table)
