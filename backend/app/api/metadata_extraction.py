from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.database_connection import DatabaseConnection
from app.models.metadata_table import MetadataTable
from app.schemas.database_connection import DatabaseConnectionRequest
from app.schemas.metadata import MetadataExtractionResponse
from app.services.metadata_extraction_service import extract_database_metadata


router = APIRouter(
    prefix="/database",
    tags=["Schema Extraction"],
)


@router.post(
    "/metadata",
    response_model=MetadataExtractionResponse,
    status_code=status.HTTP_200_OK,
)
def extract_metadata(
    connection: DatabaseConnectionRequest,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = extract_database_metadata(connection)

        # Force a fresh plain dictionary from the extracted metadata.
        metadata = {
            "database_name": result["database_name"],
            "database_type": result["database_type"],
            "tables": list(result.get("tables", [])),
            "views": list(result.get("views", [])),
        }

        # --------------------------------------------------------
        # FIND REGISTERED DATABASE CONNECTION
        # --------------------------------------------------------

        database_connection = (
            db.query(DatabaseConnection)
            .filter(
                DatabaseConnection.user_id == current_user.id,
                DatabaseConnection.database_name
                == metadata["database_name"],
                DatabaseConnection.database_type
                == metadata["database_type"],
            )
            .order_by(
                DatabaseConnection.created_at.desc()
            )
            .first()
        )

        if database_connection is None:
            raise ValueError(
                "Database connection was not found for this user."
            )

        # --------------------------------------------------------
        # PERSIST EXTRACTED TABLE METADATA
        # --------------------------------------------------------

        for table in metadata["tables"]:
            table_name = table.get("name")

            if not table_name:
                continue

            existing_table = (
                db.query(MetadataTable)
                .filter(
                    MetadataTable.user_id == current_user.id,
                    MetadataTable.database_connection_id
                    == database_connection.id,
                    MetadataTable.table_name == table_name,
                )
                .first()
            )

            if existing_table is None:
                db.add(
                    MetadataTable(
                        user_id=current_user.id,
                        database_connection_id=database_connection.id,
                        table_name=table_name,
                        table_type=table.get(
                            "table_type",
                            "table",
                        ),
                    )
                )

        db.commit()

        return {
            "message": "Database schema metadata extracted successfully.",
            "metadata": metadata,
            "metadata_only": True,
        }

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except PermissionError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database schema metadata extraction failed.",
        ) from exc