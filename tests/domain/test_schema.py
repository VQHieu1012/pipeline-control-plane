import pytest
from pydantic import ValidationError

from control_plane.domain.schema import (
    CanonicalField,
    CanonicalSchema,
    CanonicalType,
    CanonicalTypeKind,
    Column,
    NativeTypeMetadata,
    PrimaryKey,
    SourceSystem,
    TableIdentity,
    UniqueKey,
)


def make_column(
    name: str = "id",
    ordinal: int = 1,
    *,
    data_type: CanonicalType | None = None,
    nullable: bool = False,
    native: NativeTypeMetadata | None = None,
) -> Column:
    return Column(
        name=name,
        ordinal=ordinal,
        data_type=data_type or CanonicalType(kind=CanonicalTypeKind.INT),
        nullable=nullable,
        native=native
        or NativeTypeMetadata(
            type_name="int",
            full_type="INT",
        ),
    )


def make_schema(
    columns: tuple[Column, ...],
    *,
    table: TableIdentity | None = None,
    primary_key: PrimaryKey | None = None,
    unique_keys: tuple[UniqueKey, ...] = (),
) -> CanonicalSchema:
    return CanonicalSchema(
        schema_version=1,
        table=table or make_table_identity(),
        columns=columns,
        primary_key=primary_key,
        unique_keys=unique_keys,
    )


def test_valid_scalar_schema() -> None:
    schema = CanonicalSchema(
        schema_version=1,
        table=make_table_identity(),
        columns=(
            Column(
                name="id",
                ordinal=1,
                data_type=CanonicalType(kind=CanonicalTypeKind.BIGINT),
                nullable=False,
                native=NativeTypeMetadata(type_name="bigint"),
            ),
        ),
        primary_key=PrimaryKey(name="PK_orders", columns=("id",)),
    )

    assert schema.columns[0].name == "id"


@pytest.mark.parametrize(
    "kind",
    [
        CanonicalTypeKind.BOOLEAN,
        CanonicalTypeKind.TINYINT,
        CanonicalTypeKind.SMALLINT,
        CanonicalTypeKind.INT,
        CanonicalTypeKind.BIGINT,
        CanonicalTypeKind.FLOAT,
        CanonicalTypeKind.DOUBLE,
        CanonicalTypeKind.STRING,
        CanonicalTypeKind.BYTES,
        CanonicalTypeKind.DATE,
        CanonicalTypeKind.RAW,
    ],
)
def test_plain_scalar_types_are_valid(
    kind: CanonicalTypeKind,
) -> None:
    data_type = CanonicalType(kind=kind)

    assert data_type.kind == kind


def test_decimal_is_valid() -> None:
    data_type = CanonicalType(kind=CanonicalTypeKind.DECIMAL, precision=18, scale=2)

    assert data_type.kind == CanonicalTypeKind.DECIMAL
    assert data_type.precision == 18
    assert data_type.scale == 2


def test_decimal_is_invalid_without_precision() -> None:
    with pytest.raises(ValidationError, match="requires precision"):
        CanonicalType(kind=CanonicalTypeKind.DECIMAL, scale=2)


def test_decimal_is_invalid_without_scale() -> None:
    with pytest.raises(ValidationError, match="requires scale"):
        CanonicalType(kind=CanonicalTypeKind.DECIMAL, precision=18)


def test_decimal_rejects_zero_precision() -> None:
    with pytest.raises(ValidationError, match="precision must be >= 1"):
        CanonicalType(kind=CanonicalTypeKind.DECIMAL, precision=0, scale=0)


def test_decimal_is_invalid_with_negative_scale() -> None:
    with pytest.raises(ValidationError, match="0 <= scale"):
        CanonicalType(kind=CanonicalTypeKind.DECIMAL, precision=18, scale=-1)


def test_decimal_rejects_scale_greater_than_precision() -> None:
    with pytest.raises(ValidationError, match="scale <= precision"):
        CanonicalType(kind=CanonicalTypeKind.DECIMAL, precision=18, scale=20)


@pytest.mark.parametrize(
    ("precision", "scale"),
    [
        (1, 0),
        (18, 18),
    ],
)
def test_decimal_accepts_boundary_values(
    precision: int,
    scale: int,
) -> None:
    data_type = CanonicalType(
        kind=CanonicalTypeKind.DECIMAL, precision=precision, scale=scale
    )

    assert data_type.precision == precision
    assert data_type.scale == scale


@pytest.mark.parametrize(
    "kind",
    [
        CanonicalTypeKind.CHAR,
        CanonicalTypeKind.VARCHAR,
        CanonicalTypeKind.BINARY,
        CanonicalTypeKind.VARBINARY,
    ],
)
def test_length_bearing_types_accept_positive_length(kind: CanonicalTypeKind) -> None:
    data_type = CanonicalType(kind=kind, length=10)
    assert data_type.length == 10


@pytest.mark.parametrize(
    "kind",
    [
        CanonicalTypeKind.CHAR,
        CanonicalTypeKind.VARCHAR,
        CanonicalTypeKind.BINARY,
        CanonicalTypeKind.VARBINARY,
    ],
)
@pytest.mark.parametrize(
    "length",
    [0, -1],
)
def test_length_bearing_types_reject_non_positive_length(
    kind: CanonicalTypeKind, length: int
) -> None:
    with pytest.raises(ValidationError, match="requires length > 0"):
        CanonicalType(kind=kind, length=length)


@pytest.mark.parametrize(
    "kind",
    [
        CanonicalTypeKind.CHAR,
        CanonicalTypeKind.VARCHAR,
        CanonicalTypeKind.BINARY,
        CanonicalTypeKind.VARBINARY,
    ],
)
def test_length_bearing_types_require_length(
    kind: CanonicalTypeKind,
) -> None:
    with pytest.raises(
        ValidationError,
        match="requires length > 0",
    ):
        CanonicalType(kind=kind)


def test_array_is_valid() -> None:
    data_type = CanonicalType(
        kind=CanonicalTypeKind.ARRAY,
        element_type=CanonicalType(
            kind=CanonicalTypeKind.STRING,
        ),
    )

    assert data_type.kind == CanonicalTypeKind.ARRAY
    assert data_type.element_type is not None
    assert data_type.element_type.kind == CanonicalTypeKind.STRING


def test_array_rejects_missing_element_type() -> None:
    with pytest.raises(ValidationError, match="requires element_type"):
        CanonicalType(kind=CanonicalTypeKind.ARRAY)


def test_map_is_valid():
    key_type = CanonicalType(kind=CanonicalTypeKind.STRING)

    value_type = CanonicalType(kind=CanonicalTypeKind.INT)

    data_type = CanonicalType(
        kind=CanonicalTypeKind.MAP,
        key_type=key_type,
        value_type=value_type,
    )

    assert data_type.kind == CanonicalTypeKind.MAP

    assert data_type.key_type is not None
    assert data_type.value_type is not None

    assert data_type.key_type == key_type
    assert data_type.value_type == value_type


@pytest.mark.parametrize(
    ("key_type", "value_type"),
    [
        pytest.param(
            CanonicalType(kind=CanonicalTypeKind.STRING), None, id="missing-value-type"
        ),
        pytest.param(
            None,
            CanonicalType(kind=CanonicalTypeKind.INT),
            id="missing-key-type",
        ),
        pytest.param(
            None,
            None,
            id="missing-key-value-type",
        ),
    ],
)
def test_map_rejects_missing_key_or_value(
    key_type: CanonicalType | None,
    value_type: CanonicalType | None,
) -> None:
    with pytest.raises(ValidationError, match="requires key_type and value_type"):
        CanonicalType(
            kind=CanonicalTypeKind.MAP,
            key_type=key_type,
            value_type=value_type,
        )


"""
ROW
có field không duplicate    valid
không có field              invalid
có field duplicate          invalid
"""


def test_row_is_valid() -> None:
    field_1 = CanonicalField(
        name="id", data_type=CanonicalType(kind=CanonicalTypeKind.INT)
    )
    field_2 = CanonicalField(
        name="name", data_type=CanonicalType(kind=CanonicalTypeKind.STRING)
    )

    data_type = CanonicalType(kind=CanonicalTypeKind.ROW, fields=(field_1, field_2))

    assert data_type.kind == CanonicalTypeKind.ROW
    assert data_type.fields == (field_1, field_2)


def test_row_rejects_missing_field() -> None:
    with pytest.raises(ValidationError, match="requires fields"):
        CanonicalType(kind=CanonicalTypeKind.ROW, fields=())


def test_row_rejects_duplicate_field_name() -> None:
    field_1 = CanonicalField(
        name="id", data_type=CanonicalType(kind=CanonicalTypeKind.INT)
    )
    field_2 = CanonicalField(
        name="id", data_type=CanonicalType(kind=CanonicalTypeKind.STRING)
    )
    with pytest.raises(ValidationError, match="duplicate field names"):
        CanonicalType(kind=CanonicalTypeKind.ROW, fields=(field_1, field_2))


@pytest.mark.parametrize(
    "kind",
    [
        CanonicalTypeKind.TIME,
        CanonicalTypeKind.TIMESTAMP,
        CanonicalTypeKind.TIMESTAMP_LTZ,
    ],
)
def test_temporal_types_default_precision_to_three(
    kind: CanonicalTypeKind,
) -> None:
    data_type = CanonicalType(
        kind=kind,
    )

    assert data_type.precision == 3


@pytest.mark.parametrize(
    "kind",
    [
        CanonicalTypeKind.TIME,
        CanonicalTypeKind.TIMESTAMP,
        CanonicalTypeKind.TIMESTAMP_LTZ,
    ],
)
@pytest.mark.parametrize(
    "precision",
    [0, 9],
)
def test_temporal_types_accept_precision_boundaries(
    kind: CanonicalTypeKind,
    precision: int,
) -> None:
    data_type = CanonicalType(
        kind=kind,
        precision=precision,
    )

    assert data_type.precision == precision


@pytest.mark.parametrize(
    "kind",
    [
        CanonicalTypeKind.TIME,
        CanonicalTypeKind.TIMESTAMP,
        CanonicalTypeKind.TIMESTAMP_LTZ,
    ],
)
@pytest.mark.parametrize(
    "precision",
    [-1, 10],
)
def test_temporal_types_reject_precision_outside_range(
    kind: CanonicalTypeKind,
    precision: int,
) -> None:
    with pytest.raises(
        ValidationError,
        match="0 <= precision <= 9",
    ):
        CanonicalType(
            kind=kind,
            precision=precision,
        )


@pytest.mark.parametrize(
    ("kind", "extra"),
    [
        (CanonicalTypeKind.VARCHAR, {"length": 10, "precision": 10}),
        (CanonicalTypeKind.DECIMAL, {"precision": 18, "scale": 2, "length": 10}),
        (CanonicalTypeKind.ARRAY, {"length": 10}),
        (CanonicalTypeKind.MAP, {"precision": 2}),
        (CanonicalTypeKind.ROW, {"length": 10}),
        (CanonicalTypeKind.DATE, {"precision": 10}),
    ],
)
def test_data_type_rejects_invalid_parameters(
    kind: CanonicalTypeKind,
    extra: dict[str, object],
) -> None:
    payload = {"kind": kind, **extra}
    with pytest.raises(
        ValidationError,
        match="does not allow parameters",
    ):
        CanonicalType.model_validate(payload)


def test_plain_scalar_allows_irrelevant_parameter_when_none() -> None:
    data_type = CanonicalType(
        kind=CanonicalTypeKind.INT,
        length=None,
    )

    assert data_type.kind == CanonicalTypeKind.INT


def make_table_identity(
    *,
    system: SourceSystem = SourceSystem.SQLSERVER,
    catalog: str | None = "test_db",
    schema_name: str | None = "dbo",
    table: str = "users",
) -> TableIdentity:
    return TableIdentity(
        system=system,
        catalog=catalog,
        schema=schema_name,
        table=table,
    )


def test_column_is_valid() -> None:
    column = Column(
        name="UserID",
        ordinal=1,
        data_type=CanonicalType(
            kind=CanonicalTypeKind.BIGINT,
        ),
        nullable=False,
        native=NativeTypeMetadata(type_name="bigint", full_type="bigint"),
    )

    assert column.name == "UserID"
    assert column.ordinal == 1
    assert column.data_type.kind == CanonicalTypeKind.BIGINT
    assert column.nullable is False


@pytest.mark.parametrize(
    "ordinal",
    [0, -1],
)
def test_column_rejects_non_positive_ordinal(
    ordinal: int,
) -> None:
    with pytest.raises(ValidationError):
        Column(
            name="id",
            ordinal=ordinal,
            data_type=CanonicalType(
                kind=CanonicalTypeKind.INT,
            ),
            nullable=False,
            native=NativeTypeMetadata(
                type_name="int",
                full_type="int",
            ),
        )


def test_column_preserves_native_name_exactly() -> None:
    column = Column(
        name="UserId",
        ordinal=1,
        data_type=CanonicalType(
            kind=CanonicalTypeKind.INT,
        ),
        nullable=False,
        native=NativeTypeMetadata(
            type_name="int",
            full_type="int",
        ),
    )

    assert column.name == "UserId"


def test_schema_rejects_duplicate_column_names() -> None:
    column_1 = Column(
        name="id",
        ordinal=1,
        data_type=CanonicalType(kind=CanonicalTypeKind.BIGINT),
        nullable=False,
        native=NativeTypeMetadata(
            type_name="bigint", full_type="bigint", auto_increment=True
        ),
    )

    column_2 = Column(
        name="id",
        ordinal=2,
        data_type=CanonicalType(kind=CanonicalTypeKind.BIGINT),
        nullable=False,
        native=NativeTypeMetadata(
            type_name="bigint", full_type="bigint", auto_increment=True
        ),
    )

    with pytest.raises(ValidationError, match="Duplicate column names"):
        CanonicalSchema(
            schema_version=1,
            table=make_table_identity(),
            columns=(
                column_1,
                column_2,
            ),
            primary_key=PrimaryKey(name="id", columns=("id",)),
        )


def test_schema_rejects_duplicate_ordinals() -> None:
    column_1 = make_column(
        name="id",
        ordinal=1,
    )

    column_2 = make_column(
        name="user_name",
        ordinal=1,
    )

    with pytest.raises(ValidationError, match="Duplicate column ordinals"):
        CanonicalSchema(
            schema_version=1,
            table=make_table_identity(),
            columns=(
                column_1,
                column_2,
            ),
            primary_key=PrimaryKey(name="id", columns=("id",)),
        )


def test_schema_rejects_non_ordered_ordinals() -> None:
    column_1 = Column(
        name="id",
        ordinal=2,
        data_type=CanonicalType(kind=CanonicalTypeKind.BIGINT),
        nullable=False,
        native=NativeTypeMetadata(
            type_name="bigint", full_type="bigint", auto_increment=True
        ),
    )

    column_2 = Column(
        name="user_name",
        ordinal=1,
        data_type=CanonicalType(kind=CanonicalTypeKind.BIGINT),
        nullable=False,
        native=NativeTypeMetadata(
            type_name="bigint", full_type="bigint", auto_increment=True
        ),
    )

    with pytest.raises(ValidationError, match="must be ordered by ordinal"):
        CanonicalSchema(
            schema_version=1,
            table=make_table_identity(),
            columns=(
                column_1,
                column_2,
            ),
            primary_key=PrimaryKey(name="id", columns=("id",)),
        )


def test_schema_rejects_unknown_primary_key_reference() -> None:
    column_1 = Column(
        name="id",
        ordinal=1,
        data_type=CanonicalType(kind=CanonicalTypeKind.BIGINT),
        nullable=False,
        native=NativeTypeMetadata(
            type_name="bigint", full_type="bigint", auto_increment=True
        ),
    )

    column_2 = Column(
        name="user_name",
        ordinal=2,
        data_type=CanonicalType(kind=CanonicalTypeKind.BIGINT),
        nullable=False,
        native=NativeTypeMetadata(
            type_name="bigint", full_type="bigint", auto_increment=True
        ),
    )

    with pytest.raises(ValidationError, match="Primary key references unknown"):
        CanonicalSchema(
            schema_version=1,
            table=make_table_identity(),
            columns=(
                column_1,
                column_2,
            ),
            primary_key=PrimaryKey(name="pk_user", columns=("idx",)),
        )


def test_schema_rejects_unknown_unique_key_reference() -> None:
    column_1 = Column(
        name="id",
        ordinal=1,
        data_type=CanonicalType(kind=CanonicalTypeKind.BIGINT),
        nullable=False,
        native=NativeTypeMetadata(
            type_name="bigint", full_type="bigint", auto_increment=True
        ),
    )

    column_2 = Column(
        name="user_name",
        ordinal=2,
        data_type=CanonicalType(kind=CanonicalTypeKind.BIGINT),
        nullable=False,
        native=NativeTypeMetadata(
            type_name="bigint", full_type="bigint", auto_increment=True
        ),
    )

    with pytest.raises(ValidationError, match="Unique key references unknown"):
        CanonicalSchema(
            schema_version=1,
            table=make_table_identity(),
            columns=(
                column_1,
                column_2,
            ),
            unique_keys=(UniqueKey(name="uq_user_name", columns=("idx",)),),
        )


def test_schema_allows_composite_primary_key() -> None:
    column_1 = Column(
        name="id",
        ordinal=1,
        data_type=CanonicalType(kind=CanonicalTypeKind.BIGINT),
        nullable=False,
        native=NativeTypeMetadata(
            type_name="bigint", full_type="bigint", auto_increment=True
        ),
    )

    column_2 = Column(
        name="tenant_id",
        ordinal=2,
        data_type=CanonicalType(kind=CanonicalTypeKind.STRING),
        nullable=False,
        native=NativeTypeMetadata(type_name="text", full_type="text"),
    )

    column_3 = Column(
        name="name",
        ordinal=3,
        data_type=CanonicalType(kind=CanonicalTypeKind.VARCHAR, length=200),
        nullable=False,
        native=NativeTypeMetadata(type_name="varchar", full_type="varchar(200)"),
    )

    schema = CanonicalSchema(
        schema_version=1,
        table=make_table_identity(),
        columns=(column_1, column_2, column_3),
        primary_key=PrimaryKey(name="pk_id_tenant_id", columns=("id", "tenant_id")),
    )

    assert schema.primary_key is not None
    assert schema.primary_key.name == "pk_id_tenant_id"
    assert schema.primary_key.columns == ("id", "tenant_id")


def test_schema_rejects_unknown_column_in_composite_primary_key() -> None:
    column_1 = Column(
        name="id",
        ordinal=1,
        data_type=CanonicalType(kind=CanonicalTypeKind.BIGINT),
        nullable=False,
        native=NativeTypeMetadata(
            type_name="bigint", full_type="bigint", auto_increment=True
        ),
    )

    column_2 = Column(
        name="tenant_id",
        ordinal=2,
        data_type=CanonicalType(kind=CanonicalTypeKind.STRING),
        nullable=False,
        native=NativeTypeMetadata(type_name="text", full_type="text"),
    )

    with pytest.raises(ValidationError, match="Primary key references unknown"):
        CanonicalSchema(
            schema_version=1,
            table=make_table_identity(),
            columns=(column_1, column_2),
            primary_key=PrimaryKey(name="pk_id_tenant_id", columns=("id", "name")),
        )


def test_schema_allows_composite_unique_key() -> None:
    column_1 = Column(
        name="id",
        ordinal=1,
        data_type=CanonicalType(kind=CanonicalTypeKind.BIGINT),
        nullable=False,
        native=NativeTypeMetadata(
            type_name="bigint", full_type="bigint", auto_increment=True
        ),
    )

    column_2 = Column(
        name="tenant_id",
        ordinal=2,
        data_type=CanonicalType(kind=CanonicalTypeKind.STRING),
        nullable=False,
        native=NativeTypeMetadata(type_name="text", full_type="text"),
    )

    column_3 = Column(
        name="name",
        ordinal=3,
        data_type=CanonicalType(kind=CanonicalTypeKind.VARCHAR, length=200),
        nullable=False,
        native=NativeTypeMetadata(type_name="varchar", full_type="varchar(200)"),
    )

    schema = CanonicalSchema(
        schema_version=1,
        table=make_table_identity(),
        columns=(column_1, column_2, column_3),
        unique_keys=(UniqueKey(name="uniq_id_tenant_id", columns=("id", "tenant_id")),),
    )

    assert len(schema.unique_keys) == 1
    assert schema.unique_keys[0].name == "uniq_id_tenant_id"
    assert schema.unique_keys[0].columns == ("id", "tenant_id")


def test_schema_rejects_unknown_column_in_composite_unique_key() -> None:
    column_1 = Column(
        name="id",
        ordinal=1,
        data_type=CanonicalType(kind=CanonicalTypeKind.BIGINT),
        nullable=False,
        native=NativeTypeMetadata(
            type_name="bigint", full_type="bigint", auto_increment=True
        ),
    )

    column_2 = Column(
        name="tenant_id",
        ordinal=2,
        data_type=CanonicalType(kind=CanonicalTypeKind.STRING),
        nullable=False,
        native=NativeTypeMetadata(type_name="text", full_type="text"),
    )

    with pytest.raises(ValidationError, match="Unique key references unknown"):
        CanonicalSchema(
            schema_version=1,
            table=make_table_identity(),
            columns=(column_1, column_2),
            unique_keys=(
                UniqueKey(
                    name="uniq_id_tenant_id",
                    columns=("id", "name"),
                ),
            ),
        )


def test_primary_key_allows_non_empty_columns() -> None:
    pk = PrimaryKey(name="pk_id", columns=("id",))

    assert pk.name == "pk_id"
    assert pk.columns == ("id",)


def test_primary_key_rejects_empty_columns() -> None:
    with pytest.raises(ValidationError):
        PrimaryKey(name="pk_id", columns=())


def test_primary_key_rejects_duplicate_columns() -> None:
    with pytest.raises(ValidationError):
        PrimaryKey(name="pk_id", columns=("id", "id"))


def test_unique_key_allows_non_empty_columns() -> None:
    unique_key = UniqueKey(name="uniq_id", columns=("id",))

    assert unique_key.name == "uniq_id"
    assert unique_key.columns == ("id",)


def test_unique_key_rejects_empty_columns() -> None:
    with pytest.raises(ValidationError):
        UniqueKey(name="uniq_id", columns=())


def test_unique_key_rejects_duplicate_columns() -> None:
    with pytest.raises(ValidationError):
        UniqueKey(name="uniq_id", columns=("id", "id"))


def test_schema_round_trips_through_json() -> None:
    table_identity = make_table_identity()

    column_1 = Column(
        name="id",
        ordinal=1,
        data_type=CanonicalType(kind=CanonicalTypeKind.DECIMAL, precision=18, scale=0),
        native=NativeTypeMetadata(
            type_name="decimal",
            full_type="DECINAL(18,0)",
            precision=18,
            scale=0,
            auto_increment=True,
        ),
        nullable=False,
    )

    column_2 = Column(
        name="age",
        ordinal=2,
        data_type=CanonicalType(kind=CanonicalTypeKind.INT),
        native=NativeTypeMetadata(
            type_name="int",
            full_type="INT",
            auto_increment=False,
        ),
        nullable=False,
    )

    primary_key = PrimaryKey(name="pk_id", columns=("id",))
    unique_keys = (UniqueKey(name="uniq_id", columns=("id",)),)

    schema = CanonicalSchema(
        schema_version=1,
        table=table_identity,
        columns=(column_1, column_2),
        primary_key=primary_key,
        unique_keys=unique_keys,
    )

    payload = schema.model_dump_json()
    restored = CanonicalSchema.model_validate_json(payload)

    assert restored == schema


def test_schema_serializes_table_schema_using_alias() -> None:
    table_identity = make_table_identity()

    column_1 = Column(
        name="id",
        ordinal=1,
        data_type=CanonicalType(kind=CanonicalTypeKind.DECIMAL, precision=18, scale=0),
        native=NativeTypeMetadata(
            type_name="decimal",
            full_type="DECIMAL(18,0)",
            precision=18,
            scale=0,
            auto_increment=True,
        ),
        nullable=False,
    )

    column_2 = Column(
        name="age",
        ordinal=2,
        data_type=CanonicalType(kind=CanonicalTypeKind.INT),
        native=NativeTypeMetadata(
            type_name="int",
            full_type="INT",
            auto_increment=False,
        ),
        nullable=False,
    )

    primary_key = PrimaryKey(name="pk_id", columns=("id",))
    unique_keys = (UniqueKey(name="uniq_id", columns=("id",)),)

    schema = CanonicalSchema(
        schema_version=1,
        table=table_identity,
        columns=(column_1, column_2),
        primary_key=primary_key,
        unique_keys=unique_keys,
    )

    payload = schema.model_dump(by_alias=True)
    assert payload["table"]["schema"] == "dbo"
    assert "schema_name" not in payload["table"]

    restored = CanonicalSchema.model_validate(payload)

    assert restored == schema


def test_nested_logical_types_are_valid() -> None:
    id_field = CanonicalField(
        name="id",
        data_type=CanonicalType(
            kind=CanonicalTypeKind.INT,
        ),
        nullable=False,
    )

    tags_field = CanonicalField(
        name="tags",
        data_type=CanonicalType(
            kind=CanonicalTypeKind.ARRAY,
            element_type=CanonicalType(
                kind=CanonicalTypeKind.STRING,
            ),
        ),
    )

    attributes_field = CanonicalField(
        name="attributes",
        data_type=CanonicalType(
            kind=CanonicalTypeKind.MAP,
            key_type=CanonicalType(
                kind=CanonicalTypeKind.STRING,
            ),
            value_type=CanonicalType(
                kind=CanonicalTypeKind.VARCHAR,
                length=100,
            ),
        ),
    )

    data_type = CanonicalType(
        kind=CanonicalTypeKind.ROW,
        fields=(
            id_field,
            tags_field,
            attributes_field,
        ),
    )

    assert data_type.kind == CanonicalTypeKind.ROW

    tags_type = data_type.fields[1].data_type
    assert tags_type.kind == CanonicalTypeKind.ARRAY
    assert tags_type.element_type is not None
    assert tags_type.element_type.kind == CanonicalTypeKind.STRING

    attributes_type = data_type.fields[2].data_type
    assert attributes_type.kind == CanonicalTypeKind.MAP
    assert attributes_type.key_type is not None
    assert attributes_type.value_type is not None
    assert attributes_type.key_type.kind == CanonicalTypeKind.STRING
    assert attributes_type.value_type.kind == CanonicalTypeKind.VARCHAR
    assert attributes_type.value_type.length == 100


def test_canonical_type_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        CanonicalType.model_validate(
            {
                "kind": CanonicalTypeKind.INT,
                "unknown_field": 123,
            }
        )


def test_table_identity_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        TableIdentity.model_validate(
            {
                "system": SourceSystem.SQLSERVER,
                "catalog": "user",
                "schema": "dbo",
                "table": "UserInfo",
                "unexpected": "value",
            }
        )
