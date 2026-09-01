from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.database_connection import DatabaseConnection
from app.schemas.database_connection import DatabaseConnectionRequest
from app.services.database_connection_service import (
    check_database_connection,
    parse_firebase_service_account,
    test_firebase_connection,
)


router = APIRouter(
    prefix="/database",
    tags=["Database Connection"],
)


@router.post(
    "/connect",
    status_code=status.HTTP_200_OK,
)
def connect_database(
    connection: DatabaseConnectionRequest,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Test connectivity to a supported database.

    Credentials are used only for the connection attempt.
    They are never persisted or returned.
    """

    try:
        result = check_database_connection(connection)

        connected = (
            result.connected
            if hasattr(result, "connected")
            else bool(result)
        )

        database_name = (
            getattr(connection, "database_name", None)
            or getattr(connection, "keyspace", None)
            or "N/A"
        )

        # Save only non-sensitive connection metadata.
        if connected:
            existing = (
                db.query(DatabaseConnection)
                .filter(
                    DatabaseConnection.user_id == current_user.id,
                    DatabaseConnection.database_name == database_name,
                    DatabaseConnection.database_type
                    == connection.database_type,
                )
                .first()
            )

            if existing is None:
                existing = DatabaseConnection(
                    user_id=current_user.id,
                    database_type=connection.database_type,
                    database_name=database_name,
                    connected=True,
                )
                db.add(existing)
            else:
                existing.connected = True

            db.commit()

        return {
            "message": (
                result.message
                if hasattr(result, "message")
                else "Database connection test completed."
            ),
            "database_type": connection.database_type,
            "database_name": database_name,
            "connected": connected,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Database connection test failed.",
        ) from exc


@router.post(
    "/connect/firebase",
    status_code=status.HTTP_200_OK,
)
async def connect_firebase(
    file: UploadFile = File(...),
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Test Firebase Firestore connectivity.

    The service-account credentials are used only for the
    connection attempt and are never persisted.
    """

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A Firebase service-account JSON file is required.",
        )

    if not file.filename.lower().endswith(".json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Firebase service-account file must be a JSON file.",
        )

    try:
        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded Firebase JSON file is empty.",
            )

        service_account = parse_firebase_service_account(contents)

        result = test_firebase_connection(
            service_account
        )

        connected = (
            result.connected
            if hasattr(result, "connected")
            else bool(result)
        )

        database_name = (
            service_account.get(
                "project_id",
                "firestore",
            )
        )

        if connected:
            existing = (
                db.query(DatabaseConnection)
                .filter(
                    DatabaseConnection.user_id == current_user.id,
                    DatabaseConnection.database_type == "firebase",
                    DatabaseConnection.database_name
                    == database_name,
                )
                .first()
            )

            if existing is None:
                existing = DatabaseConnection(
                    user_id=current_user.id,
                    database_type="firebase",
                    database_name=database_name,
                    connected=True,
                )
                db.add(existing)
            else:
                existing.connected = True

            db.commit()

        return {
            "message": (
                result.message
                if hasattr(result, "message")
                else (
                    "Firebase Firestore connection successful."
                    if connected
                    else "Firebase Firestore connection failed."
                )
            ),
            "database_type": "firebase",
            "database_name": database_name,
            "connected": connected,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Firebase Firestore connection test failed.",
        ) from exc


@router.delete(
    "/disconnect/{connection_id}",
    status_code=status.HTTP_200_OK,
)
def disconnect_database(
    connection_id: int,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disconnect a previously registered database.

    Only the authenticated user's connection metadata is removed.

    No database credentials are stored by this application,
    so there are no credentials to retain after disconnect.
    """

    connection = (
        db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.id == connection_id,
            DatabaseConnection.user_id == current_user.id,
        )
        .first()
    )

    if connection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Database connection not found.",
        )

    db.delete(connection)
    db.commit()

    return {
        "message": "Database disconnected successfully.",
        "connection_id": connection_id,
    }