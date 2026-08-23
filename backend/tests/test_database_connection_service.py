import builtins
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pydantic import TypeAdapter, ValidationError

from app.schemas.database_connection import (
    CassandraConnectionRequest,
    DatabaseConnectionRequest,
    DynamoDBConnectionRequest,
    MongoDBConnectionRequest,
    MySQLConnectionRequest,
    PostgreSQLConnectionRequest,
    OracleConnectionRequest,
    SQLServerConnectionRequest,
    SQLiteConnectionRequest,
)

from app.services.database_connection_service import (
    test_database_connection,
    check_database_connection,
    parse_firebase_service_account,
    test_firebase_connection,
)


class TestDatabaseConnectionSchemas(unittest.TestCase):

    def test_unsupported_database_type(self):
        adapter = TypeAdapter(
            DatabaseConnectionRequest
        )

        with self.assertRaises(ValidationError):
            adapter.validate_python(
                {
                    "database_type": "redis"
                }
            )

    def test_missing_required_sql_fields(self):
        with self.assertRaises(ValidationError):
            MySQLConnectionRequest(
                database_type="mysql",
                host="localhost",
            )

    def test_mongodb_requires_connection_string(self):
        with self.assertRaises(ValidationError):
            MongoDBConnectionRequest(
                database_type="mongodb"
            )

    def test_dynamodb_credentials_must_be_a_pair(self):
        with self.assertRaises(ValidationError):
            DynamoDBConnectionRequest(
                database_type="dynamodb",
                region="ap-south-1",
                aws_access_key_id="example",
            )

    def test_cassandra_credentials_must_be_a_pair(self):
        with self.assertRaises(ValidationError):
            CassandraConnectionRequest(
                database_type="cassandra",
                host="localhost",
                keyspace="metadata",
                username="user",
            )


class TestDatabaseConnections(unittest.TestCase):

    def test_sqlite_success(self):

        with tempfile.TemporaryDirectory() as temp_dir:

            with patch.dict(
                os.environ,
                {
                    "SQLITE_DATABASE_ROOT": temp_dir
                },
                clear=False,
            ):

                request = SQLiteConnectionRequest(
                    database_type="sqlite",
                    database_name="test.db",
                )

                result = check_database_connection(
                    request
                )

                self.assertTrue(
                    result.connected
                )

                self.assertEqual(
                    result.database_type,
                    "sqlite",
                )

    @patch(
        "sqlite3.connect",
        side_effect=Exception(
            "database unavailable"
        ),
    )
    def test_sqlite_failure(
        self,
        mock_connect,
    ):

        request = SQLiteConnectionRequest(
            database_type="sqlite",
            database_name="test.db",
        )

        result = test_database_connection(
            request
        )

        self.assertFalse(
            result.connected
        )

    @patch("pymysql.connect")
    def test_mysql_connection_path(
        self,
        mock_connect,
    ):

        mock_connection = MagicMock()
        mock_connect.return_value = (
            mock_connection
        )

        request = MySQLConnectionRequest(
            database_type="mysql",
            host="localhost",
            port=3306,
            database_name="metadata",
            username="test",
            password="secret",
        )

        result = test_database_connection(
            request
        )

        self.assertTrue(
            result.connected
        )

        mock_connect.assert_called_once()
        mock_connection.close.assert_called_once()

    @patch("psycopg2.connect")
    def test_postgresql_connection_path(
        self,
        mock_connect,
    ):

        mock_connection = MagicMock()
        mock_connect.return_value = (
            mock_connection
        )

        request = PostgreSQLConnectionRequest(
            database_type="postgresql",
            host="localhost",
            port=5432,
            database_name="metadata_dashboard",
            username="postgres",
            password="secret",
        )

        result = test_database_connection(
            request
        )

        self.assertTrue(
            result.connected
        )

        mock_connection.close.assert_called_once()

    @patch("pyodbc.connect")
    @patch(
        "pyodbc.drivers",
        return_value=[
            "ODBC Driver 18 for SQL Server"
        ],
    )
    def test_sqlserver_connection_path(
        self,
        mock_drivers,
        mock_connect,
    ):

        mock_connection = MagicMock()
        mock_connect.return_value = (
            mock_connection
        )

        request = SQLServerConnectionRequest(
            database_type="sqlserver",
            host="localhost",
            port=1433,
            database_name="metadata",
            username="sa",
            password="secret",
        )

        result = test_database_connection(
            request
        )

        self.assertTrue(
            result.connected
        )

        mock_connection.close.assert_called_once()

    @patch("oracledb.connect")
    @patch("oracledb.ConnectParams")
    def test_oracle_connection_path(
        self,
        mock_params,
        mock_connect,
    ):

        mock_connection = MagicMock()
        mock_connect.return_value = (
            mock_connection
        )

        request = OracleConnectionRequest(
            database_type="oracle",
            host="localhost",
            port=1521,
            database_name="ORCL",
            username="system",
            password="secret",
        )

        result = test_database_connection(
            request
        )

        self.assertTrue(
            result.connected
        )

        mock_connection.close.assert_called_once()

    @patch("pymongo.MongoClient")
    def test_mongodb_unavailable(
        self,
        mock_client,
    ):

        from pymongo.errors import (
            ServerSelectionTimeoutError,
        )

        mock_client.side_effect = (
            ServerSelectionTimeoutError(
                "server unavailable"
            )
        )

        request = MongoDBConnectionRequest(
            database_type="mongodb",
            connection_string=(
                "mongodb://localhost:27017/"
            ),
        )

        result = test_database_connection(
            request
        )

        self.assertFalse(
            result.connected
        )

    def test_firebase_invalid_json(self):

        with self.assertRaises(
            ValueError
        ):
            parse_firebase_service_account(
                b"{invalid json"
            )

    @patch("boto3.client")
    def test_dynamodb_connection_path(
        self,
        mock_client,
    ):

        mock_dynamodb = MagicMock()

        mock_client.return_value = (
            mock_dynamodb
        )

        request = DynamoDBConnectionRequest(
            database_type="dynamodb",
            region="ap-south-1",
        )

        result = test_database_connection(
            request
        )

        self.assertTrue(
            result.connected
        )

        mock_dynamodb.list_tables.assert_called_once()

    def test_cassandra_compatibility_failure(
        self,
    ):

        real_import = builtins.__import__

        def blocked_cassandra_import(
            name,
            globals=None,
            locals=None,
            fromlist=(),
            level=0,
        ):

            if name.startswith(
                "cassandra"
            ):
                raise ImportError(
                    "asyncore compatibility unavailable"
                )

            return real_import(
                name,
                globals,
                locals,
                fromlist,
                level,
            )

        request = CassandraConnectionRequest(
            database_type="cassandra",
            host="localhost",
            port=9042,
            keyspace="metadata",
        )

        with patch(
            "builtins.__import__",
            side_effect=blocked_cassandra_import,
        ):

            result = test_database_connection(
                request
            )

        self.assertFalse(
            result.connected
        )


if __name__ == "__main__":
    unittest.main()