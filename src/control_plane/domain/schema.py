from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DomainModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
    )


class SourceSystem(StrEnum):
    SQLSERVER = "sqlserver"
    MYSQL = "mysql"
    MARIADB = "mariadb"
    POSTGRESQL = "postgresql"


class TableIdentity(DomainModel):
    system: SourceSystem

    catalog: str | None = None
    schema_name: str | None = Field(default=None, alias="schema")

    table: str


class CanonicalTypeKind(StrEnum):
    BOOLEAN = "BOOLEAN"

    TINYINT = "TINYINT"
    SMALLINT = "SMALLINT"
    INT = "INT"
    BIGINT = "BIGINT"

    DECIMAL = "DECIMAL"
    FLOAT = "FLOAT"
    DOUBLE = "DOUBLE"

    CHAR = "CHAR"
    VARCHAR = "VARCHAR"
    STRING = "STRING"

    BINARY = "BINARY"
    VARBINARY = "VARBINARY"
    BYTES = "BYTES"

    DATE = "DATE"
    TIME = "TIME"
    TIMESTAMP = "TIMESTAMP"
    TIMESTAMP_LTZ = "TIMESTAMP_LTZ"

    ARRAY = "ARRAY"
    MAP = "MAP"
    ROW = "ROW"

    RAW = "RAW"


ALLOWED_TYPE_PARAMETERS = {
    CanonicalTypeKind.DECIMAL: {"precision", "scale"},
    CanonicalTypeKind.CHAR: {"length"},
    CanonicalTypeKind.VARCHAR: {"length"},
    CanonicalTypeKind.BINARY: {"length"},
    CanonicalTypeKind.VARBINARY: {"length"},
    CanonicalTypeKind.TIME: {"precision"},
    CanonicalTypeKind.TIMESTAMP: {"precision"},
    CanonicalTypeKind.TIMESTAMP_LTZ: {"precision"},
    CanonicalTypeKind.ARRAY: {"element_type"},
    CanonicalTypeKind.MAP: {"key_type", "value_type"},
    CanonicalTypeKind.ROW: {"fields"},
}

TYPE_PARAMETER_FIELDS = {
    "length",
    "precision",
    "scale",
    "element_type",
    "key_type",
    "value_type",
    "fields",
}


class NativeTypeMetadata(DomainModel):
    type_name: str
    full_type: str | None = None

    jdbc_type_code: int | None = None

    precision: int | None = None
    scale: int | None = None
    length: int | None = None

    unsigned: bool | None = None
    fixed_length: bool | None = None

    charset: str | None = None
    collation: str | None = None

    auto_increment: bool | None = None
    identity: bool | None = None

    vendor_properties: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict
    )


class CanonicalField(DomainModel):
    name: str
    data_type: CanonicalType
    nullable: bool = True


class CanonicalType(DomainModel):
    kind: CanonicalTypeKind

    length: int | None = None

    precision: int | None = None
    scale: int | None = None

    element_type: CanonicalType | None = None

    key_type: CanonicalType | None = None
    value_type: CanonicalType | None = None

    fields: tuple[CanonicalField, ...] = ()

    def _validate_allowed_parameters(self) -> None:
        allowed = ALLOWED_TYPE_PARAMETERS.get(self.kind, set())

        supplied = self.model_fields_set & TYPE_PARAMETER_FIELDS
        invalid = supplied - allowed

        if invalid:
            invalid_names = ", ".join(sorted(invalid))

            raise ValueError(
                f"{self.kind} does not allow parameters: " f"{invalid_names}"
            )

    @model_validator(mode="before")
    def apply_default(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        kind = data.get("kind")

        temporal_types = {
            CanonicalTypeKind.TIME,
            CanonicalTypeKind.TIMESTAMP,
            CanonicalTypeKind.TIMESTAMP_LTZ,
            "TIME",
            "TIMESTAMP",
            "TIMESTAMP_LTZ",
        }

        if kind in temporal_types and data.get("precision") is None:
            data = dict(data)
            data["precision"] = 3

        return data

    @model_validator(mode="after")
    def validate_type(self) -> CanonicalType:
        self._validate_allowed_parameters()

        if self.kind == CanonicalTypeKind.DECIMAL:
            if self.precision is None:
                raise ValueError("DECIMAL requires precision")
            if self.scale is None:
                raise ValueError("DECIMAL requires scale")

            if self.precision < 1:
                raise ValueError("DECIMAL precision must be >= 1")
            if not 0 <= self.scale <= self.precision:
                raise ValueError("DECIMAL scale must satisfy 0 <= scale <= precision")

        if self.kind in (  # noqa: SIM102
            CanonicalTypeKind.CHAR,
            CanonicalTypeKind.VARCHAR,
            CanonicalTypeKind.BINARY,
            CanonicalTypeKind.VARBINARY,
        ):
            if self.length is None or self.length <= 0:
                raise ValueError(f"{self.kind} requires length > 0")

        if self.kind in {
            CanonicalTypeKind.TIME,
            CanonicalTypeKind.TIMESTAMP,
            CanonicalTypeKind.TIMESTAMP_LTZ,
        }:
            if self.precision is None:
                raise ValueError(f"{self.kind} requires precision")

            if not 0 <= self.precision <= 9:
                raise ValueError(f"{self.kind} must satisfy 0 <= precision <= 9")

        if self.kind == CanonicalTypeKind.MAP:  # noqa: SIM102
            if self.key_type is None or self.value_type is None:
                raise ValueError("MAP requires key_type and value_type")

        if self.kind == CanonicalTypeKind.ARRAY:  # noqa: SIM102
            if self.element_type is None:
                raise ValueError("ARRAY requires element_type")

        if self.kind == CanonicalTypeKind.ROW:
            if not self.fields:
                raise ValueError("ROW requires fields")

            names = [field.name for field in self.fields]

            if len(names) != len(set(names)):
                raise ValueError("ROW contains duplicate field names")

        return self


class Column(DomainModel):
    name: str

    ordinal: int = Field(ge=1)

    data_type: CanonicalType

    nullable: bool

    native: NativeTypeMetadata

    default_expression: str | None = None

    generated: bool = False
    generated_expression: str | None = None
    comment: str | None = None


class PrimaryKey(DomainModel):
    name: str | None = None
    columns: tuple[str, ...]
    source_enforced: bool = True


class UniqueKey(DomainModel):
    name: str | None = None
    columns: tuple[str, ...]
    source_enforced: bool = True


class CanonicalSchema(DomainModel):
    schema_version: int = 1

    table: TableIdentity

    columns: tuple[Column, ...]

    primary_key: PrimaryKey | None = None

    unique_keys: tuple[UniqueKey, ...] = ()

    native_properties: dict[
        str,
        str | int | float | bool | None,
    ] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_schema(self) -> CanonicalSchema:
        column_names = [column.name for column in self.columns]

        if len(column_names) != len(set(column_names)):
            raise ValueError("Duplicate column names")

        ordinals = [column.ordinal for column in self.columns]

        if len(ordinals) != len(set(ordinals)):
            raise ValueError("Duplicate column ordinals")

        if ordinals != sorted(ordinals):
            raise ValueError("columns must be ordered by ordinal")

        known_columns = set(column_names)

        if self.primary_key is not None:
            unknown = set(self.primary_key.columns) - known_columns

            if unknown:
                raise ValueError(f"primary key references unknown columns: {unknown}")

        for unique_key in self.unique_keys:
            unknown = set(unique_key.columns) - known_columns

            if unknown:
                raise ValueError(f"unique key references unknown columns: {unknown}")

        return self
