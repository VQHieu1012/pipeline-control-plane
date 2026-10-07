# CanonicalSchema V1

## Purpose

CanonicalSchema is the platform-owned, database-independent representation of a source table.

It acts as the stable contract between:

- source metadata discovery
- pipeline planning
- downstream resource generation

The model must preserve enough information to represent the source table accurately without coupling the control plane directly to a database driver, PyFlink, Avro, Elasticsearch, Clickhouse, or another downstream system.

The intended flow is:

```
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

- Database-independent logical types
- preservation of native database metadata
- deterministic column ordering
- explicit primary-key and unique-key metadata
- support for nested logical types
- strict validation
- lossless JSON round-trip
- stable semantics for downstream planners and renderers

CanonicalSchema must not depend on:

- database drivers
- PyFlink
- sink-specific libraries
- serialization-specific libraries such as Avro

## Core model

The root model is:

```
CanonicalSchema
```

Conceptually:

```
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

TableIdentity identifies the native source table.

It contains:

```
system
catalog
schema
table
```

The Python field corresponding to the external schema field is named `schema_name` to avoid collision with Pydantic APIs.

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

Each Column represents one source column.

A column contains:

```
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

## Columns invariants

A column ordinal must satisfy:

```
ordinal >= 1
```

Column names are preserved exactly as discovered from the source system.

Validation involving relationships between multiple columns is performed at the CanonicalSchema level rather than inside an individual Column.

## Canonical logical types

V1 supports the following logical type vocabulary.

### Boolean

```
BOOLEAN
```

### Integer

```
TINYINT
SMALLINT
INT
BIGINT
```

### Numeric

```
DECIMAL
FLOAT
DOUBLE
```

### Character

```
CHAR
VARCHAR
STRING
```

### Binary

```
BINARY
VARBINARY
BYTES
```

### Temporal

```
DATE
TIME
TIMESTAMP
TIMESTAMP_LTZ
```

### Nested

```
ARRAY
MAP
ROW
```

### FALLBACK

```
RAW
```

The canonical logical type is intentionally different from the source-native database type.

For example:

```
MySQL BIGINT UNSIGNED
```

may be represented as:

```
Canonical kind: BIGINT
Native metadata:
    type_name = BIGINT
    unsigned = true
```

This allows downstream systems to reason about logical type while preserving source-specific information.

## Type parameters

