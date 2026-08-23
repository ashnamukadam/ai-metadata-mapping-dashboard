from typing import Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)


# ============================================================
# SUPPORTED DATABASE TYPES
# ============================================================

SupportedDatabaseType = Literal[
    "mysql",
    "postgresql",
    "sqlserver",
    "oracle",
    "sqlite",
    "mongodb",
    "firebase",
    "dynamodb",
    "cassandra",
]


# ============================================================
# GENERIC DATABASE CONNECTION REQUEST
# ============================================================

class DatabaseConnectionRequest(BaseModel):
    """
    Backward-compatible generic request model used by the
    existing /database/connect endpoint.

    The database_type field is restricted to the databases
    supported by Module 3.
    """

    database_type: SupportedDatabaseType

    host: Optional[str] = None
    port: Optional[int] = Field(
        default=None,
        ge=1,
        le=65535,
    )

    database_name: Optional[str] = None

    username: Optional[str] = None
    password: Optional[str] = None

    connection_string: Optional[str] = None

    keyspace: Optional[str] = None

    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "database_type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database_name": "metadata_dashboard",
                "username": "your-username",
                "password": "<your-password>",
            }
        }
    )

    @model_validator(mode="after")
    def validate_database_fields(self):
        """
        Validate database-specific required fields while
        keeping the generic request model backward compatible.
        """

        database_type = self.database_type.lower()

        if database_type in {
            "mysql",
            "postgresql",
            "sqlserver",
            "oracle",
        }:
            required_fields = {
                "host": self.host,
                "port": self.port,
                "database_name": self.database_name,
                "username": self.username,
                "password": self.password,
            }

            missing = [
                field
                for field, value in required_fields.items()
                if value is None or value == ""
            ]

            if missing:
                raise ValueError(
                    f"Missing required fields for {database_type}: "
                    + ", ".join(missing)
                )

        elif database_type == "sqlite":
            if not self.database_name:
                raise ValueError(
                    "database_name is required for sqlite"
                )

        elif database_type == "mongodb":
            if not self.connection_string:
                raise ValueError(
                    "connection_string is required for mongodb"
                )

        elif database_type == "cassandra":
            if not self.host:
                raise ValueError(
                    "host is required for cassandra"
                )

            if not self.port:
                raise ValueError(
                    "port is required for cassandra"
                )

            if not self.keyspace:
                raise ValueError(
                    "keyspace is required for cassandra"
                )

            if (
                (self.username is None)
                != (self.password is None)
            ):
                raise ValueError(
                    "Cassandra username and password must be "
                    "provided together"
                )

        elif database_type == "dynamodb":
            if not self.aws_region:
                raise ValueError(
                    "aws_region is required for dynamodb"
                )

            if (
                (self.aws_access_key_id is None)
                != (self.aws_secret_access_key is None)
            ):
                raise ValueError(
                    "DynamoDB AWS access key ID and secret access "
                    "key must be provided together"
                )

        return self


# ============================================================
# SQL DATABASES
# ============================================================

class SQLConnectionRequest(BaseModel):
    database_type: Literal[
        "mysql",
        "postgresql",
        "sqlserver",
        "oracle",
    ]

    host: str = Field(..., min_length=1)
    port: int = Field(..., ge=1, le=65535)
    database_name: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "database_type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database_name": "metadata_dashboard",
                "username": "your-username",
                "password": "<your-password>",
            }
        }
    )


class MySQLConnectionRequest(SQLConnectionRequest):
    database_type: Literal["mysql"] = "mysql"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "database_type": "mysql",
                "host": "localhost",
                "port": 3306,
                "database_name": "metadata_dashboard",
                "username": "your-username",
                "password": "<your-password>",
            }
        }
    )


class PostgreSQLConnectionRequest(SQLConnectionRequest):
    database_type: Literal["postgresql"] = "postgresql"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "database_type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "database_name": "metadata_dashboard",
                "username": "your-username",
                "password": "<your-password>",
            }
        }
    )


class SQLServerConnectionRequest(SQLConnectionRequest):
    database_type: Literal["sqlserver"] = "sqlserver"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "database_type": "sqlserver",
                "host": "localhost",
                "port": 1433,
                "database_name": "metadata_dashboard",
                "username": "your-username",
                "password": "<your-password>",
            }
        }
    )


class OracleConnectionRequest(SQLConnectionRequest):
    database_type: Literal["oracle"] = "oracle"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "database_type": "oracle",
                "host": "localhost",
                "port": 1521,
                "database_name": "XEPDB1",
                "username": "your-username",
                "password": "<your-password>",
            }
        }
    )


# ============================================================
# SQLITE
# ============================================================

class SQLiteConnectionRequest(BaseModel):
    database_type: Literal["sqlite"] = "sqlite"

    database_name: str = Field(
        ...,
        min_length=1,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "database_type": "sqlite",
                "database_name": "metadata_dashboard.db",
            }
        }
    )


# ============================================================
# MONGODB
# ============================================================

class MongoDBConnectionRequest(BaseModel):
    database_type: Literal["mongodb"] = "mongodb"

    connection_string: str = Field(
        ...,
        min_length=1,
    )

    # Optional because MongoDB connectivity itself can be
    # tested by pinging the server without requiring the
    # database name in the request.
    database_name: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "database_type": "mongodb",
                "connection_string": "mongodb://localhost:27017/",
                "database_name": "metadata_dashboard",
            }
        }
    )


# ============================================================
# FIREBASE FIRESTORE
# ============================================================

class FirebaseConnectionRequest(BaseModel):
    database_type: Literal["firebase"] = "firebase"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "database_type": "firebase",
            }
        }
    )


# ============================================================
# DYNAMODB
# ============================================================

class DynamoDBConnectionRequest(BaseModel):
    database_type: Literal["dynamodb"] = "dynamodb"

    region: str = Field(
        ...,
        min_length=1,
    )

    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    @model_validator(mode="after")
    def validate_credentials_pair(self):
        """
        AWS credentials must either both be provided or both
        be omitted.

        When omitted, boto3 uses its normal AWS credential
        provider chain.
        """

        access_key_present = bool(
            self.aws_access_key_id
        )

        secret_key_present = bool(
            self.aws_secret_access_key
        )

        if access_key_present != secret_key_present:
            raise ValueError(
                "aws_access_key_id and "
                "aws_secret_access_key must be provided together"
            )

        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "database_type": "dynamodb",
                "region": "ap-south-1",
            }
        }
    )
# ============================================================
# CASSANDRA
# ============================================================

class CassandraConnectionRequest(BaseModel):
    database_type: Literal["cassandra"] = "cassandra"

    host: str = Field(
        ...,
        min_length=1,
    )

    port: int = Field(
        default=9042,
        ge=1,
        le=65535,
    )

    keyspace: str = Field(
        ...,
        min_length=1,
    )

    username: Optional[str] = None
    password: Optional[str] = None

    @model_validator(mode="after")
    def validate_credentials_pair(self):
        """
        Cassandra username and password must either both be
        supplied or both be omitted.
        """

        username_present = bool(self.username)
        password_present = bool(self.password)

        if username_present != password_present:
            raise ValueError(
                "username and password must be provided together"
            )

        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "database_type": "cassandra",
                "host": "localhost",
                "port": 9042,
                "keyspace": "metadata_dashboard",
                "username": "your-username",
                "password": "<your-password>",
            }
        }
    )


# ============================================================
# RESPONSE MODEL
# ============================================================

class DatabaseConnectionResponse(BaseModel):
    """
    Safe API response.

    Never include passwords, AWS secrets, Firebase service
    account contents, JWTs, or credential-bearing connection
    strings.
    """

    message: str
    database_type: str
    database_name: str
    connected: bool