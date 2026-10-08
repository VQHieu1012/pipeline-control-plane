from control_plane.domain.schema import (
    CanonicalSchema,
    CanonicalType,
    CanonicalTypeKind,
    Column,
    NativeTypeMetadata,
    SourceSystem,
    TableIdentity,
)
from control_plane.ports.source_introspector import SourceIntrospector


class FakeSourceIntrospector:
    def __init__(
        self,
        tables: tuple[TableIdentity, ...],
        schemas: dict[TableIdentity, CanonicalSchema],
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
        return self._schemas[table]


def test_source_introspector_lists_concrete_tables() -> None:
    table = TableIdentity(
        system=SourceSystem.SQLSERVER, catalog="sales", schema="dbo", table="users"
    )

    introspector: SourceIntrospector = FakeSourceIntrospector(
        tables=(table,),
        schemas={},
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
        schemas={
            table: schema,  # type: ignore
        },
    )

    result = introspector.list_tables(
        catalog="sales",
        schema_name="dbo",
    )

    schema_result = introspector.introspect_table(result[0])

    assert schema_result == schema
