import json
import logging
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================
# RESPONSE OBJECT
# ============================================================

@dataclass
class DatabaseConnectionResult:
    message: str
    database_type: str
    database_name: str
    connected: bool


def _result(
    database_type: str,
    database_name: str,
    connected: bool,
    message: str,
) -> DatabaseConnectionResult:
    return DatabaseConnectionResult(
        message=message,
        database_type=database_type,
        database_name=database_name,
        connected=connected,
    )


def _sanitize_error(exc: Exception) -> str:
    """
    Sanitize errors so credentials and sensitive information
    are never returned to the client or logs.
    """

    message = str(exc)

    sensitive_values = [
        os.getenv("DATABASE_URL", ""),
        os.getenv("SECRET_KEY", ""),
        os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        os.getenv("AWS_ACCESS_KEY_ID", ""),
    ]

    for value in sensitive_values:
        if value:
            message = message.replace(value, "[REDACTED]")

    # Avoid exposing credential-bearing URLs.
    if "://" in message and "@" in message:
        return "Database connection failed. Check the supplied connection configuration."

    return message[:500]


# ============================================================
# FIREBASE SERVICE ACCOUNT
# ============================================================

def validate_firebase_service_account(
    service_account: dict,
) -> None:

    if not isinstance(service_account, dict):
        raise ValueError(
            "Firebase service account JSON must contain an object."
        )

    required_fields = {
        "type",
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "client_id",
        "auth_uri",
        "token_uri",
    }

    missing = required_fields - set(service_account.keys())

    if missing:
        raise ValueError(
            "Invalid Firebase service account: required fields are missing."
        )

    if service_account.get("type") != "service_account":
        raise ValueError(
            "Invalid Firebase service account: type must be 'service_account'."
        )


def parse_firebase_service_account(
    service_account: Any,
) -> dict:

    if isinstance(service_account, dict):
        data = service_account

    elif isinstance(service_account, (bytes, bytearray)):
        try:
            data = json.loads(
                service_account.decode("utf-8")
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(
                "Firebase service account contains invalid JSON."
            ) from exc

    elif isinstance(service_account, str):
        try:
            data = json.loads(service_account)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Firebase service account contains invalid JSON."
            ) from exc

    else:
        raise ValueError(
            "Firebase service account must be a JSON object, string, or bytes."
        )

    validate_firebase_service_account(data)

    return data


# ============================================================
# MYSQL
# ============================================================

def _test_mysql(connection: Any) -> DatabaseConnectionResult:

    try:
        import pymysql

        conn = pymysql.connect(
            host=connection.host,
            port=connection.port,
            database=connection.database_name,
            user=connection.username,
            password=connection.password,
            connect_timeout=5,
        )

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        finally:
            conn.close()

        return _result(
            "mysql",
            connection.database_name,
            True,
            "MySQL connection successful",
        )

    except Exception as exc:

        safe_error = _sanitize_error(exc)

        logger.warning(
            "MySQL connection failed: %s",
            safe_error,
        )

        return _result(
            "mysql",
            connection.database_name,
            False,
            f"MySQL connection failed: {safe_error}",
        )


# ============================================================
# POSTGRESQL
# ============================================================

def _test_postgresql(connection: Any) -> DatabaseConnectionResult:

    try:
        import psycopg2

        conn = psycopg2.connect(
            host=connection.host,
            port=connection.port,
            dbname=connection.database_name,
            user=connection.username,
            password=connection.password,
            connect_timeout=5,
        )

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        finally:
            conn.close()

        return _result(
            "postgresql",
            connection.database_name,
            True,
            "PostgreSQL connection successful",
        )

    except Exception as exc:

        safe_error = _sanitize_error(exc)

        logger.warning(
            "PostgreSQL connection failed: %s",
            safe_error,
        )

        return _result(
            "postgresql",
            connection.database_name,
            False,
            f"PostgreSQL connection failed: {safe_error}",
        )


# ============================================================
# SQL SERVER
# ============================================================

def _test_sqlserver(connection: Any) -> DatabaseConnectionResult:

    try:
        import pyodbc

        drivers = pyodbc.drivers()

        sql_driver = next(
            (
                driver
                for driver in drivers
                if "ODBC Driver 18 for SQL Server" in driver
            ),
            None,
        )

        if sql_driver is None:
            sql_driver = next(
                (
                    driver
                    for driver in drivers
                    if "ODBC Driver 17 for SQL Server" in driver
                ),
                None,
            )

        if sql_driver is None:
            return _result(
                "sqlserver",
                connection.database_name,
                False,
                "SQL Server connection failed: Microsoft ODBC Driver 17 or 18 for SQL Server is not installed.",
            )

        connection_string = (
            f"DRIVER={{{sql_driver}}};"
            f"SERVER={connection.host},{connection.port};"
            f"DATABASE={connection.database_name};"
            f"UID={connection.username};"
            f"PWD={connection.password};"
            "TrustServerCertificate=yes;"
            "Connection Timeout=5;"
        )

        conn = pyodbc.connect(connection_string)

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        finally:
            conn.close()

        return _result(
            "sqlserver",
            connection.database_name,
            True,
            "SQL Server connection successful",
        )

    except Exception as exc:

        safe_error = _sanitize_error(exc)

        logger.warning(
            "SQL Server connection failed: %s",
            safe_error,
        )

        return _result(
            "sqlserver",
            connection.database_name,
            False,
            f"SQL Server connection failed: {safe_error}",
        )


# ============================================================
# ORACLE
# ============================================================

def _test_oracle(connection: Any) -> DatabaseConnectionResult:

    try:
        import oracledb

        dsn = oracledb.makedsn(
            connection.host,
            connection.port,
            service_name=connection.database_name,
        )

        conn = oracledb.connect(
            user=connection.username,
            password=connection.password,
            dsn=dsn,
        )

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            cursor.fetchone()
            cursor.close()
        finally:
            conn.close()

        return _result(
            "oracle",
            connection.database_name,
            True,
            "Oracle connection successful",
        )

    except Exception as exc:

        safe_error = _sanitize_error(exc)

        logger.warning(
            "Oracle connection failed: %s",
            safe_error,
        )

        return _result(
            "oracle",
            connection.database_name,
            False,
            f"Oracle connection failed: {safe_error}",
        )


# ============================================================
# SQLITE
# ============================================================

def _resolve_sqlite_path(database_name: str) -> str:

    root = os.getenv("SQLITE_DATABASE_ROOT")

    if not root:
        return database_name

    database_path = Path(database_name)

    # Absolute path supplied by caller.
    if database_path.is_absolute():
        return str(database_path)

    # Keep SQLite databases inside configured root.
    root_path = Path(root).resolve()
    final_path = (root_path / database_path).resolve()

    try:
        final_path.relative_to(root_path)
    except ValueError as exc:
        raise ValueError(
            "SQLite database path must remain inside SQLITE_DATABASE_ROOT."
        ) from exc

    return str(final_path)


def _test_sqlite(connection: Any) -> DatabaseConnectionResult:

    try:

        database_path = _resolve_sqlite_path(
            connection.database_name
        )

        conn = sqlite3.connect(
            database_path
        )

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
        finally:
            conn.close()

        return _result(
            "sqlite",
            connection.database_name,
            True,
            "SQLite connection successful",
        )

    except Exception as exc:

        safe_error = _sanitize_error(exc)

        logger.warning(
            "SQLite connection failed: %s",
            safe_error,
        )

        return _result(
            "sqlite",
            connection.database_name,
            False,
            f"SQLite connection failed: {safe_error}",
        )


# ============================================================
# MONGODB
# ============================================================

def _test_mongodb(connection: Any) -> DatabaseConnectionResult:

    try:

        from pymongo import MongoClient

        client = MongoClient(
            connection.connection_string,
            serverSelectionTimeoutMS=5000,
        )

        try:
            client.admin.command("ping")
        finally:
            client.close()

        return _result(
            "mongodb",
            getattr(
                connection,
                "database_name",
                "N/A",
            ),
            True,
            "MongoDB connection successful",
        )

    except Exception as exc:

        safe_error = _sanitize_error(exc)

        logger.warning(
            "MongoDB connection failed: %s",
            safe_error,
        )

        return _result(
            "mongodb",
            getattr(
                connection,
                "database_name",
                "N/A",
            ),
            False,
            f"MongoDB connection failed: {safe_error}",
        )


# ============================================================
# DYNAMODB
# ============================================================

def _test_dynamodb(connection: Any) -> DatabaseConnectionResult:

    try:

        import boto3

        if not connection.region:
            return _result(
                "dynamodb",
                "AWS DynamoDB",
                False,
                "DynamoDB connection failed: AWS region is required.",
            )

        client_kwargs = {
            "region_name": connection.region,
        }

        if (
            getattr(
                connection,
                "aws_access_key_id",
                None,
            )
            and getattr(
                connection,
                "aws_secret_access_key",
                None,
            )
        ):
            client_kwargs[
                "aws_access_key_id"
            ] = connection.aws_access_key_id

            client_kwargs[
                "aws_secret_access_key"
            ] = connection.aws_secret_access_key

        client = boto3.client(
            "dynamodb",
            **client_kwargs,
        )

        client.list_tables(
            Limit=1
        )

        return _result(
            "dynamodb",
            "AWS DynamoDB",
            True,
            "DynamoDB connection successful",
        )

    except Exception as exc:

        safe_error = _sanitize_error(exc)

        logger.warning(
            "DynamoDB connection failed: %s",
            safe_error,
        )

        return _result(
            "dynamodb",
            "AWS DynamoDB",
            False,
            f"DynamoDB connection failed: {safe_error}",
        )


# ============================================================
# CASSANDRA
# ============================================================

def _test_cassandra(connection: Any) -> DatabaseConnectionResult:

    try:

        # IMPORTANT:
        # Lazy import prevents Cassandra compatibility problems
        # from crashing FastAPI during application startup.

        from cassandra.cluster import Cluster
        from cassandra.auth import PlainTextAuthProvider

    except Exception as exc:

        safe_error = _sanitize_error(exc)

        logger.warning(
            "Cassandra driver unavailable: %s",
            safe_error,
        )

        return _result(
            "cassandra",
            connection.keyspace,
            False,
            "Cassandra driver is unavailable or incompatible with the current Python environment.",
        )

    cluster = None
    session = None

    try:

        auth_provider = None

        if (
            getattr(
                connection,
                "username",
                None,
            )
            and getattr(
                connection,
                "password",
                None,
            )
        ):
            auth_provider = PlainTextAuthProvider(
                username=connection.username,
                password=connection.password,
            )

        cluster_kwargs = {
            "contact_points": [
                connection.host
            ],
            "port": connection.port,
        }

        if auth_provider:
            cluster_kwargs[
                "auth_provider"
            ] = auth_provider

        cluster = Cluster(
            **cluster_kwargs
        )

        session = cluster.connect(
            connection.keyspace
        )

        session.execute(
            "SELECT release_version FROM system.local"
        )

        return _result(
            "cassandra",
            connection.keyspace,
            True,
            "Cassandra connection successful",
        )

    except Exception as exc:

        safe_error = _sanitize_error(exc)

        logger.warning(
            "Cassandra connection failed: %s",
            safe_error,
        )

        return _result(
            "cassandra",
            connection.keyspace,
            False,
            f"Cassandra connection failed: {safe_error}",
        )

    finally:

        if session is not None:
            try:
                session.shutdown()
            except Exception:
                pass

        if cluster is not None:
            try:
                cluster.shutdown()
            except Exception:
                pass


# ============================================================
# MAIN DATABASE DISPATCHER
# ============================================================

def test_database_connection(
    connection: Any,
) -> DatabaseConnectionResult:

    database_type = (
        getattr(
            connection,
            "database_type",
            "",
        )
        or ""
    ).lower()

    if database_type == "mysql":
        return _test_mysql(connection)

    if database_type in {
        "postgresql",
        "postgres",
    }:
        return _test_postgresql(connection)

    if database_type in {
        "sqlserver",
        "sql_server",
        "mssql",
    }:
        return _test_sqlserver(connection)

    if database_type == "oracle":
        return _test_oracle(connection)

    if database_type == "sqlite":
        return _test_sqlite(connection)

    if database_type == "mongodb":
        return _test_mongodb(connection)

    if database_type == "dynamodb":
        return _test_dynamodb(connection)

    if database_type == "cassandra":
        return _test_cassandra(connection)

    return _result(
        database_type or "unknown",
        getattr(
            connection,
            "database_name",
            "N/A",
        ),
        False,
        f"Unsupported database type: {database_type or 'unknown'}",
    )


# ============================================================
# BACKWARD-COMPATIBILITY ALIAS
# ============================================================

def check_database_connection(
    connection: Any,
) -> DatabaseConnectionResult:
    """
    Compatibility wrapper expected by the existing test suite
    and any existing callers.
    """

    return test_database_connection(
        connection
    )


# Prevent pytest from treating service functions as tests.
test_database_connection.__test__ = False
check_database_connection.__test__ = False


# ============================================================
# FIREBASE FIRESTORE
# ============================================================

def test_firebase_connection(
    service_account: Any,
) -> DatabaseConnectionResult:

    try:

        service_account = parse_firebase_service_account(
            service_account
        )

        import firebase_admin
        from firebase_admin import credentials
        from firebase_admin import firestore

        try:
            app = firebase_admin.get_app()

        except ValueError:

            credential = credentials.Certificate(
                service_account
            )

            app = firebase_admin.initialize_app(
                credential
            )

        db = firestore.client(
            app=app
        )

        # Force Firestore client creation/access.
        db.collections()

        return _result(
            "firebase",
            service_account.get(
                "project_id",
                "Firebase",
            ),
            True,
            "Firebase Firestore connection successful",
        )

    except Exception as exc:

        safe_error = _sanitize_error(exc)

        logger.warning(
            "Firebase connection failed: %s",
            safe_error,
        )

        return _result(
            "firebase",
            "Firebase",
            False,
            f"Firebase connection failed: {safe_error}",
        )


test_firebase_connection.__test__ = False