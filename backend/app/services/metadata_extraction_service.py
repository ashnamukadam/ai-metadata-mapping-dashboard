from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import quote_plus


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class ColumnMetadata:
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    auto_increment: bool = False
    default: Any = None
    constraints: list[str] = field(default_factory=list)


@dataclass
class IndexMetadata:
    name: str
    columns: list[str] = field(default_factory=list)
    unique: bool = False


@dataclass
class ConstraintMetadata:
    name: str
    constraint_type: str
    columns: list[str] = field(default_factory=list)
    definition: str | None = None


@dataclass
class ForeignKeyMetadata:
    column: str
    referenced_table: str
    referenced_column: str
    constraint_name: str | None = None


@dataclass
class TableMetadata:
    name: str
    table_type: str
    schema_name: str = "public"
    columns: list[ColumnMetadata] = field(default_factory=list)
    primary_keys: list[str] = field(default_factory=list)
    foreign_keys: list[ForeignKeyMetadata] = field(default_factory=list)
    indexes: list[IndexMetadata] = field(default_factory=list)
    constraints: list[ConstraintMetadata] = field(default_factory=list)


@dataclass
class DatabaseMetadata:
    database_name: str
    database_type: str
    tables: list[TableMetadata] = field(default_factory=list)
    views: list[TableMetadata] = field(default_factory=list)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _safe_database_name(connection: Any) -> str:
    """
    Safely get database name from connection object.
    """

    database_name = getattr(
        connection,
        "database_name",
        None,
    )

    if database_name:
        return str(database_name)

    return "unknown"


def _safe_error(exc: Exception) -> str:
    """
    Convert exceptions into a safe string.
    """

    message = str(exc).strip()

    if not message:
        return exc.__class__.__name__

    return message


def _serialize_metadata(
    metadata: DatabaseMetadata,
) -> dict[str, Any]:
    """
    Convert dataclass metadata into a JSON-serializable dictionary.
    """

    return asdict(metadata)


def _get_database_type(connection: Any) -> str:
    """
    Safely get database type.
    """

    database_type = getattr(
        connection,
        "database_type",
        "",
    )

    return str(database_type).lower().strip()


def _clean_host(host: Any) -> str:
    """
    Clean a database host before creating a connection URL.

    Handles malformed values such as:

        2405@localhost
        http://localhost
        https://localhost
        localhost/database

    and converts them into:

        localhost
    """

    if host is None:
        return ""

    cleaned = str(host).strip()

    # Remove accidental user/prefix data.
    # Example:
    # 2405@localhost -> localhost
    if "@" in cleaned:
        cleaned = cleaned.rsplit("@", 1)[-1].strip()

    # Remove protocol if accidentally entered.
    # Example:
    # http://localhost -> localhost
    if "://" in cleaned:
        cleaned = cleaned.split("://", 1)[1].strip()

    # Remove path.
    # Example:
    # localhost/database -> localhost
    cleaned = cleaned.split("/", 1)[0].strip()

    # Remove accidental whitespace.
    cleaned = cleaned.strip()

    return cleaned


# ============================================================
# MYSQL
# ============================================================

def _extract_mysql(
    connection: Any,
) -> dict[str, Any]:

    from sqlalchemy import create_engine, inspect

    engine = None

    try:

        connection_string = getattr(
            connection,
            "connection_string",
            None,
        )

        if connection_string:

            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
            )

        else:

            host = _clean_host(
                getattr(connection, "host", None)
            )

            port = connection.port
            username = connection.username
            password = connection.password
            database_name = connection.database_name

            username = quote_plus(str(username))
            password = quote_plus(str(password))

            connection_string = (
                f"mysql+pymysql://"
                f"{username}:{password}@"
                f"{host}:{port}/"
                f"{database_name}"
            )

            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
            )

        inspector = inspect(engine)

        database_name = _safe_database_name(
            connection
        )

        metadata = DatabaseMetadata(
            database_name=database_name,
            database_type="mysql",
        )

        table_names = inspector.get_table_names()

        for table_name in table_names:

            table = TableMetadata(
                name=table_name,
                table_type="TABLE",
                schema_name="public",
            )

            columns = inspector.get_columns(
                table_name
            )

            primary_key_data = (
                inspector.get_pk_constraint(
                    table_name
                )
            )

            primary_key_columns = (
                primary_key_data.get(
                    "constrained_columns",
                    [],
                )
            )

            table.primary_keys = (
                primary_key_columns
            )

            for column in columns:

                column_name = column.get(
                    "name"
                )

                data_type = str(
                    column.get("type", "unknown")
                )

                nullable = column.get(
                    "nullable",
                    True,
                )

                default = column.get(
                    "default"
                )

                is_primary_key = (
                    column_name
                    in primary_key_columns
                )

                table.columns.append(
                    ColumnMetadata(
                        name=column_name,
                        data_type=data_type,
                        nullable=nullable,
                        primary_key=is_primary_key,
                        default=default,
                    )
                )

            foreign_keys = (
                inspector.get_foreign_keys(
                    table_name
                )
            )

            for foreign_key in foreign_keys:

                constrained_columns = (
                    foreign_key.get(
                        "constrained_columns",
                        [],
                    )
                )

                referred_columns = (
                    foreign_key.get(
                        "referred_columns",
                        [],
                    )
                )

                referred_table = (
                    foreign_key.get(
                        "referred_table"
                    )
                )

                constraint_name = (
                    foreign_key.get("name")
                )

                for index, column_name in enumerate(
                    constrained_columns
                ):

                    if index < len(
                        referred_columns
                    ):

                        referenced_column = (
                            referred_columns[index]
                        )

                        table.foreign_keys.append(
                            ForeignKeyMetadata(
                                column=column_name,
                                referenced_table=(
                                    referred_table
                                ),
                                referenced_column=(
                                    referenced_column
                                ),
                                constraint_name=(
                                    constraint_name
                                ),
                            )
                        )

            indexes = inspector.get_indexes(
                table_name
            )

            for index in indexes:

                table.indexes.append(
                    IndexMetadata(
                        name=index.get(
                            "name",
                            "",
                        ),
                        columns=index.get(
                            "column_names",
                            [],
                        ),
                        unique=index.get(
                            "unique",
                            False,
                        ),
                    )
                )

            metadata.tables.append(table)

        return _serialize_metadata(
            metadata
        )

    except Exception as exc:

        raise ValueError(
            "MySQL metadata extraction failed: "
            f"{_safe_error(exc)}"
        ) from exc

    finally:

        if engine is not None:
            engine.dispose()


# ============================================================
# POSTGRESQL
# ============================================================

def _extract_postgresql(
    connection: Any,
) -> dict[str, Any]:

    from sqlalchemy import create_engine, inspect

    engine = None

    try:

        # ====================================================
        # IMPORTANT:
        # Build the PostgreSQL connection ourselves instead
        # of trusting a malformed connection string.
        # ====================================================

        host = _clean_host(
            getattr(connection, "host", None)
        )

        port = getattr(
            connection,
            "port",
            None,
        )

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

        database_name = getattr(
            connection,
            "database_name",
            None,
        )

        if not host:
            raise ValueError(
                "PostgreSQL host is required"
            )

        if not port:
            raise ValueError(
                "PostgreSQL port is required"
            )

        if not username:
            raise ValueError(
                "PostgreSQL username is required"
            )

        if password is None:
            raise ValueError(
                "PostgreSQL password is required"
            )

        if not database_name:
            raise ValueError(
                "PostgreSQL database_name is required"
            )

        # Safely encode credentials.
        #
        # This prevents special characters such as @, :, / etc.
        # inside username/password from breaking the URL.
        encoded_username = quote_plus(
            str(username)
        )

        encoded_password = quote_plus(
            str(password)
        )

        connection_string = (
            f"postgresql+psycopg2://"
            f"{encoded_username}:"
            f"{encoded_password}@"
            f"{host}:"
            f"{port}/"
            f"{database_name}"
        )

        engine = create_engine(
            connection_string,
            pool_pre_ping=True,
        )

        inspector = inspect(engine)

        metadata = DatabaseMetadata(
            database_name=_safe_database_name(
                connection
            ),
            database_type="postgresql",
        )

        schemas = inspector.get_schema_names()

        for schema_name in schemas:

            if schema_name in {
                "information_schema",
                "pg_catalog",
                "pg_toast",
            }:

                continue

            table_names = (
                inspector.get_table_names(
                    schema=schema_name
                )
            )

            for table_name in table_names:

                table = TableMetadata(
                    name=table_name,
                    table_type="TABLE",
                    schema_name=schema_name,
                )

                columns = inspector.get_columns(
                    table_name,
                    schema=schema_name,
                )

                primary_key_data = (
                    inspector.get_pk_constraint(
                        table_name,
                        schema=schema_name,
                    )
                )

                primary_key_columns = (
                    primary_key_data.get(
                        "constrained_columns",
                        [],
                    )
                )

                table.primary_keys = (
                    primary_key_columns
                )

                for column in columns:

                    column_name = column.get(
                        "name"
                    )

                    data_type = str(
                        column.get(
                            "type",
                            "unknown",
                        )
                    )

                    nullable = column.get(
                        "nullable",
                        True,
                    )

                    default = column.get(
                        "default"
                    )

                    is_primary_key = (
                        column_name
                        in primary_key_columns
                    )

                    table.columns.append(
                        ColumnMetadata(
                            name=column_name,
                            data_type=data_type,
                            nullable=nullable,
                            primary_key=is_primary_key,
                            default=default,
                        )
                    )

                foreign_keys = (
                    inspector.get_foreign_keys(
                        table_name,
                        schema=schema_name,
                    )
                )

                for foreign_key in foreign_keys:

                    constrained_columns = (
                        foreign_key.get(
                            "constrained_columns",
                            [],
                        )
                    )

                    referred_columns = (
                        foreign_key.get(
                            "referred_columns",
                            [],
                        )
                    )

                    referred_table = (
                        foreign_key.get(
                            "referred_table"
                        )
                    )

                    constraint_name = (
                        foreign_key.get("name")
                    )

                    for index, column_name in enumerate(
                        constrained_columns
                    ):

                        if index < len(
                            referred_columns
                        ):

                            table.foreign_keys.append(
                                ForeignKeyMetadata(
                                    column=column_name,
                                    referenced_table=(
                                        referred_table
                                    ),
                                    referenced_column=(
                                        referred_columns[
                                            index
                                        ]
                                    ),
                                    constraint_name=(
                                        constraint_name
                                    ),
                                )
                            )

                indexes = inspector.get_indexes(
                    table_name,
                    schema=schema_name,
                )

                for index in indexes:

                    table.indexes.append(
                        IndexMetadata(
                            name=index.get(
                                "name",
                                "",
                            ),
                            columns=index.get(
                                "column_names",
                                [],
                            ),
                            unique=index.get(
                                "unique",
                                False,
                            ),
                        )
                    )

                metadata.tables.append(table)

            # =================================================
            # VIEWS
            # =================================================

            view_names = (
                inspector.get_view_names(
                    schema=schema_name
                )
            )

            for view_name in view_names:

                view = TableMetadata(
                    name=view_name,
                    table_type="VIEW",
                    schema_name=schema_name,
                )

                columns = inspector.get_columns(
                    view_name,
                    schema=schema_name,
                )

                for column in columns:

                    view.columns.append(
                        ColumnMetadata(
                            name=column.get(
                                "name"
                            ),
                            data_type=str(
                                column.get(
                                    "type",
                                    "unknown",
                                )
                            ),
                            nullable=column.get(
                                "nullable",
                                True,
                            ),
                            default=column.get(
                                "default"
                            ),
                        )
                    )

                metadata.views.append(view)

        return _serialize_metadata(
            metadata
        )

    except Exception as exc:

        raise ValueError(
            "PostgreSQL metadata extraction failed: "
            f"{_safe_error(exc)}"
        ) from exc

    finally:

        if engine is not None:
            engine.dispose()


# ============================================================
# SQLITE
# ============================================================

def _extract_sqlite(
    connection: Any,
) -> dict[str, Any]:

    from sqlalchemy import create_engine, inspect

    engine = None

    try:

        database_name = _safe_database_name(
            connection
        )

        engine = create_engine(
            f"sqlite:///{database_name}"
        )

        inspector = inspect(engine)

        metadata = DatabaseMetadata(
            database_name=database_name,
            database_type="sqlite",
        )

        table_names = inspector.get_table_names()

        for table_name in table_names:

            table = TableMetadata(
                name=table_name,
                table_type="TABLE",
                schema_name="main",
            )

            columns = inspector.get_columns(
                table_name
            )

            primary_key_data = (
                inspector.get_pk_constraint(
                    table_name
                )
            )

            primary_key_columns = (
                primary_key_data.get(
                    "constrained_columns",
                    [],
                )
            )

            table.primary_keys = (
                primary_key_columns
            )

            for column in columns:

                column_name = column.get(
                    "name"
                )

                table.columns.append(
                    ColumnMetadata(
                        name=column_name,
                        data_type=str(
                            column.get(
                                "type",
                                "unknown",
                            )
                        ),
                        nullable=column.get(
                            "nullable",
                            True,
                        ),
                        primary_key=(
                            column_name
                            in primary_key_columns
                        ),
                        default=column.get(
                            "default"
                        ),
                    )
                )

            foreign_keys = (
                inspector.get_foreign_keys(
                    table_name
                )
            )

            for foreign_key in foreign_keys:

                constrained_columns = (
                    foreign_key.get(
                        "constrained_columns",
                        [],
                    )
                )

                referred_columns = (
                    foreign_key.get(
                        "referred_columns",
                        [],
                    )
                )

                referred_table = (
                    foreign_key.get(
                        "referred_table"
                    )
                )

                constraint_name = (
                    foreign_key.get("name")
                )

                for index, column_name in enumerate(
                    constrained_columns
                ):

                    if index < len(
                        referred_columns
                    ):

                        table.foreign_keys.append(
                            ForeignKeyMetadata(
                                column=column_name,
                                referenced_table=(
                                    referred_table
                                ),
                                referenced_column=(
                                    referred_columns[
                                        index
                                    ]
                                ),
                                constraint_name=(
                                    constraint_name
                                ),
                            )
                        )

            indexes = inspector.get_indexes(
                table_name
            )

            for index in indexes:

                table.indexes.append(
                    IndexMetadata(
                        name=index.get(
                            "name",
                            "",
                        ),
                        columns=index.get(
                            "column_names",
                            [],
                        ),
                        unique=index.get(
                            "unique",
                            False,
                        ),
                    )
                )

            metadata.tables.append(table)

        view_names = inspector.get_view_names()

        for view_name in view_names:

            view = TableMetadata(
                name=view_name,
                table_type="VIEW",
                schema_name="main",
            )

            columns = inspector.get_columns(
                view_name
            )

            for column in columns:

                view.columns.append(
                    ColumnMetadata(
                        name=column.get(
                            "name"
                        ),
                        data_type=str(
                            column.get(
                                "type",
                                "unknown",
                            )
                        ),
                        nullable=column.get(
                            "nullable",
                            True,
                        ),
                        default=column.get(
                            "default"
                        ),
                    )
                )

            metadata.views.append(view)

        return _serialize_metadata(
            metadata
        )

    except Exception as exc:

        raise ValueError(
            "SQLite metadata extraction failed: "
            f"{_safe_error(exc)}"
        ) from exc

    finally:

        if engine is not None:
            engine.dispose()


# ============================================================
# ORACLE
# ============================================================

def _extract_oracle(
    connection: Any,
) -> dict[str, Any]:

    from sqlalchemy import create_engine, inspect

    engine = None

    try:

        connection_string = getattr(
            connection,
            "connection_string",
            None,
        )

        if not connection_string:

            host = _clean_host(
                getattr(connection, "host", None)
            )

            port = connection.port
            username = connection.username
            password = connection.password
            database_name = connection.database_name

            username = quote_plus(str(username))
            password = quote_plus(str(password))

            connection_string = (
                f"oracle+oracledb://"
                f"{username}:{password}@"
                f"{host}:{port}/"
                f"{database_name}"
            )

        engine = create_engine(
            connection_string,
            pool_pre_ping=True,
        )

        inspector = inspect(engine)

        metadata = DatabaseMetadata(
            database_name=_safe_database_name(
                connection
            ),
            database_type="oracle",
        )

        table_names = inspector.get_table_names()

        for table_name in table_names:

            table = TableMetadata(
                name=table_name,
                table_type="TABLE",
                schema_name="public",
            )

            columns = inspector.get_columns(
                table_name
            )

            for column in columns:

                table.columns.append(
                    ColumnMetadata(
                        name=column.get(
                            "name"
                        ),
                        data_type=str(
                            column.get(
                                "type",
                                "unknown",
                            )
                        ),
                        nullable=column.get(
                            "nullable",
                            True,
                        ),
                        default=column.get(
                            "default"
                        ),
                    )
                )

            metadata.tables.append(table)

        return _serialize_metadata(
            metadata
        )

    except Exception as exc:

        raise ValueError(
            "Oracle metadata extraction failed: "
            f"{_safe_error(exc)}"
        ) from exc

    finally:

        if engine is not None:
            engine.dispose()


# ============================================================
# SQL SERVER
# ============================================================

def _extract_sqlserver(
    connection: Any,
) -> dict[str, Any]:

    from sqlalchemy import create_engine, inspect
    from urllib.parse import quote_plus

    engine = None

    try:

        connection_string = getattr(
            connection,
            "connection_string",
            None,
        )

        if connection_string:

            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
            )

        else:

            host = _clean_host(
                getattr(connection, "host", None)
            )

            port = connection.port
            username = connection.username
            password = connection.password
            database_name = connection.database_name

            odbc_connection = (
                "DRIVER={ODBC Driver 17 for SQL Server};"
                f"SERVER={host},{port};"
                f"DATABASE={database_name};"
                f"UID={username};"
                f"PWD={password};"
                "TrustServerCertificate=yes;"
            )

            encoded = quote_plus(
                odbc_connection
            )

            connection_string = (
                f"mssql+pyodbc:///?odbc_connect={encoded}"
            )

            engine = create_engine(
                connection_string,
                pool_pre_ping=True,
            )

        inspector = inspect(engine)

        metadata = DatabaseMetadata(
            database_name=_safe_database_name(
                connection
            ),
            database_type="sqlserver",
        )

        table_names = inspector.get_table_names()

        for table_name in table_names:

            table = TableMetadata(
                name=table_name,
                table_type="TABLE",
                schema_name="dbo",
            )

            columns = inspector.get_columns(
                table_name
            )

            primary_key_data = (
                inspector.get_pk_constraint(
                    table_name
                )
            )

            primary_key_columns = (
                primary_key_data.get(
                    "constrained_columns",
                    [],
                )
            )

            table.primary_keys = (
                primary_key_columns
            )

            for column in columns:

                column_name = column.get(
                    "name"
                )

                table.columns.append(
                    ColumnMetadata(
                        name=column_name,
                        data_type=str(
                            column.get(
                                "type",
                                "unknown",
                            )
                        ),
                        nullable=column.get(
                            "nullable",
                            True,
                        ),
                        primary_key=(
                            column_name
                            in primary_key_columns
                        ),
                        default=column.get(
                            "default"
                        ),
                    )
                )

            metadata.tables.append(table)

        return _serialize_metadata(
            metadata
        )

    except Exception as exc:

        raise ValueError(
            "SQL Server metadata extraction failed: "
            f"{_safe_error(exc)}"
        ) from exc

    finally:

        if engine is not None:
            engine.dispose()


# ============================================================
# MONGODB
# ============================================================

def _extract_mongodb(
    connection: Any,
) -> dict[str, Any]:

    from pymongo import MongoClient

    client = None

    try:

        connection_string = getattr(
            connection,
            "connection_string",
            None,
        )

        if not connection_string:

            raise ValueError(
                "MongoDB connection_string is required"
            )

        database_name = getattr(
            connection,
            "database_name",
            None,
        )

        if not database_name:

            raise ValueError(
                "MongoDB database_name is required"
            )

        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000,
        )

        client.admin.command("ping")

        database = client[
            database_name
        ]

        metadata = DatabaseMetadata(
            database_name=database_name,
            database_type="mongodb",
        )

        collection_names = (
            database.list_collection_names()
        )

        for collection_name in collection_names:

            table = TableMetadata(
                name=collection_name,
                table_type="COLLECTION",
                schema_name=database_name,
            )

            collection = database[
                collection_name
            ]

            sample = collection.find_one()

            if sample:

                for key, value in sample.items():

                    if key == "_id":

                        data_type = "ObjectId"

                    else:

                        data_type = type(
                            value
                        ).__name__

                    table.columns.append(
                        ColumnMetadata(
                            name=key,
                            data_type=data_type,
                            nullable=True,
                            primary_key=(
                                key == "_id"
                            ),
                        )
                    )

            try:

                indexes = collection.index_information()

                for index_name, index_data in indexes.items():

                    key_list = index_data.get(
                        "key",
                        [],
                    )

                    index_columns = [
                        column_name
                        for column_name, _direction
                        in key_list
                    ]

                    table.indexes.append(
                        IndexMetadata(
                            name=index_name,
                            columns=index_columns,
                            unique=index_data.get(
                                "unique",
                                False,
                            ),
                        )
                    )

            except Exception:
                pass

            metadata.tables.append(table)

        return _serialize_metadata(
            metadata
        )

    except Exception as exc:

        raise ValueError(
            "MongoDB metadata extraction failed: "
            f"{_safe_error(exc)}"
        ) from exc

    finally:

        if client is not None:
            client.close()


# ============================================================
# DYNAMODB
# ============================================================

def _extract_dynamodb(
    connection: Any,
) -> dict[str, Any]:

    try:

        import boto3

        aws_access_key_id = getattr(
            connection,
            "aws_access_key_id",
            None,
        )

        aws_secret_access_key = getattr(
            connection,
            "aws_secret_access_key",
            None,
        )

        aws_region = getattr(
            connection,
            "aws_region",
            None,
        )

        database_name = _safe_database_name(
            connection
        )

        dynamodb = boto3.resource(
            "dynamodb",
            aws_access_key_id=(
                aws_access_key_id
            ),
            aws_secret_access_key=(
                aws_secret_access_key
            ),
            region_name=aws_region,
        )

        client = dynamodb.meta.client

        response = client.list_tables()

        table_names = response.get(
            "TableNames",
            [],
        )

        metadata = DatabaseMetadata(
            database_name=database_name,
            database_type="dynamodb",
        )

        for table_name in table_names:

            table_resource = dynamodb.Table(
                table_name
            )

            description = (
                table_resource.meta.client
                .describe_table(
                    TableName=table_name
                )
            )

            table_info = description.get(
                "Table",
                {},
            )

            table = TableMetadata(
                name=table_name,
                table_type="TABLE",
                schema_name="dynamodb",
            )

            key_schema = table_info.get(
                "KeySchema",
                [],
            )

            attribute_definitions = (
                table_info.get(
                    "AttributeDefinitions",
                    [],
                )
            )

            attribute_type_map = {
                item.get("AttributeName"):
                    item.get("AttributeType")
                for item in attribute_definitions
            }

            for key in key_schema:

                attribute_name = key.get(
                    "AttributeName"
                )

                attribute_type = (
                    attribute_type_map.get(
                        attribute_name,
                        "unknown",
                    )
                )

                table.columns.append(
                    ColumnMetadata(
                        name=attribute_name,
                        data_type=attribute_type,
                        nullable=False,
                        primary_key=True,
                    )
                )

                table.primary_keys.append(
                    attribute_name
                )

            metadata.tables.append(table)

        return _serialize_metadata(
            metadata
        )

    except Exception as exc:

        raise ValueError(
            "DynamoDB metadata extraction failed: "
            f"{_safe_error(exc)}"
        ) from exc


# ============================================================
# CASSANDRA
# ============================================================

def _extract_cassandra(
    connection: Any,
) -> dict[str, Any]:

    try:

        from cassandra.cluster import Cluster

        host = _clean_host(
            getattr(connection, "host", None)
        )

        port = connection.port
        keyspace = connection.keyspace

        cluster = Cluster(
            [host],
            port=port,
        )

        session = cluster.connect(
            keyspace
        )

        metadata_source = (
            cluster.metadata
        )

        keyspace_metadata = (
            metadata_source.keyspaces.get(
                keyspace
            )
        )

        metadata = DatabaseMetadata(
            database_name=keyspace,
            database_type="cassandra",
        )

        if keyspace_metadata:

            for table_name, table_info in (
                keyspace_metadata.tables.items()
            ):

                table = TableMetadata(
                    name=table_name,
                    table_type="TABLE",
                    schema_name=keyspace,
                )

                for column_name, column_info in (
                    table_info.columns.items()
                ):

                    data_type = str(
                        column_info.cql_type
                    )

                    primary_key = (
                        column_name
                        in table_info.primary_key
                    )

                    table.columns.append(
                        ColumnMetadata(
                            name=column_name,
                            data_type=data_type,
                            nullable=(
                                not primary_key
                            ),
                            primary_key=(
                                primary_key
                            ),
                        )
                    )

                    if primary_key:

                        table.primary_keys.append(
                            column_name
                        )

                metadata.tables.append(
                    table
                )

        session.shutdown()
        cluster.shutdown()

        return _serialize_metadata(
            metadata
        )

    except Exception as exc:

        raise ValueError(
            "Cassandra metadata extraction failed: "
            f"{_safe_error(exc)}"
        ) from exc


# ============================================================
# FIREBASE
# ============================================================

def _extract_firebase(
    connection: Any,
) -> dict[str, Any]:

    try:

        import firebase_admin
        from firebase_admin import credentials
        from firebase_admin import firestore

        database_name = _safe_database_name(
            connection
        )

        if not firebase_admin._apps:

            credential_path = getattr(
                connection,
                "connection_string",
                None,
            )

            if not credential_path:

                raise ValueError(
                    "Firebase credentials are required"
                )

            cred = credentials.Certificate(
                credential_path
            )

            firebase_admin.initialize_app(
                cred
            )

        db = firestore.client()

        metadata = DatabaseMetadata(
            database_name=database_name,
            database_type="firebase",
        )

        collections = db.collections()

        for collection in collections:

            collection_name = (
                collection.id
            )

            table = TableMetadata(
                name=collection_name,
                table_type="COLLECTION",
                schema_name="firebase",
            )

            document = next(
                collection.stream(),
                None,
            )

            if document:

                document_data = (
                    document.to_dict()
                )

                if document_data:

                    for key, value in (
                        document_data.items()
                    ):

                        table.columns.append(
                            ColumnMetadata(
                                name=key,
                                data_type=type(
                                    value
                                ).__name__,
                                nullable=True,
                            )
                        )

            metadata.tables.append(
                table
            )

        return _serialize_metadata(
            metadata
        )

    except Exception as exc:

        raise ValueError(
            "Firebase metadata extraction failed: "
            f"{_safe_error(exc)}"
        ) from exc


# ============================================================
# MAIN EXTRACTION FUNCTION
# ============================================================

def extract_database_metadata(
    connection: Any,
) -> dict[str, Any]:

    database_type = _get_database_type(
        connection
    )

    if database_type == "mysql":

        return _extract_mysql(
            connection
        )

    if database_type == "postgresql":

        return _extract_postgresql(
            connection
        )

    if database_type == "sqlite":

        return _extract_sqlite(
            connection
        )

    if database_type == "oracle":

        return _extract_oracle(
            connection
        )

    if database_type == "sqlserver":

        return _extract_sqlserver(
            connection
        )

    if database_type == "mongodb":

        return _extract_mongodb(
            connection
        )

    if database_type == "dynamodb":

        return _extract_dynamodb(
            connection
        )

    if database_type == "cassandra":

        return _extract_cassandra(
            connection
        )

    if database_type == "firebase":

        return _extract_firebase(
            connection
        )

    raise ValueError(
        f"Unsupported database type: "
        f"{database_type}"
    )