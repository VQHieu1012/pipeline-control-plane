import pytest
from unittest.mock import Mock

from control_plane.adapters.sqlserver.query_executor import PyodbcSqlServerExecutor


def test_executor_executes_query_with_parameters() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []

    connection = Mock()
    connection.cursor.return_value = cursor

    executor = PyodbcSqlServerExecutor(connection)  # type: ignore[arg-type]

    executor.fetch_all(
        "SELECT * FROM sys.tables WHERE name = ?",
        ("users",),
    )

    cursor.execute.assert_called_once_with(
        "SELECT * FROM sys.tables WHERE name = ?",
        "users",
    )


def test_executor_fetches_all_rows() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = [
        ("dbo", "users"),
        ("dbo", "orders"),
    ]

    connection = Mock()
    connection.cursor.return_value = cursor

    executor = PyodbcSqlServerExecutor(connection)

    result = executor.fetch_all(
        "SELECT schema_name, table_name FROM tables where schema_name = ?",
        ("dbo",),
    )

    assert result == (
        ("dbo", "users"),
        ("dbo", "orders"),
    )


def test_executor_closes_cursor_after_fetch() -> None:
    cursor = Mock()
    cursor.fetchall.return_value = []

    connection = Mock()
    connection.cursor.return_value = cursor

    executor = PyodbcSqlServerExecutor(connection)  # type: ignore[arg-type]

    executor.fetch_all("SELECT 1")

    cursor.close.assert_called_once_with()


def test_executor_closes_cursor_when_fetch_fails() -> None:
    cursor = Mock()
    cursor.fetchall.side_effect = RuntimeError("boom")

    connection = Mock()
    connection.cursor.return_value = cursor

    executor = PyodbcSqlServerExecutor(connection)  # type: ignore[arg-type]

    with pytest.raises(RuntimeError, match="boom"):
        executor.fetch_all("SELECT 1")

    cursor.close.assert_called_once_with()
