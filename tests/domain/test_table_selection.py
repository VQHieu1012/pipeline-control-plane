import pytest
from pydantic import ValidationError

from control_plane.domain.schema import SourceSystem
from control_plane.domain.table_selection import TableSelector, TableSelectorMode


def test_table_selection_mode_is_valid() -> None:
    mode = TableSelectorMode.EXACT
    assert mode == "exact"

    mode = TableSelectorMode.REGEX
    assert mode == "regex"


def test_table_selector_allows_exact_table() -> None:
    selector = TableSelector(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema="dbo",
        mode=TableSelectorMode.EXACT,
        table_expression="UserInfo",
    )

    assert selector.system == SourceSystem.SQLSERVER
    assert selector.catalog == "sales"
    assert selector.schema_name == "dbo"
    assert selector.mode == TableSelectorMode.EXACT
    assert selector.table_expression == "UserInfo"


def test_table_selector_allows_regex_table() -> None:
    selector = TableSelector(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema="dbo",
        mode=TableSelectorMode.REGEX,
        table_expression=r"^customer_.*$",
    )

    assert selector.mode == TableSelectorMode.REGEX
    assert selector.table_expression == r"^customer_.*$"


@pytest.mark.parametrize(
    "mode",
    [
        TableSelectorMode.EXACT,
        TableSelectorMode.REGEX,
    ],
)
def test_table_selector_rejects_empty_table_expression(
    mode: TableSelectorMode,
) -> None:
    with pytest.raises(ValidationError):
        TableSelector(
            system=SourceSystem.SQLSERVER,
            catalog="sales",
            schema="dbo",
            mode=mode,
            table_expression="",
        )


def test_table_selector_rejects_invalid_regex_expression() -> None:
    with pytest.raises(
        ValidationError,
        match="Invalid table regex",
    ):
        TableSelector(
            system=SourceSystem.SQLSERVER,
            catalog="sales",
            schema="dbo",
            mode=TableSelectorMode.REGEX,
            table_expression="[user",
        )


def test_exact_selector_allows_regex_like_characters() -> None:
    selector = TableSelector(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema="dbo",
        mode=TableSelectorMode.EXACT,
        table_expression="[user",
    )

    assert selector.table_expression == "[user"


def test_table_selector_is_valid() -> None:
    table_selector = TableSelector(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema="dbo",
        mode=TableSelectorMode.EXACT,
        table_expression="user",
    )

    assert table_selector.system == SourceSystem.SQLSERVER
    assert table_selector.catalog == "sales"
    assert table_selector.schema_name == "dbo"
    assert table_selector.table_expression == "user"


def test_table_selector_round_trips_through_json() -> None:
    table_selector = TableSelector(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema="dbo",
        mode=TableSelectorMode.EXACT,
        table_expression="user",
    )

    payload = table_selector.model_dump_json()
    restored = TableSelector.model_validate_json(payload)

    assert restored == table_selector


def test_table_selector_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        TableSelector.model_validate(
            {
                "system": SourceSystem.SQLSERVER,
                "catalog": "sales",
                "schema": "dbo",
                "mode": TableSelectorMode.EXACT,
                "table_expression": "user",
                "unexpected": "value",
            }
        )


def test_table_selector_serializes_schema_using_alias() -> None:
    selector = TableSelector(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema="dbo",
        mode=TableSelectorMode.EXACT,
        table_expression="user",
    )

    payload = selector.model_dump(by_alias=True)

    assert payload["schema"] == "dbo"
    assert "schema_name" not in payload


def test_regex_table_selector_round_trips_through_json() -> None:
    selector = TableSelector(
        system=SourceSystem.SQLSERVER,
        catalog="sales",
        schema="dbo",
        mode=TableSelectorMode.REGEX,
        table_expression=r"^customer_.*$",
    )

    payload = selector.model_dump_json(by_alias=True)
    restored = TableSelector.model_validate_json(payload)

    assert restored == selector
