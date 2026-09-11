import { useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  MenuItem,
  Alert,
  CircularProgress,
} from "@mui/material";

import UploadFileIcon from "@mui/icons-material/UploadFile";
import StorageIcon from "@mui/icons-material/Storage";

import api from "../services/api";


const databaseOptions = [
  { value: "postgresql", label: "PostgreSQL" },
  { value: "mysql", label: "MySQL" },
  { value: "sqlserver", label: "SQL Server" },
  { value: "oracle", label: "Oracle" },
  { value: "sqlite", label: "SQLite" },
  { value: "mongodb", label: "MongoDB" },
  { value: "firebase", label: "Firebase" },
  { value: "dynamodb", label: "DynamoDB" },
  { value: "cassandra", label: "Cassandra" },
];


const sqlDatabases = [
  "postgresql",
  "mysql",
  "sqlserver",
  "oracle",
];


function ConnectDatabase() {
  const navigate = useNavigate();

  // ============================================================
  // STATE
  // ============================================================

  const [databaseType, setDatabaseType] = useState("postgresql");

  const [host, setHost] = useState("localhost");
  const [port, setPort] = useState("5432");
  const [databaseName, setDatabaseName] = useState("");
  const [username, setUsername] = useState("postgres");
  const [password, setPassword] = useState("");

  const [connectionString, setConnectionString] = useState("");

  const [keyspace, setKeyspace] = useState("");

  const [awsRegion, setAwsRegion] = useState("");
  const [awsAccessKeyId, setAwsAccessKeyId] = useState("");
  const [awsSecretAccessKey, setAwsSecretAccessKey] = useState("");

  const [firebaseFile, setFirebaseFile] = useState(null);

  const [testing, setTesting] = useState(false);
  const [extracting, setExtracting] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");


  // ============================================================
  // DATABASE TYPE CHANGE
  // ============================================================

  const handleDatabaseTypeChange = (event) => {
    const type = event.target.value;

    setDatabaseType(type);

    setError("");
    setSuccess("");

    // Reset common fields
    setHost("localhost");
    setDatabaseName("");
    setUsername("");
    setPassword("");
    setConnectionString("");
    setKeyspace("");

    setAwsRegion("");
    setAwsAccessKeyId("");
    setAwsSecretAccessKey("");

    setFirebaseFile(null);

    // Default values
    if (type === "postgresql") {
      setHost("localhost");
      setPort("5432");
      setUsername("postgres");
    }

    if (type === "mysql") {
      setHost("localhost");
      setPort("3306");
      setUsername("root");
    }

    if (type === "sqlserver") {
      setHost("localhost");
      setPort("1433");
      setUsername("");
    }

    if (type === "oracle") {
      setHost("localhost");
      setPort("1521");
      setUsername("");
    }

    if (type === "cassandra") {
      setHost("localhost");
      setPort("9042");
    }
  };


  // ============================================================
  // FIREBASE FILE CHANGE
  // ============================================================

  const handleFirebaseFileChange = (event) => {
    const file = event.target.files?.[0];

    setError("");
    setSuccess("");

    if (!file) {
      setFirebaseFile(null);
      return;
    }

    if (!file.name.toLowerCase().endsWith(".json")) {
      setFirebaseFile(null);
      setError(
        "Please select a Firebase service-account JSON file."
      );
      return;
    }

    setFirebaseFile(file);
  };


  // ============================================================
  // VALIDATION
  // ============================================================

  const validateForm = () => {
    setError("");

    // ----------------------------------------------------------
    // SQL DATABASES
    // ----------------------------------------------------------

    if (sqlDatabases.includes(databaseType)) {
      if (!host.trim()) {
        setError("Host is required.");
        return false;
      }

      if (!port) {
        setError("Port is required.");
        return false;
      }

      if (!databaseName.trim()) {
        setError("Database name is required.");
        return false;
      }

      if (!username.trim()) {
        setError("Username is required.");
        return false;
      }

      if (!password) {
        setError("Password is required.");
        return false;
      }

      return true;
    }


    // ----------------------------------------------------------
    // SQLITE
    // ----------------------------------------------------------

    if (databaseType === "sqlite") {
      if (!databaseName.trim()) {
        setError("Database file/path is required.");
        return false;
      }

      return true;
    }


    // ----------------------------------------------------------
    // MONGODB
    // ----------------------------------------------------------

    if (databaseType === "mongodb") {
      if (!connectionString.trim()) {
        setError("MongoDB connection string is required.");
        return false;
      }

      return true;
    }


    // ----------------------------------------------------------
    // FIREBASE
    // ----------------------------------------------------------

    if (databaseType === "firebase") {
      if (!firebaseFile) {
        setError(
          "Please upload your Firebase service-account JSON file."
        );
        return false;
      }

      return true;
    }


    // ----------------------------------------------------------
    // DYNAMODB
    // ----------------------------------------------------------

    if (databaseType === "dynamodb") {
      if (!awsRegion.trim()) {
        setError("AWS Region is required.");
        return false;
      }

      if (
        (awsAccessKeyId && !awsSecretAccessKey) ||
        (!awsAccessKeyId && awsSecretAccessKey)
      ) {
        setError(
          "AWS Access Key ID and Secret Access Key must be provided together."
        );
        return false;
      }

      return true;
    }


    // ----------------------------------------------------------
    // CASSANDRA
    // ----------------------------------------------------------

    if (databaseType === "cassandra") {
      if (!host.trim()) {
        setError("Host is required.");
        return false;
      }

      if (!port) {
        setError("Port is required.");
        return false;
      }

      if (!keyspace.trim()) {
        setError("Keyspace is required.");
        return false;
      }

      if (
        (username && !password) ||
        (!username && password)
      ) {
        setError(
          "Cassandra username and password must be provided together."
        );
        return false;
      }

      return true;
    }

    return true;
  };


  // ============================================================
  // BUILD NORMAL DATABASE PAYLOAD
  // ============================================================

  const buildPayload = () => {

    // SQL
    if (sqlDatabases.includes(databaseType)) {
      return {
        database_type: databaseType,
        host: host.trim(),
        port: Number(port),
        database_name: databaseName.trim(),
        username: username.trim(),
        password,
      };
    }


    // SQLite
    if (databaseType === "sqlite") {
      return {
        database_type: "sqlite",
        database_name: databaseName.trim(),
      };
    }


    // MongoDB
    if (databaseType === "mongodb") {
      return {
        database_type: "mongodb",
        connection_string: connectionString.trim(),
        database_name: databaseName.trim() || null,
      };
    }


    // DynamoDB
    if (databaseType === "dynamodb") {
      return {
        database_type: "dynamodb",
        aws_region: awsRegion.trim(),
        aws_access_key_id:
          awsAccessKeyId.trim() || null,
        aws_secret_access_key:
          awsSecretAccessKey.trim() || null,
      };
    }


    // Cassandra
    if (databaseType === "cassandra") {
      return {
        database_type: "cassandra",
        host: host.trim(),
        port: Number(port),
        keyspace: keyspace.trim(),
        username: username.trim() || null,
        password: password || null,
      };
    }


    return {
      database_type: databaseType,
    };
  };


  // ============================================================
  // TEST CONNECTION
  // ============================================================

  const handleTestConnection = async () => {
    setError("");
    setSuccess("");

    if (!validateForm()) {
      return;
    }

    const token = localStorage.getItem("token");

    if (!token) {
      setError("Please login again. Authentication token not found.");
      return;
    }

    setTesting(true);

    try {

      // --------------------------------------------------------
      // FIREBASE
      // --------------------------------------------------------

      if (databaseType === "firebase") {
        const formData = new FormData();

        formData.append("file", firebaseFile);

        const response = await api.post(
          "/database/connect/firebase",
          formData,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "multipart/form-data",
            },
          }
        );

        const data = response.data;

        if (data.connected) {
          setSuccess(
            data.message ||
              `Firebase connection successful: ${data.database_name}`
          );

          localStorage.setItem(
            "metadata_database_type",
            "firebase"
          );

          localStorage.setItem(
            "metadata_database_name",
            data.database_name
          );
        } else {
          setError(
            data.message ||
              "Firebase connection failed."
          );
        }

        return;
      }


      // --------------------------------------------------------
      // NORMAL DATABASES
      // --------------------------------------------------------

      const payload = buildPayload();

      console.log(
        "Testing database connection:",
        databaseType
      );

      const response = await api.post(
        "/database/connect",
        payload,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = response.data;

      if (data.connected) {
        setSuccess(
          data.message ||
            `${databaseType} connection successful.`
        );

        localStorage.setItem(
          "metadata_database_type",
          data.database_type
        );

        localStorage.setItem(
          "metadata_database_name",
          data.database_name
        );
      } else {
        setError(
          data.message ||
            "Database connection failed."
        );
      }

    } catch (err) {

      console.error(
        "Database connection error:",
        err
      );

      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Database connection failed.";

      setError(message);

    } finally {
      setTesting(false);
    }
  };


  // ============================================================
  // EXTRACT METADATA
  // ============================================================

  const handleExtractMetadata = async () => {
    setError("");
    setSuccess("");

    if (!validateForm()) {
      return;
    }

    const token = localStorage.getItem("token");

    if (!token) {
      setError(
        "Please login again. Authentication token not found."
      );
      return;
    }

    setExtracting(true);

    try {

      // --------------------------------------------------------
      // FIREBASE
      // --------------------------------------------------------

      if (databaseType === "firebase") {

        const formData = new FormData();

        formData.append("file", firebaseFile);

        // First connect/test Firebase
        const connectResponse = await api.post(
          "/database/connect/firebase",
          formData,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "multipart/form-data",
            },
          }
        );

        const connectData = connectResponse.data;

        if (!connectData.connected) {
          setError(
            connectData.message ||
              "Firebase connection failed."
          );
          return;
        }

        localStorage.setItem(
          "metadata_database_type",
          "firebase"
        );

        localStorage.setItem(
          "metadata_database_name",
          connectData.database_name
        );

        setSuccess(
          "Firebase connected successfully."
        );

        /*
          Firebase metadata extraction currently depends
          on the backend metadata implementation.

          We navigate to Schema Viewer after successful
          Firebase connection.
        */

        setTimeout(() => {
          navigate("/schema-viewer");
        }, 700);

        return;
      }


      // --------------------------------------------------------
      // NORMAL DATABASES
      // --------------------------------------------------------

      const payload = buildPayload();

      // Step 1: Test/connect database
      const connectResponse = await api.post(
        "/database/connect",
        payload,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const connectData = connectResponse.data;

      if (!connectData.connected) {
        setError(
          connectData.message ||
            "Database connection failed."
        );
        return;
      }


      // Step 2: Extract metadata
      const metadataResponse = await api.post(
        "/database/metadata",
        payload,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const metadataData = metadataResponse.data;

      console.log(
        "Metadata extraction response:",
        metadataData
      );


      // Save active database information
      localStorage.setItem(
        "metadata_database_type",
        connectData.database_type
      );

      localStorage.setItem(
        "metadata_database_name",
        connectData.database_name
      );


      setSuccess(
        metadataData.message ||
          "Metadata extracted successfully."
      );


      // Navigate to Schema Viewer
      setTimeout(() => {
        navigate("/schema-viewer");
      }, 700);

    } catch (err) {

      console.error(
        "Metadata extraction error:",
        err
      );

      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Metadata extraction failed.";

      setError(message);

    } finally {
      setExtracting(false);
    }
  };


  // ============================================================
  // UI
  // ============================================================

  return (
    <Box
      sx={{
        minHeight: "100vh",
        bgcolor: "#FFF8D6",
        p: { xs: 2, md: 4 },
      }}
    >

      <Paper
        elevation={4}
        sx={{
          maxWidth: 850,
          mx: "auto",
          p: { xs: 3, md: 5 },
          borderRadius: 4,
          bgcolor: "#FFFDF2",
          border: "1px solid #E6D9A8",
        }}
      >

        {/* =====================================================
            HEADER
        ====================================================== */}

        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 2,
            mb: 4,
          }}
        >

          <StorageIcon
            sx={{
              fontSize: 42,
              color: "#6D4C41",
            }}
          />

          <Box>
            <Typography
              variant="h4"
              fontWeight="bold"
              sx={{
                color: "#6D4C41",
              }}
            >
              Connect Database
            </Typography>

            <Typography
              sx={{
                color: "#795548",
                mt: 0.5,
              }}
            >
              Connect your database and extract metadata
            </Typography>
          </Box>

        </Box>


        {/* =====================================================
            ALERTS
        ====================================================== */}

        {error && (
          <Alert
            severity="error"
            sx={{ mb: 3 }}
          >
            {error}
          </Alert>
        )}

        {success && (
          <Alert
            severity="success"
            sx={{ mb: 3 }}
          >
            {success}
          </Alert>
        )}


        {/* =====================================================
            DATABASE TYPE
        ====================================================== */}

        <TextField
          select
          fullWidth
          label="Database Type"
          value={databaseType}
          onChange={handleDatabaseTypeChange}
          sx={{ mb: 3 }}
        >

          {databaseOptions.map((option) => (
            <MenuItem
              key={option.value}
              value={option.value}
            >
              {option.label}
            </MenuItem>
          ))}

        </TextField>


        {/* =====================================================
            SQL DATABASES
        ====================================================== */}

        {sqlDatabases.includes(databaseType) && (
          <>

            <TextField
              fullWidth
              label="Host"
              value={host}
              onChange={(e) =>
                setHost(e.target.value)
              }
              placeholder="localhost"
              sx={{ mb: 3 }}
            />


            <TextField
              fullWidth
              type="number"
              label="Port"
              value={port}
              onChange={(e) =>
                setPort(e.target.value)
              }
              sx={{ mb: 3 }}
            />


            <TextField
              fullWidth
              label="Database Name"
              value={databaseName}
              onChange={(e) =>
                setDatabaseName(e.target.value)
              }
              placeholder="Enter database name"
              sx={{ mb: 3 }}
            />


            <TextField
              fullWidth
              label="Username"
              value={username}
              onChange={(e) =>
                setUsername(e.target.value)
              }
              sx={{ mb: 3 }}
            />


            <TextField
              fullWidth
              type="password"
              label="Password"
              value={password}
              onChange={(e) =>
                setPassword(e.target.value)
              }
              sx={{ mb: 3 }}
            />

          </>
        )}


        {/* =====================================================
            SQLITE
        ====================================================== */}

        {databaseType === "sqlite" && (
          <>

            <TextField
              fullWidth
              label="Database File / Path"
              value={databaseName}
              onChange={(e) =>
                setDatabaseName(e.target.value)
              }
              placeholder="example.db"
              helperText="Enter the SQLite database file path."
              sx={{ mb: 3 }}
            />

          </>
        )}


        {/* =====================================================
            MONGODB
        ====================================================== */}

        {databaseType === "mongodb" && (
          <>

            <TextField
              fullWidth
              label="MongoDB Connection String"
              value={connectionString}
              onChange={(e) =>
                setConnectionString(e.target.value)
              }
              placeholder="mongodb://localhost:27017"
              helperText="Example: mongodb://localhost:27017"
              sx={{ mb: 3 }}
            />


            <TextField
              fullWidth
              label="Database Name"
              value={databaseName}
              onChange={(e) =>
                setDatabaseName(e.target.value)
              }
              placeholder="Optional database name"
              helperText="Leave empty if the connection string already identifies the database."
              sx={{ mb: 3 }}
            />

          </>
        )}


        {/* =====================================================
            FIREBASE
        ====================================================== */}

        {databaseType === "firebase" && (
          <Box
            sx={{
              border: "2px dashed #D6C58A",
              borderRadius: 3,
              p: 4,
              mb: 3,
              textAlign: "center",
              bgcolor: "#FFF9DF",
            }}
          >

            <UploadFileIcon
              sx={{
                fontSize: 50,
                color: "#6D4C41",
                mb: 1,
              }}
            />

            <Typography
              variant="h6"
              fontWeight="bold"
              sx={{
                color: "#6D4C41",
                mb: 1,
              }}
            >
              Firebase Firestore
            </Typography>

            <Typography
              sx={{
                color: "#795548",
                mb: 3,
              }}
            >
              Upload your Firebase service-account JSON
              file to test the Firestore connection.
            </Typography>


            <Button
              variant="outlined"
              component="label"
              startIcon={<UploadFileIcon />}
              sx={{
                color: "#6D4C41",
                borderColor: "#6D4C41",
                "&:hover": {
                  borderColor: "#4E342E",
                  bgcolor: "#FFF3C4",
                },
              }}
            >
              Choose JSON File

              <input
                hidden
                type="file"
                accept=".json,application/json"
                onChange={handleFirebaseFileChange}
              />
            </Button>


            {firebaseFile && (
              <Typography
                sx={{
                  mt: 2,
                  color: "#6D4C41",
                  fontWeight: "bold",
                }}
              >
                Selected: {firebaseFile.name}
              </Typography>
            )}

          </Box>
        )}


        {/* =====================================================
            DYNAMODB
        ====================================================== */}

        {databaseType === "dynamodb" && (
          <>

            <TextField
              fullWidth
              label="AWS Region"
              value={awsRegion}
              onChange={(e) =>
                setAwsRegion(e.target.value)
              }
              placeholder="ap-south-1"
              helperText="Example: ap-south-1"
              sx={{ mb: 3 }}
            />


            <TextField
              fullWidth
              label="AWS Access Key ID"
              value={awsAccessKeyId}
              onChange={(e) =>
                setAwsAccessKeyId(e.target.value)
              }
              placeholder="Optional"
              sx={{ mb: 3 }}
            />


            <TextField
              fullWidth
              type="password"
              label="AWS Secret Access Key"
              value={awsSecretAccessKey}
              onChange={(e) =>
                setAwsSecretAccessKey(e.target.value)
              }
              placeholder="Optional"
              sx={{ mb: 3 }}
            />

          </>
        )}


        {/* =====================================================
            CASSANDRA
        ====================================================== */}

        {databaseType === "cassandra" && (
          <>

            <TextField
              fullWidth
              label="Host"
              value={host}
              onChange={(e) =>
                setHost(e.target.value)
              }
              placeholder="localhost"
              sx={{ mb: 3 }}
            />


            <TextField
              fullWidth
              type="number"
              label="Port"
              value={port}
              onChange={(e) =>
                setPort(e.target.value)
              }
              sx={{ mb: 3 }}
            />


            <TextField
              fullWidth
              label="Keyspace"
              value={keyspace}
              onChange={(e) =>
                setKeyspace(e.target.value)
              }
              placeholder="Enter keyspace"
              sx={{ mb: 3 }}
            />


            <TextField
              fullWidth
              label="Username"
              value={username}
              onChange={(e) =>
                setUsername(e.target.value)
              }
              placeholder="Optional"
              sx={{ mb: 3 }}
            />


            <TextField
              fullWidth
              type="password"
              label="Password"
              value={password}
              onChange={(e) =>
                setPassword(e.target.value)
              }
              placeholder="Optional"
              sx={{ mb: 3 }}
            />

          </>
        )}


        {/* =====================================================
            BUTTONS
        ====================================================== */}

        <Box
          sx={{
            display: "flex",
            gap: 2,
            flexDirection: {
              xs: "column",
              sm: "row",
            },
          }}
        >

          {/* TEST CONNECTION */}

          <Button
            fullWidth
            variant="outlined"
            onClick={handleTestConnection}
            disabled={testing || extracting}
            sx={{
              py: 1.5,
              borderRadius: 2,
              color: "#6D4C41",
              borderColor: "#6D4C41",
              fontWeight: "bold",

              "&:hover": {
                borderColor: "#4E342E",
                bgcolor: "#FFF3C4",
              },
            }}
          >

            {testing ? (
              <>
                <CircularProgress
                  size={22}
                  sx={{ mr: 1 }}
                />

                Testing...
              </>
            ) : (
              "Test Connection"
            )}

          </Button>


          {/* EXTRACT METADATA */}

          <Button
            fullWidth
            variant="contained"
            onClick={handleExtractMetadata}
            disabled={testing || extracting}
            sx={{
              py: 1.5,
              borderRadius: 2,
              bgcolor: "#6D4C41",
              fontWeight: "bold",

              "&:hover": {
                bgcolor: "#4E342E",
              },
            }}
          >

            {extracting ? (
              <>
                <CircularProgress
                  size={22}
                  sx={{
                    mr: 1,
                    color: "#FFFFFF",
                  }}
                />

                Extracting...
              </>
            ) : (
              "Extract Metadata"
            )}

          </Button>

        </Box>

      </Paper>

    </Box>
  );
}

export default ConnectDatabase;