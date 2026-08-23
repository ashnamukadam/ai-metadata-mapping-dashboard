import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PermissionValidationResult:
    message: str
    database_type: str
    database_name: str
    connected: bool
    metadata_access: bool
    metadata_only: bool


def _result(
    database_type: str,
    database_name: str,
    connected: bool,
    metadata_access: bool,
    message: str,
) -> PermissionValidationResult:
    return PermissionValidationResult(
        message=message,
        database_type=database_type,
        database_name=database_name,
        connected=connected,
        metadata_access=metadata_access,
        metadata_only=True,
    )


def _sanitize_error(exc: Exception) -> str:
    """
    Return a safe error message.

    Credentials, connection strings, tokens and secret values
    must never be returned to the client or written to logs.
    """

    message = str(exc)

    sensitive_terms = (
        "password",
        "secret_access_key",
        "aws_secret",
        "private_key",
        "access_token",
        "authorization",
    )

    lowered = message.lower()

    if any(term in lowered for term in sensitive_terms):
        return "Metadata permission validation failed."

    if "://" in message and "@" in message:
        return "Metadata permission validation failed."

    return message[:500]


# ============================================================
# MYSQL
# ============================================================

def _validate_mysql(
    connection: Any,
) -> PermissionValidationResult:

    conn = None

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

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT TABLE_NAME
            FROM information_schema.tables
            WHERE table_schema = %s
            LIMIT 1
            """,
            (connection.database_name,),
        )

        cursor.fetchone()
        cursor.close()

        return _result(
            "mysql",
            connection.database_name,
            True,
            True,
            "MySQL metadata permission validated successfully.",
        )

    except Exception as exc:
        safe_error = _sanitize_error(exc)

        logger.warning(
            "MySQL metadata permission validation failed: %s",
            safe_error,
        )

        return _result(
            "mysql",
            connection.database_name,
            False,
            False,
            f"MySQL metadata permission validation failed: {safe_error}",
        )

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# POSTGRESQL
# ============================================================

def _validate_postgresql(
    connection: Any,
) -> PermissionValidationResult:

    conn = None

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

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_catalog = %s
            LIMIT 1
            """,
            (connection.database_name,),
        )

        cursor.fetchone()
        cursor.close()

        return _result(
            "postgresql",
            connection.database_name,
            True,
            True,
            "PostgreSQL metadata permission validated successfully.",
        )

    except Exception as exc:
        safe_error = _sanitize_error(exc)

        logger.warning(
            "PostgreSQL metadata permission validation failed: %s",
            safe_error,
        )

        return _result(
            "postgresql",
            connection.database_name,
            False,
            False,
            (
                "PostgreSQL metadata permission validation failed: "
                f"{safe_error}"
            ),
        )

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# SQL SERVER
# ============================================================

def _validate_sqlserver(
    connection: Any,
) -> PermissionValidationResult:

    conn = None

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
                False,
                (
                    "SQL Server metadata permission validation failed: "
                    "Microsoft ODBC Driver 17 or 18 is not installed."
                ),
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

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT TOP 1 TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            """
        )

        cursor.fetchone()
        cursor.close()

        return _result(
            "sqlserver",
            connection.database_name,
            True,
            True,
            "SQL Server metadata permission validated successfully.",
        )

    except Exception as exc:
        safe_error = _sanitize_error(exc)

        logger.warning(
            "SQL Server metadata permission validation failed: %s",
            safe_error,
        )

        return _result(
            "sqlserver",
            connection.database_name,
            False,
            False,
            (
                "SQL Server metadata permission validation failed: "
                f"{safe_error}"
            ),
        )

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# ORACLE
# ============================================================

def _validate_oracle(
    connection: Any,
) -> PermissionValidationResult:

    conn = None

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

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT OWNER
            FROM ALL_TABLES
            FETCH FIRST 1 ROWS ONLY
            """
        )

        cursor.fetchone()
        cursor.close()

        return _result(
            "oracle",
            connection.database_name,
            True,
            True,
            "Oracle metadata permission validated successfully.",
        )

    except Exception as exc:
        safe_error = _sanitize_error(exc)

        logger.warning(
            "Oracle metadata permission validation failed: %s",
            safe_error,
        )

        return _result(
            "oracle",
            connection.database_name,
            False,
            False,
            (
                "Oracle metadata permission validation failed: "
                f"{safe_error}"
            ),
        )

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# SQLITE
# ============================================================

def _validate_sqlite(
    connection: Any,
) -> PermissionValidationResult:

    import os
    import sqlite3
    from pathlib import Path

    conn = None

    try:
        database_name = connection.database_name

        # SQLite's in-memory database is a valid special database
        # name and must not be converted into a filesystem path.
        if database_name == ":memory:":
            final_database = ":memory:"

        else:
            root = os.getenv("SQLITE_DATABASE_ROOT")

            if root:
                database_path = Path(database_name)

                if database_path.is_absolute():
                    final_path = database_path
                else:
                    root_path = Path(root).resolve()

                    final_path = (
                        root_path / database_path
                    ).resolve()

                    try:
                        final_path.relative_to(root_path)
                    except ValueError as exc:
                        raise ValueError(
                            "SQLite database path must remain "
                            "inside SQLITE_DATABASE_ROOT."
                        ) from exc

                final_database = str(final_path)

            else:
                final_database = str(
                    Path(database_name)
                )

        conn = sqlite3.connect(
            final_database
        )

        cursor = conn.cursor()

        # METADATA ONLY.
        # sqlite_master contains schema metadata, not business records.
        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type IN ('table', 'view')
            LIMIT 1
            """
        )

        cursor.fetchone()
        cursor.close()

        return _result(
            "sqlite",
            database_name,
            True,
            True,
            "SQLite metadata permission validated successfully.",
        )

    except Exception as exc:
        safe_error = _sanitize_error(exc)

        logger.warning(
            "SQLite metadata permission validation failed: %s",
            safe_error,
        )

        return _result(
            "sqlite",
            connection.database_name,
            False,
            False,
            (
                "SQLite metadata permission validation failed: "
                f"{safe_error}"
            ),
        )

    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# MONGODB
# ============================================================

def _validate_mongodb(
    connection: Any,
) -> PermissionValidationResult:

    client = None

    try:
        from pymongo import MongoClient

        client = MongoClient(
            connection.connection_string,
            serverSelectionTimeoutMS=5000,
        )

        client.admin.command("ping")

        database_name = (
            getattr(
                connection,
                "database_name",
                None,
            )
            or "N/A"
        )

        # METADATA ONLY.
        if database_name != "N/A":
            database = client[database_name]
            database.list_collection_names()

        return _result(
            "mongodb",
            database_name,
            True,
            True,
            "MongoDB metadata permission validated successfully.",
        )

    except Exception as exc:
        safe_error = _sanitize_error(exc)

        logger.warning(
            "MongoDB metadata permission validation failed: %s",
            safe_error,
        )

        return _result(
            "mongodb",
            getattr(
                connection,
                "database_name",
                None,
            )
            or "N/A",
            False,
            False,
            f"MongoDB metadata permission validation failed: {safe_error}",
        )

    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass


# ============================================================
# DYNAMODB
# ============================================================

def _validate_dynamodb(
    connection: Any,
) -> PermissionValidationResult:

    try:
        import boto3

        region = (
            getattr(
                connection,
                "aws_region",
                None,
            )
            or getattr(
                connection,
                "region",
                None,
            )
        )

        if not region:
            return _result(
                "dynamodb",
                "AWS DynamoDB",
                False,
                False,
                "DynamoDB metadata validation failed: AWS region is required.",
            )

        client_kwargs = {
            "region_name": region,
        }

        access_key = getattr(
            connection,
            "aws_access_key_id",
            None,
        )

        secret_key = getattr(
            connection,
            "aws_secret_access_key",
            None,
        )

        if access_key and secret_key:
            client_kwargs["aws_access_key_id"] = access_key
            client_kwargs["aws_secret_access_key"] = secret_key

        client = boto3.client(
            "dynamodb",
            **client_kwargs,
        )

        # METADATA ONLY.
        client.list_tables(
            Limit=1
        )

        return _result(
            "dynamodb",
            "AWS DynamoDB",
            True,
            True,
            "DynamoDB metadata permission validated successfully.",
        )

    except Exception as exc:
        safe_error = _sanitize_error(exc)

        logger.warning(
            "DynamoDB metadata permission validation failed: %s",
            safe_error,
        )

        return _result(
            "dynamodb",
            "AWS DynamoDB",
            False,
            False,
            (
                "DynamoDB metadata permission validation failed: "
                f"{safe_error}"
            ),
        )


# ============================================================
# CASSANDRA
# ============================================================

def _validate_cassandra(
    connection: Any,
) -> PermissionValidationResult:

    try:
        from cassandra.auth import PlainTextAuthProvider
        from cassandra.cluster import Cluster

    except Exception:
        return _result(
            "cassandra",
            connection.keyspace,
            False,
            False,
            (
                "Cassandra metadata validation failed: "
                "Cassandra driver is unavailable or incompatible "
                "with the current Python environment."
            ),
        )

    cluster = None
    session = None

    try:
        auth_provider = None

        username = getattr(
            connection,
            "username",
            None,
        )

        password = getattr(
            connection,
            "password",
            None,
        )

        if username and password:
            auth_provider = PlainTextAuthProvider(
                username=username,
                password=password,
            )

        cluster_kwargs = {
            "contact_points": [
                connection.host
            ],
            "port": connection.port,
        }

        if auth_provider is not None:
            cluster_kwargs[
                "auth_provider"
            ] = auth_provider

        cluster = Cluster(
            **cluster_kwargs
        )

        session = cluster.connect(
            connection.keyspace
        )

        # METADATA ONLY.
        session.execute(
            """
            SELECT keyspace_name
            FROM system_schema.keyspaces
            LIMIT 1
            """
        )

        return _result(
            "cassandra",
            connection.keyspace,
            True,
            True,
            "Cassandra metadata permission validated successfully.",
        )

    except Exception as exc:
        safe_error = _sanitize_error(exc)

        logger.warning(
            "Cassandra metadata permission validation failed: %s",
            safe_error,
        )

        return _result(
            "cassandra",
            connection.keyspace,
            False,
            False,
            (
                "Cassandra metadata permission validation failed: "
                f"{safe_error}"
            ),
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
# MAIN DISPATCHER
# ============================================================

def validate_metadata_permission(
    connection: Any,
) -> PermissionValidationResult:

    database_type = (
        getattr(
            connection,
            "database_type",
            "",
        )
        or ""
    ).lower()

    if database_type == "mysql":
        return _validate_mysql(connection)

    if database_type in {
        "postgresql",
        "postgres",
    }:
        return _validate_postgresql(connection)

    if database_type in {
        "sqlserver",
        "sql_server",
        "mssql",
    }:
        return _validate_sqlserver(connection)

    if database_type == "oracle":
        return _validate_oracle(connection)

    if database_type == "sqlite":
        return _validate_sqlite(connection)

    if database_type == "mongodb":
        return _validate_mongodb(connection)

    if database_type == "dynamodb":
        return _validate_dynamodb(connection)

    if database_type == "cassandra":
        return _validate_cassandra(connection)

    return _result(
        database_type or "unknown",
        getattr(
            connection,
            "database_name",
            None,
        )
        or getattr(
            connection,
            "keyspace",
            None,
        )
        or "N/A",
        False,
        False,
        f"Unsupported database type: {database_type or 'unknown'}",
    )


validate_metadata_permission.__test__ = False