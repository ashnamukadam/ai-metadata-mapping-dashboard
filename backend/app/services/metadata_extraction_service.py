import logging
from dataclasses import asdict, dataclass, field
from typing import Any
from dataclasses import asdict

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
            root_path = Path(root).resolve()
            database_path = Path(database_name)

            # Absolute paths are allowed for programmatic/test use.
            # Relative paths remain restricted to SQLITE_DATABASE_ROOT.
            if database_path.is_absolute():
                final_path = database_path.resolve()
            else:
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

            if not final_path.exists():
                raise ValueError(
                    f"SQLite database was not found: {final_path}"
                )

            final_database = str(final_path)

        else:
            final_database = str(
                Path(database_name).resolve()
            )

    conn = None

    try:
        conn = sqlite3.connect(final_database)
        cursor = conn.cursor()

        metadata = DatabaseMetadata(
            database_name=database_name,
            database_type="sqlite",
        )

        cursor.execute(
            """
            SELECT name, type
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

            cursor.execute(
                f'PRAGMA table_info("{object_name}")'
            )

            for row in cursor.fetchall():

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
                    constraints.append("AUTO_INCREMENT")

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
                    table.primary_keys.append(column_name)

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

        return asdict(metadata)

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
        host = connection.host
        port = connection.port
        service_name = getattr(
            connection,
            "service_name",
            None,
        )

        # Some request/model objects may not define
        # service_name. MagicMock and similar dynamic
        # objects can return a non-string placeholder here,
        # so fall back to database_name unless we have a
        # real non-empty string.
        if (
            not isinstance(service_name, str)
            or not service_name.strip()
        ):
            service_name = getattr(
                connection,
                "database_name",
                None,
            )

        dsn = oracledb.makedsn(
            host,
            port,
            service_name=service_name,
        )

        conn = oracledb.connect(
            user=connection.username,
            password=connection.password,
            dsn=dsn,
        )

        cursor = conn.cursor()

        database_name = getattr(
            connection,
            "database_name",
            None,
        ) or "N/A"

        metadata = DatabaseMetadata(
            database_name=database_name,
            database_type="oracle",
        )

        # Tables.
        cursor.execute(
            """
            SELECT table_name
            FROM user_tables
            ORDER BY table_name
            """
        )
        table_names = [
            row[0]
            for row in cursor.fetchall()
        ]

        # Views.
        cursor.execute(
            """
            SELECT view_name
            FROM user_views
            ORDER BY view_name
            """
        )
        view_names = [
            row[0]
            for row in cursor.fetchall()
        ]

        def extract_object(
            object_name: str,
            table_type: str,
        ) -> TableMetadata:
            table = TableMetadata(
                name=object_name,
                table_type=table_type,
            )

            cursor.execute(
                """
                SELECT
                    column_name,
                    data_type,
                    nullable,
                    data_default
                FROM user_tab_columns
                WHERE table_name = :table_name
                ORDER BY column_id
                """,
                {"table_name": object_name},
            )

            for (
                column_name,
                data_type,
                nullable,
                default_value,
            ) in cursor.fetchall():
                table.columns.append(
                    ColumnMetadata(
                        name=column_name,
                        data_type=str(data_type),
                        nullable=nullable == "Y",
                        default=default_value,
                        constraints=(
                            ["NOT NULL"]
                            if nullable == "N"
                            else []
                        ),
                    )
                )

            cursor.execute(
                """
                SELECT column_name
                FROM user_cons_columns
                WHERE constraint_name IN (
                    SELECT constraint_name
                    FROM user_constraints
                    WHERE table_name = :table_name
                      AND constraint_type = 'P'
                )
                ORDER BY position
                """,
                {"table_name": object_name},
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

            cursor.execute(
                """
                SELECT column_name
                FROM user_tab_identity_cols
                WHERE table_name = :table_name
                """,
                {"table_name": object_name},
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

            cursor.execute(
                """
                SELECT
                    c.constraint_name,
                    cc.column_name,
                    r.table_name,
                    rcc.column_name
                FROM user_constraints c
                JOIN user_cons_columns cc
                  ON c.constraint_name = cc.constraint_name
                 AND c.owner = cc.owner
                JOIN user_constraints r
                  ON c.r_constraint_name = r.constraint_name
                 AND c.r_owner = r.owner
                JOIN user_cons_columns rcc
                  ON r.constraint_name = rcc.constraint_name
                 AND r.owner = rcc.owner
                 AND cc.position = rcc.position
                WHERE c.table_name = :table_name
                  AND c.constraint_type = 'R'
                ORDER BY c.constraint_name, cc.position
                """,
                {"table_name": object_name},
            )

            for (
                constraint_name,
                column_name,
                referenced_table,
                referenced_column,
            ) in cursor.fetchall():
                table.foreign_keys.append(
                    ForeignKeyMetadata(
                        column=column_name,
                        referenced_table=referenced_table,
                        referenced_column=referenced_column,
                        constraint_name=constraint_name,
                    )
                )

            cursor.execute(
                """
                SELECT
                    index_name,
                    column_name,
                    CASE
                        WHEN uniqueness = 'UNIQUE'
                        THEN 1
                        ELSE 0
                    END
                FROM user_ind_columns
                JOIN user_indexes USING (index_name)
                WHERE table_name = :table_name
                ORDER BY index_name, column_position
                """,
                {"table_name": object_name},
            )

            indexes: dict[str, IndexMetadata] = {}

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
                indexes[index_name].columns.append(
                    column_name
                )

            table.indexes = list(indexes.values())
            return table

        for table_name in table_names:
            metadata.tables.append(
                extract_object(
                    table_name,
                    "TABLE",
                )
            )

        for view_name in view_names:
            metadata.views.append(
                extract_object(
                    view_name,
                    "VIEW",
                )
            )

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
        available_drivers = pyodbc.drivers()
        if not available_drivers:
            raise ValueError(
                "No SQL Server ODBC driver is installed."
            )

        preferred_drivers = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "SQL Server",
        ]

        driver = next(
            (
                candidate
                for candidate in preferred_drivers
                if candidate in available_drivers
            ),
            available_drivers[0],
        )

        conn = pyodbc.connect(
            f"DRIVER={{{driver}}};"
            f"SERVER={connection.host},{connection.port};"
            f"DATABASE={connection.database_name};"
            f"UID={connection.username};"
            f"PWD={connection.password};"
            "TrustServerCertificate=yes;",
            timeout=5,
        )

        cursor = conn.cursor()

        database_name = getattr(
            connection,
            "database_name",
            None,
        ) or "N/A"

        metadata = DatabaseMetadata(
            database_name=database_name,
            database_type="sqlserver",
        )

        cursor.execute(
            """
            SELECT
                s.name,
                o.name,
                CASE
                    WHEN o.type = 'V'
                    THEN 'VIEW'
                    ELSE 'BASE TABLE'
                END
            FROM sys.objects o
            INNER JOIN sys.schemas s
                ON o.schema_id = s.schema_id
            WHERE o.type IN ('U', 'V')
              AND o.is_ms_shipped = 0
            ORDER BY s.name, o.name
            """
        )

        objects = cursor.fetchall()

        for schema_name, object_name, object_type in objects:
            table = TableMetadata(
                name=object_name,
                table_type=object_type,
            )

            cursor.execute(
                """
                SELECT
                    c.name,
                    t.name,
                    CASE
                        WHEN c.is_nullable = 1
                        THEN 'YES'
                        ELSE 'NO'
                    END,
                    dc.definition
                FROM sys.columns c
                INNER JOIN sys.tables tb
                    ON c.object_id = tb.object_id
                INNER JOIN sys.types t
                    ON c.user_type_id = t.user_type_id
                INNER JOIN sys.schemas s
                    ON tb.schema_id = s.schema_id
                LEFT JOIN sys.default_constraints dc
                    ON c.default_object_id = dc.object_id
                WHERE s.name = ?
                  AND tb.name = ?
                ORDER BY c.column_id
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
                table.columns.append(
                    ColumnMetadata(
                        name=column_name,
                        data_type=str(data_type),
                        nullable=nullable == "YES",
                        default=default_value,
                        constraints=(
                            ["NOT NULL"]
                            if nullable == "NO"
                            else []
                        ),
                    )
                )

            cursor.execute(
                """
                SELECT c.name
                FROM sys.columns c
                INNER JOIN sys.tables tb
                    ON c.object_id = tb.object_id
                INNER JOIN sys.schemas s
                    ON tb.schema_id = s.schema_id
                WHERE s.name = ?
                  AND tb.name = ?
                  AND c.is_identity = 1
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
                    column.constraints.append(
                        "AUTO_INCREMENT"
                    )

            cursor.execute(
                """
                SELECT c.name
                FROM sys.indexes i
                INNER JOIN sys.index_columns ic
                    ON i.object_id = ic.object_id
                   AND i.index_id = ic.index_id
                INNER JOIN sys.columns c
                    ON ic.object_id = c.object_id
                   AND ic.column_id = c.column_id
                INNER JOIN sys.tables tb
                    ON i.object_id = tb.object_id
                INNER JOIN sys.schemas s
                    ON tb.schema_id = s.schema_id
                WHERE s.name = ?
                  AND tb.name = ?
                  AND i.is_primary_key = 1
                ORDER BY ic.key_ordinal
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

            cursor.execute(
                """
                SELECT
                    fk.name,
                    pc.name,
                    rs.name,
                    rt.name,
                    rc.name
                FROM sys.foreign_keys fk
                INNER JOIN sys.foreign_key_columns fkc
                    ON fk.object_id = fkc.constraint_object_id
                INNER JOIN sys.tables pt
                    ON fk.parent_object_id = pt.object_id
                INNER JOIN sys.schemas ps
                    ON pt.schema_id = ps.schema_id
                INNER JOIN sys.columns pc
                    ON fkc.parent_object_id = pc.object_id
                   AND fkc.parent_column_id = pc.column_id
                INNER JOIN sys.tables rt
                    ON fk.referenced_object_id = rt.object_id
                INNER JOIN sys.schemas rs
                    ON rt.schema_id = rs.schema_id
                INNER JOIN sys.columns rc
                    ON fkc.referenced_object_id = rc.object_id
                   AND fkc.referenced_column_id = rc.column_id
                WHERE ps.name = ?
                  AND pt.name = ?
                ORDER BY fk.name, fkc.constraint_column_id
                """,
                schema_name,
                object_name,
            )

            for (
                constraint_name,
                column_name,
                referenced_schema,
                referenced_table,
                referenced_column,
            ) in cursor.fetchall():
                table.foreign_keys.append(
                    ForeignKeyMetadata(
                        column=column_name,
                        referenced_table=referenced_table,
                        referenced_column=referenced_column,
                        constraint_name=constraint_name,
                    )
                )

            cursor.execute(
                """
                SELECT
                    i.name,
                    c.name,
                    i.is_unique
                FROM sys.indexes i
                INNER JOIN sys.index_columns ic
                    ON i.object_id = ic.object_id
                   AND i.index_id = ic.index_id
                INNER JOIN sys.columns c
                    ON ic.object_id = c.object_id
                   AND ic.column_id = c.column_id
                INNER JOIN sys.tables tb
                    ON i.object_id = tb.object_id
                INNER JOIN sys.schemas s
                    ON tb.schema_id = s.schema_id
                WHERE s.name = ?
                  AND tb.name = ?
                  AND i.is_primary_key = 0
                  AND i.is_unique_constraint = 0
                ORDER BY i.name, ic.key_ordinal
                """,
                schema_name,
                object_name,
            )

            indexes: dict[str, IndexMetadata] = {}

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

        if database_type == "oracle":
            return _extract_oracle(connection)

        if database_type == "sqlserver":
            return _extract_sqlserver(connection)

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