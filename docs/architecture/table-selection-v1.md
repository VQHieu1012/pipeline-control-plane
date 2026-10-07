# Table Selection V1

## Purpose

Table selection defines how the control plane represents a user's intent to select source tables before database discovery and schema introspection occur.

The contract separates:

```text
desired selection
        ↓
TableSelector
        ↓
source discovery / resolution
        ↓
0..N TableIdentity
```

`TableSelector` describes what the user wants.

`TableIdentity` describes one concrete source table that actually exists.

The selection contract does not perform database I/O and does not guarantee that a matching table currently exists.

## Design goals

Table Selection V1 is designed to provide:

- explicit exact-table selection,
- regex-based table selection,
- preservation of native identifiers,
- strict validation,
- database-driver independence,
- PyFlink independence,
- deterministic serialization,
- lossless JSON round-trip,
- a simple resolution output based on existing `TableIdentity`.

## Domain model

The main domain objects are:

```text
TableSelectorMode
TableSelector
TableIdentity
```

Conceptually:

```text
TableSelector
├── system
├── catalog
├── schema
├── mode
└── table_expression
```

A selector is later resolved into:

```text
tuple[TableIdentity, ...]
```

## TableSelectorMode

`TableSelectorMode` determines how `table_expression` must be interpreted.

V1 supports:

```text
EXACT
REGEX
```

### EXACT

`EXACT` means `table_expression` is a literal native table name.

Example:

```text
mode = EXACT
table_expression = UserInfo
```

The expression must not be interpreted as a regular expression.

For example:

```text
table_expression = [user
```

is a valid exact expression even though the same string would be an invalid regular expression.

The resolver will treat the expression as a literal table identifier.

### REGEX

`REGEX` means `table_expression` contains a regular-expression pattern.

Example:

```text
mode = REGEX
table_expression = ^customer_.*$
```

The expression must be syntactically valid as a regular expression.

Malformed expressions are rejected when the `TableSelector` is created.

For example:

```text
[user
```

is invalid in `REGEX` mode.

## TableSelector

`TableSelector` represents desired table-selection intent.

Conceptually:

```python
TableSelector(
    system=...,
    catalog=...,
    schema=...,
    mode=...,
    table_expression=...,
)
```

Example exact selector:

```text
system           = sqlserver
catalog          = sales
schema           = dbo
mode             = exact
table_expression = UserInfo
```

Example regex selector:

```text
system           = sqlserver
catalog          = sales
schema           = dbo
mode             = regex
table_expression = ^customer_.*$
```

## Source scope

In V1, `catalog` and `schema` define the source scope of the selector.

Only the table expression supports selection modes.

V1 does not support:

```text
catalog regex
schema regex
```

For example:

```text
catalog = sales
schema  = dbo
mode    = REGEX
table_expression = ^customer_.*
```

means:

> Search within the exact `sales.dbo` scope and select table names matching the expression.

This keeps the V1 selector contract intentionally narrow.

## Selection invariants

### Table expression must be non-empty

The following is invalid:

```text
mode = EXACT
table_expression = ""
```

The following is also invalid:

```text
mode = REGEX
table_expression = ""
```

### Regex expressions must be valid

For `REGEX` mode:

```text
^customer_.*$    valid
[user             invalid
```

Regex syntax validation is part of the `TableSelector` domain contract.

### Exact expressions are literal

For `EXACT` mode, regex syntax is irrelevant.

For example:

```text
mode = EXACT
table_expression = [user
```

is valid.

The selector does not attempt to determine whether an exact expression "looks like" a regex.

### Unknown fields are rejected

The domain models use strict validation.

For example:

```json
{
  "system": "sqlserver",
  "catalog": "sales",
  "schema": "dbo",
  "mode": "exact",
  "table_expression": "users",
  "unexpected": true
}
```

is invalid.

## Identifier preservation

Native source identifiers are preserved exactly.

The selector must not automatically:

- lowercase identifiers,
- uppercase identifiers,
- trim identifiers,
- case-fold identifiers,
- otherwise normalize native names.

For example:

```text
UserInfo
```

must remain:

```text
UserInfo
```

and must not silently become:

```text
userinfo
```

Source-specific identifier semantics belong to the source adapter or discovery implementation.

## Schema alias

Internally, the Python field is:

```text
schema_name
```

The external alias is:

```text
schema
```

This avoids collision with Pydantic APIs while retaining a natural external representation.

Example external representation:

```json
{
  "system": "sqlserver",
  "catalog": "sales",
  "schema": "dbo",
  "mode": "exact",
  "table_expression": "users"
}
```

Pydantic validation accepts both configured field names and aliases, while the internal representation remains consistent.

## Resolution semantics

`TableSelector` does not itself perform resolution.

A later discovery component receives a selector and returns concrete table identities.

Conceptually:

```text
TableSelector
        ↓
source discovery
        ↓
tuple[TableIdentity, ...]
```

### Exact example

Input:

```text
catalog          = sales
schema           = dbo
mode             = EXACT
table_expression = users
```

Possible result:

```text
(
    sales.dbo.users,
)
```

If the table does not exist, the resolution result may be empty.

### Regex example

Input:

```text
catalog          = sales
schema           = dbo
mode             = REGEX
table_expression = ^customer_.*
```

Suppose the source contains:

```text
customer_us
customer_eu
orders
customer_asia
```

The resolution result may be:

```text
(
    sales.dbo.customer_us,
    sales.dbo.customer_eu,
    sales.dbo.customer_asia,
)
```

One selector therefore resolves conceptually to:

```text
0..N TableIdentity
```

A selector never guarantees that at least one matching table exists.

## TableIdentity as the V1 resolution result

V1 does not introduce a separate `ResolvedTable` model.

The resolution output is:

```python
tuple[TableIdentity, ...]
```

This decision is intentional.

A wrapper such as:

```python
class ResolvedTable:
    identity: TableIdentity
```

would not add any semantic information beyond `TableIdentity`.

A dedicated resolved/discovered-table model should only be introduced when discovery produces information that cannot naturally belong to `TableIdentity`.

Possible future examples include:

```text
relation type
discovery-specific metadata
source capabilities
view/table classification
```

Until such a use case exists, introducing another domain object would add abstraction without adding meaning.

## Separation of responsibilities

### TableSelector

Responsible for:

- representing desired selection intent,
- distinguishing exact and regex selection,
- validating selector structure,
- validating regex syntax,
- preserving selector values.

Not responsible for:

- connecting to databases,
- listing tables,
- checking whether a table exists,
- applying source-specific identifier rules,
- reading column metadata,
- producing `CanonicalSchema`.

### Source discovery

Future source-discovery components will be responsible for:

```text
TableSelector
        ↓
database metadata lookup
        ↓
matching concrete tables
        ↓
TableIdentity(s)
```

Database-specific behavior belongs outside the selector domain model.

### Schema introspection

After a concrete table has been identified, schema introspection can produce:

```text
TableIdentity
        ↓
source introspection
        ↓
CanonicalSchema
```

Table selection and schema introspection are separate responsibilities.

## Regex matching semantics

M1.2 validates that regex expressions are syntactically valid.

M1.2 does not define the exact matching API used by the resolver.

For example, the choice between:

```text
re.match
re.search
re.fullmatch
```

is deferred to the discovery contract.

The selector only guarantees:

```text
mode = REGEX
→ table_expression is a valid regex
```

The resolution behavior will be defined together with `SourceIntrospector` / source discovery semantics.

## Serialization

`TableSelector` supports lossless JSON round-trip.

Conceptually:

```python
payload = selector.model_dump_json(by_alias=True)

restored = TableSelector.model_validate_json(payload)

assert restored == selector
```

This permits selectors to be:

- received from APIs,
- persisted as desired state,
- included in pipeline specifications,
- compared during reconciliation.

## Example flow

A user submits:

```text
Source:
    SQL Server

Scope:
    catalog = sales
    schema  = dbo

Selection:
    mode = REGEX
    expression = ^customer_.*
```

The control plane represents this as:

```text
TableSelector
```

A discovery component later resolves it:

```text
TableSelector
        ↓
SQL Server discovery
        ↓
sales.dbo.customer_us
sales.dbo.customer_eu
sales.dbo.customer_asia
```

Each result is represented as a `TableIdentity`.

Schema discovery may then operate independently:

```text
TableIdentity
        ↓
Source introspection
        ↓
CanonicalSchema
```

## Out of scope

Table Selection V1 does not implement:

- live database discovery,
- SQL Server metadata queries,
- MySQL/MariaDB metadata queries,
- PostgreSQL metadata queries,
- `information_schema` queries,
- exact-versus-regex matching execution,
- `SourceIntrospector`,
- column discovery,
- native type mapping,
- `CanonicalSchema` generation,
- detection of newly created matching tables,
- polling or reconciliation,
- Kafka Connect configuration,
- Kafka topic creation,
- Flink planning,
- pipeline provisioning.

These capabilities consume `TableSelector` in subsequent milestones.

## V1 contract summary

The V1 flow is:

```text
User desired intent
        ↓
TableSelector
        ↓
future source discovery
        ↓
0..N TableIdentity
        ↓
future schema introspection
        ↓
CanonicalSchema
```

`TableSelector` answers:

> Which tables does the user want?

`TableIdentity` answers:

> Which concrete table is this?

`CanonicalSchema` answers:

> What does this concrete table look like?
```

Tài liệu này phù hợp với quyết định hiện tại là defer `ResolvedTable` cho đến khi có metadata discovery thực sự cần một domain object riêng.