import { useState } from "react";

import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  InputAdornment,
  CircularProgress,
} from "@mui/material";

import StorageIcon from "@mui/icons-material/Storage";
import LinkIcon from "@mui/icons-material/Link";
import DatabaseIcon from "@mui/icons-material/AccountTree";
import SchemaIcon from "@mui/icons-material/Schema";

import { useNavigate } from "react-router-dom";

import DashboardLayout from "../layouts/DashboardLayout";


function MongoDB() {
  const navigate = useNavigate();

  const [connectionString, setConnectionString] =
    useState("");

  const [databaseName, setDatabaseName] =
    useState("");

  const [status, setStatus] = useState("");

  const [statusType, setStatusType] =
    useState("info");

  const [testing, setTesting] =
    useState(false);

  const [connecting, setConnecting] =
    useState(false);

  const [extracting, setExtracting] =
    useState(false);


  // ==========================================================
  // BACKEND URL
  // ==========================================================

  const API_URL =
    import.meta.env.VITE_API_URL ||
    "http://127.0.0.1:8000";


  // ==========================================================
  // GET AUTH TOKEN
  // ==========================================================

  const getToken = () => {
    return localStorage.getItem("token");
  };


  // ==========================================================
  // ERROR MESSAGE HELPER
  // ==========================================================

  const getErrorMessage = (data, fallback) => {
    const errorMessage =
      data?.detail ||
      data?.message ||
      fallback;

    if (Array.isArray(errorMessage)) {
      return errorMessage
        .map((err) => err?.msg || "Validation error")
        .join(", ");
    }

    return String(errorMessage);
  };


  // ==========================================================
  // VALIDATE INPUTS
  // ==========================================================

  const validateInputs = () => {
    if (!connectionString.trim()) {
      setStatus(
        "Please enter your MongoDB connection string."
      );

      setStatusType("warning");

      return false;
    }


    if (
      !connectionString.startsWith(
        "mongodb://"
      ) &&
      !connectionString.startsWith(
        "mongodb+srv://"
      )
    ) {
      setStatus(
        "Invalid MongoDB connection string. It should start with mongodb:// or mongodb+srv://"
      );

      setStatusType("warning");

      return false;
    }


    if (!databaseName.trim()) {
      setStatus(
        "Please enter the MongoDB database name."
      );

      setStatusType("warning");

      return false;
    }


    return true;
  };


  // ==========================================================
  // TEST CONNECTION
  // ==========================================================

  const handleTestConnection = async () => {
    setStatus("");

    if (!validateInputs()) {
      return;
    }


    const token = getToken();


    if (!token) {
      setStatus(
        "You are not logged in. Please login again."
      );

      setStatusType("error");

      return;
    }


    setTesting(true);


    try {
      const response = await fetch(
        `${API_URL}/database/connect`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },

          body: JSON.stringify({
            database_type: "mongodb",

            connection_string:
              connectionString.trim(),

            database_name:
              databaseName.trim(),
          }),
        }
      );


      const data =
        await response.json();


      if (!response.ok) {
        setStatus(
          getErrorMessage(
            data,
            "MongoDB connection test failed."
          )
        );

        setStatusType("error");

        return;
      }


      if (data.connected) {
        setStatus(
          data.message ||
            "MongoDB connection successful!"
        );

        setStatusType("success");

      } else {
        setStatus(
          data.message ||
            "MongoDB connection failed."
        );

        setStatusType("error");
      }

    } catch (error) {

      console.error(
        "MongoDB Test Connection Error:",
        error
      );

      setStatus(
        "Unable to connect to the backend. Make sure FastAPI is running on port 8000."
      );

      setStatusType("error");

    } finally {

      setTesting(false);

    }
  };


  // ==========================================================
  // CONNECT DATABASE
  // ==========================================================

  const handleConnect = async () => {
    setStatus("");

    if (!validateInputs()) {
      return;
    }


    const token = getToken();


    if (!token) {
      setStatus(
        "You are not logged in. Please login again."
      );

      setStatusType("error");

      return;
    }


    setConnecting(true);


    try {

      const response = await fetch(
        `${API_URL}/database/connect`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },

          body: JSON.stringify({
            database_type: "mongodb",

            connection_string:
              connectionString.trim(),

            database_name:
              databaseName.trim(),
          }),
        }
      );


      const data =
        await response.json();


      if (!response.ok) {

        setStatus(
          getErrorMessage(
            data,
            "MongoDB connection failed."
          )
        );

        setStatusType("error");

        return;
      }


      if (data.connected) {

        setStatus(
          `MongoDB connected successfully${
            data.database_name
              ? ` to ${data.database_name}`
              : ""
          }!`
        );

        setStatusType("success");

      } else {

        setStatus(
          data.message ||
            "MongoDB connection failed."
        );

        setStatusType("error");
      }

    } catch (error) {

      console.error(
        "MongoDB Connect Error:",
        error
      );

      setStatus(
        "Unable to connect to the backend. Make sure FastAPI is running on port 8000."
      );

      setStatusType("error");

    } finally {

      setConnecting(false);

    }
  };


  // ==========================================================
  // EXTRACT METADATA
  // ==========================================================

  const handleExtractMetadata = async () => {
    setStatus("");

    if (!validateInputs()) {
      return;
    }


    const token = getToken();


    if (!token) {
      setStatus(
        "You are not logged in. Please login again."
      );

      setStatusType("error");

      return;
    }


    setExtracting(true);


    try {

      const response = await fetch(
        `${API_URL}/database/metadata`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },

          body: JSON.stringify({
            database_type: "mongodb",

            host: null,

            port: null,

            username: null,

            password: null,

            database_name:
              databaseName.trim(),

            connection_string:
              connectionString.trim(),
          }),
        }
      );


      const data =
        await response.json();


      console.log(
        "MONGODB METADATA EXTRACTION:",
        data
      );


      if (!response.ok) {

        setStatus(
          getErrorMessage(
            data,
            "MongoDB metadata extraction failed."
          )
        );

        setStatusType("error");

        return;
      }


      setStatus(
        `Metadata extracted successfully! ${
          data.tables || 0
        } collections and ${
          data.columns || 0
        } fields found.`
      );

      setStatusType("success");


      // ------------------------------------------------------
      // After successful extraction, open Schema Viewer
      // ------------------------------------------------------

      setTimeout(() => {
        navigate("/schema-viewer");
      }, 1200);

    } catch (error) {

      console.error(
        "MongoDB Metadata Extraction Error:",
        error
      );

      setStatus(
        "Unable to extract metadata. Make sure your MongoDB connection is valid and the backend is running."
      );

      setStatusType("error");

    } finally {

      setExtracting(false);

    }
  };


  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <DashboardLayout>

      <Box
        sx={{
          minHeight: "100%",
          backgroundColor: "#FFF9D9",
          p: {
            xs: 2,
            md: 4,
          },
        }}
      >

        {/* ==================================================
            PAGE HEADER
        ================================================== */}

        <Box sx={{ mb: 4 }}>

          <Typography
            variant="h4"
            sx={{
              fontWeight: "bold",
              color: "#5D4037",
              mb: 1,
            }}
          >
            MongoDB Connection
          </Typography>


          <Typography
            sx={{
              color: "#795548",
              fontSize: "16px",
            }}
          >
            Connect your MongoDB database to the
            metadata mapping dashboard.
          </Typography>

        </Box>


        {/* ==================================================
            MAIN CARD
        ================================================== */}

        <Paper
          elevation={3}
          sx={{
            maxWidth: "850px",
            mx: "auto",
            p: {
              xs: 3,
              md: 4,
            },
            borderRadius: 4,
            backgroundColor: "#FFFDF2",
            border:
              "1px solid #E6D89A",
          }}
        >

          {/* ==================================================
              CARD HEADER
          ================================================== */}

          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 2,
              mb: 3,
            }}
          >

            <Box
              sx={{
                width: 55,
                height: 55,
                borderRadius: 3,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: "#6D4C41",
              }}
            >

              <StorageIcon
                sx={{
                  color: "#FFF9D9",
                  fontSize: 30,
                }}
              />

            </Box>


            <Box>

              <Typography
                variant="h5"
                sx={{
                  fontWeight: "bold",
                  color: "#5D4037",
                }}
              >
                MongoDB
              </Typography>


              <Typography
                sx={{
                  color: "#8D6E63",
                  fontSize: "14px",
                }}
              >
                Database Configuration
              </Typography>

            </Box>

          </Box>


          {/* ==================================================
              CONNECTION STRING
          ================================================== */}

          <Typography
            sx={{
              fontWeight: "bold",
              color: "#5D4037",
              mb: 1,
            }}
          >
            Connection String
          </Typography>


          <TextField
            fullWidth
            placeholder="mongodb://localhost:27017"
            value={connectionString}
            onChange={(e) =>
              setConnectionString(
                e.target.value
              )
            }
            sx={{
              mb: 3,

              "& .MuiOutlinedInput-root": {
                borderRadius: 2,
                backgroundColor: "#FFFFFF",
              },
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">

                  <LinkIcon
                    sx={{
                      color: "#795548",
                    }}
                  />

                </InputAdornment>
              ),
            }}
          />


          {/* ==================================================
              DATABASE NAME
          ================================================== */}

          <Typography
            sx={{
              fontWeight: "bold",
              color: "#5D4037",
              mb: 1,
            }}
          >
            Database Name
          </Typography>


          <TextField
            fullWidth
            placeholder="Enter database name"
            value={databaseName}
            onChange={(e) =>
              setDatabaseName(
                e.target.value
              )
            }
            sx={{
              mb: 2,

              "& .MuiOutlinedInput-root": {
                borderRadius: 2,
                backgroundColor: "#FFFFFF",
              },
            }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">

                  <DatabaseIcon
                    sx={{
                      color: "#795548",
                    }}
                  />

                </InputAdornment>
              ),
            }}
          />


          {/* ==================================================
              INFORMATION
          ================================================== */}

          <Typography
            sx={{
              color: "#8D6E63",
              fontSize: "13px",
              mb: 4,
              lineHeight: 1.6,
            }}
          >

            Username and password are normally
            included inside the MongoDB connection
            string.

            <br />

            Example:

            <br />

            <strong>
              mongodb://username:password@localhost:27017
            </strong>

          </Typography>


          {/* ==================================================
              STATUS
          ================================================== */}

          {status && (

            <Alert
              severity={statusType}
              sx={{
                mb: 3,
                borderRadius: 2,
              }}
            >
              {status}
            </Alert>

          )}


          {/* ==================================================
              BUTTONS
          ================================================== */}

          <Box
            sx={{
              display: "grid",

              gridTemplateColumns: {
                xs: "1fr",
                sm: "1fr 1fr",
                md: "1fr 1fr 1fr",
              },

              gap: 2,
            }}
          >

            {/* ==================================================
                TEST CONNECTION
            ================================================== */}

            <Button
              variant="outlined"
              fullWidth
              onClick={
                handleTestConnection
              }
              disabled={
                testing ||
                connecting ||
                extracting
              }
              sx={{
                py: 1.5,
                borderRadius: 2,
                borderColor: "#6D4C41",
                color: "#6D4C41",
                fontWeight: "bold",

                "&:hover": {
                  borderColor: "#4E342E",
                  backgroundColor:
                    "#FFF3C4",
                },
              }}
            >

              {testing ? (

                <>
                  <CircularProgress
                    size={20}
                    sx={{
                      mr: 1,
                      color: "#6D4C41",
                    }}
                  />

                  Testing...
                </>

              ) : (

                "Test Connection"

              )}

            </Button>


            {/* ==================================================
                CONNECT DATABASE
            ================================================== */}

            <Button
              variant="contained"
              fullWidth
              onClick={handleConnect}
              disabled={
                testing ||
                connecting ||
                extracting
              }
              sx={{
                py: 1.5,
                borderRadius: 2,
                backgroundColor: "#6D4C41",
                color: "#FFFFFF",
                fontWeight: "bold",

                "&:hover": {
                  backgroundColor:
                    "#4E342E",
                },
              }}
            >

              {connecting ? (

                <>
                  <CircularProgress
                    size={20}
                    sx={{
                      mr: 1,
                      color: "#FFFFFF",
                    }}
                  />

                  Connecting...
                </>

              ) : (

                "Connect MongoDB"

              )}

            </Button>


            {/* ==================================================
                EXTRACT METADATA
            ================================================== */}

            <Button
              variant="contained"
              fullWidth
              onClick={
                handleExtractMetadata
              }
              disabled={
                testing ||
                connecting ||
                extracting
              }
              startIcon={
                extracting ? (
                  <CircularProgress
                    size={19}
                    sx={{
                      color: "#FFFFFF",
                    }}
                  />
                ) : (
                  <SchemaIcon />
                )
              }
              sx={{
                py: 1.5,
                borderRadius: 2,
                backgroundColor: "#8D6E63",
                color: "#FFFFFF",
                fontWeight: "bold",

                "&:hover": {
                  backgroundColor:
                    "#6D4C41",
                },
              }}
            >

              {extracting
                ? "Extracting..."
                : "Extract Metadata"}

            </Button>

          </Box>


          {/* ==================================================
              HELP TEXT
          ================================================== */}

          <Box
            sx={{
              mt: 3,
              p: 2,
              borderRadius: 2,
              backgroundColor: "#F9F4D8",
              border:
                "1px solid #E6D89A",
            }}
          >

            <Typography
              sx={{
                color: "#6D4C41",
                fontSize: "13px",
                lineHeight: 1.6,
              }}
            >

              <strong>
                Next step:
              </strong>{" "}

              After connecting MongoDB, click
              <strong>
                {" Extract Metadata "}
              </strong>
              to read your collections, fields,
              data types and indexes. You will then
              be taken to the Schema Viewer.

            </Typography>

          </Box>

        </Paper>

      </Box>

    </DashboardLayout>
  );
}


export default MongoDB;