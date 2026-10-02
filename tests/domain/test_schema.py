from control_plane.domain.schema import *
import pytest
from pydantic import ValidationError


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
    data_type = CanonicalType(kind=CanonicalTypeKind.DECIMAL, precision=200, scale=2)

    assert data_type.kind == CanonicalTypeKind.DECIMAL
    assert data_type.precision == 200
    assert data_type.scale == 2


def test_decimal_is_invalid_without_precision() -> None:
    with pytest.raises(ValidationError, match="DECIMAL"):
        CanonicalType(kind=CanonicalTypeKind.DECIMAL, scale=20)


def test_decimal_is_invalid_without_scale() -> None:
    with pytest.raises(ValidationError, match="scale"):
        CanonicalType(kind=CanonicalTypeKind.DECIMAL, precision=200)


def test_decimal_is_invalid_with_invalid_precicion() -> None:
    with pytest.raises(ValidationError, match=">="):
        CanonicalType(kind=CanonicalTypeKind.DECIMAL, precision=0, scale=10)


def test_decimal_is_invalid_with_invalid_scale() -> None:
    with pytest.raises(ValidationError):
        CanonicalType(kind=CanonicalTypeKind.DECIMAL, precision=20, scale=-1)
