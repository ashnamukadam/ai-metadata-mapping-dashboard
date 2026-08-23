import unittest
from unittest.mock import MagicMock, patch

from app.services.permission_validation_service import (
    validate_metadata_permission,
)


class TestPermissionValidation(unittest.TestCase):

    # ========================================================
    # UNSUPPORTED DATABASE
    # ========================================================

    def test_unsupported_database(self):
        connection = MagicMock()
        connection.database_type = "unsupported_db"
        connection.database_name = "test"

        result = validate_metadata_permission(connection)

        self.assertFalse(result.connected)
        self.assertFalse(result.metadata_access)
        self.assertTrue(result.metadata_only)

    # ========================================================
    # SQLITE METADATA SUCCESS
    # ========================================================

    def test_sqlite_metadata_success(self):
        connection = MagicMock()
        connection.database_type = "sqlite"
        connection.database_name = ":memory:"

        result = validate_metadata_permission(connection)

        self.assertTrue(result.connected)
        self.assertTrue(result.metadata_access)
        self.assertTrue(result.metadata_only)
        self.assertEqual(
            result.database_type,
            "sqlite",
        )

    # ========================================================
    # SQLITE DOES NOT READ BUSINESS DATA
    # ========================================================

    @patch("sqlite3.connect")
    def test_sqlite_uses_metadata_query_only(
        self,
        mock_connect,
    ):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        connection = MagicMock()
        connection.database_type = "sqlite"
        connection.database_name = "test.db"

        result = validate_metadata_permission(connection)

        self.assertTrue(result.connected)
        self.assertTrue(result.metadata_access)

        executed_queries = [
            call.args[0]
            for call in mock_cursor.execute.call_args_list
        ]

        for query in executed_queries:
            normalized = query.upper()

            self.assertNotIn(
                "SELECT *",
                normalized,
            )

            self.assertNotIn(
                " FROM CUSTOMER",
                normalized,
            )

            self.assertNotIn(
                " FROM INVOICE",
                normalized,
            )

        mock_connection.close.assert_called_once()

    # ========================================================
    # MYSQL METADATA PATH
    # ========================================================

    @patch("pymysql.connect")
    def test_mysql_metadata_path(
        self,
        mock_connect,
    ):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        connection = MagicMock()
        connection.database_type = "mysql"
        connection.database_name = "metadata_dashboard"
        connection.host = "localhost"
        connection.port = 3306
        connection.username = "test-user"
        connection.password = "test-password"

        result = validate_metadata_permission(connection)

        self.assertTrue(result.connected)
        self.assertTrue(result.metadata_access)
        self.assertTrue(result.metadata_only)

        query = mock_cursor.execute.call_args.args[0]

        self.assertIn(
            "information_schema.tables",
            query.lower(),
        )

        self.assertNotIn(
            "select *",
            query.lower(),
        )

        mock_connection.close.assert_called_once()

    # ========================================================
    # POSTGRESQL METADATA PATH
    # ========================================================

    @patch("psycopg2.connect")
    def test_postgresql_metadata_path(
        self,
        mock_connect,
    ):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        connection = MagicMock()
        connection.database_type = "postgresql"
        connection.database_name = "metadata_dashboard"
        connection.host = "localhost"
        connection.port = 5432
        connection.username = "test-user"
        connection.password = "test-password"

        result = validate_metadata_permission(connection)

        self.assertTrue(result.connected)
        self.assertTrue(result.metadata_access)
        self.assertTrue(result.metadata_only)

        query = mock_cursor.execute.call_args.args[0]

        self.assertIn(
            "information_schema.tables",
            query.lower(),
        )

        self.assertNotIn(
            "select *",
            query.lower(),
        )

        mock_connection.close.assert_called_once()

    # ========================================================
    # SQL SERVER METADATA PATH
    # ========================================================

    @patch("pyodbc.connect")
    @patch("pyodbc.drivers")
    def test_sqlserver_metadata_path(
        self,
        mock_drivers,
        mock_connect,
    ):
        mock_drivers.return_value = [
            "ODBC Driver 18 for SQL Server"
        ]

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        connection = MagicMock()
        connection.database_type = "sqlserver"
        connection.database_name = "metadata_dashboard"
        connection.host = "localhost"
        connection.port = 1433
        connection.username = "test-user"
        connection.password = "test-password"

        result = validate_metadata_permission(connection)

        self.assertTrue(result.connected)
        self.assertTrue(result.metadata_access)

        query = mock_cursor.execute.call_args.args[0]

        self.assertIn(
            "INFORMATION_SCHEMA.TABLES",
            query,
        )

        self.assertNotIn(
            "SELECT *",
            query.upper(),
        )

        mock_connection.close.assert_called_once()

    # ========================================================
    # SQL SERVER DRIVER MISSING
    # ========================================================

    @patch("pyodbc.drivers")
    def test_sqlserver_driver_missing(
        self,
        mock_drivers,
    ):
        mock_drivers.return_value = []

        connection = MagicMock()
        connection.database_type = "sqlserver"
        connection.database_name = "metadata_dashboard"
        connection.host = "localhost"
        connection.port = 1433
        connection.username = "test-user"
        connection.password = "test-password"

        result = validate_metadata_permission(connection)

        self.assertFalse(result.connected)
        self.assertFalse(result.metadata_access)
        self.assertTrue(result.metadata_only)

    # ========================================================
    # ORACLE METADATA PATH
    # ========================================================

    @patch("oracledb.connect")
    @patch("oracledb.makedsn")
    def test_oracle_metadata_path(
        self,
        mock_makedsn,
        mock_connect,
    ):
        mock_makedsn.return_value = "test-dsn"

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        connection = MagicMock()
        connection.database_type = "oracle"
        connection.database_name = "XEPDB1"
        connection.host = "localhost"
        connection.port = 1521
        connection.username = "test-user"
        connection.password = "test-password"

        result = validate_metadata_permission(connection)

        self.assertTrue(result.connected)
        self.assertTrue(result.metadata_access)

        query = mock_cursor.execute.call_args.args[0]

        self.assertIn(
            "ALL_TABLES",
            query.upper(),
        )

        self.assertNotIn(
            "SELECT *",
            query.upper(),
        )

        mock_connection.close.assert_called_once()

    # ========================================================
    # MONGODB METADATA PATH
    # ========================================================

    @patch("pymongo.MongoClient")
    def test_mongodb_metadata_path(
        self,
        mock_client,
    ):
        client = MagicMock()
        database = MagicMock()

        mock_client.return_value = client
        client.__getitem__.return_value = database

        connection = MagicMock()
        connection.database_type = "mongodb"
        connection.connection_string = (
            "mongodb://localhost:27017/"
        )
        connection.database_name = (
            "metadata_dashboard"
        )

        result = validate_metadata_permission(connection)

        self.assertTrue(result.connected)
        self.assertTrue(result.metadata_access)
        self.assertTrue(result.metadata_only)

        client.admin.command.assert_called_once_with(
            "ping"
        )

        database.list_collection_names.assert_called_once()

        client.close.assert_called_once()

    # ========================================================
    # DYNAMODB METADATA PATH
    # ========================================================

    @patch("boto3.client")
    def test_dynamodb_metadata_path(
        self,
        mock_client,
    ):
        dynamodb = MagicMock()
        mock_client.return_value = dynamodb

        connection = MagicMock()
        connection.database_type = "dynamodb"
        connection.region = "ap-south-1"
        connection.aws_access_key_id = None
        connection.aws_secret_access_key = None

        result = validate_metadata_permission(connection)

        self.assertTrue(result.connected)
        self.assertTrue(result.metadata_access)
        self.assertTrue(result.metadata_only)

        dynamodb.list_tables.assert_called_once_with(
            Limit=1
        )

    # ========================================================
    # CASSANDRA IMPORT / COMPATIBILITY FAILURE
    # ========================================================

    @patch(
        "builtins.__import__",
        side_effect=ImportError(
            "Cassandra driver unavailable"
        ),
    )
    def test_cassandra_import_failure(
        self,
        mock_import,
    ):
        connection = MagicMock()
        connection.database_type = "cassandra"
        connection.host = "localhost"
        connection.port = 9042
        connection.keyspace = "metadata_dashboard"

        result = validate_metadata_permission(connection)

        self.assertFalse(result.connected)
        self.assertFalse(result.metadata_access)
        self.assertTrue(result.metadata_only)

    # ========================================================
    # RESULT NEVER MARKS RECORD ACCESS AS ALLOWED
    # ========================================================

    def test_result_is_always_metadata_only(self):
        connection = MagicMock()
        connection.database_type = "unsupported_db"
        connection.database_name = "test"

        result = validate_metadata_permission(connection)

        self.assertTrue(
            result.metadata_only
        )


if __name__ == "__main__":
    unittest.main()