# CanonicalSchema V1

## Purpose

`CanonicalSchema` is the platform-owned, database-independent representation of a source table.

It acts as the stable contract between:

- source metadata discovery,
- pipeline planning,
- downstream resource generation.

The model must preserve enough information to represent the source table accurately without coupling the control plane directly to a database driver, PyFlink, Avro, Elasticsearch, ClickHouse, or another downstream system.

The intended flow is:

```text
Source database metadata
        |
        v
Source adapter
        |
        v
CanonicalSchema
        |
        +--> Flink planning
        |
        +--> Avro schema generation
        |
        +--> Elasticsearch mapping
        |
        +--> ClickHouse DDL
        |
        +--> Other downstream representations
```

## Design goals

CanonicalSchema V1 is designed to provide:

- database-independent logical types,
- preservation of native database metadata,
- deterministic column ordering,
- explicit primary-key and unique-key metadata,
- support for nested logical types,
- strict validation,
- lossless JSON round-trip,
- stable semantics for downstream planners and renderers.

CanonicalSchema must not depend on:

- database drivers,
- PyFlink,
- sink-specific libraries,
- serialization-specific libraries such as Avro.

## Core model

The root model is:

```python
CanonicalSchema
```

Conceptually:

```text
CanonicalSchema
├── schema_version
├── table
│   └── TableIdentity
├── columns
│   └── tuple[Column, ...]
├── primary_key
│   └── PrimaryKey | None
├── unique_keys
│   └── tuple[UniqueKey, ...]
└── native_properties
```

## Table identity

`TableIdentity` identifies the native source table.

It contains:

```text
system
catalog
schema
table
```

The Python field corresponding to the external `schema` field is named `schema_name` to avoid collision with Pydantic APIs.

Example external representation:

```json
{
  "system": "sqlserver",
  "catalog": "sales",
  "schema": "dbo",
  "table": "orders"
}
```

Native identifiers are preserved exactly.

CanonicalSchema does not lowercase, uppercase, trim, or otherwise normalize native table or column names.

## Columns

Each `Column` represents one source column.

A column contains:

```text
name
ordinal
data_type
nullable
native
default_expression
generated
generated_expression
comment
```

### Column invariants

A column ordinal must satisfy:

```text
ordinal >= 1
```

Column names are preserved exactly as discovered from the source system.

Validation involving relationships between multiple columns is performed at the `CanonicalSchema` level rather than inside an individual `Column`.

## Canonical logical types

V1 supports the following logical type vocabulary.

### Boolean

```text
BOOLEAN
```

### Integer

```text
TINYINT
SMALLINT
INT
BIGINT
```

### Numeric

```text
DECIMAL
FLOAT
DOUBLE
```

### Character

```text
CHAR
VARCHAR
STRING
```

### Binary

```text
BINARY
VARBINARY
BYTES
```

### Temporal

```text
DATE
TIME
TIMESTAMP
TIMESTAMP_LTZ
```

### Nested

```text
ARRAY
MAP
ROW
```

### Fallback

```text
RAW
```

The canonical logical type is intentionally different from the source-native database type.

For example:

```text
MySQL BIGINT UNSIGNED
```

may be represented as:

```text
Canonical kind: BIGINT
Native metadata:
    type_name = BIGINT
    unsigned = true
```

This allows downstream systems to reason about logical type while preserving source-specific information.

## Type parameters

Different logical types allow different parameters.

### DECIMAL

Allowed parameters:

```text
precision
scale
```

Required invariants:

```text
precision >= 1
0 <= scale <= precision
```

Both precision and scale must be present.

Examples:

```text
DECIMAL(18, 2)   valid
DECIMAL(1, 0)    valid
DECIMAL(18, 18)  valid
DECIMAL(0, 0)    invalid
DECIMAL(18, -1)  invalid
DECIMAL(18, 19)  invalid
```

### Length-bearing types

The following types use `length`:

```text
CHAR
VARCHAR
BINARY
VARBINARY
```

Invariant:

```text
length > 0
```

### Temporal types

The following types support precision:

```text
TIME
TIMESTAMP
TIMESTAMP_LTZ
```

If precision is omitted, the canonical default is:

```text
3
```

Allowed range:

```text
0 <= precision <= 9
```

`DATE` does not use temporal precision.

### ARRAY

`ARRAY` requires:

```text
element_type
```

Example:

```text
ARRAY<STRING>
```

Nested arrays are allowed.

### MAP

`MAP` requires:

```text
key_type
value_type
```

Example:

```text
MAP<STRING, INT>
```

### ROW

`ROW` requires at least one field.

Each field is represented by `CanonicalField`.

Field names inside one ROW must be unique.

Example:

```text
ROW<
    id INT,
    name STRING
>
```

## Nested logical types

Canonical types are recursive.

Examples include:

```text
ARRAY<ARRAY<INT>>
```

and:

```text
ROW<
    id INT,
    tags ARRAY<STRING>,
    attributes MAP<STRING, VARCHAR(100)>
>
```

Nested types must remain representable without depending on PyFlink or another downstream type system.

## Parameter validity

A logical type may only contain parameters that belong to that type.

Examples:

```text
VARCHAR(length=100)                     valid

VARCHAR(length=100, precision=10)       invalid

DECIMAL(precision=18, scale=2)          valid

DECIMAL(
    precision=18,
    scale=2,
    length=100
)                                       invalid

INT(length=10)                          invalid
```

Default or absent values do not make the canonical object semantically parameterized.

This is required so objects produced by CanonicalSchema serialization can be deserialized without violating their own type contract.

## Native type metadata

`NativeTypeMetadata` preserves information that may not exist in the canonical logical type vocabulary.

It may contain:

```text
type_name
full_type
jdbc_type_code
precision
scale
length
unsigned
fixed_length
charset
collation
auto_increment
identity
vendor_properties
```

Native metadata must not determine the canonical logical type by itself.

Source adapters are responsible for mapping native metadata into both:

```text
CanonicalType
+
NativeTypeMetadata
```

## Primary keys

A table may contain zero or one primary-key constraint.

Therefore:

```text
primary_key: PrimaryKey | None
```

A primary key may contain one or more columns.

Example:

```text
PRIMARY KEY (tenant_id, id)
```

is represented as one `PrimaryKey` containing:

```text
columns = ("tenant_id", "id")
```

### Primary-key invariants

A primary key:

- must contain at least one column,
- must not contain duplicate column names,
- must only reference columns that exist in the enclosing `CanonicalSchema`.

## Unique keys

A table may contain multiple unique constraints.

Therefore:

```text
unique_keys: tuple[UniqueKey, ...]
```

Each `UniqueKey` may itself contain multiple columns.

Example:

```text
UNIQUE (tenant_id, email)

UNIQUE (tenant_id, username)
```

is represented as two separate `UniqueKey` objects.

### Unique-key invariants

Each unique key:

- must contain at least one column,
- must not contain duplicate column names,
- must only reference columns that exist in the enclosing `CanonicalSchema`.

## Schema-level invariants

A valid `CanonicalSchema` guarantees:

### Unique column names

Column names must not be duplicated.

Example:

```text
id ordinal=1
id ordinal=2
```

is invalid.

### Unique ordinals

Column ordinals must not be duplicated.

Example:

```text
id        ordinal=1
user_name ordinal=1
```

is invalid.

### Deterministic ordering

Columns must already be ordered by ordinal.

Example:

```text
1, 2, 3
```

is valid.

```text
2, 1, 3
```

is invalid.

CanonicalSchema does not silently reorder columns.

V1 does not require ordinal values to be contiguous.

Therefore:

```text
1, 3, 7
```

may still be valid as long as ordering and uniqueness requirements are satisfied.

### Key references

All columns referenced by:

```text
PrimaryKey
UniqueKey
```

must exist in the schema.

This rule applies equally to single-column and composite keys.

## Unknown fields

All domain models use strict field validation.

Unknown fields are rejected.

For example:

```json
{
  "kind": "INT",
  "unexpected_field": 123
}
```

is invalid.

This prevents silently accepting unsupported contract fields.

## Serialization

CanonicalSchema must support lossless JSON round-trip:

```text
CanonicalSchema
        |
        v
JSON
        |
        v
CanonicalSchema
```

with no semantic loss.

Conceptually:

```python
payload = schema.model_dump_json(by_alias=True)

restored = CanonicalSchema.model_validate_json(payload)

assert restored == schema
```

Pydantic validation accepts both internal field names and configured aliases.

For `TableIdentity`:

```text
internal field name: schema_name
external alias:      schema
```

Both may be accepted as input, while external canonical serialization may use `schema`.

## Versioning

V1 currently uses:

```text
schema_version = 1
```

The version identifies the CanonicalSchema contract version, not the source database schema version.

Schema evolution, compatibility comparison, and schema hashing are outside the scope of M1.1.

## Out of scope

CanonicalSchema V1 does not implement:

- SQL Server metadata discovery,
- MySQL metadata discovery,
- MariaDB metadata discovery,
- PostgreSQL metadata discovery,
- native database type to CanonicalType mapping,
- CanonicalType to Flink DataType mapping,
- Avro schema generation,
- Elasticsearch mapping generation,
- ClickHouse DDL generation,
- schema evolution,
- compatibility classification,
- schema hashing,
- schema version comparison,
- pipeline provisioning,
- runtime reconciliation.

These capabilities consume or produce CanonicalSchema in later milestones but are not part of the V1 schema contract itself.