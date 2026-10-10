import pyodbc


class PyodbcSqlServerExecutor:
    def __init__(self, connection: pyodbc.Connection) -> None:
        self._connection = connection

    def fetch_all(
        self,
        query: str,
        params: tuple[object, ...] = (),
    ) -> tuple[tuple[object, ...], ...]:
        cursor = self._connection.cursor()

        try:
            cursor.execute(query, *params)
            rows = cursor.fetchall()

            return tuple(tuple(row) for row in rows)  # type: ignore
        finally:
            cursor.close()
