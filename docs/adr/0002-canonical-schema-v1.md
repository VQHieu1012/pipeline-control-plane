# ADR 0002: CanonicalSchema as the Platform-Owned Schema Contract

## Status

Accepted

## Context

The pipeline control plane must work with metadata originating from multiple database systems, including:

- SQL Server,
- MySQL,
- MariaDB,
- PostgreSQL.

The same source schema will later be consumed by several different parts of the platform, including:

- Flink planning,
- Kafka and Schema Registry integration,
- Avro schema generation,
- Elasticsearch mapping generation,
- ClickHouse DDL generation,
- schema validation,
- pipeline reconciliation.

Each source and downstream system has its own type system and metadata representation.

For example:

```text
SQL Server metadata
MySQL metadata
PostgreSQL metadata
```

are not structurally identical.

Likewise:

```text
PyFlink DataType
Avro schema
Elasticsearch mapping
ClickHouse type
```

represent different downstream concerns.

Without an intermediate platform-owned model, components would need to understand source-specific metadata directly.

A possible flow would become:

```text
SQL Server metadata
        |
        +--> Flink planner
        +--> Avro generator
        +--> Elasticsearch generator
        +--> ClickHouse generator
```

and separately:

```text
MySQL metadata
        |
        +--> Flink planner
        +--> Avro generator
        +--> Elasticsearch generator
        +--> ClickHouse generator
```

This would cause source-specific rules to leak across the entire control plane.

Another possible approach is to use PyFlink's type system as the platform schema representation.

However, PyFlink types are designed for Flink planning and execution rather than for preserving complete database metadata.

Important source information may include:

```text
native type name
unsigned semantics
identity
auto increment
charset
collation
vendor-specific properties
```

These properties may not map directly into a Flink logical type.

Using PyFlink types as the central domain model would also couple the control-plane domain layer to a particular execution engine.

## Decision

The control plane will define and own a database-independent schema representation named:

```text
CanonicalSchema
```

The architecture will use the following boundary:

```text
Source metadata
      |
      v
Source adapter
      |
      v
CanonicalSchema
      |
      +--> Flink planner
      |
      +--> Avro renderer
      |
      +--> Elasticsearch renderer
      |
      +--> ClickHouse renderer
      |
      +--> other downstream consumers
```

Source adapters are responsible for converting native database metadata into `CanonicalSchema`.

Downstream components are responsible for converting `CanonicalSchema` into their own required representation.

## Canonical logical types

CanonicalSchema defines its own logical type vocabulary.

Examples include:

```text
INT
BIGINT
DECIMAL
VARCHAR
TIMESTAMP
ARRAY
MAP
ROW
```

These logical types are inspired by common relational and Flink logical types but are owned by the control-plane domain model.

CanonicalSchema does not expose PyFlink `DataType` objects directly.

## Native metadata preservation

Canonical logical types alone are not sufficient to represent all important source information.

Therefore each column also preserves native database metadata.

For example:

```text
MySQL source:

BIGINT UNSIGNED
```

may become:

```text
Canonical type:
BIGINT

Native metadata:
type_name = BIGINT
unsigned = true
```

Similarly:

```text
PostgreSQL UUID
```

may become:

```text
Canonical type:
STRING

Native metadata:
type_name = uuid
full_type = uuid
```

This allows the platform to retain source semantics without expanding the canonical logical type vocabulary for every vendor-specific type.

## Separation of responsibilities

The architecture establishes the following responsibilities.

### Source adapters

Source adapters understand:

```text
native database metadata
        ↓
CanonicalSchema
```

Examples:

```text
SQL Server adapter
MySQL adapter
PostgreSQL adapter
```

### CanonicalSchema

CanonicalSchema understands:

- table identity,
- canonical logical types,
- native metadata,
- column ordering,
- nullability,
- primary keys,
- unique keys,
- schema-level invariants.

CanonicalSchema does not understand:

- JDBC execution,
- PyFlink APIs,
- Kafka topic creation,
- Elasticsearch APIs,
- ClickHouse APIs.

### Downstream renderers and planners

Downstream components understand:

```text
CanonicalSchema
        ↓
target representation
```

Examples:

```text
CanonicalSchema → Flink DataType
CanonicalSchema → Flink DDL
CanonicalSchema → Avro schema
CanonicalSchema → Elasticsearch mapping
CanonicalSchema → ClickHouse DDL
```

## Deterministic representation

CanonicalSchema must be deterministic.

Column order is therefore part of the contract.

Columns must already be ordered by their source ordinal.

CanonicalSchema does not silently sort columns during validation.

Invalid ordering is rejected.

This allows callers to detect malformed discovery output instead of having the domain model silently repair it.

## Strict validation

CanonicalSchema uses strict validation.

Examples of invalid state include:

- duplicate column names,
- duplicate ordinals,
- unordered columns,
- invalid logical-type parameters,
- primary keys referencing unknown columns,
- unique keys referencing unknown columns,
- duplicate members inside a key constraint,
- unknown model fields.

The purpose of strict validation is to make invalid metadata fail at the domain boundary rather than propagate into planners and provisioners.

## Serialization

CanonicalSchema must support lossless serialization and deserialization.

The following operation must preserve semantic equality:

```text
CanonicalSchema
→ JSON
→ CanonicalSchema
```

This allows the model to be stored in PostgreSQL, transmitted through APIs, included in pipeline plans, or compared during future reconciliation workflows.

Internal Python field names may differ from external aliases when necessary.

For example:

```text
Python:
schema_name

External contract:
schema
```

Validation accepts supported internal names and aliases while maintaining a single internal field representation.

## Consequences

### Positive consequences

#### Source isolation

Source-specific type handling is isolated inside source adapters.

Downstream components no longer need to know whether the original table came from SQL Server, MySQL, or PostgreSQL except when native metadata is intentionally inspected.

#### Execution-engine independence

The domain model is not coupled to PyFlink.

A future execution engine can consume the same canonical representation without redesigning source discovery.

#### Reusable downstream generation

Multiple target representations can be generated from the same schema contract.

```text
                +--> Flink
                |
CanonicalSchema +--> Avro
                |
                +--> Elasticsearch
                |
                +--> ClickHouse
```

#### Better testing

Schema validation can be tested independently from:

- databases,
- Flink clusters,
- Kafka,
- Elasticsearch,
- ClickHouse.

#### Durable control-plane state

CanonicalSchema can be serialized and persisted as part of desired or observed pipeline state.

### Negative consequences

#### Additional mapping layer

Every supported source database requires a native-to-canonical mapping implementation.

Every downstream system requires a canonical-to-target mapping implementation.

#### Canonical vocabulary must be maintained

The platform now owns the semantics of CanonicalType and must evolve the contract carefully.

#### Some native information has no canonical equivalent

Vendor-specific details may need to remain in `NativeTypeMetadata` rather than becoming first-class canonical types.

#### Schema evolution requires explicit versioning

Future changes to CanonicalSchema may require schema contract versioning and compatibility rules.

These concerns are accepted because they provide a stable architectural boundary.

## Alternatives considered

### Alternative 1: Use source-native metadata everywhere

Example:

```text
SQL Server metadata → Flink planner
SQL Server metadata → Avro generator
SQL Server metadata → Elasticsearch generator
```

This was rejected because it would cause every downstream component to understand every source database.

Adding another database would require changes across many unrelated modules.

## Alternative 2: Use PyFlink DataType as the canonical model

Example:

```text
Source metadata
      ↓
PyFlink DataType
      ↓
all downstream processing
```

This was rejected because:

- PyFlink is execution-engine specific,
- PyFlink types do not preserve all native source metadata,
- the domain layer would become coupled to Flink,
- non-Flink consumers would depend on a Flink-specific representation.

PyFlink remains an important downstream consumer of CanonicalSchema, but not the owner of the schema contract.

## Alternative 3: Use Avro schema as the canonical model

This was rejected because Avro is primarily a serialization schema.

It does not naturally represent every piece of relational metadata required by the control plane, including:

- source identity,
- native type information,
- primary-key semantics,
- unique constraints,
- source ordinals.

Avro schema generation will instead consume CanonicalSchema.

## Alternative 4: Define canonical types but discard native metadata

This was rejected because canonical logical types may collapse important source distinctions.

Examples include:

```text
BIGINT vs BIGINT UNSIGNED
VARCHAR with source charset/collation
PostgreSQL UUID vs generic STRING
identity/auto-increment semantics
```

CanonicalSchema therefore stores both:

```text
logical representation
+
native metadata
```

## Future work

This ADR establishes only the schema boundary.

Future decisions will define:

- source introspection interfaces,
- database-specific type mappings,
- CanonicalType to Flink DataType mapping,
- schema compatibility classification,
- schema evolution handling,
- schema hashing,
- schema version comparison,
- rollout behavior when source schemas change.