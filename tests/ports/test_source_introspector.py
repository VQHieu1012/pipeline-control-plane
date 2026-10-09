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
)


class FakeSourceIntrospector:
    def __init__(
        self,
        tables: tuple[TableIdentity, ...],
        schemas: tuple[CanonicalSchema, ...],
    ) -> None:
        self._tables = tables
        self._schemas = schemas

    def list_tables(
        self,
        *,
        catalog: str | None,
        schema_name: str | None,
    ) -> tuple[TableIdentity, ...]:
        return self._tables

    def introspect_table(
        self,
        table: TableIdentity,
    ) -> CanonicalSchema:
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
        schema_name="dbo",
        table="users",
    )

    unknown_table = TableIdentity(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema_name="dbo",
        table="orders",
    )

    introspector: SourceIntrospector = FakeSourceIntrospector(
        tables=(known_table,),
        schemas=(),
    )

    with pytest.raises(SourceTableNotFoundError):
        introspector.introspect_table(unknown_table)
