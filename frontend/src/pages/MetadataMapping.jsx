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
  Paper,
  Select,
  Snackbar,
  TextField,
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

function MetadataMapping() {
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

  const [metadata, setMetadata] = useState(null);

  const [loading, setLoading] = useState(false);

  const [selectedTable, setSelectedTable] = useState("");


  // ============================================================
  // BUSINESS MAPPING
  // ============================================================

  const [businessEntity, setBusinessEntity] = useState("");

  const [tablePurpose, setTablePurpose] = useState("");

  const [aliases, setAliases] = useState("");

  const [primaryIdentifier, setPrimaryIdentifier] = useState("");

  const [dateField, setDateField] = useState("");

  const [amountField, setAmountField] = useState("");

  const [statusField, setStatusField] = useState("");

  const [customerReference, setCustomerReference] = useState("");

  const [description, setDescription] = useState("");


  // ============================================================
  // COLUMN MAPPING
  // ============================================================

  const [selectedColumn, setSelectedColumn] = useState("");

  const [columnMappings, setColumnMappings] = useState({
    database_name: "",
    table_name: "",
    column_name: "",
    business_name: "",
    description: "",
  });


  // ============================================================
  // AI
  // ============================================================

  const [businessAIPreview, setBusinessAIPreview] = useState("");

  const [columnAIPreview, setColumnAIPreview] = useState("");

  const [aiLoading, setAiLoading] = useState(false);


  // ============================================================
  // SEARCH / MESSAGES
  // ============================================================

  const [search, setSearch] = useState("");

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

      setMetadata(response.data);

      if (response.data?.tables?.length > 0) {
        const firstTable = response.data.tables[0];

        const firstTableName =
          typeof firstTable === "string"
            ? firstTable
            : firstTable.name;

        setSelectedTable(firstTableName || "");
      } else {
        setSelectedTable("");
      }
    } catch (error) {
      console.error(
        "LOAD METADATA ERROR:",
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
  // LOAD METADATA WHEN DATABASE CHANGES
  // ============================================================

  useEffect(() => {
    if (token) {
      loadMetadata();
    } else {
      setErrorMessage("Please login first.");
    }
  }, [databaseType, databaseName]);


  // ============================================================
  // TABLES
  // ============================================================

  const tables = useMemo(() => {
    if (!metadata?.tables) return [];

    return metadata.tables;
  }, [metadata]);


  // ============================================================
  // CURRENT TABLE
  // ============================================================

  const currentTable = useMemo(() => {
    if (!selectedTable) return null;

    return tables.find((table) => {
      const tableName =
        typeof table === "string"
          ? table
          : table.name;

      return tableName === selectedTable;
    });
  }, [tables, selectedTable]);


  // ============================================================
  // CURRENT COLUMNS
  // ============================================================

  const currentColumns = useMemo(() => {
    if (!currentTable) return [];

    return currentTable.columns || [];
  }, [currentTable]);


  // ============================================================
  // FILTERED TABLES
  // ============================================================

  const filteredTables = useMemo(() => {
    if (!search.trim()) return tables;

    const searchValue = search.toLowerCase();

    return tables.filter((table) => {
      const tableName =
        typeof table === "string"
          ? table
          : table.name;

      return tableName
        ?.toLowerCase()
        .includes(searchValue);
    });
  }, [tables, search]);


  // ============================================================
  // TABLE CHANGE
  // ============================================================

  const handleTableChange = (event) => {
    const tableName = event.target.value;

    setSelectedTable(tableName);

    setBusinessEntity("");
    setTablePurpose("");
    setAliases("");
    setPrimaryIdentifier("");
    setDateField("");
    setAmountField("");
    setStatusField("");
    setCustomerReference("");
    setDescription("");

    setSelectedColumn("");

    setColumnMappings({
      database_name: databaseName,
      table_name: tableName,
      column_name: "",
      business_name: "",
      description: "",
    });

    setBusinessAIPreview("");
    setColumnAIPreview("");
  };


  // ============================================================
  // COLUMN NAME HELPER
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
  // COLUMN CHANGE
  // ============================================================

  const handleColumnChange = (event) => {
    const columnName = event.target.value;

    setSelectedColumn(columnName);

    setColumnMappings({
      database_name: databaseName,
      table_name: selectedTable,
      column_name: columnName,
      business_name: "",
      description: "",
    });
  };


  // ============================================================
  // AI BUSINESS MAPPING
  // ============================================================

  const handleBusinessAIMapping = async () => {
    if (!selectedTable) {
      setErrorMessage("Please select a table first.");
      return;
    }

    try {
      setAiLoading(true);
      setErrorMessage("");

      const response = await axios.post(
        `${API_URL}/database/ai-mapping`,
        {
          database_name: databaseName,
          table_name: selectedTable,
          mapping_type: "business_mapping",

          columns: currentTable?.columns || [],

          relationships:
            currentTable?.foreign_keys || [],
        },
        {
          headers: authHeaders,
        }
      );

      console.log(
        "BUSINESS AI RESPONSE:",
        response.data
      );

      // IMPORTANT:
      // Backend returns:
      // response.data.business_mapping
      const mapping =
        response.data?.business_mapping;

      if (!mapping) {
        throw new Error(
          "Business mapping was not returned by the backend."
        );
      }

      setBusinessEntity(
        mapping.business_entity || ""
      );

      setTablePurpose(
        mapping.table_purpose || ""
      );

      const aliasesValue =
        mapping.ai_aliases || [];

      setAliases(
        Array.isArray(aliasesValue)
          ? aliasesValue.join(", ")
          : aliasesValue
      );

      setPrimaryIdentifier(
        mapping.primary_identifier || ""
      );

      setDateField(
        mapping.date_field || ""
      );

      setAmountField(
        mapping.amount_field || ""
      );

      setStatusField(
        mapping.status_field || ""
      );

      setCustomerReference(
        mapping.customer_reference || ""
      );

      setDescription(
        mapping.description || ""
      );

      setSuccessMessage(
        "AI Business Mapping generated successfully."
      );

      setSnackbarOpen(true);
    } catch (error) {
      console.error(
        "BUSINESS AI MAPPING ERROR:",
        error.response?.data || error
      );

      setErrorMessage(
        error.response?.data?.detail ||
          error.message ||
          "Failed to generate AI business mapping."
      );
    } finally {
      setAiLoading(false);
    }
  };


  // ============================================================
  // AI COLUMN MAPPING
  // ============================================================

  const handleColumnAIMapping = async () => {
    if (!selectedTable) {
      setErrorMessage("Please select a table first.");
      return;
    }

    if (!selectedColumn) {
      setErrorMessage("Please select a column first.");
      return;
    }

    try {
      setAiLoading(true);
      setErrorMessage("");

      const response = await axios.post(
        `${API_URL}/database/ai-mapping`,
        {
          database_name: databaseName,
          table_name: selectedTable,
          mapping_type: "column_mapping",

          columns: currentTable?.columns || [],

          relationships:
            currentTable?.foreign_keys || [],
        },
        {
          headers: authHeaders,
        }
      );

      console.log(
        "COLUMN AI RESPONSE:",
        response.data
      );

      // IMPORTANT:
      // Backend returns:
      // response.data.column_mappings
      const mappings =
        response.data?.column_mappings || [];

      if (!mappings.length) {
        throw new Error(
          "Column mappings were not returned by the backend."
        );
      }

      const selectedMapping =
        mappings.find(
          (item) =>
            item.column_name === selectedColumn
        );

      if (!selectedMapping) {
        throw new Error(
          `No AI mapping found for column "${selectedColumn}".`
        );
      }

      setColumnMappings({
        database_name: databaseName,

        table_name: selectedTable,

        column_name:
          selectedMapping.column_name ||
          selectedColumn,

        business_name:
          selectedMapping.business_name || "",

        description:
          selectedMapping.description || "",
      });

      setSuccessMessage(
        "AI Column Mapping generated successfully."
      );

      setSnackbarOpen(true);
    } catch (error) {
      console.error(
        "COLUMN AI MAPPING ERROR:",
        error.response?.data || error
      );

      setErrorMessage(
        error.response?.data?.detail ||
          error.message ||
          "Failed to generate AI column mapping."
      );
    } finally {
      setAiLoading(false);
    }
  };


  // ============================================================
  // BUSINESS PROMPT PREVIEW
  // ============================================================

  const handleBusinessPromptPreview = async () => {
    if (!selectedTable) {
      setErrorMessage("Please select a table first.");
      return;
    }

    try {
      setErrorMessage("");

      const response = await axios.post(
        `${API_URL}/database/ai-prompt-preview`,
        {
          database_name: databaseName,

          table_name: selectedTable,

          prompt_type: "business_mapping",

          important_fields:
            currentTable?.columns
              ? currentTable.columns.map(
                  (column) =>
                    typeof column === "string"
                      ? column
                      : column.name
                )
              : [],

          relationships:
            currentTable?.foreign_keys || [],
        },
        {
          headers: authHeaders,
        }
      );

      console.log(
        "BUSINESS PROMPT PREVIEW:",
        response.data
      );

      setBusinessAIPreview(
        response.data?.preview || ""
      );
    } catch (error) {
      console.error(
        "BUSINESS PROMPT PREVIEW ERROR:",
        error.response?.data || error
      );

      setErrorMessage(
        error.response?.data?.detail ||
          "Failed to generate prompt preview."
      );
    }
  };


  // ============================================================
  // COLUMN PROMPT PREVIEW
  // ============================================================

  const handleColumnPromptPreview = async () => {
    if (!selectedTable) {
      setErrorMessage("Please select a table first.");
      return;
    }

    if (!selectedColumn) {
      setErrorMessage("Please select a column first.");
      return;
    }

    try {
      setErrorMessage("");

      const response = await axios.post(
        `${API_URL}/database/ai-prompt-preview`,
        {
          database_name: databaseName,

          table_name: selectedTable,

          prompt_type: "column_mapping",

          important_fields:
            currentTable?.columns
              ? currentTable.columns.map(
                  (column) =>
                    typeof column === "string"
                      ? column
                      : column.name
                )
              : [],

          relationships:
            currentTable?.foreign_keys || [],
        },
        {
          headers: authHeaders,
        }
      );

      console.log(
        "COLUMN PROMPT PREVIEW:",
        response.data
      );

      setColumnAIPreview(
        response.data?.preview || ""
      );
    } catch (error) {
      console.error(
        "COLUMN PROMPT PREVIEW ERROR:",
        error.response?.data || error
      );

      setErrorMessage(
        error.response?.data?.detail ||
          "Failed to generate prompt preview."
      );
    }
  };


  // ============================================================
  // SAVE BUSINESS MAPPING
  // ============================================================

  const handleSaveBusinessMapping = async () => {
    if (!selectedTable) {
      setErrorMessage("Please select a table first.");
      return;
    }

    if (!businessEntity.trim()) {
      setErrorMessage(
        "Business Entity is required."
      );
      return;
    }

    try {
      setErrorMessage("");

      await axios.post(
        `${API_URL}/database/business-mapping`,
        {
          mapping: {
            database_name: databaseName,

            table_name: selectedTable,

            business_entity: businessEntity,

            table_purpose: tablePurpose,

            ai_aliases: aliases
              .split(",")
              .map((item) => item.trim())
              .filter(Boolean),

            primary_identifier:
              primaryIdentifier || null,

            date_field:
              dateField || null,

            amount_field:
              amountField || null,

            status_field:
              statusField || null,

            customer_reference:
              customerReference || null,

            description:
              description || null,
          },

          schema_metadata:
            metadata || {},
        },
        {
          headers: authHeaders,
        }
      );

      setSuccessMessage(
        "Business Mapping saved successfully."
      );

      setSnackbarOpen(true);
    } catch (error) {
      console.error(
        "SAVE BUSINESS MAPPING ERROR:",
        error.response?.data || error
      );

      setErrorMessage(
        error.response?.data?.detail ||
          "Failed to save business mapping."
      );
    }
  };


  // ============================================================
  // SAVE COLUMN MAPPING
  // ============================================================

  const handleSaveColumnMapping = async () => {
    if (!selectedTable) {
      setErrorMessage("Please select a table first.");
      return;
    }

    if (!selectedColumn) {
      setErrorMessage("Please select a column first.");
      return;
    }

    try {
      setErrorMessage("");

      await axios.post(
        `${API_URL}/database/column-mapping`,
        {
          mapping: columnMappings,

          schema_metadata:
            metadata || {},
        },
        {
          headers: authHeaders,
        }
      );

      setSuccessMessage(
        "Column Mapping saved successfully."
      );

      setSnackbarOpen(true);
    } catch (error) {
      console.error(
        "SAVE COLUMN MAPPING ERROR:",
        error.response?.data || error
      );

      setErrorMessage(
        error.response?.data?.detail ||
          "Failed to save column mapping."
      );
    }
  };


  // ============================================================
  // EXPORT MAPPING
  // ============================================================

  const handleExport = async (format) => {
    try {
      setErrorMessage("");

      const response = await axios.post(
        `${API_URL}/database/export-mapping`,
        {
          database: databaseName,

          entities: [],

          relationships: [],

          format,
        },
        {
          headers: authHeaders,

          responseType: "blob",
        }
      );

      const blob = new Blob(
        [response.data],
        {
          type:
            format === "json"
              ? "application/json"
              : "text/plain",
        }
      );

      const url =
        window.URL.createObjectURL(blob);

      const link =
        document.createElement("a");

      link.href = url;

      link.download =
        `metadata_mapping.${format}`;

      document.body.appendChild(link);

      link.click();

      link.remove();

      window.URL.revokeObjectURL(url);

      setSuccessMessage(
        `Mapping exported as ${format.toUpperCase()} successfully.`
      );

      setSnackbarOpen(true);
    } catch (error) {
      console.error(
        "EXPORT MAPPING ERROR:",
        error.response?.data || error
      );

      setErrorMessage(
        error.response?.data?.detail ||
          "Failed to export mapping."
      );
    }
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

        {/* ======================================================
            HEADER
        ====================================================== */}

        <Box sx={{ mb: 4 }}>
          <Typography
            variant="h4"
            sx={{
              color: "#6D4C41",
              fontWeight: "bold",
              mb: 1,
            }}
          >
            Metadata Mapping
          </Typography>

          <Typography
            sx={{
              color: "#795548",
              fontSize: "1rem",
            }}
          >
            Map database metadata into meaningful
            business and column-level information.
          </Typography>
        </Box>


        {/* ======================================================
            ACTIVE DATABASE
        ====================================================== */}

        <Card
          sx={{
            mb: 3,
            borderRadius: 3,
            border: "1px solid #E6D89A",
            boxShadow: "0 4px 12px rgba(109,76,65,0.08)",
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

            <Divider sx={{ mb: 3 }} />

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
              <TextField
                label="Database Type"
                value={databaseType}
                onChange={(event) => {
                  setDatabaseType(
                    event.target.value
                  );

                  localStorage.setItem(
                    "databaseType",
                    event.target.value
                  );
                }}
                fullWidth
              />

              <TextField
                label="Database Name"
                value={databaseName}
                onChange={(event) => {
                  setDatabaseName(
                    event.target.value
                  );

                  localStorage.setItem(
                    "databaseName",
                    event.target.value
                  );
                }}
                fullWidth
              />
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
                  sx={{ color: "white" }}
                />
              ) : (
                "Refresh Metadata"
              )}
            </Button>
          </CardContent>
        </Card>


        {/* ======================================================
            SEARCH & FILTER
        ====================================================== */}

        <Card
          sx={{
            mb: 3,
            borderRadius: 3,
            border: "1px solid #E6D89A",
            boxShadow: "0 4px 12px rgba(109,76,65,0.08)",
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
              Search & Filter
            </Typography>

            <Divider sx={{ mb: 3 }} />

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
              <TextField
                label="Search Table"
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                fullWidth
              />

              <Select
                value={selectedTable}
                onChange={handleTableChange}
                displayEmpty
                fullWidth
              >
                <MenuItem value="">
                  Select Table
                </MenuItem>

                {filteredTables.map(
                  (table, index) => {
                    const tableName =
                      typeof table === "string"
                        ? table
                        : table.name;

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

            {selectedTable && (
              <Typography
                sx={{
                  mt: 2,
                  color: "#795548",
                }}
              >
                Selected table:{" "}
                <strong>
                  {selectedTable}
                </strong>
              </Typography>
            )}
          </CardContent>
        </Card>


        {/* ======================================================
            BUSINESS AI MAPPING
        ====================================================== */}

        <Card
          sx={{
            mb: 3,
            borderRadius: 3,
            border: "1px solid #E6D89A",
            boxShadow: "0 4px 12px rgba(109,76,65,0.08)",
          }}
        >
          <CardContent>
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: {
                  xs: "flex-start",
                  md: "center",
                },
                flexDirection: {
                  xs: "column",
                  md: "row",
                },
                gap: 2,
                mb: 2,
              }}
            >
              <Typography
                variant="h6"
                sx={{
                  color: "#6D4C41",
                  fontWeight: "bold",
                }}
              >
                AI Business Mapping
              </Typography>

              <Button
                variant="contained"
                onClick={
                  handleBusinessAIMapping
                }
                disabled={
                  aiLoading || !selectedTable
                }
                sx={{
                  bgcolor: "#6D4C41",
                  "&:hover": {
                    bgcolor: "#5D4037",
                  },
                }}
              >
                {aiLoading ? (
                  <CircularProgress
                    size={22}
                    sx={{ color: "white" }}
                  />
                ) : (
                  "Generate AI Mapping"
                )}
              </Button>
            </Box>

            <Divider sx={{ mb: 3 }} />

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
              <TextField
                label="Business Entity"
                value={businessEntity}
                onChange={(event) =>
                  setBusinessEntity(
                    event.target.value
                  )
                }
                fullWidth
              />

              <TextField
                label="Table Purpose"
                value={tablePurpose}
                onChange={(event) =>
                  setTablePurpose(
                    event.target.value
                  )
                }
                fullWidth
              />

              <TextField
                label="AI Aliases"
                value={aliases}
                onChange={(event) =>
                  setAliases(event.target.value)
                }
                fullWidth
                placeholder="Customer, Client, User"
              />

              <TextField
                label="Primary Identifier"
                value={primaryIdentifier}
                onChange={(event) =>
                  setPrimaryIdentifier(
                    event.target.value
                  )
                }
                fullWidth
              />

              <TextField
                label="Date Field"
                value={dateField}
                onChange={(event) =>
                  setDateField(
                    event.target.value
                  )
                }
                fullWidth
              />

              <TextField
                label="Amount Field"
                value={amountField}
                onChange={(event) =>
                  setAmountField(
                    event.target.value
                  )
                }
                fullWidth
              />

              <TextField
                label="Status Field"
                value={statusField}
                onChange={(event) =>
                  setStatusField(
                    event.target.value
                  )
                }
                fullWidth
              />

              <TextField
                label="Customer Reference"
                value={customerReference}
                onChange={(event) =>
                  setCustomerReference(
                    event.target.value
                  )
                }
                fullWidth
              />

              <TextField
                label="Description"
                value={description}
                onChange={(event) =>
                  setDescription(
                    event.target.value
                  )
                }
                fullWidth
                multiline
                minRows={3}
                sx={{
                  gridColumn: {
                    xs: "auto",
                    md: "1 / -1",
                  },
                }}
              />
            </Box>

            <Box
              sx={{
                display: "flex",
                gap: 2,
                flexWrap: "wrap",
                mt: 3,
              }}
            >
              <Button
                variant="outlined"
                onClick={
                  handleBusinessPromptPreview
                }
                disabled={!selectedTable}
                sx={{
                  color: "#6D4C41",
                  borderColor: "#6D4C41",
                }}
              >
                Prompt Preview
              </Button>

              <Button
                variant="contained"
                onClick={
                  handleSaveBusinessMapping
                }
                disabled={!selectedTable}
                sx={{
                  bgcolor: "#6D4C41",
                  "&:hover": {
                    bgcolor: "#5D4037",
                  },
                }}
              >
                Save Business Mapping
              </Button>
            </Box>

            {businessAIPreview && (
              <Paper
                sx={{
                  mt: 3,
                  p: 3,
                  bgcolor: "#FFFDF2",
                  borderRadius: 2,
                  border:
                    "1px solid #E6D89A",
                }}
              >
                <Typography
                  variant="subtitle1"
                  sx={{
                    color: "#6D4C41",
                    fontWeight: "bold",
                    mb: 1,
                  }}
                >
                  AI Business Prompt Preview
                </Typography>

                <Typography
                  component="pre"
                  sx={{
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    color: "#5D4037",
                    fontFamily:
                      "monospace",
                    fontSize: "0.9rem",
                  }}
                >
                  {businessAIPreview}
                </Typography>
              </Paper>
            )}
          </CardContent>
        </Card>


        {/* ======================================================
            COLUMN AI MAPPING
        ====================================================== */}

        <Card
          sx={{
            mb: 3,
            borderRadius: 3,
            border: "1px solid #E6D89A",
            boxShadow: "0 4px 12px rgba(109,76,65,0.08)",
          }}
        >
          <CardContent>
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: {
                  xs: "flex-start",
                  md: "center",
                },
                flexDirection: {
                  xs: "column",
                  md: "row",
                },
                gap: 2,
                mb: 2,
              }}
            >
              <Typography
                variant="h6"
                sx={{
                  color: "#6D4C41",
                  fontWeight: "bold",
                }}
              >
                AI Column Mapping
              </Typography>

              <Button
                variant="contained"
                onClick={
                  handleColumnAIMapping
                }
                disabled={
                  aiLoading ||
                  !selectedTable ||
                  !selectedColumn
                }
                sx={{
                  bgcolor: "#6D4C41",
                  "&:hover": {
                    bgcolor: "#5D4037",
                  },
                }}
              >
                {aiLoading ? (
                  <CircularProgress
                    size={22}
                    sx={{ color: "white" }}
                  />
                ) : (
                  "Generate AI Mapping"
                )}
              </Button>
            </Box>

            <Divider sx={{ mb: 3 }} />

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
              <Select
                value={selectedColumn}
                onChange={handleColumnChange}
                displayEmpty
                fullWidth
              >
                <MenuItem value="">
                  Select Column
                </MenuItem>

                {currentColumns.map(
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

              <TextField
                label="Business Name"
                value={
                  columnMappings.business_name
                }
                onChange={(event) =>
                  setColumnMappings(
                    (previous) => ({
                      ...previous,
                      business_name:
                        event.target.value,
                    })
                  )
                }
                fullWidth
              />

              <TextField
                label="Business Description"
                value={
                  columnMappings.description
                }
                onChange={(event) =>
                  setColumnMappings(
                    (previous) => ({
                      ...previous,
                      description:
                        event.target.value,
                    })
                  )
                }
                fullWidth
                multiline
                minRows={3}
                sx={{
                  gridColumn: {
                    xs: "auto",
                    md: "1 / -1",
                  },
                }}
              />
            </Box>

            <Box
              sx={{
                display: "flex",
                gap: 2,
                flexWrap: "wrap",
                mt: 3,
              }}
            >
              <Button
                variant="outlined"
                onClick={
                  handleColumnPromptPreview
                }
                disabled={
                  !selectedTable ||
                  !selectedColumn
                }
                sx={{
                  color: "#6D4C41",
                  borderColor: "#6D4C41",
                }}
              >
                Prompt Preview
              </Button>

              <Button
                variant="contained"
                onClick={
                  handleSaveColumnMapping
                }
                disabled={
                  !selectedTable ||
                  !selectedColumn
                }
                sx={{
                  bgcolor: "#6D4C41",
                  "&:hover": {
                    bgcolor: "#5D4037",
                  },
                }}
              >
                Save Column Mapping
              </Button>
            </Box>

            {columnAIPreview && (
              <Paper
                sx={{
                  mt: 3,
                  p: 3,
                  bgcolor: "#FFFDF2",
                  borderRadius: 2,
                  border:
                    "1px solid #E6D89A",
                }}
              >
                <Typography
                  variant="subtitle1"
                  sx={{
                    color: "#6D4C41",
                    fontWeight: "bold",
                    mb: 1,
                  }}
                >
                  AI Column Prompt Preview
                </Typography>

                <Typography
                  component="pre"
                  sx={{
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    color: "#5D4037",
                    fontFamily:
                      "monospace",
                    fontSize: "0.9rem",
                  }}
                >
                  {columnAIPreview}
                </Typography>
              </Paper>
            )}
          </CardContent>
        </Card>


        {/* ======================================================
            EXPORT MAPPING
        ====================================================== */}

        <Card
          sx={{
            mb: 3,
            borderRadius: 3,
            border: "1px solid #E6D89A",
            boxShadow: "0 4px 12px rgba(109,76,65,0.08)",
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
              Export Mapping
            </Typography>

            <Divider sx={{ mb: 3 }} />

            <Box
              sx={{
                display: "flex",
                gap: 2,
                flexWrap: "wrap",
              }}
            >
              <Button
                variant="contained"
                onClick={() =>
                  handleExport("json")
                }
                sx={{
                  bgcolor: "#6D4C41",
                  "&:hover": {
                    bgcolor: "#5D4037",
                  },
                }}
              >
                Export JSON
              </Button>

              <Button
                variant="outlined"
                onClick={() =>
                  handleExport("txt")
                }
                sx={{
                  color: "#6D4C41",
                  borderColor: "#6D4C41",
                }}
              >
                Export TXT
              </Button>
            </Box>
          </CardContent>
        </Card>


        {/* ======================================================
            ERROR
        ====================================================== */}

        {errorMessage && (
          <Alert
            severity="error"
            onClose={() =>
              setErrorMessage("")
            }
            sx={{
              mb: 3,
              borderRadius: 2,
            }}
          >
            {errorMessage}
          </Alert>
        )}


        {/* ======================================================
            SUCCESS SNACKBAR
        ====================================================== */}

        <Snackbar
          open={snackbarOpen}
          autoHideDuration={4000}
          onClose={() =>
            setSnackbarOpen(false)
          }
          message={successMessage}
        />

      </Box>
    </DashboardLayout>
  );
}

export default MetadataMapping;