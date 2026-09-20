from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db

from app.models.relationship import Relationship

from app.schemas.relationship import (
    RelationshipRequest,
    RelationshipResponse,
)

from app.services.relationship_service import (
    create_relationship,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/database",
    tags=["Relationships"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class RelationshipWithMetadataRequest(BaseModel):
    relationship: RelationshipRequest
    schema_metadata: dict[str, Any]


# ============================================================
# CREATE RELATIONSHIP
# ============================================================

@router.post(
    "/relationship",
    response_model=RelationshipResponse,
    status_code=status.HTTP_200_OK,
)
def create_relationship_mapping(
    request: RelationshipWithMetadataRequest,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create and validate a relationship between two
    database columns.

    Only schema metadata is used.

    No business records are read.
    No SELECT * is performed.
    No customer/business data is stored.
    """

    try:

        relationship = create_relationship(
            request=request.relationship,
            schema_metadata=request.schema_metadata,
            db=db,
            user_id=current_user.id,
        )

        return {
            "message": "Relationship created successfully.",
            "relationship": relationship,
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        db.rollback()

        print(
            "CREATE RELATIONSHIP ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create relationship.",
        ) from exc


# ============================================================
# GET ALL RELATIONSHIPS
# ============================================================

@router.get(
    "/relationships",
)
def get_relationships(
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all saved relationships for the logged-in user.

    Only metadata about relationships is returned.
    No business/customer data is accessed.
    """

    try:

        relationships = (
            db.query(Relationship)
            .filter(
                Relationship.user_id
                == current_user.id
            )
            .order_by(
                Relationship.id.asc()
            )
            .all()
        )

        return {
            "relationships": [
                {
                    "id": relationship.id,
                    "database_connection_id": (
                        relationship.database_connection_id
                    ),
                    "parent_table": (
                        relationship.parent_table
                    ),
                    "parent_column": (
                        relationship.parent_column
                    ),
                    "child_table": (
                        relationship.child_table
                    ),
                    "child_column": (
                        relationship.child_column
                    ),
                    "created_at": (
                        relationship.created_at
                    ),
                }
                for relationship in relationships
            ],
            "count": len(
                relationships
            ),
        }

    except Exception as exc:

        print(
            "GET RELATIONSHIPS ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch relationships.",
        ) from exc