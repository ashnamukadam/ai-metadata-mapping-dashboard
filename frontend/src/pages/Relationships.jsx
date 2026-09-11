import { useEffect, useMemo, useState } from "react";
import axios from "axios";

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Divider,
  MenuItem,
  Select,
  Snackbar,
  Typography,
} from "@mui/material";

import DashboardLayout from "../layouts/DashboardLayout";


// ============================================================
// API
// ============================================================

const API_URL = "http://127.0.0.1:8000";


// ============================================================
// COMPONENT
// ============================================================

function Relationships() {
  // ============================================================
  // AUTH
  // ============================================================

  const token = localStorage.getItem("token");

  const authHeaders = useMemo(
    () => ({
      Authorization: `Bearer ${token}`,
      Accept: "application/json",
    }),
    [token]
  );


  // ============================================================
  // DATABASE
  // ============================================================

  const [databaseType, setDatabaseType] = useState(
    localStorage.getItem("databaseType") || "postgresql"
  );

  const [databaseName, setDatabaseName] = useState(
    localStorage.getItem("databaseName") || "metadata_dashboard"
  );


  // ============================================================
  // METADATA
  // ============================================================

  const [metadata, setMetadata] = useState(null);

  const [loading, setLoading] = useState(false);


  // ============================================================
  // RELATIONSHIP FORM
  // ============================================================

  const [parentTable, setParentTable] = useState("");

  const [parentColumn, setParentColumn] = useState("");

  const [childTable, setChildTable] = useState("");

  const [childColumn, setChildColumn] = useState("");


  // ============================================================
  // SAVED RELATIONSHIPS
  // ============================================================

  const [savedRelationships, setSavedRelationships] =
    useState([]);


  // ============================================================
  // MESSAGES
  // ============================================================

  const [errorMessage, setErrorMessage] = useState("");

  const [successMessage, setSuccessMessage] = useState("");

  const [snackbarOpen, setSnackbarOpen] = useState(false);


  // ============================================================
  // LOAD METADATA
  // ============================================================

  const loadMetadata = async () => {
    try {
      setLoading(true);

      setErrorMessage("");

      console.log(
        "================================================"
      );

      console.log(
        "RELATIONSHIPS - LOADING METADATA"
      );

      console.log(
        "DATABASE TYPE:",
        databaseType
      );

      console.log(
        "DATABASE NAME:",
        databaseName
      );

      console.log(
        "================================================"
      );


      // --------------------------------------------------------
      // EXACT SAME REQUEST AS METADATA MAPPING
      // --------------------------------------------------------

      const response = await axios.get(
        `${API_URL}/database/metadata`,
        {
          params: {
            database_type: databaseType,
            database_name: databaseName,
          },

          headers: authHeaders,
        }
      );


      console.log(
        "================================================"
      );

      console.log(
        "RELATIONSHIPS - METADATA RESPONSE"
      );

      console.log(response.data);

      console.log(
        "TABLES:",
        response.data?.tables
      );

      console.log(
        "TABLE COUNT:",
        response.data?.tables?.length
      );

      console.log(
        "================================================"
      );


      // --------------------------------------------------------
      // IMPORTANT
      // Use EXACT same structure as MetadataMapping.jsx
      // --------------------------------------------------------

      setMetadata(response.data);


      // --------------------------------------------------------
      // RESET SELECTED VALUES
      // --------------------------------------------------------

      setParentTable("");

      setParentColumn("");

      setChildTable("");

      setChildColumn("");

    } catch (error) {
      console.error(
        "RELATIONSHIPS LOAD METADATA ERROR:",
        error.response?.data || error
      );

      setErrorMessage(
        error.response?.data?.detail ||
          "Failed to load metadata."
      );
    } finally {
      setLoading(false);
    }
  };


  // ============================================================
  // LOAD SAVED RELATIONSHIPS
  // ============================================================

  const loadSavedRelationships = async () => {
    try {
      console.log(
        "================================================"
      );

      console.log(
        "RELATIONSHIPS - LOADING SAVED RELATIONSHIPS"
      );


      const response = await axios.get(
        `${API_URL}/database/relationships`,
        {
          headers: authHeaders,
        }
      );


      console.log(
        "SAVED RELATIONSHIPS RESPONSE:",
        response.data
      );


      const relationships =
        response.data?.relationships || [];


      setSavedRelationships(
        Array.isArray(relationships)
          ? relationships
          : []
      );


      console.log(
        "SAVED RELATIONSHIP COUNT:",
        relationships.length
      );


      console.log(
        "================================================"
      );

    } catch (error) {
      console.error(
        "LOAD SAVED RELATIONSHIPS ERROR:",
        error.response?.data || error
      );

      setErrorMessage(
        error.response?.data?.detail ||
          "Failed to load saved relationships."
      );
    }
  };


  // ============================================================
  // INITIAL LOAD
  // ============================================================

  useEffect(() => {
    if (!token) {
      setErrorMessage("Please login first.");
      return;
    }

    loadMetadata();

    loadSavedRelationships();
  }, [databaseType, databaseName]);


  // ============================================================
  // TABLES
  // ============================================================

  const tables = useMemo(() => {
    if (!metadata?.tables) {
      return [];
    }

    return metadata.tables;
  }, [metadata]);


  // ============================================================
  // DEBUG TABLES
  // ============================================================

  useEffect(() => {
    console.log(
      "================================================"
    );

    console.log(
      "RELATIONSHIPS - TABLE INFORMATION"
    );

    console.log(
      "METADATA:",
      metadata
    );

    console.log(
      "TABLES:",
      tables
    );

    console.log(
      "TABLE COUNT:",
      tables.length
    );

    console.log(
      "================================================"
    );
  }, [metadata, tables]);


  // ============================================================
  // TABLE NAME
  // ============================================================

  const getTableName = (table) => {
    if (typeof table === "string") {
      return table;
    }

    return table?.name || "";
  };


  // ============================================================
  // TABLE COLUMNS
  // ============================================================

  const getColumns = (table) => {
    if (!table || typeof table === "string") {
      return [];
    }

    return table.columns || [];
  };


  // ============================================================
  // COLUMN NAME
  // ============================================================

  const getColumnName = (column) => {
    if (typeof column === "string") {
      return column;
    }

    return (
      column?.name ||
      column?.column_name ||
      ""
    );
  };


  // ============================================================
  // SELECTED PARENT TABLE
  // ============================================================

  const selectedParentTable = useMemo(() => {
    return tables.find(
      (table) =>
        getTableName(table) === parentTable
    );
  }, [tables, parentTable]);


  // ============================================================
  // SELECTED CHILD TABLE
  // ============================================================

  const selectedChildTable = useMemo(() => {
    return tables.find(
      (table) =>
        getTableName(table) === childTable
    );
  }, [tables, childTable]);


  // ============================================================
  // PARENT COLUMNS
  // ============================================================

  const parentColumns = useMemo(() => {
    return getColumns(selectedParentTable);
  }, [selectedParentTable]);


  // ============================================================
  // CHILD COLUMNS
  // ============================================================

  const childColumns = useMemo(() => {
    return getColumns(selectedChildTable);
  }, [selectedChildTable]);


  // ============================================================
  // PARENT TABLE CHANGE
  // ============================================================

  const handleParentTableChange = (event) => {
    const value = event.target.value;

    setParentTable(value);

    setParentColumn("");
  };


  // ============================================================
  // CHILD TABLE CHANGE
  // ============================================================

  const handleChildTableChange = (event) => {
    const value = event.target.value;

    setChildTable(value);

    setChildColumn("");
  };


  // ============================================================
  // CREATE RELATIONSHIP
  // ============================================================

  const handleCreateRelationship = async () => {
    if (!parentTable) {
      setErrorMessage(
        "Please select a parent table."
      );

      return;
    }


    if (!parentColumn) {
      setErrorMessage(
        "Please select a parent column."
      );

      return;
    }


    if (!childTable) {
      setErrorMessage(
        "Please select a child table."
      );

      return;
    }


    if (!childColumn) {
      setErrorMessage(
        "Please select a child column."
      );

      return;
    }


    try {
      setErrorMessage("");

      console.log(
        "================================================"
      );

      console.log(
        "CREATING RELATIONSHIP"
      );


      const payload = {
        relationship: {
          database_name: databaseName,

          parent_table: parentTable,

          parent_column: parentColumn,

          child_table: childTable,

          child_column: childColumn,
        },

        schema_metadata: metadata || {},
      };


      console.log(
        "PAYLOAD:",
        payload
      );


      console.log(
        "================================================"
      );


      await axios.post(
        `${API_URL}/database/relationship`,
        payload,
        {
          headers: authHeaders,
        }
      );


      setSuccessMessage(
        "Relationship created successfully."
      );

      setSnackbarOpen(true);


      // Reset form
      setParentTable("");

      setParentColumn("");

      setChildTable("");

      setChildColumn("");


      // Refresh saved relationships
      await loadSavedRelationships();

    } catch (error) {
      console.error(
        "CREATE RELATIONSHIP ERROR:",
        error.response?.data || error
      );

      setErrorMessage(
        error.response?.data?.detail ||
          "Failed to create relationship."
      );
    }
  };


  // ============================================================
  // CLOSE SNACKBAR
  // ============================================================

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };


  // ============================================================
  // RENDER
  // ============================================================

  return (
    <DashboardLayout>

      <Box
        sx={{
          minHeight: "100vh",

          bgcolor: "#FFF8D6",

          p: {
            xs: 2,
            md: 4,
          },
        }}
      >

        {/* ====================================================
            HEADER
        ==================================================== */}

        <Box sx={{ mb: 4 }}>

          <Typography
            variant="h4"
            sx={{
              color: "#6D4C41",

              fontWeight: "bold",

              mb: 1,
            }}
          >
            Relationships
          </Typography>


          <Typography
            sx={{
              color: "#795548",
            }}
          >
            Define relationships between tables
            in your active database.
          </Typography>

        </Box>


        {/* ====================================================
            ACTIVE DATABASE
        ==================================================== */}

        <Card
          sx={{
            mb: 3,

            borderRadius: 3,

            border:
              "1px solid #E6D89A",

            boxShadow:
              "0 4px 12px rgba(109,76,65,0.08)",
          }}
        >

          <CardContent>

            <Typography
              variant="h6"
              sx={{
                color: "#6D4C41",

                fontWeight: "bold",

                mb: 2,
              }}
            >
              Active Database
            </Typography>


            <Divider
              sx={{ mb: 3 }}
            />


            <Box
              sx={{
                display: "grid",

                gridTemplateColumns: {
                  xs: "1fr",
                  md: "1fr 1fr",
                },

                gap: 2,
              }}
            >

              <Box>

                <Typography
                  sx={{
                    color: "#795548",
                    fontWeight: "bold",
                  }}
                >
                  Database Type
                </Typography>


                <Typography
                  sx={{
                    color: "#6D4C41",
                    mt: 0.5,
                  }}
                >
                  {databaseType}
                </Typography>

              </Box>


              <Box>

                <Typography
                  sx={{
                    color: "#795548",
                    fontWeight: "bold",
                  }}
                >
                  Database Name
                </Typography>


                <Typography
                  sx={{
                    color: "#6D4C41",
                    mt: 0.5,
                  }}
                >
                  {databaseName}
                </Typography>

              </Box>

            </Box>


            <Button
              variant="contained"
              onClick={loadMetadata}
              disabled={loading}
              sx={{
                mt: 3,

                bgcolor: "#6D4C41",

                "&:hover": {
                  bgcolor: "#5D4037",
                },
              }}
            >

              {loading ? (
                <CircularProgress
                  size={22}
                  sx={{
                    color: "white",
                  }}
                />
              ) : (
                "Refresh Metadata"
              )}

            </Button>

          </CardContent>

        </Card>


        {/* ====================================================
            TABLE STATUS
        ==================================================== */}

        <Card
          sx={{
            mb: 3,

            borderRadius: 3,

            border:
              "1px solid #E6D89A",

            boxShadow:
              "0 4px 12px rgba(109,76,65,0.08)",
          }}
        >

          <CardContent>

            <Typography
              variant="h6"
              sx={{
                color: "#6D4C41",

                fontWeight: "bold",

                mb: 2,
              }}
            >
              Available Tables
            </Typography>


            <Divider
              sx={{ mb: 2 }}
            />


            {tables.length > 0 ? (

              <Alert severity="success">
                {tables.length} table(s)
                available for creating
                relationships.
              </Alert>

            ) : (

              <Alert severity="warning">
                No tables found for the
                selected database.
              </Alert>

            )}

          </CardContent>

        </Card>


        {/* ====================================================
            CREATE RELATIONSHIP
        ==================================================== */}

        <Card
          sx={{
            mb: 3,

            borderRadius: 3,

            border:
              "1px solid #E6D89A",

            boxShadow:
              "0 4px 12px rgba(109,76,65,0.08)",
          }}
        >

          <CardContent>

            <Typography
              variant="h6"
              sx={{
                color: "#6D4C41",

                fontWeight: "bold",

                mb: 3,
              }}
            >
              Create Relationship
            </Typography>


            <Box
              sx={{
                display: "grid",

                gridTemplateColumns: {
                  xs: "1fr",
                  md: "1fr 1fr",
                },

                gap: 3,
              }}
            >

              {/* ==================================================
                  PARENT TABLE
              ================================================== */}

              <Box>

                <Typography
                  sx={{
                    color: "#6D4C41",

                    fontWeight: "bold",

                    mb: 1,
                  }}
                >
                  Parent Table
                </Typography>


                <Select
                  value={parentTable}
                  onChange={
                    handleParentTableChange
                  }
                  displayEmpty
                  fullWidth
                >

                  <MenuItem value="">
                    Select Parent Table
                  </MenuItem>


                  {tables.map(
                    (table, index) => {
                      const tableName =
                        getTableName(table);

                      return (
                        <MenuItem
                          key={`${tableName}-${index}`}
                          value={tableName}
                        >
                          {tableName}
                        </MenuItem>
                      );
                    }
                  )}

                </Select>

              </Box>


              {/* ==================================================
                  PARENT COLUMN
              ================================================== */}

              <Box>

                <Typography
                  sx={{
                    color: "#6D4C41",

                    fontWeight: "bold",

                    mb: 1,
                  }}
                >
                  Parent Column
                </Typography>


                <Select
                  value={parentColumn}
                  onChange={(event) =>
                    setParentColumn(
                      event.target.value
                    )
                  }
                  displayEmpty
                  fullWidth
                  disabled={!parentTable}
                >

                  <MenuItem value="">
                    Select Parent Column
                  </MenuItem>


                  {parentColumns.map(
                    (column, index) => {
                      const columnName =
                        getColumnName(column);

                      return (
                        <MenuItem
                          key={`${columnName}-${index}`}
                          value={columnName}
                        >
                          {columnName}
                        </MenuItem>
                      );
                    }
                  )}

                </Select>

              </Box>


              {/* ==================================================
                  CHILD TABLE
              ================================================== */}

              <Box>

                <Typography
                  sx={{
                    color: "#6D4C41",

                    fontWeight: "bold",

                    mb: 1,
                  }}
                >
                  Child Table
                </Typography>


                <Select
                  value={childTable}
                  onChange={
                    handleChildTableChange
                  }
                  displayEmpty
                  fullWidth
                >

                  <MenuItem value="">
                    Select Child Table
                  </MenuItem>


                  {tables.map(
                    (table, index) => {
                      const tableName =
                        getTableName(table);

                      return (
                        <MenuItem
                          key={`${tableName}-${index}`}
                          value={tableName}
                        >
                          {tableName}
                        </MenuItem>
                      );
                    }
                  )}

                </Select>

              </Box>


              {/* ==================================================
                  CHILD COLUMN
              ================================================== */}

              <Box>

                <Typography
                  sx={{
                    color: "#6D4C41",

                    fontWeight: "bold",

                    mb: 1,
                  }}
                >
                  Child Column
                </Typography>


                <Select
                  value={childColumn}
                  onChange={(event) =>
                    setChildColumn(
                      event.target.value
                    )
                  }
                  displayEmpty
                  fullWidth
                  disabled={!childTable}
                >

                  <MenuItem value="">
                    Select Child Column
                  </MenuItem>


                  {childColumns.map(
                    (column, index) => {
                      const columnName =
                        getColumnName(column);

                      return (
                        <MenuItem
                          key={`${columnName}-${index}`}
                          value={columnName}
                        >
                          {columnName}
                        </MenuItem>
                      );
                    }
                  )}

                </Select>

              </Box>

            </Box>


            {/* ==================================================
                CREATE BUTTON
            ================================================== */}

            <Box
              sx={{
                mt: 3,

                display: "flex",

                justifyContent: "flex-end",
              }}
            >

              <Button
                variant="contained"
                onClick={
                  handleCreateRelationship
                }
                disabled={
                  loading ||
                  tables.length === 0
                }
                sx={{
                  bgcolor: "#6D4C41",

                  "&:hover": {
                    bgcolor: "#5D4037",
                  },

                  px: 3,
                }}
              >
                Create Relationship
              </Button>

            </Box>

          </CardContent>

        </Card>


        {/* ====================================================
            SAVED RELATIONSHIPS
        ==================================================== */}

        <Card
          sx={{
            mb: 3,

            borderRadius: 3,

            border:
              "1px solid #E6D89A",

            boxShadow:
              "0 4px 12px rgba(109,76,65,0.08)",
          }}
        >

          <CardContent>

            <Typography
              variant="h6"
              sx={{
                color: "#6D4C41",

                fontWeight: "bold",

                mb: 2,
              }}
            >
              Saved Relationships
            </Typography>


            <Divider
              sx={{ mb: 3 }}
            />


            {savedRelationships.length === 0 ? (

              <Alert severity="info">
                No relationships saved yet.
              </Alert>

            ) : (

              <Box
                sx={{
                  display: "flex",

                  flexDirection: "column",

                  gap: 1.5,
                }}
              >

                {savedRelationships.map(
                  (relationship, index) => (

                    <Box
                      key={
                        relationship.id ||
                        index
                      }
                      sx={{
                        p: 2,

                        borderRadius: 2,

                        bgcolor: "#FFF8D6",

                        border:
                          "1px solid #E6D89A",
                      }}
                    >

                      <Typography
                        sx={{
                          color: "#6D4C41",

                          fontWeight: "bold",
                        }}
                      >

                        {relationship.parent_table}
                        {"."}
                        {relationship.parent_column}

                        {"  →  "}

                        {relationship.child_table}
                        {"."}
                        {relationship.child_column}

                      </Typography>


                      {relationship.created_at && (

                        <Typography
                          variant="body2"
                          sx={{
                            color: "#795548",

                            mt: 0.5,
                          }}
                        >
                          Created:{" "}
                          {new Date(
                            relationship.created_at
                          ).toLocaleString()}
                        </Typography>

                      )}

                    </Box>

                  )
                )}

              </Box>

            )}

          </CardContent>

        </Card>


        {/* ====================================================
            ERROR MESSAGE
        ==================================================== */}

        {errorMessage && (

          <Alert
            severity="error"
            onClose={() =>
              setErrorMessage("")
            }
            sx={{
              mb: 3,
            }}
          >
            {errorMessage}
          </Alert>

        )}


        {/* ====================================================
            SUCCESS SNACKBAR
        ==================================================== */}

        <Snackbar
          open={snackbarOpen}
          autoHideDuration={4000}
          onClose={handleCloseSnackbar}
          message={successMessage}
        />

      </Box>

    </DashboardLayout>
  );
}

export default Relationships;