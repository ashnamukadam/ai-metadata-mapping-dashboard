from typing import Any
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.session import get_db

from app.models.database_connection import (
    DatabaseConnection,
)

from app.models.metadata_table import (
    MetadataTable,
)

from app.models.metadata_column import (
    MetadataColumn,
)

from app.models.metadata_index import (
    MetadataIndex,
)

from app.models.metadata_constraint import (
    MetadataConstraint,
)

from app.models.relationship import (
    Relationship,
)

from app.auth.dependencies import (
    get_current_user,
)

from app.services.metadata_extraction_service import (
    extract_database_metadata,
)


router = APIRouter(
    prefix="/database",
    tags=["Metadata Extraction"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class MetadataExtractionRequest(BaseModel):

    database_type: str

    # SQL DATABASE FIELDS
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None

    # COMMON
    database_name: str

    # MONGODB
    connection_string: str | None = None


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def normalize_database_type(
    database_type: str | None
) -> str:

    if not database_type:
        return ""

    return database_type.strip().lower()


def normalize_database_name(
    database_name: str | None
) -> str:

    if not database_name:
        return ""

    return database_name.strip()


def normalize_sql_host(
    host: str | None
) -> str | None:

    if not host:
        return host

    host = host.strip()

    if "@" in host:

        host = host.rsplit(
            "@",
            1
        )[-1].strip()

    return host


def find_database_connection(
    db: Session,
    current_user: Any,
    database_type: str,
    database_name: str,
):

    query = (
        db.query(
            DatabaseConnection
        )
        .filter(
            DatabaseConnection.user_id
            == current_user.id,

            DatabaseConnection.database_type
            == database_type,

            DatabaseConnection.database_name
            == database_name,
        )
        .order_by(
            DatabaseConnection.id.desc()
        )
    )

    return query.first()


# ============================================================
# POST /database/metadata
# ============================================================

@router.post("/metadata")
def extract_metadata(

    request: MetadataExtractionRequest,

    current_user: Any = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    try:

        # ====================================================
        # VALIDATE DATABASE TYPE
        # ====================================================

        database_type = normalize_database_type(
            request.database_type
        )

        if not database_type:

            raise HTTPException(
                status_code=400,
                detail="Database type is required.",
            )

        # ====================================================
        # VALIDATE DATABASE NAME
        # ====================================================

        database_name = normalize_database_name(
            request.database_name
        )

        if not database_name:

            raise HTTPException(
                status_code=400,
                detail="Database name is required.",
            )

        # ====================================================
        # MONGODB
        # ====================================================

        if database_type == "mongodb":

            connection_string = (
                request.connection_string.strip()
                if request.connection_string
                else ""
            )

            if not connection_string:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "connection_string is required "
                        "for MongoDB."
                    ),
                )

        else:

            connection_string = None

        # ====================================================
        # SQL DATABASES
        # ====================================================

        sql_databases = {
            "mysql",
            "postgresql",
            "sqlserver",
            "oracle",
        }

        host = request.host
        port = request.port
        username = request.username
        password = request.password

        if database_type in sql_databases:

            host = normalize_sql_host(
                host
            )

            if not host:

                raise HTTPException(
                    status_code=400,
                    detail="Host is required.",
                )

            if not port:

                raise HTTPException(
                    status_code=400,
                    detail="Port is required.",
                )

            if not username:

                raise HTTPException(
                    status_code=400,
                    detail="Username is required.",
                )

            if password is None:

                raise HTTPException(
                    status_code=400,
                    detail="Password is required.",
                )

        # ====================================================
        # FIND EXACT DATABASE CONNECTION
        # ====================================================

        connection = find_database_connection(
            db=db,
            current_user=current_user,
            database_type=database_type,
            database_name=database_name,
        )

        # ====================================================
        # DEACTIVATE OTHER CONNECTIONS
        #
        # IMPORTANT:
        #
        # If the user switches from MongoDB to PostgreSQL
        # for the same database name, the old MongoDB
        # connection must no longer be considered active.
        #
        # Example:
        #
        # MongoDB       -> connected=False
        # PostgreSQL    -> connected=True
        #
        # This allows GET /database/metadata to return
        # the currently selected database type.
        # ====================================================

        db.query(
            DatabaseConnection
        ).filter(

            DatabaseConnection.user_id
            == current_user.id,

            DatabaseConnection.database_name
            == database_name,

            DatabaseConnection.id
            != (
                connection.id
                if connection is not None
                else -1
            ),

        ).update(

            {
                DatabaseConnection.connected:
                    False
            },

            synchronize_session=False,

        )

        # ====================================================
        # CREATE CONNECTION IF NEEDED
        # ====================================================

        if connection is None:

            connection = DatabaseConnection(

                user_id=current_user.id,

                database_type=database_type,

                database_name=database_name,

                host=host,

                port=port,

                username=username,

                connected=True,

            )

            if database_type == "mongodb":

                connection.connection_string = (
                    connection_string
                )

            db.add(
                connection
            )

            db.commit()

            db.refresh(
                connection
            )

        else:

            # =================================================
            # UPDATE EXISTING CONNECTION
            # =================================================

            connection.database_type = (
                database_type
            )

            connection.database_name = (
                database_name
            )

            connection.connected = True

            if database_type in sql_databases:

                connection.host = host

                connection.port = port

                connection.username = username

            if database_type == "mongodb":

                connection.connection_string = (
                    connection_string
                )

            db.commit()

            db.refresh(
                connection
            )

        # ====================================================
        # BUILD EXTRACTION CONNECTION
        # ====================================================

        extraction_connection = SimpleNamespace(

            database_type=database_type,

            host=host,

            port=port,

            database_name=database_name,

            username=username,

            password=password,

            connection_string=connection_string,

        )

        # ====================================================
        # EXTRACT METADATA
        # ====================================================

        metadata = extract_database_metadata(
            extraction_connection
        )

        if not isinstance(
            metadata,
            dict
        ):

            raise ValueError(
                "Metadata extraction service returned "
                "an invalid response."
            )

        # ====================================================
        # DELETE OLD COLUMNS
        # ====================================================

        db.query(
            MetadataColumn
        ).filter(

            MetadataColumn.user_id
            == current_user.id,

            MetadataColumn.database_connection_id
            == connection.id,

        ).delete(
            synchronize_session=False
        )

        # ====================================================
        # DELETE OLD INDEXES
        # ====================================================

        db.query(
            MetadataIndex
        ).filter(

            MetadataIndex.user_id
            == current_user.id,

            MetadataIndex.database_connection_id
            == connection.id,

        ).delete(
            synchronize_session=False
        )

        # ====================================================
        # DELETE OLD CONSTRAINTS
        # ====================================================

        db.query(
            MetadataConstraint
        ).filter(

            MetadataConstraint.user_id
            == current_user.id,

            MetadataConstraint.database_connection_id
            == connection.id,

        ).delete(
            synchronize_session=False
        )

        # ====================================================
        # DELETE OLD TABLES
        # ====================================================

        db.query(
            MetadataTable
        ).filter(

            MetadataTable.user_id
            == current_user.id,

            MetadataTable.database_connection_id
            == connection.id,

        ).delete(
            synchronize_session=False
        )

        # ====================================================
        # DELETE OLD RELATIONSHIPS
        # ====================================================

        db.query(
            Relationship
        ).filter(

            Relationship.user_id
            == current_user.id,

            Relationship.database_connection_id
            == connection.id,

        ).delete(
            synchronize_session=False
        )

        db.commit()

        # ====================================================
        # COUNTERS
        # ====================================================

        tables_count = 0
        views_count = 0
        columns_count = 0
        relationships_count = 0
        indexes_count = 0
        constraints_count = 0

        # ====================================================
        # GET TABLES AND VIEWS
        # ====================================================

        tables = metadata.get(
            "tables",
            []
        )

        views = metadata.get(
            "views",
            []
        )

        # ====================================================
        # SAVE TABLES
        # ====================================================

        for table in tables:

            if not isinstance(
                table,
                dict
            ):
                continue

            table_name = table.get(
                "name"
            )

            if not table_name:
                continue

            metadata_table = MetadataTable(

                user_id=current_user.id,

                database_connection_id=
                    connection.id,

                schema_name=table.get(
                    "schema_name",
                    table.get(
                        "schema",
                        "public"
                    )
                ),

                table_name=table_name,

                table_type=table.get(
                    "table_type",
                    "table"
                ),

            )

            db.add(
                metadata_table
            )

            tables_count += 1

            # =================================================
            # COLUMNS
            # =================================================

            for column in table.get(
                "columns",
                []
            ):

                if not isinstance(
                    column,
                    dict
                ):
                    continue

                column_name = column.get(
                    "name"
                )

                if not column_name:
                    continue

                metadata_column = MetadataColumn(

                    user_id=current_user.id,

                    database_connection_id=
                        connection.id,

                    table_name=table_name,

                    column_name=column_name,

                    data_type=column.get(
                        "data_type",
                        "unknown"
                    ),

                    nullable=int(
                        bool(
                            column.get(
                                "nullable",
                                True
                            )
                        )
                    ),

                    primary_key=int(
                        bool(
                            column.get(
                                "primary_key",
                                False
                            )
                        )
                    ),

                    auto_increment=int(
                        bool(
                            column.get(
                                "auto_increment",
                                False
                            )
                        )
                    ),

                )

                db.add(
                    metadata_column
                )

                columns_count += 1

            # =================================================
            # INDEXES
            # =================================================

            for index in table.get(
                "indexes",
                []
            ):

                if not isinstance(
                    index,
                    dict
                ):
                    continue

                index_name = index.get(
                    "name"
                )

                if not index_name:
                    continue

                index_columns = index.get(
                    "columns",
                    []
                )

                if isinstance(
                    index_columns,
                    list
                ):

                    columns_text = ", ".join(
                        str(column)
                        for column in index_columns
                        if column
                    )

                else:

                    columns_text = str(
                        index_columns
                    )

                metadata_index = MetadataIndex(

                    user_id=current_user.id,

                    database_connection_id=
                        connection.id,

                    table_name=table_name,

                    index_name=index_name,

                    columns=columns_text,

                    unique=bool(
                        index.get(
                            "unique",
                            False
                        )
                    ),

                )

                db.add(
                    metadata_index
                )

                indexes_count += 1

            # =================================================
            # FOREIGN KEY RELATIONSHIPS
            # =================================================

            for foreign_key in table.get(
                "foreign_keys",
                []
            ):

                if not isinstance(
                    foreign_key,
                    dict
                ):
                    continue

                referenced_table = (
                    foreign_key.get(
                        "referenced_table"
                    )
                )

                referenced_column = (
                    foreign_key.get(
                        "referenced_column"
                    )
                )

                child_column = (
                    foreign_key.get(
                        "column"
                    )
                )

                if not (
                    referenced_table
                    and referenced_column
                    and child_column
                ):
                    continue

                relationship = Relationship(

                    user_id=current_user.id,

                    database_connection_id=
                        connection.id,

                    parent_table=
                        referenced_table,

                    parent_column=
                        referenced_column,

                    child_table=
                        table_name,

                    child_column=
                        child_column,

                )

                db.add(
                    relationship
                )

                relationships_count += 1

            # =================================================
            # CONSTRAINTS
            # =================================================

            constraint_names = set()

            # -------------------------------------------------
            # EXTRACTED CONSTRAINTS
            # -------------------------------------------------

            for constraint in table.get(
                "constraints",
                []
            ):

                if not isinstance(
                    constraint,
                    dict
                ):
                    continue

                constraint_name = constraint.get(
                    "name"
                )

                constraint_type = constraint.get(
                    "constraint_type"
                )

                if not constraint_name:
                    continue

                if not constraint_type:
                    continue

                if constraint_name in constraint_names:
                    continue

                constraint_columns = constraint.get(
                    "columns",
                    []
                )

                if isinstance(
                    constraint_columns,
                    list
                ):

                    columns_text = ", ".join(
                        str(column)
                        for column in constraint_columns
                        if column
                    )

                else:

                    columns_text = str(
                        constraint_columns
                    )

                definition = constraint.get(
                    "definition"
                )

                db.add(
                    MetadataConstraint(

                        user_id=current_user.id,

                        database_connection_id=
                            connection.id,

                        table_name=table_name,

                        constraint_name=
                            constraint_name,

                        constraint_type=
                            str(
                                constraint_type
                            ),

                        columns=columns_text,

                        definition=definition,

                    )
                )

                constraint_names.add(
                    constraint_name
                )

                constraints_count += 1

            # -------------------------------------------------
            # PRIMARY KEY FALLBACK
            # -------------------------------------------------

            primary_keys = table.get(
                "primary_keys",
                []
            )

            if primary_keys:

                existing_primary = any(

                    str(
                        constraint.get(
                            "constraint_type",
                            ""
                        )
                    ).upper()
                    == "PRIMARY KEY"

                    for constraint
                    in table.get(
                        "constraints",
                        []
                    )

                    if isinstance(
                        constraint,
                        dict
                    )

                )

                if not existing_primary:

                    constraint_name = (
                        f"pk_{table_name}"
                    )

                    if (
                        constraint_name
                        not in constraint_names
                    ):

                        columns_text = ", ".join(
                            str(column)
                            for column in primary_keys
                        )

                        db.add(
                            MetadataConstraint(

                                user_id=
                                    current_user.id,

                                database_connection_id=
                                    connection.id,

                                table_name=
                                    table_name,

                                constraint_name=
                                    constraint_name,

                                constraint_type=
                                    "PRIMARY KEY",

                                columns=
                                    columns_text,

                                definition=
                                    "PRIMARY KEY",

                            )
                        )

                        constraint_names.add(
                            constraint_name
                        )

                        constraints_count += 1

            # -------------------------------------------------
            # FOREIGN KEY FALLBACK
            # -------------------------------------------------

            for foreign_key in table.get(
                "foreign_keys",
                []
            ):

                if not isinstance(
                    foreign_key,
                    dict
                ):
                    continue

                constraint_name = (
                    foreign_key.get(
                        "constraint_name"
                    )
                )

                if not constraint_name:

                    constraint_name = (
                        "fk_"
                        + table_name
                        + "_"
                        + str(
                            foreign_key.get(
                                "column",
                                ""
                            )
                        )
                    )

                if constraint_name in constraint_names:
                    continue

                child_column = (
                    foreign_key.get(
                        "column",
                        ""
                    )
                )

                referenced_table = (
                    foreign_key.get(
                        "referenced_table",
                        ""
                    )
                )

                referenced_column = (
                    foreign_key.get(
                        "referenced_column",
                        ""
                    )
                )

                if not (
                    child_column
                    and referenced_table
                    and referenced_column
                ):
                    continue

                definition = (
                    f"{table_name}."
                    f"{child_column}"
                    f" REFERENCES "
                    f"{referenced_table}."
                    f"{referenced_column}"
                )

                db.add(
                    MetadataConstraint(

                        user_id=
                            current_user.id,

                        database_connection_id=
                            connection.id,

                        table_name=
                            table_name,

                        constraint_name=
                            constraint_name,

                        constraint_type=
                            "FOREIGN KEY",

                        columns=
                            str(
                                child_column
                            ),

                        definition=
                            definition,

                    )
                )

                constraint_names.add(
                    constraint_name
                )

                constraints_count += 1

            # -------------------------------------------------
            # NOT NULL CONSTRAINTS
            # -------------------------------------------------

            for column in table.get(
                "columns",
                []
            ):

                if not isinstance(
                    column,
                    dict
                ):
                    continue

                if (
                    column.get(
                        "nullable",
                        True
                    )
                    is False
                ):

                    column_name = column.get(
                        "name",
                        ""
                    )

                    if not column_name:
                        continue

                    constraint_name = (
                        f"nn_{table_name}_"
                        f"{column_name}"
                    )

                    if (
                        constraint_name
                        in constraint_names
                    ):
                        continue

                    db.add(
                        MetadataConstraint(

                            user_id=
                                current_user.id,

                            database_connection_id=
                                connection.id,

                            table_name=
                                table_name,

                            constraint_name=
                                constraint_name,

                            constraint_type=
                                "NOT NULL",

                            columns=
                                column_name,

                            definition=
                                "NOT NULL",

                        )
                    )

                    constraint_names.add(
                        constraint_name
                    )

                    constraints_count += 1

            # -------------------------------------------------
            # UNIQUE INDEX CONSTRAINTS
            # -------------------------------------------------

            for index in table.get(
                "indexes",
                []
            ):

                if not isinstance(
                    index,
                    dict
                ):
                    continue

                if not index.get(
                    "unique",
                    False
                ):
                    continue

                index_name = index.get(
                    "name"
                )

                if not index_name:
                    continue

                if index_name in constraint_names:
                    continue

                index_columns = index.get(
                    "columns",
                    []
                )

                if isinstance(
                    index_columns,
                    list
                ):

                    columns_text = ", ".join(
                        str(column)
                        for column in index_columns
                        if column
                    )

                else:

                    columns_text = str(
                        index_columns
                    )

                db.add(
                    MetadataConstraint(

                        user_id=
                            current_user.id,

                        database_connection_id=
                            connection.id,

                        table_name=
                            table_name,

                        constraint_name=
                            index_name,

                        constraint_type=
                            "UNIQUE",

                        columns=
                            columns_text,

                        definition=
                            "UNIQUE INDEX",

                    )
                )

                constraint_names.add(
                    index_name
                )

                constraints_count += 1

        # ====================================================
        # SAVE VIEWS
        # ====================================================

        for view in views:

            if not isinstance(
                view,
                dict
            ):
                continue

            view_name = view.get(
                "name"
            )

            if not view_name:
                continue

            metadata_table = MetadataTable(

                user_id=current_user.id,

                database_connection_id=
                    connection.id,

                schema_name=view.get(
                    "schema_name",
                    view.get(
                        "schema",
                        "public"
                    )
                ),

                table_name=view_name,

                table_type="VIEW",

            )

            db.add(
                metadata_table
            )

            views_count += 1

            # =================================================
            # VIEW COLUMNS
            # =================================================

            for column in view.get(
                "columns",
                []
            ):

                if not isinstance(
                    column,
                    dict
                ):
                    continue

                column_name = column.get(
                    "name"
                )

                if not column_name:
                    continue

                metadata_column = MetadataColumn(

                    user_id=current_user.id,

                    database_connection_id=
                        connection.id,

                    table_name=view_name,

                    column_name=column_name,

                    data_type=column.get(
                        "data_type",
                        "unknown"
                    ),

                    nullable=int(
                        bool(
                            column.get(
                                "nullable",
                                True
                            )
                        )
                    ),

                    primary_key=int(
                        bool(
                            column.get(
                                "primary_key",
                                False
                            )
                        )
                    ),

                    auto_increment=int(
                        bool(
                            column.get(
                                "auto_increment",
                                False
                            )
                        )
                    ),

                )

                db.add(
                    metadata_column
                )

                columns_count += 1

        # ====================================================
        # FINAL COMMIT
        # ====================================================

        db.commit()

        # ====================================================
        # RESPONSE
        # ====================================================

        return {

            "message":
                "Metadata extracted successfully.",

            "database":
                database_name,

            "database_name":
                database_name,

            "database_type":
                database_type,

            "tables":
                tables_count,

            "views":
                views_count,

            "columns":
                columns_count,

            "relationships":
                relationships_count,

            "indexes":
                indexes_count,

            "constraints":
                constraints_count,

        }

    except HTTPException:

        raise

    except Exception as exc:

        db.rollback()

        print(
            "POST METADATA ERROR:",
            repr(exc)
        )

        raise HTTPException(

            status_code=400,

            detail=(
                "Metadata extraction failed: "
                + str(exc)
            ),

        ) from exc


# ============================================================
# GET /database/metadata
# ============================================================

@router.get("/metadata")
def get_metadata(

    database_type: str | None = Query(
        default=None
    ),

    database_name: str | None = Query(
        default=None
    ),

    current_user: Any = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    ),

):

    try:

        # ====================================================
        # NORMALIZE FILTERS
        # ====================================================

        requested_type = normalize_database_type(
            database_type
        )

        requested_name = normalize_database_name(
            database_name
        )

        # ====================================================
        # FIND CONNECTION FIRST
        # ====================================================

        query = (
            db.query(
                DatabaseConnection
            )
            .filter(
                DatabaseConnection.user_id
                == current_user.id,
            )
        )

        # ====================================================
        # DATABASE TYPE FILTER
        # ====================================================

        if requested_type:

            query = query.filter(
                DatabaseConnection.database_type
                == requested_type
            )

        # ====================================================
        # DATABASE NAME FILTER
        # ====================================================

        if requested_name:

            query = query.filter(
                DatabaseConnection.database_name
                == requested_name
            )

        # ====================================================
        # ONLY ACTIVE CONNECTION
        # ====================================================

        query = query.filter(
            DatabaseConnection.connected
            == True
        )

        # ====================================================
        # LATEST ACTIVE CONNECTION
        # ====================================================

        connection = (
            query
            .order_by(
                DatabaseConnection.id.desc()
            )
            .first()
        )

        # ====================================================
        # FALLBACK
        # ====================================================

        if connection is None:

            fallback_query = (
                db.query(
                    DatabaseConnection
                )
                .filter(
                    DatabaseConnection.user_id
                    == current_user.id,
                )
            )

            if requested_type:

                fallback_query = (
                    fallback_query.filter(
                        DatabaseConnection.database_type
                        == requested_type
                    )
                )

            if requested_name:

                fallback_query = (
                    fallback_query.filter(
                        DatabaseConnection.database_name
                        == requested_name
                    )
                )

            connection = (
                fallback_query
                .order_by(
                    DatabaseConnection.id.desc()
                )
                .first()
            )

        # ====================================================
        # NO CONNECTION
        # ====================================================

        if connection is None:

            raise HTTPException(

                status_code=404,

                detail=(
                    "No database connection found "
                    "for the selected database."
                ),

            )

        # ====================================================
        # TABLES
        # ====================================================

        metadata_tables = (

            db.query(
                MetadataTable
            )

            .filter(

                MetadataTable.user_id
                == current_user.id,

                MetadataTable.database_connection_id
                == connection.id,

            )

            .order_by(
                MetadataTable.id
            )

            .all()

        )

        # ====================================================
        # COLUMNS
        # ====================================================

        metadata_columns = (

            db.query(
                MetadataColumn
            )

            .filter(

                MetadataColumn.user_id
                == current_user.id,

                MetadataColumn.database_connection_id
                == connection.id,

            )

            .order_by(
                MetadataColumn.id
            )

            .all()

        )

        # ====================================================
        # INDEXES
        # ====================================================

        metadata_indexes = (

            db.query(
                MetadataIndex
            )

            .filter(

                MetadataIndex.user_id
                == current_user.id,

                MetadataIndex.database_connection_id
                == connection.id,

            )

            .order_by(
                MetadataIndex.id
            )

            .all()

        )

        # ====================================================
        # CONSTRAINTS
        # ====================================================

        metadata_constraints = (

            db.query(
                MetadataConstraint
            )

            .filter(

                MetadataConstraint.user_id
                == current_user.id,

                MetadataConstraint.database_connection_id
                == connection.id,

            )

            .order_by(
                MetadataConstraint.id
            )

            .all()

        )

        # ====================================================
        # RELATIONSHIPS
        # ====================================================

        relationships = (

            db.query(
                Relationship
            )

            .filter(

                Relationship.user_id
                == current_user.id,

                Relationship.database_connection_id
                == connection.id,

            )

            .all()

        )

        # ====================================================
        # GROUP COLUMNS
        # ====================================================

        columns_by_table = {}

        for column in metadata_columns:

            table_name = column.table_name

            if table_name not in columns_by_table:

                columns_by_table[
                    table_name
                ] = []

            column_constraints = []

            if not bool(
                column.nullable
            ):

                column_constraints.append(
                    "NOT NULL"
                )

            if bool(
                column.primary_key
            ):

                column_constraints.append(
                    "PRIMARY KEY"
                )

            if bool(
                column.auto_increment
            ):

                column_constraints.append(
                    "AUTO_INCREMENT"
                )

            # ------------------------------------------------
            # FOREIGN KEY
            # ------------------------------------------------

            for relationship in relationships:

                if (
                    relationship.child_table
                    == table_name
                    and
                    relationship.child_column
                    == column.column_name
                ):

                    if (
                        "FOREIGN KEY"
                        not in column_constraints
                    ):

                        column_constraints.append(
                            "FOREIGN KEY"
                        )

            columns_by_table[
                table_name
            ].append(

                {

                    "name":
                        column.column_name,

                    "data_type":
                        column.data_type,

                    "nullable":
                        bool(
                            column.nullable
                        ),

                    "primary_key":
                        bool(
                            column.primary_key
                        ),

                    "auto_increment":
                        bool(
                            column.auto_increment
                        ),

                    "default":
                        None,

                    "constraints":
                        column_constraints,

                }

            )

        # ====================================================
        # GROUP INDEXES
        # ====================================================

        indexes_by_table = {}

        for index in metadata_indexes:

            if (
                index.table_name
                not in indexes_by_table
            ):

                indexes_by_table[
                    index.table_name
                ] = []

            if index.columns:

                columns = [

                    column.strip()

                    for column
                    in index.columns.split(",")

                    if column.strip()

                ]

            else:

                columns = []

            indexes_by_table[
                index.table_name
            ].append(

                {

                    "name":
                        index.index_name,

                    "columns":
                        columns,

                    "unique":
                        bool(
                            index.unique
                        ),

                }

            )

        # ====================================================
        # GROUP CONSTRAINTS
        # ====================================================

        constraints_by_table = {}

        for constraint in metadata_constraints:

            if (
                constraint.table_name
                not in constraints_by_table
            ):

                constraints_by_table[
                    constraint.table_name
                ] = []

            constraint_text = (
                constraint.constraint_type
            )

            if constraint.constraint_name:

                constraint_text += (
                    f" ({constraint.constraint_name})"
                )

            if constraint.columns:

                constraint_text += (
                    f" - {constraint.columns}"
                )

            if constraint.definition:

                constraint_text += (
                    f" - {constraint.definition}"
                )

            constraints_by_table[
                constraint.table_name
            ].append(
                constraint_text
            )

        # ====================================================
        # BUILD TABLES / VIEWS
        # ====================================================

        tables = []
        views = []

        for metadata_table in metadata_tables:

            table_name = (
                metadata_table.table_name
            )

            table_type = (
                metadata_table.table_type
            )

            table_columns = (
                columns_by_table.get(
                    table_name,
                    []
                )
            )

            # =================================================
            # PRIMARY KEYS
            # =================================================

            primary_keys = [

                column["name"]

                for column
                in table_columns

                if column["primary_key"]

            ]

            # =================================================
            # FOREIGN KEYS
            # =================================================

            foreign_keys = []

            for relationship in relationships:

                if (
                    relationship.child_table
                    == table_name
                ):

                    foreign_keys.append(

                        {

                            "column":
                                relationship.child_column,

                            "referenced_table":
                                relationship.parent_table,

                            "referenced_column":
                                relationship.parent_column,

                            "constraint_name":
                                None,

                        }

                    )

            # =================================================
            # TABLE DATA
            # =================================================

            table_data = {

                "name":
                    table_name,

                "table_type":
                    table_type,

                "schema":
                    metadata_table.schema_name,

                "schema_name":
                    metadata_table.schema_name,

                "columns":
                    table_columns,

                "primary_keys":
                    primary_keys,

                "foreign_keys":
                    foreign_keys,

                "indexes":
                    indexes_by_table.get(
                        table_name,
                        []
                    ),

                "constraints":
                    constraints_by_table.get(
                        table_name,
                        []
                    ),

            }

            # =================================================
            # VIEW OR TABLE
            # =================================================

            if (
                str(table_type).upper()
                == "VIEW"
            ):

                views.append(
                    table_data
                )

            else:

                tables.append(
                    table_data
                )

        # ====================================================
        # FINAL RESPONSE
        # ====================================================

        return {

            "database_name":
                connection.database_name,

            "database_type":
                connection.database_type,

            "tables":
                tables,

            "views":
                views,

        }

    except HTTPException:

        raise

    except Exception as exc:

        print(
            "GET METADATA ERROR:",
            repr(exc)
        )

        raise HTTPException(

            status_code=500,

            detail=(
                "Unable to load database metadata."
            ),

        ) from exc