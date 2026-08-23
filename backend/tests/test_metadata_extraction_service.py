import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.services.metadata_extraction_service import (
    extract_database_metadata,
)


class TestMetadataExtraction(unittest.TestCase):

    # ========================================================
    # SQLITE — FULL SCHEMA EXTRACTION
    # ========================================================

    def test_sqlite_schema_extraction(self):
        with tempfile.TemporaryDirectory() as temp_dir:

            database_path = Path(temp_dir) / "test.db"

            connection = sqlite3.connect(
                database_path
            )

            cursor = connection.cursor()

            # Test schema only.
            # These are definitions, not business records.
            cursor.execute(
                """
                CREATE TABLE Customer (
                    CustomerID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Name VARCHAR(100) NOT NULL,
                    Email VARCHAR(150),
                    Phone VARCHAR(20)
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE Invoice (
                    InvoiceID INTEGER PRIMARY KEY AUTOINCREMENT,
                    CustomerID INTEGER NOT NULL,
                    InvoiceNo VARCHAR(50) NOT NULL,
                    Total DECIMAL(10,2),
                    FOREIGN KEY (
                        CustomerID
                    )
                    REFERENCES Customer(CustomerID)
                )
                """
            )

            cursor.execute(
                """
                CREATE INDEX idx_invoice_customer
                ON Invoice(CustomerID)
                """
            )

            cursor.execute(
                """
                CREATE VIEW CustomerInvoices AS
                SELECT
                    InvoiceID,
                    CustomerID,
                    InvoiceNo
                FROM Invoice
                """
            )

            connection.commit()
            connection.close()

            connection_request = MagicMock()

            connection_request.database_type = "sqlite"
            connection_request.database_name = str(
                database_path
            )

            result = extract_database_metadata(
                connection_request
            )

            self.assertEqual(
                result["database_type"],
                "sqlite",
            )

            self.assertEqual(
                result["database_name"],
                str(database_path),
            )

            table_names = {
                table["name"]
                for table in result["tables"]
            }

            self.assertIn(
                "Customer",
                table_names,
            )

            self.assertIn(
                "Invoice",
                table_names,
            )

            view_names = {
                view["name"]
                for view in result["views"]
            }

            self.assertIn(
                "CustomerInvoices",
                view_names,
            )

            invoice = next(
                table
                for table in result["tables"]
                if table["name"] == "Invoice"
            )

            column_names = {
                column["name"]
                for column in invoice["columns"]
            }

            self.assertIn(
                "InvoiceID",
                column_names,
            )

            self.assertIn(
                "CustomerID",
                column_names,
            )

            self.assertIn(
                "InvoiceNo",
                column_names,
            )

            primary_keys = invoice[
                "primary_keys"
            ]

            self.assertIn(
                "InvoiceID",
                primary_keys,
            )

            foreign_keys = invoice[
                "foreign_keys"
            ]

            self.assertTrue(
                any(
                    fk["column"] == "CustomerID"
                    and fk["referenced_table"]
                    == "Customer"
                    and fk["referenced_column"]
                    == "CustomerID"
                    for fk in foreign_keys
                )
            )

            indexes = invoice["indexes"]

            self.assertTrue(
                any(
                    "CustomerID"
                    in index["columns"]
                    for index in indexes
                )
            )

            invoice_id = next(
                column
                for column in invoice["columns"]
                if column["name"] == "InvoiceID"
            )

            self.assertTrue(
                invoice_id["primary_key"]
            )

            self.assertTrue(
                invoice_id["auto_increment"]
            )

            customer_id = next(
                column
                for column in invoice["columns"]
                if column["name"] == "CustomerID"
            )

            self.assertFalse(
                customer_id["nullable"]
            )

            self.assertIn(
                "NOT NULL",
                customer_id["constraints"],
            )

    # ========================================================
    # SQLITE — IN-MEMORY DATABASE
    # ========================================================

    def test_sqlite_memory_database(self):

        connection_request = MagicMock()

        connection_request.database_type = "sqlite"
        connection_request.database_name = ":memory:"

        result = extract_database_metadata(
            connection_request
        )

        self.assertEqual(
            result["database_type"],
            "sqlite",
        )

        self.assertEqual(
            result["database_name"],
            ":memory:",
        )

        self.assertEqual(
            result["tables"],
            [],
        )

        self.assertEqual(
            result["views"],
            [],
        )

    # ========================================================
    # SQLITE — PATH SECURITY
    # ========================================================

    def test_sqlite_path_outside_root_is_rejected(self):

        with tempfile.TemporaryDirectory() as temp_dir:

            connection_request = MagicMock()

            connection_request.database_type = "sqlite"
            connection_request.database_name = (
                "../outside.db"
            )

            with patch.dict(
                "os.environ",
                {
                    "SQLITE_DATABASE_ROOT": temp_dir
                },
                clear=False,
            ):

                with self.assertRaises(
                    ValueError
                ):
                    extract_database_metadata(
                        connection_request
                    )

    # ========================================================
    # UNSUPPORTED DATABASE
    # ========================================================

    def test_unsupported_database_type(self):

        connection_request = MagicMock()

        connection_request.database_type = (
            "unsupported_database"
        )

        connection_request.database_name = "test"

        with self.assertRaises(
            ValueError
        ):
            extract_database_metadata(
                connection_request
            )

    # ========================================================
    # MYSQL — METADATA QUERY ONLY
    # ========================================================

    @patch("pymysql.connect")
    def test_mysql_metadata_query_only(
        self,
        mock_connect,
    ):

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_connect.return_value = (
            mock_connection
        )

        mock_connection.cursor.return_value = (
            mock_cursor
        )

        mock_cursor.fetchall.side_effect = [
            [
                (
                    "Customer",
                    "BASE TABLE",
                )
            ],
            [
                (
                    "CustomerID",
                    "int",
                    "NO",
                    "PRI",
                    "auto_increment",
                    None,
                )
            ],
            [],
            [],
        ]

        connection_request = MagicMock()

        connection_request.database_type = "mysql"
        connection_request.database_name = "test_db"
        connection_request.host = "localhost"
        connection_request.port = 3306
        connection_request.username = "test"
        connection_request.password = "test"

        result = extract_database_metadata(
            connection_request
        )

        self.assertEqual(
            result["database_type"],
            "mysql",
        )

        queries = [
            call.args[0]
            for call in mock_cursor.execute.call_args_list
        ]

        for query in queries:

            self.assertNotIn(
                "SELECT *",
                query.upper(),
            )

        mock_connection.close.assert_called_once()

    # ========================================================
    # POSTGRESQL — METADATA QUERY ONLY
    # ========================================================

    @patch("psycopg2.connect")
    def test_postgresql_metadata_query_only(
        self,
        mock_connect,
    ):

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_connect.return_value = (
            mock_connection
        )

        mock_connection.cursor.return_value = (
            mock_cursor
        )

        mock_cursor.fetchall.side_effect = [
            [],
        ]

        connection_request = MagicMock()

        connection_request.database_type = (
            "postgresql"
        )

        connection_request.database_name = (
            "test_db"
        )

        connection_request.host = "localhost"
        connection_request.port = 5432
        connection_request.username = "test"
        connection_request.password = "test"

        result = extract_database_metadata(
            connection_request
        )

        self.assertEqual(
            result["database_type"],
            "postgresql",
        )

        queries = [
            call.args[0]
            for call in mock_cursor.execute.call_args_list
        ]

        for query in queries:

            self.assertNotIn(
                "SELECT *",
                query.upper(),
            )

        mock_connection.close.assert_called_once()

    # ========================================================
    # MONGODB — COLLECTION METADATA ONLY
    # ========================================================

    @patch("pymongo.MongoClient")
    def test_mongodb_collection_metadata(
        self,
        mock_client,
    ):

        client = MagicMock()
        database = MagicMock()

        mock_client.return_value = client

        client.__getitem__.return_value = (
            database
        )

        database.list_collection_names.return_value = [
            "Customer",
            "Invoice",
        ]

        connection_request = MagicMock()

        connection_request.database_type = (
            "mongodb"
        )

        connection_request.database_name = (
            "metadata_dashboard"
        )

        connection_request.connection_string = (
            "mongodb://localhost:27017/"
        )

        result = extract_database_metadata(
            connection_request
        )

        collection_names = {
            table["name"]
            for table in result["tables"]
        }

        self.assertEqual(
            collection_names,
            {
                "Customer",
                "Invoice",
            },
        )

        client.admin.command.assert_called_once_with(
            "ping"
        )

        database.list_collection_names.assert_called_once()

        client.close.assert_called_once()

    # ========================================================
    # DYNAMODB — TABLE METADATA ONLY
    # ========================================================

    @patch("boto3.client")
    def test_dynamodb_metadata(
        self,
        mock_client,
    ):

        dynamodb = MagicMock()

        mock_client.return_value = (
            dynamodb
        )

        dynamodb.list_tables.return_value = {
            "TableNames": [
                "Customer",
                "Invoice",
            ]
        }

        connection_request = MagicMock()

        connection_request.database_type = (
            "dynamodb"
        )

        connection_request.aws_region = (
            "ap-south-1"
        )

        connection_request.aws_access_key_id = None
        connection_request.aws_secret_access_key = None

        result = extract_database_metadata(
            connection_request
        )

        table_names = {
            table["name"]
            for table in result["tables"]
        }

        self.assertEqual(
            table_names,
            {
                "Customer",
                "Invoice",
            },
        )

        dynamodb.list_tables.assert_called_once()

    # ========================================================
    # CASSANDRA — DRIVER FAILURE IS HANDLED
    # ========================================================

    @patch(
        "builtins.__import__",
        side_effect=ImportError(
            "Cassandra driver unavailable"
        ),
    )
    def test_cassandra_failure(
        self,
        mock_import,
    ):

        connection_request = MagicMock()

        connection_request.database_type = (
            "cassandra"
        )

        connection_request.host = (
            "localhost"
        )

        connection_request.port = 9042

        connection_request.keyspace = (
            "metadata_dashboard"
        )

        with self.assertRaises(
            ValueError
        ):
            extract_database_metadata(
                connection_request
            )


if __name__ == "__main__":
    unittest.main()