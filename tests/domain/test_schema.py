import pytest
from pydantic import ValidationError

from control_plane.domain.schema import (
    CanonicalSchema,
    CanonicalType,
    CanonicalTypeKind,
    Column,
    NativeTypeMetadata,
    PrimaryKey,
    SourceSystem,
    TableIdentity,
)


def test_valid_scalar_schema() -> None:
    schema = CanonicalSchema(
        schema_version=1,
        table=TableIdentity(
            system=SourceSystem.SQLSERVER, catalog="sales", schema="dbo", table="orders"
        ),
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


"""
String
length = 10 -> valid
length = 0 -> invalid
lenght = -1 -> invalid
"""


@pytest.mark.parametrize(
    "kind",
    [
        CanonicalTypeKind.CHAR,
        CanonicalTypeKind.VARCHAR,
        CanonicalTypeKind.BINARY,
        CanonicalTypeKind.VARBINARY,
    ],
)
def test_length_bearing_type_accept_positive_length(kind: CanonicalTypeKind) -> None:
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
def test_length_bearing_type_reject_non_positive_length(
    kind: CanonicalTypeKind, length: int
) -> None:
    with pytest.raises(ValueError, match="requires length > 0"):
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
