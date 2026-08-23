from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.auth.dependencies import get_current_user
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
):
    """
    Test connectivity to a supported database.

    This endpoint is protected by JWT authentication.
    Credentials are never returned in the response.
    """

    try:
        result = check_database_connection(connection)

        # The service returns a standardized result.
        if isinstance(result, dict):
            return result

        return {
            "message": "Database connection test completed.",
            "database_type": getattr(connection, "database_type", "unknown"),
            "database_name": (
                getattr(connection, "database_name", None)
                or getattr(connection, "keyspace", None)
                or "N/A"
            ),
            "connected": bool(result),
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
        # Do not expose stack traces or credentials to the client.
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
):
    """
    Test Firebase Firestore connectivity using a Firebase
    service-account JSON file.

    The uploaded credentials are never returned or logged.
    """

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A Firebase service-account JSON file is required.",
        )

    # Basic file-type validation.
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

        # Parse and validate without exposing the contents.
        service_account = parse_firebase_service_account(contents)

        result = test_firebase_connection(service_account)

        if isinstance(result, dict):
            return result

        return {
            "message": (
                "Firebase Firestore connection successful."
                if result
                else "Firebase Firestore connection failed."
            ),
            "database_type": "firebase",
            "database_name": "firestore",
            "connected": bool(result),
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
        # Never return Firebase credentials or raw credential payloads.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Firebase Firestore connection test failed.",
        ) from exc