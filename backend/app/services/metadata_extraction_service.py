import logging
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================
# METADATA RESULT MODELS
# ============================================================

@dataclass
class ColumnMetadata:
    name: str
    data_type: str
    nullable: bool
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
class ForeignKeyMetadata:
    column: str
    referenced_table: str
    referenced_column: str
    constraint_name: str | None = None


@dataclass
class TableMetadata:
    name: str
    table_type: str
    columns: list[ColumnMetadata] = field(default_factory=list)
    primary_keys: list[str] = field(default_factory=list)
    foreign_keys: list[ForeignKeyMetadata] = field(default_factory=list)
    indexes: list[IndexMetadata] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)


@dataclass
class DatabaseMetadata:
    database_name: str
    database_type: str
    tables: list[TableMetadata] = field(default_factory=list)
    views: list[TableMetadata] = field(default_factory=list)


# ============================================================
# SAFE HELPERS
# ============================================================

def _safe_database_name(connection: Any) -> str:
    return (
        getattr(connection, "database_name", None)
        or getattr(connection, "keyspace", None)
        or getattr(connection, "database", None)
        or "N/A"
    )


def _safe_error(exc: Exception) -> str:
    """
    Never expose credentials, passwords, tokens or
    credential-bearing connection strings.
    """

    message = str(exc)

    sensitive_terms = (
        "password",
        "secret",
        "access_key",
        "secret_access_key",
        "token",
        "authorization",
        "private_key",
    )

    lowered = message.lower()

    if any(term in lowered for term in sensitive_terms):
        return "Metadata extraction failed."

    if "://" in message and "@" in message:
        return "Metadata extraction failed."

    return message[:500]


def _serialize_metadata(metadata: DatabaseMetadata) -> dict[str, Any]:
    return asdict(metadata)


# ============================================================
# MYSQL
# ============================================================

def _extract_mysql(connection: Any) -> dict[str, Any]:

    import pymysql

    conn = None

    try:
        conn = pymysql.connect(
            host=connection.host,
            port=connection.port,
            database=connection.database_name,
            user=connection.username,
            password=connection.password,
            connect_timeout=5,
        )

        cursor = conn.cursor()

        database_name = connection.database_name

        # ----------------------------------------------------
        # TABLES + VIEWS
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                TABLE_NAME,
                TABLE_TYPE
            FROM information_schema.tables
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME
            """,
            (database_name,),
        )

        objects = cursor.fetchall()

        metadata = DatabaseMetadata(
            database_name=database_name,
            database_type="mysql",
        )

        for object_name, object_type in objects:

            table = TableMetadata(
                name=object_name,
                table_type=object_type,
            )

            # ------------------------------------------------
            # COLUMNS
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    COLUMN_NAME,
                    COLUMN_TYPE,
                    IS_NULLABLE,
                    COLUMN_KEY,
                    EXTRA,
                    COLUMN_DEFAULT
                FROM information_schema.columns
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
                """,
                (database_name, object_name),
            )

            columns = cursor.fetchall()

            for (
                column_name,
                column_type,
                nullable,
                column_key,
                extra,
                default_value,
            ) in columns:

                is_primary = column_key == "PRI"

                auto_increment = (
                    extra is not None
                    and "auto_increment" in str(extra).lower()
                )

                constraints = []

                if is_primary:
                    constraints.append("PRIMARY KEY")

                if nullable == "NO":
                    constraints.append("NOT NULL")

                if auto_increment:
                    constraints.append("AUTO_INCREMENT")

                table.columns.append(
                    ColumnMetadata(
                        name=column_name,
                        data_type=str(column_type),
                        nullable=nullable == "YES",
                        primary_key=is_primary,
                        auto_increment=auto_increment,
                        default=default_value,
                        constraints=constraints,
                    )
                )

                if is_primary:
                    table.primary_keys.append(column_name)

            # ------------------------------------------------
            # FOREIGN KEYS
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    CONSTRAINT_NAME,
                    COLUMN_NAME,
                    REFERENCED_TABLE_NAME,
                    REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = %s
                  AND REFERENCED_TABLE_NAME IS NOT NULL
                ORDER BY ORDINAL_POSITION
                """,
                (database_name, object_name),
            )

            foreign_keys = cursor.fetchall()

            for (
                constraint_name,
                column_name,
                referenced_table,
                referenced_column,
            ) in foreign_keys:

                table.foreign_keys.append(
                    ForeignKeyMetadata(
                        column=column_name,
                        referenced_table=referenced_table,
                        referenced_column=referenced_column,
                        constraint_name=constraint_name,
                    )
                )

            # ------------------------------------------------
            # INDEXES
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    INDEX_NAME,
                    COLUMN_NAME,
                    NON_UNIQUE
                FROM information_schema.statistics
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = %s
                ORDER BY INDEX_NAME, SEQ_IN_INDEX
                """,
                (database_name, object_name),
            )

            indexes = {}

            for index_name, column_name, non_unique in cursor.fetchall():

                if index_name not in indexes:
                    indexes[index_name] = IndexMetadata(
                        name=index_name,
                        unique=non_unique == 0,
                    )

                indexes[index_name].columns.append(column_name)

            table.indexes = list(indexes.values())

            if object_type == "VIEW":
                metadata.views.append(table)
            else:
                metadata.tables.append(table)

        cursor.close()

        return _serialize_metadata(metadata)

    finally:
        if conn is not None:
            conn.close()


# ============================================================
# POSTGRESQL
# ============================================================

def _extract_postgresql(connection: Any) -> dict[str, Any]:

    import psycopg2

    conn = None

    try:
        conn = psycopg2.connect(
            host=connection.host,
            port=connection.port,
            dbname=connection.database_name,
            user=connection.username,
            password=connection.password,
            connect_timeout=5,
        )

        cursor = conn.cursor()

        metadata = DatabaseMetadata(
            database_name=connection.database_name,
            database_type="postgresql",
        )

        # ----------------------------------------------------
        # TABLES + VIEWS
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                table_name,
                table_type
            FROM information_schema.tables
            WHERE table_schema NOT IN (
                'pg_catalog',
                'information_schema'
            )
            ORDER BY table_schema, table_name
            """
        )

        objects = cursor.fetchall()

        for object_name, object_type in objects:

            table = TableMetadata(
                name=object_name,
                table_type=object_type,
            )

            # ------------------------------------------------
            # COLUMNS
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
                """,
                (object_name,),
            )

            for (
                column_name,
                data_type,
                nullable,
                default_value,
            ) in cursor.fetchall():

                default_text = str(default_value or "")

                auto_increment = (
                    "nextval(" in default_text.lower()
                    or "identity" in default_text.lower()
                )

                table.columns.append(
                    ColumnMetadata(
                        name=column_name,
                        data_type=data_type,
                        nullable=nullable == "YES",
                        auto_increment=auto_increment,
                        default=default_value,
                        constraints=(
                            ["NOT NULL"]
                            if nullable == "NO"
                            else []
                        ),
                    )
                )

            # ------------------------------------------------
            # PRIMARY KEYS
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                    AND tc.table_name = kcu.table_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
                  AND tc.table_name = %s
                ORDER BY kcu.ordinal_position
                """,
                (object_name,),
            )

            primary_keys = [
                row[0]
                for row in cursor.fetchall()
            ]

            table.primary_keys = primary_keys

            for column in table.columns:
                if column.name in primary_keys:
                    column.primary_key = True
                    if "PRIMARY KEY" not in column.constraints:
                        column.constraints.append(
                            "PRIMARY KEY"
                        )

            # ------------------------------------------------
            # FOREIGN KEYS
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name,
                    ccu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_name = %s
                """,
                (object_name,),
            )

            for row in cursor.fetchall():

                (
                    constraint_name,
                    column_name,
                    referenced_table,
                    referenced_column,
                ) = row

                table.foreign_keys.append(
                    ForeignKeyMetadata(
                        column=column_name,
                        referenced_table=referenced_table,
                        referenced_column=referenced_column,
                        constraint_name=constraint_name,
                    )
                )

            # ------------------------------------------------
            # INDEXES
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE tablename = %s
                """,
                (object_name,),
            )

            for index_name, index_definition in cursor.fetchall():

                unique = " UNIQUE " in (
                    f" {index_definition.upper()} "
                )

                table.indexes.append(
                    IndexMetadata(
                        name=index_name,
                        columns=[],
                        unique=unique,
                    )
                )

            if object_type == "VIEW":
                metadata.views.append(table)
            else:
                metadata.tables.append(table)

        cursor.close()

        return _serialize_metadata(metadata)

    finally:
        if conn is not None:
            conn.close()



# ============================================================
# SQL SERVER
# ============================================================

def _extract_sqlserver(connection: Any) -> dict[str, Any]:

    import pyodbc

    conn = None

    try:
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
            raise ValueError(
                "Microsoft ODBC Driver 17 or 18 for SQL Server is not installed."
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

        metadata = DatabaseMetadata(
            database_name=connection.database_name,
            database_type="sqlserver",
        )

        # ----------------------------------------------------
        # TABLES + VIEWS
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                TABLE_SCHEMA,
                TABLE_NAME,
                TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES
            ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
        )

        objects = cursor.fetchall()

        for schema_name, object_name, object_type in objects:

            table = TableMetadata(
                name=object_name,
                table_type=object_type,
            )

            # ------------------------------------------------
            # COLUMNS
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    IS_NULLABLE,
                    COLUMN_DEFAULT
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = ?
                  AND TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
                """,
                schema_name,
                object_name,
            )

            for (
                column_name,
                data_type,
                nullable,
                default_value,
            ) in cursor.fetchall():

                constraints = []

                if nullable == "NO":
                    constraints.append("NOT NULL")

                table.columns.append(
                    ColumnMetadata(
                        name=column_name,
                        data_type=str(data_type),
                        nullable=nullable == "YES",
                        default=default_value,
                        constraints=constraints,
                    )
                )

            # ------------------------------------------------
            # AUTO-INCREMENT / IDENTITY
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    c.name
                FROM sys.identity_columns c
                INNER JOIN sys.tables t
                    ON c.object_id = t.object_id
                INNER JOIN sys.schemas s
                    ON t.schema_id = s.schema_id
                WHERE s.name = ?
                  AND t.name = ?
                """,
                schema_name,
                object_name,
            )

            identity_columns = {
                row[0]
                for row in cursor.fetchall()
            }

            for column in table.columns:

                if column.name in identity_columns:

                    column.auto_increment = True

                    if "AUTO_INCREMENT" not in column.constraints:
                        column.constraints.append(
                            "AUTO_INCREMENT"
                        )

            # ------------------------------------------------
            # PRIMARY KEYS
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    kcu.COLUMN_NAME
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
                    ON tc.CONSTRAINT_NAME =
                       kcu.CONSTRAINT_NAME
                    AND tc.TABLE_SCHEMA =
                       kcu.TABLE_SCHEMA
                    AND tc.TABLE_NAME =
                       kcu.TABLE_NAME
                WHERE tc.CONSTRAINT_TYPE = 'PRIMARY KEY'
                  AND tc.TABLE_SCHEMA = ?
                  AND tc.TABLE_NAME = ?
                ORDER BY kcu.ORDINAL_POSITION
                """,
                schema_name,
                object_name,
            )

            primary_keys = [
                row[0]
                for row in cursor.fetchall()
            ]

            table.primary_keys = primary_keys

            for column in table.columns:

                if column.name in primary_keys:

                    column.primary_key = True

                    if "PRIMARY KEY" not in column.constraints:
                        column.constraints.append(
                            "PRIMARY KEY"
                        )

            # ------------------------------------------------
            # FOREIGN KEYS
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    fk.name,
                    COL_NAME(
                        fkc.parent_object_id,
                        fkc.parent_column_id
                    ),
                    OBJECT_SCHEMA_NAME(
                        fkc.referenced_object_id
                    ),
                    OBJECT_NAME(
                        fkc.referenced_object_id
                    ),
                    COL_NAME(
                        fkc.referenced_object_id,
                        fkc.referenced_column_id
                    )
                FROM sys.foreign_keys fk
                INNER JOIN sys.foreign_key_columns fkc
                    ON fk.object_id = fkc.constraint_object_id
                WHERE OBJECT_SCHEMA_NAME(
                    fkc.parent_object_id
                ) = ?
                  AND OBJECT_NAME(
                    fkc.parent_object_id
                ) = ?
                ORDER BY fk.name, fkc.constraint_column_id
                """,
                schema_name,
                object_name,
            )

            for row in cursor.fetchall():

                (
                    constraint_name,
                    column_name,
                    referenced_schema,
                    referenced_table,
                    referenced_column,
                ) = row

                table.foreign_keys.append(
                    ForeignKeyMetadata(
                        column=column_name,
                        referenced_table=referenced_table,
                        referenced_column=referenced_column,
                        constraint_name=constraint_name,
                    )
                )

            # ------------------------------------------------
            # INDEXES
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    i.name,
                    COL_NAME(
                        ic.object_id,
                        ic.column_id
                    ),
                    i.is_unique
                FROM sys.indexes i
                INNER JOIN sys.index_columns ic
                    ON i.object_id = ic.object_id
                    AND i.index_id = ic.index_id
                INNER JOIN sys.tables t
                    ON i.object_id = t.object_id
                INNER JOIN sys.schemas s
                    ON t.schema_id = s.schema_id
                WHERE s.name = ?
                  AND t.name = ?
                  AND i.name IS NOT NULL
                ORDER BY i.name, ic.key_ordinal
                """,
                schema_name,
                object_name,
            )

            indexes = {}

            for (
                index_name,
                column_name,
                unique,
            ) in cursor.fetchall():

                if index_name not in indexes:
                    indexes[index_name] = IndexMetadata(
                        name=index_name,
                        unique=bool(unique),
                    )

                if column_name:
                    indexes[index_name].columns.append(
                        column_name
                    )

            table.indexes = list(indexes.values())

            if object_type == "VIEW":
                metadata.views.append(table)
            else:
                metadata.tables.append(table)

        cursor.close()

        return _serialize_metadata(metadata)

    finally:

        if conn is not None:
            conn.close()


# ============================================================
# ORACLE
# ============================================================

def _extract_oracle(connection: Any) -> dict[str, Any]:

    import oracledb

    conn = None

    try:

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

        metadata = DatabaseMetadata(
            database_name=connection.database_name,
            database_type="oracle",
        )

        # ----------------------------------------------------
        # TABLES
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT TABLE_NAME
            FROM USER_TABLES
            ORDER BY TABLE_NAME
            """
        )

        table_names = [
            row[0]
            for row in cursor.fetchall()
        ]

        # ----------------------------------------------------
        # VIEWS
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT VIEW_NAME
            FROM USER_VIEWS
            ORDER BY VIEW_NAME
            """
        )

        view_names = [
            row[0]
            for row in cursor.fetchall()
        ]

        all_objects = (
            [(name, "TABLE") for name in table_names]
            + [(name, "VIEW") for name in view_names]
        )

        for object_name, object_type in all_objects:

            table = TableMetadata(
                name=object_name,
                table_type=object_type,
            )

            # ------------------------------------------------
            # COLUMNS
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    COLUMN_NAME,
                    DATA_TYPE,
                    NULLABLE,
                    DATA_DEFAULT
                FROM USER_TAB_COLUMNS
                WHERE TABLE_NAME = :table_name
                ORDER BY COLUMN_ID
                """,
                table_name=object_name,
            )

            for (
                column_name,
                data_type,
                nullable,
                default_value,
            ) in cursor.fetchall():

                constraints = []

                if nullable == "N":
                    constraints.append("NOT NULL")

                table.columns.append(
                    ColumnMetadata(
                        name=column_name,
                        data_type=str(data_type),
                        nullable=nullable == "Y",
                        default=default_value,
                        constraints=constraints,
                    )
                )

            # ------------------------------------------------
            # PRIMARY KEYS
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    acc.COLUMN_NAME
                FROM USER_CONSTRAINTS ac
                JOIN USER_CONS_COLUMNS acc
                    ON ac.CONSTRAINT_NAME =
                       acc.CONSTRAINT_NAME
                WHERE ac.CONSTRAINT_TYPE = 'P'
                  AND ac.TABLE_NAME = :table_name
                ORDER BY acc.POSITION
                """,
                table_name=object_name,
            )

            primary_keys = [
                row[0]
                for row in cursor.fetchall()
            ]

            table.primary_keys = primary_keys

            for column in table.columns:

                if column.name in primary_keys:

                    column.primary_key = True

                    if "PRIMARY KEY" not in column.constraints:
                        column.constraints.append(
                            "PRIMARY KEY"
                        )

            # ------------------------------------------------
            # IDENTITY COLUMNS
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    COLUMN_NAME
                FROM USER_TAB_IDENTITY_COLS
                WHERE TABLE_NAME = :table_name
                """,
                table_name=object_name,
            )

            identity_columns = {
                row[0]
                for row in cursor.fetchall()
            }

            for column in table.columns:

                if column.name in identity_columns:

                    column.auto_increment = True

                    if "AUTO_INCREMENT" not in column.constraints:
                        column.constraints.append(
                            "AUTO_INCREMENT"
                        )

            # ------------------------------------------------
            # FOREIGN KEYS
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    ac.CONSTRAINT_NAME,
                    acc.COLUMN_NAME,
                    ac_r.TABLE_NAME,
                    acc_r.COLUMN_NAME
                FROM USER_CONSTRAINTS ac
                JOIN USER_CONS_COLUMNS acc
                    ON ac.CONSTRAINT_NAME =
                       acc.CONSTRAINT_NAME
                JOIN USER_CONSTRAINTS ac_r
                    ON ac.R_CONSTRAINT_NAME =
                       ac_r.CONSTRAINT_NAME
                JOIN USER_CONS_COLUMNS acc_r
                    ON ac_r.CONSTRAINT_NAME =
                       acc_r.CONSTRAINT_NAME
                    AND acc.POSITION =
                        acc_r.POSITION
                WHERE ac.CONSTRAINT_TYPE = 'R'
                  AND ac.TABLE_NAME = :table_name
                ORDER BY ac.CONSTRAINT_NAME,
                         acc.POSITION
                """,
                table_name=object_name,
            )

            for row in cursor.fetchall():

                (
                    constraint_name,
                    column_name,
                    referenced_table,
                    referenced_column,
                ) = row

                table.foreign_keys.append(
                    ForeignKeyMetadata(
                        column=column_name,
                        referenced_table=referenced_table,
                        referenced_column=referenced_column,
                        constraint_name=constraint_name,
                    )
                )

            # ------------------------------------------------
            # INDEXES
            # ------------------------------------------------

            cursor.execute(
                """
                SELECT
                    ui.INDEX_NAME,
                    uic.COLUMN_NAME,
                    ui.UNIQUENESS
                FROM USER_INDEXES ui
                JOIN USER_IND_COLUMNS uic
                    ON ui.INDEX_NAME =
                       uic.INDEX_NAME
                WHERE ui.TABLE_NAME = :table_name
                ORDER BY ui.INDEX_NAME,
                         uic.COLUMN_POSITION
                """,
                table_name=object_name,
            )

            indexes = {}

            for (
                index_name,
                column_name,
                uniqueness,
            ) in cursor.fetchall():

                if index_name not in indexes:
                    indexes[index_name] = IndexMetadata(
                        name=index_name,
                        unique=uniqueness == "UNIQUE",
                    )

                if column_name:
                    indexes[index_name].columns.append(
                        column_name
                    )

            table.indexes = list(indexes.values())

            if object_type == "VIEW":
                metadata.views.append(table)
            else:
                metadata.tables.append(table)

        cursor.close()

        return _serialize_metadata(metadata)

    finally:

        if conn is not None:
            conn.close()


# ============================================================
# SQLITE
# ============================================================

def _extract_sqlite(connection: Any) -> dict[str, Any]:

    import os
    import sqlite3
    from pathlib import Path

    database_name = connection.database_name

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
            final_database = str(Path(database_name))

    conn = None

    try:
        conn = sqlite3.connect(final_database)
        cursor = conn.cursor()

        metadata = DatabaseMetadata(
            database_name=database_name,
            database_type="sqlite",
        )

        # ----------------------------------------------------
        # TABLES + VIEWS
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                name,
                type
            FROM sqlite_master
            WHERE type IN ('table', 'view')
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )

        objects = cursor.fetchall()

        for object_name, object_type in objects:

            table = TableMetadata(
                name=object_name,
                table_type=object_type,
            )

            # ------------------------------------------------
            # COLUMNS + PRIMARY KEYS + AUTOINCREMENT
            # ------------------------------------------------

            cursor.execute(
                f'PRAGMA table_info("{object_name}")'
            )

            rows = cursor.fetchall()

            for row in rows:

                (
                    cid,
                    column_name,
                    data_type,
                    not_null,
                    default_value,
                    primary_key_position,
                ) = row

                is_primary = primary_key_position > 0

                auto_increment = (
                    is_primary
                    and str(data_type).upper() == "INTEGER"
                )

                constraints = []

                if is_primary:
                    constraints.append("PRIMARY KEY")

                if not_null:
                    constraints.append("NOT NULL")

                if auto_increment:
                    constraints.append(
                        "AUTO_INCREMENT"
                    )

                table.columns.append(
                    ColumnMetadata(
                        name=column_name,
                        data_type=data_type,
                        nullable=not bool(not_null),
                        primary_key=is_primary,
                        auto_increment=auto_increment,
                        default=default_value,
                        constraints=constraints,
                    )
                )

                if is_primary:
                    table.primary_keys.append(
                        column_name
                    )

            # ------------------------------------------------
            # FOREIGN KEYS
            # ------------------------------------------------

            cursor.execute(
                f'PRAGMA foreign_key_list("{object_name}")'
            )

            for row in cursor.fetchall():

                (
                    fk_id,
                    sequence,
                    referenced_table,
                    from_column,
                    to_column,
                    on_update,
                    on_delete,
                    match,
                ) = row[:8]

                table.foreign_keys.append(
                    ForeignKeyMetadata(
                        column=from_column,
                        referenced_table=referenced_table,
                        referenced_column=to_column,
                        constraint_name=f"fk_{fk_id}",
                    )
                )

            # ------------------------------------------------
            # INDEXES
            # ------------------------------------------------

            cursor.execute(
                f'PRAGMA index_list("{object_name}")'
            )

            for row in cursor.fetchall():

                index_name = row[1]
                unique = bool(row[2])

                index_columns = []

                cursor.execute(
                    f'PRAGMA index_info("{index_name}")'
                )

                for index_row in cursor.fetchall():
                    index_columns.append(index_row[2])

                table.indexes.append(
                    IndexMetadata(
                        name=index_name,
                        columns=index_columns,
                        unique=unique,
                    )
                )

            if object_type == "view":
                metadata.views.append(table)
            else:
                metadata.tables.append(table)

        cursor.close()

        return _serialize_metadata(metadata)

    finally:
        if conn is not None:
            conn.close()


# ============================================================
# MONGODB
# ============================================================

def _extract_mongodb(connection: Any) -> dict[str, Any]:

    from pymongo import MongoClient

    client = None

    try:
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

        metadata = DatabaseMetadata(
            database_name=database_name,
            database_type="mongodb",
        )

        if database_name != "N/A":

            database = client[database_name]

            # Metadata only.
            collection_names = (
                database.list_collection_names()
            )

            for collection_name in collection_names:

                metadata.tables.append(
                    TableMetadata(
                        name=collection_name,
                        table_type="COLLECTION",
                    )
                )

        return _serialize_metadata(metadata)

    finally:
        if client is not None:
            client.close()


# ============================================================
# DYNAMODB
# ============================================================

def _extract_dynamodb(connection: Any) -> dict[str, Any]:

    import boto3

    region = (
        getattr(connection, "aws_region", None)
        or getattr(connection, "region", None)
    )

    if not region:
        raise ValueError(
            "AWS region is required for DynamoDB."
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
        client_kwargs.update(
            {
                "aws_access_key_id": access_key,
                "aws_secret_access_key": secret_key,
            }
        )

    client = boto3.client(
        "dynamodb",
        **client_kwargs,
    )

    metadata = DatabaseMetadata(
        database_name="AWS DynamoDB",
        database_type="dynamodb",
    )

    # Metadata-only API.
    response = client.list_tables()

    for table_name in response.get(
        "TableNames",
        [],
    ):

        metadata.tables.append(
            TableMetadata(
                name=table_name,
                table_type="DYNAMODB_TABLE",
            )
        )

    return _serialize_metadata(metadata)


# ============================================================
# CASSANDRA
# ============================================================

def _extract_cassandra(connection: Any) -> dict[str, Any]:

    from cassandra.cluster import Cluster

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

        from cassandra.auth import PlainTextAuthProvider

        auth_provider = PlainTextAuthProvider(
            username=username,
            password=password,
        )

    cluster = Cluster(
        [connection.host],
        port=connection.port,
        auth_provider=auth_provider,
    )

    session = cluster.connect()

    try:

        keyspace = connection.keyspace

        metadata = DatabaseMetadata(
            database_name=keyspace,
            database_type="cassandra",
        )

        # Cassandra driver metadata is schema metadata only.
        cluster_metadata = cluster.metadata

        keyspace_metadata = (
            cluster_metadata.keyspaces.get(keyspace)
        )

        if keyspace_metadata is None:
            raise ValueError(
                f"Cassandra keyspace '{keyspace}' not found."
            )

        for table_name, table_info in (
            keyspace_metadata.tables.items()
        ):

            table = TableMetadata(
                name=table_name,
                table_type="TABLE",
            )

            for column_name, column_info in (
                table_info.columns.items()
            ):

                is_primary = (
                    column_name
                    in table_info.partition_key
                    or column_name
                    in table_info.clustering_key
                )

                table.columns.append(
                    ColumnMetadata(
                        name=column_name,
                        data_type=str(
                            column_info.cql_type
                        ),
                        nullable=True,
                        primary_key=is_primary,
                        auto_increment=False,
                        constraints=(
                            ["PRIMARY KEY"]
                            if is_primary
                            else []
                        ),
                    )
                )

                if is_primary:
                    table.primary_keys.append(
                        column_name
                    )

            metadata.tables.append(table)

        return _serialize_metadata(metadata)

    finally:
        session.shutdown()
        cluster.shutdown()


# ============================================================
# FIREBASE FIRESTORE
# ============================================================

def _extract_firebase(connection: Any) -> dict[str, Any]:

    """
    Firestore is schemaless.

    We intentionally do NOT read documents to infer fields,
    because that would violate the SRS metadata-only rule.

    Therefore Module 5 reports collection-level metadata only.
    """

    import firebase_admin
    from firebase_admin import credentials
    from firebase_admin import firestore

    app = None

    service_account = getattr(
        connection,
        "service_account",
        None,
    )

    if not service_account:
        raise ValueError(
            "Firebase service account configuration is required."
        )

    try:

        cred = credentials.Certificate(
            service_account
        )

        app = firebase_admin.initialize_app(
            cred
        )

        database = firestore.client(
            app=app
        )

        metadata = DatabaseMetadata(
            database_name="Firebase Firestore",
            database_type="firebase",
        )

        # Collection references are schema-level metadata.
        for collection in database.collections():

            metadata.tables.append(
                TableMetadata(
                    name=collection.id,
                    table_type="COLLECTION",
                )
            )

        return _serialize_metadata(metadata)

    finally:

        if app is not None:

            try:
                firebase_admin.delete_app(app)
            except Exception:
                pass


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def extract_database_metadata(
    connection: Any,
) -> dict[str, Any]:

    """
    Extract database schema metadata only.

    NEVER:
    - SELECT *
    - read business records
    - cache business records
    - return credentials
    - return passwords
    - return connection strings
    """

    database_type = (
        getattr(
            connection,
            "database_type",
            "",
        )
        or ""
    ).lower()

    database_name = _safe_database_name(
        connection
    )

    try:

        if database_type == "mysql":
            return _extract_mysql(connection)

        if database_type == "postgresql":
            return _extract_postgresql(connection)

        if database_type == "sqlserver":
            return _extract_sqlserver(connection)

        if database_type == "oracle":
            return _extract_oracle(connection)

        if database_type == "sqlite":
            return _extract_sqlite(connection)

        if database_type == "mongodb":
            return _extract_mongodb(connection)

        if database_type == "dynamodb":
            return _extract_dynamodb(connection)

        if database_type == "cassandra":
            return _extract_cassandra(connection)

        if database_type == "firebase":
            return _extract_firebase(connection)

        raise ValueError(
            f"Unsupported database type: {database_type}"
        )

    except Exception as exc:

        safe_error = _safe_error(exc)

        logger.warning(
            "Metadata extraction failed for %s: %s",
            database_type,
            safe_error,
        )

        raise ValueError(
            f"Metadata extraction failed: {safe_error}"
        ) from exc