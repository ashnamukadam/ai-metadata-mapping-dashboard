import { useEffect, useMemo, useState } from "react";

import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";

import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import RefreshIcon from "@mui/icons-material/Refresh";
import SearchIcon from "@mui/icons-material/Search";
import StorageIcon from "@mui/icons-material/Storage";
import TableChartIcon from "@mui/icons-material/TableChart";
import ViewColumnIcon from "@mui/icons-material/ViewColumn";
import ViewListIcon from "@mui/icons-material/ViewList";

import api from "../services/api";
import DashboardLayout from "../layouts/DashboardLayout";


function SchemaViewer() {
  const [metadata, setMetadata] = useState({
    database_name: "",
    database_type: "",
    tables: [],
    views: [],
  });

  const [selectedDatabaseType, setSelectedDatabaseType] =
    useState(
      localStorage.getItem("metadata_database_type") ||
        "mongodb"
    );

  const [selectedDatabaseName, setSelectedDatabaseName] =
    useState(
      localStorage.getItem("metadata_database_name") || ""
    );

  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");


  // ============================================================
  // FETCH METADATA
  // ============================================================

  const fetchMetadata = async (
    showLoader = true,
    databaseType = selectedDatabaseType,
    databaseName = selectedDatabaseName
  ) => {
    try {
      if (showLoader) {
        setLoading(true);
      } else {
        setRefreshing(true);
      }

      setError("");

      const type =
        databaseType?.trim().toLowerCase() || "";

      const name =
        databaseName?.trim() || "";

      console.log(
        "=========================================="
      );

      console.log(
        "REQUESTING DATABASE METADATA"
      );

      console.log(
        "Database Type:",
        type
      );

      console.log(
        "Database Name:",
        name
      );

      console.log(
        "=========================================="
      );


      const response = await api.get(
        "/database/metadata",
        {
          params: {
            database_type:
              type || undefined,

            database_name:
              name || undefined,
          },
        }
      );


      console.log(
        "SCHEMA METADATA RESPONSE:",
        response.data
      );


      const returnedType =
        response.data?.database_type
          ?.toLowerCase() || "";

      const returnedName =
        response.data?.database_name || "";


      // ----------------------------------------------------------
      // IMPORTANT:
      // If backend returned a different database than requested,
      // show an error instead of silently displaying PostgreSQL.
      // ----------------------------------------------------------

      if (
        type &&
        returnedType &&
        returnedType !== type
      ) {
        console.error(
          "DATABASE TYPE MISMATCH",
          {
            requested: type,
            returned: returnedType,
          }
        );

        setError(
          `Requested ${type.toUpperCase()} metadata, but backend returned ${returnedType.toUpperCase()} metadata.`
        );

        setMetadata({
          database_name: "",
          database_type: "",
          tables: [],
          views: [],
        });

        return;
      }


      setMetadata({
        database_name: returnedName,
        database_type: returnedType,
        tables: Array.isArray(
          response.data?.tables
        )
          ? response.data.tables
          : [],
        views: Array.isArray(
          response.data?.views
        )
          ? response.data.views
          : [],
      });


      // Save the successfully loaded database
      localStorage.setItem(
        "metadata_database_type",
        returnedType || type
      );

      if (returnedName || name) {
        localStorage.setItem(
          "metadata_database_name",
          returnedName || name
        );
      }


    } catch (err) {
      console.error(
        "Schema metadata error:",
        err
      );

      const message =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message ||
        "Failed to load schema metadata.";

      setError(message);

      setMetadata({
        database_name: "",
        database_type: "",
        tables: [],
        views: [],
      });

    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };


  // ============================================================
  // INITIAL LOAD
  // ============================================================

  useEffect(() => {
    const savedType =
      localStorage.getItem(
        "metadata_database_type"
      );

    const savedName =
      localStorage.getItem(
        "metadata_database_name"
      );


    if (savedType) {
      setSelectedDatabaseType(
        savedType.toLowerCase()
      );
    }

    if (savedName) {
      setSelectedDatabaseName(
        savedName
      );
    }


    fetchMetadata(
      true,
      savedType || "mongodb",
      savedName || ""
    );

  }, []);


  // ============================================================
  // CHANGE DATABASE
  // ============================================================

  const handleDatabaseChange = async (
    event
  ) => {
    const newType =
      event.target.value;

    console.log(
      "Changing database type to:",
      newType
    );

    setSelectedDatabaseType(
      newType
    );

    setSearch("");

    localStorage.setItem(
      "metadata_database_type",
      newType
    );

    await fetchMetadata(
      true,
      newType,
      selectedDatabaseName
    );
  };


  // ============================================================
  // REFRESH
  // ============================================================

  const handleRefresh = () => {
    fetchMetadata(
      false,
      selectedDatabaseType,
      selectedDatabaseName
    );
  };


  // ============================================================
  // SEARCH
  // ============================================================

  const filteredTables = useMemo(() => {
    const query =
      search.trim().toLowerCase();

    if (!query) {
      return metadata.tables;
    }

    return metadata.tables.filter(
      (table) => {
        const tableName =
          table?.name?.toLowerCase() ||
          "";

        const tableType =
          table?.table_type?.toLowerCase() ||
          "";

        const schemaName =
          table?.schema_name?.toLowerCase() ||
          "";

        const columns =
          Array.isArray(
            table?.columns
          )
            ? table.columns
            : [];

        const columnMatch =
          columns.some(
            (column) => {
              const columnName =
                column?.name?.toLowerCase() ||
                "";

              const dataType =
                column?.data_type?.toLowerCase() ||
                "";

              return (
                columnName.includes(query) ||
                dataType.includes(query)
              );
            }
          );

        return (
          tableName.includes(query) ||
          tableType.includes(query) ||
          schemaName.includes(query) ||
          columnMatch
        );
      }
    );
  }, [metadata.tables, search]);


  const filteredViews = useMemo(() => {
    const query =
      search.trim().toLowerCase();

    if (!query) {
      return metadata.views;
    }

    return metadata.views.filter(
      (view) => {
        const viewName =
          view?.name?.toLowerCase() ||
          "";

        const schemaName =
          view?.schema_name?.toLowerCase() ||
          "";

        const columns =
          Array.isArray(
            view?.columns
          )
            ? view.columns
            : [];

        const columnMatch =
          columns.some(
            (column) => {
              const columnName =
                column?.name?.toLowerCase() ||
                "";

              const dataType =
                column?.data_type?.toLowerCase() ||
                "";

              return (
                columnName.includes(query) ||
                dataType.includes(query)
              );
            }
          );

        return (
          viewName.includes(query) ||
          schemaName.includes(query) ||
          columnMatch
        );
      }
    );
  }, [metadata.views, search]);


  // ============================================================
  // DATABASE INFORMATION
  // ============================================================

  const databaseType =
    metadata.database_type
      ?.toLowerCase() || "";

  const databaseTypeDisplay =
    databaseType
      ? databaseType.toUpperCase()
      : "UNKNOWN";

  const isMongoDB =
    databaseType === "mongodb";

  const tables =
    metadata.tables || [];

  const views =
    metadata.views || [];


  const totalColumns =
    tables.reduce(
      (total, table) =>
        total +
        (
          Array.isArray(
            table?.columns
          )
            ? table.columns.length
            : 0
        ),
      0
    );


  const totalIndexes =
    tables.reduce(
      (total, table) =>
        total +
        (
          Array.isArray(
            table?.indexes
          )
            ? table.indexes.length
            : 0
        ),
      0
    );


  // ============================================================
  // TABLE / COLLECTION CARD
  // ============================================================

  const renderTable = (
    table,
    index
  ) => {
    const columns =
      Array.isArray(
        table?.columns
      )
        ? table.columns
        : [];

    const indexes =
      Array.isArray(
        table?.indexes
      )
        ? table.indexes
        : [];

    const primaryKeys =
      Array.isArray(
        table?.primary_keys
      )
        ? table.primary_keys
        : [];

    const foreignKeys =
      Array.isArray(
        table?.foreign_keys
      )
        ? table.foreign_keys
        : [];

    const constraints =
      Array.isArray(
        table?.constraints
      )
        ? table.constraints
        : [];


    return (
      <Accordion
        key={`${table?.name || "table"}-${index}`}
        sx={{
          mb: 2,
          borderRadius:
            "12px !important",
          overflow: "hidden",
          border:
            "1px solid #D7C29E",
          backgroundColor:
            "#FFFDF2",
          boxShadow: "none",

          "&:before": {
            display: "none",
          },

          "&.Mui-expanded": {
            margin:
              "0 0 16px 0",
          },
        }}
      >
        <AccordionSummary
          expandIcon={
            <ExpandMoreIcon
              sx={{
                color: "#6D4C41",
              }}
            />
          }
          sx={{
            px: 3,
            py: 1,
            backgroundColor:
              "#FFF8D8",

            "& .MuiAccordionSummary-content":
              {
                alignItems:
                  "center",
                gap: 2,
              },
          }}
        >
          <TableChartIcon
            sx={{
              color: "#6D4C41",
              fontSize: 25,
            }}
          />

          <Box
            sx={{
              flexGrow: 1,
            }}
          >
            <Typography
              fontWeight="bold"
              color="#5D4037"
              sx={{
                fontSize:
                  "1.05rem",
                wordBreak:
                  "break-word",
              }}
            >
              {table?.name ||
                "Unnamed"}
            </Typography>

            {table?.schema_name && (
              <Typography
                variant="caption"
                color="#8D6E63"
              >
                {table.schema_name}
              </Typography>
            )}
          </Box>

          <Chip
            label={
              isMongoDB
                ? "COLLECTION"
                : table?.table_type ||
                  "TABLE"
            }
            size="small"
            sx={{
              backgroundColor:
                "#E8D7A8",
              color:
                "#5D4037",
              fontWeight:
                "bold",
            }}
          />

          <Chip
            label={
              isMongoDB
                ? `${columns.length} fields`
                : `${columns.length} columns`
            }
            size="small"
            variant="outlined"
            sx={{
              borderColor:
                "#BCAAA4",
              color:
                "#6D4C41",
              fontWeight: 600,
            }}
          />
        </AccordionSummary>


        <AccordionDetails
          sx={{ p: 3 }}
        >

          {/* PRIMARY KEYS */}

          {primaryKeys.length >
            0 && (
            <Box sx={{ mb: 3 }}>
              <Typography
                fontWeight="bold"
                color="#6D4C41"
                sx={{ mb: 1 }}
              >
                Primary Key
              </Typography>

              <Stack
                direction="row"
                spacing={1}
                flexWrap="wrap"
              >
                {primaryKeys.map(
                  (key) => (
                    <Chip
                      key={key}
                      label={key}
                      size="small"
                      sx={{
                        backgroundColor:
                          "#E8F5E9",
                        color:
                          "#33691E",
                        fontWeight:
                          600,
                      }}
                    />
                  )
                )}
              </Stack>
            </Box>
          )}


          {/* FOREIGN KEYS */}

          {foreignKeys.length >
            0 && (
            <Box sx={{ mb: 3 }}>
              <Typography
                fontWeight="bold"
                color="#6D4C41"
                sx={{ mb: 1 }}
              >
                Foreign Keys
              </Typography>

              <Stack spacing={1}>
                {foreignKeys.map(
                  (
                    fk,
                    fkIndex
                  ) => (
                    <Box
                      key={`${fk?.column || "fk"}-${fkIndex}`}
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        backgroundColor:
                          "#FFF8E1",
                        border:
                          "1px solid #E6D5B8",
                      }}
                    >
                      <Typography
                        variant="body2"
                        color="#5D4037"
                      >
                        <strong>
                          {fk?.column ||
                            "Unknown"}
                        </strong>

                        {" → "}

                        {fk?.referenced_table ||
                          "Unknown"}
                        .
                        {fk?.referenced_column ||
                          "Unknown"}
                      </Typography>

                      {fk?.constraint_name && (
                        <Typography
                          variant="caption"
                          color="#8D6E63"
                        >
                          Constraint:{" "}
                          {
                            fk.constraint_name
                          }
                        </Typography>
                      )}
                    </Box>
                  )
                )}
              </Stack>
            </Box>
          )}


          {/* COLUMNS / FIELDS */}

          <Typography
            fontWeight="bold"
            color="#6D4C41"
            sx={{ mb: 1.5 }}
          >
            {isMongoDB
              ? "Fields"
              : "Columns"}
          </Typography>


          {columns.length ===
          0 ? (
            <Alert
              severity="info"
              sx={{
                backgroundColor:
                  "#FFF8E1",
                color:
                  "#6D4C41",
              }}
            >
              {isMongoDB
                ? "No fields were detected. This collection may be empty."
                : "No columns were detected."}
            </Alert>
          ) : (
            <TableContainer
              component={Paper}
              sx={{
                borderRadius: 2,
                border:
                  "1px solid #E0D0B5",
                boxShadow: "none",
                backgroundColor:
                  "#FFFDF2",
              }}
            >
              <Table
                size="small"
              >
                <TableHead>
                  <TableRow
                    sx={{
                      backgroundColor:
                        "#F4E8B8",
                    }}
                  >
                    <TableCell
                      sx={{
                        fontWeight:
                          "bold",
                        color:
                          "#5D4037",
                      }}
                    >
                      #
                    </TableCell>

                    <TableCell
                      sx={{
                        fontWeight:
                          "bold",
                        color:
                          "#5D4037",
                      }}
                    >
                      {isMongoDB
                        ? "Field"
                        : "Column"}
                    </TableCell>

                    <TableCell
                      sx={{
                        fontWeight:
                          "bold",
                        color:
                          "#5D4037",
                      }}
                    >
                      Data Type
                    </TableCell>

                    <TableCell
                      sx={{
                        fontWeight:
                          "bold",
                        color:
                          "#5D4037",
                      }}
                    >
                      Nullable
                    </TableCell>

                    <TableCell
                      sx={{
                        fontWeight:
                          "bold",
                        color:
                          "#5D4037",
                      }}
                    >
                      Key
                    </TableCell>

                    {!isMongoDB && (
                      <TableCell
                        sx={{
                          fontWeight:
                            "bold",
                          color:
                            "#5D4037",
                        }}
                      >
                        Auto Increment
                      </TableCell>
                    )}

                    <TableCell
                      sx={{
                        fontWeight:
                          "bold",
                        color:
                          "#5D4037",
                      }}
                    >
                      Constraints
                    </TableCell>
                  </TableRow>
                </TableHead>


                <TableBody>
                  {columns.map(
                    (
                      column,
                      columnIndex
                    ) => {
                      const columnConstraints =
                        Array.isArray(
                          column?.constraints
                        )
                          ? column.constraints
                          : [];

                      return (
                        <TableRow
                          key={`${column?.name || "column"}-${columnIndex}`}
                          hover
                        >
                          <TableCell>
                            {columnIndex +
                              1}
                          </TableCell>

                          <TableCell
                            sx={{
                              fontWeight:
                                600,
                              color:
                                "#5D4037",
                            }}
                          >
                            {column?.name ||
                              "-"}
                          </TableCell>

                          <TableCell>
                            <Chip
                              label={
                                column?.data_type ||
                                "unknown"
                              }
                              size="small"
                              variant="outlined"
                              sx={{
                                borderColor:
                                  "#BCAAA4",
                                color:
                                  "#6D4C41",
                              }}
                            />
                          </TableCell>

                          <TableCell>
                            {column?.nullable ===
                            false
                              ? "NO"
                              : "YES"}
                          </TableCell>

                          <TableCell>
                            {column?.primary_key ? (
                              <Chip
                                label="PRIMARY KEY"
                                size="small"
                                sx={{
                                  backgroundColor:
                                    "#E8F5E9",
                                  color:
                                    "#33691E",
                                  fontWeight:
                                    "bold",
                                }}
                              />
                            ) : (
                              "-"
                            )}
                          </TableCell>

                          {!isMongoDB && (
                            <TableCell>
                              {column?.auto_increment
                                ? "YES"
                                : "NO"}
                            </TableCell>
                          )}

                          <TableCell>
                            {columnConstraints.length >
                            0 ? (
                              <Stack
                                direction="row"
                                spacing={0.5}
                                flexWrap="wrap"
                                useFlexGap
                              >
                                {columnConstraints.map(
                                  (
                                    constraint,
                                    constraintIndex
                                  ) => (
                                    <Chip
                                      key={`${constraint}-${constraintIndex}`}
                                      label={
                                        constraint
                                      }
                                      size="small"
                                      sx={{
                                        mb:
                                          0.5,
                                        backgroundColor:
                                          "#F5EED7",
                                        color:
                                          "#6D4C41",
                                        fontSize:
                                          "0.72rem",
                                      }}
                                    />
                                  )
                                )}
                              </Stack>
                            ) : (
                              "-"
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    }
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          )}


          {/* INDEXES */}

          {indexes.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography
                fontWeight="bold"
                color="#6D4C41"
                sx={{ mb: 1.5 }}
              >
                Indexes
              </Typography>

              <TableContainer
                component={Paper}
                sx={{
                  borderRadius: 2,
                  border:
                    "1px solid #E0D0B5",
                  boxShadow: "none",
                  backgroundColor:
                    "#FFFDF2",
                }}
              >
                <Table size="small">
                  <TableHead>
                    <TableRow
                      sx={{
                        backgroundColor:
                          "#F4E8B8",
                      }}
                    >
                      <TableCell
                        sx={{
                          fontWeight:
                            "bold",
                          color:
                            "#5D4037",
                        }}
                      >
                        Index Name
                      </TableCell>

                      <TableCell
                        sx={{
                          fontWeight:
                            "bold",
                          color:
                            "#5D4037",
                        }}
                      >
                        Columns / Fields
                      </TableCell>

                      <TableCell
                        sx={{
                          fontWeight:
                            "bold",
                          color:
                            "#5D4037",
                        }}
                      >
                        Unique
                      </TableCell>
                    </TableRow>
                  </TableHead>

                  <TableBody>
                    {indexes.map(
                      (
                        indexData,
                        indexIndex
                      ) => (
                        <TableRow
                          key={`${indexData?.name || "index"}-${indexIndex}`}
                        >
                          <TableCell>
                            {indexData?.name ||
                              "-"}
                          </TableCell>

                          <TableCell>
                            {Array.isArray(
                              indexData?.columns
                            )
                              ? indexData.columns.join(
                                  ", "
                                )
                              : "-"}
                          </TableCell>

                          <TableCell>
                            {indexData?.unique
                              ? "YES"
                              : "NO"}
                          </TableCell>
                        </TableRow>
                      )
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}


          {/* CONSTRAINTS */}

          {constraints.length > 0 && (
            <Box sx={{ mt: 3 }}>
              <Typography
                fontWeight="bold"
                color="#6D4C41"
                sx={{ mb: 1.5 }}
              >
                Constraints
              </Typography>

              <Stack spacing={1}>
                {constraints.map(
                  (
                    constraint,
                    constraintIndex
                  ) => (
                    <Box
                      key={`${constraint?.name || "constraint"}-${constraintIndex}`}
                      sx={{
                        p: 1.5,
                        borderRadius: 2,
                        border:
                          "1px solid #E0D0B5",
                        backgroundColor:
                          "#FFF8E1",
                      }}
                    >
                      <Typography
                        variant="body2"
                        fontWeight="bold"
                        color="#5D4037"
                      >
                        {constraint?.name ||
                          "Unnamed constraint"}
                      </Typography>

                      <Typography
                        variant="body2"
                        color="#6D4C41"
                      >
                        Type:{" "}
                        {constraint?.constraint_type ||
                          "Unknown"}
                      </Typography>

                      {Array.isArray(
                        constraint?.columns
                      ) &&
                        constraint.columns
                          .length >
                          0 && (
                          <Typography
                            variant="body2"
                            color="#6D4C41"
                          >
                            Columns:{" "}
                            {constraint.columns.join(
                              ", "
                            )}
                          </Typography>
                        )}

                      {constraint?.definition && (
                        <Typography
                          variant="caption"
                          color="#8D6E63"
                        >
                          {
                            constraint.definition
                          }
                        </Typography>
                      )}
                    </Box>
                  )
                )}
              </Stack>
            </Box>
          )}

        </AccordionDetails>
      </Accordion>
    );
  };


  // ============================================================
  // VIEW CARD
  // ============================================================

  const renderView = (
    view,
    index
  ) => {
    const columns =
      Array.isArray(
        view?.columns
      )
        ? view.columns
        : [];

    return (
      <Accordion
        key={`${view?.name || "view"}-${index}`}
        sx={{
          mb: 2,
          borderRadius:
            "12px !important",
          overflow: "hidden",
          border:
            "1px solid #D7C29E",
          backgroundColor:
            "#FFFDF2",
          boxShadow: "none",

          "&:before": {
            display: "none",
          },
        }}
      >
        <AccordionSummary
          expandIcon={
            <ExpandMoreIcon
              sx={{
                color: "#6D4C41",
              }}
            />
          }
          sx={{
            px: 3,
            backgroundColor:
              "#FFF8D8",

            "& .MuiAccordionSummary-content":
              {
                alignItems:
                  "center",
                gap: 2,
              },
          }}
        >
          <ViewListIcon
            sx={{
              color: "#6D4C41",
            }}
          />

          <Box
            sx={{
              flexGrow: 1,
            }}
          >
            <Typography
              fontWeight="bold"
              color="#5D4037"
            >
              {view?.name ||
                "Unnamed View"}
            </Typography>

            {view?.schema_name && (
              <Typography
                variant="caption"
                color="#8D6E63"
              >
                {view.schema_name}
              </Typography>
            )}
          </Box>

          <Chip
            label="VIEW"
            size="small"
            sx={{
              backgroundColor:
                "#E8D7A8",
              color:
                "#5D4037",
              fontWeight:
                "bold",
            }}
          />

          <Chip
            label={`${columns.length} columns`}
            size="small"
            variant="outlined"
            sx={{
              borderColor:
                "#BCAAA4",
              color:
                "#6D4C41",
            }}
          />
        </AccordionSummary>

        <AccordionDetails
          sx={{ p: 3 }}
        >
          {columns.length ===
          0 ? (
            <Alert
              severity="info"
              sx={{
                backgroundColor:
                  "#FFF8E1",
                color:
                  "#6D4C41",
              }}
            >
              No columns were detected
              for this view.
            </Alert>
          ) : (
            <TableContainer
              component={Paper}
              sx={{
                borderRadius: 2,
                border:
                  "1px solid #E0D0B5",
                boxShadow: "none",
              }}
            >
              <Table size="small">
                <TableHead>
                  <TableRow
                    sx={{
                      backgroundColor:
                        "#F4E8B8",
                    }}
                  >
                    <TableCell
                      sx={{
                        fontWeight:
                          "bold",
                        color:
                          "#5D4037",
                      }}
                    >
                      #
                    </TableCell>

                    <TableCell
                      sx={{
                        fontWeight:
                          "bold",
                        color:
                          "#5D4037",
                      }}
                    >
                      Column
                    </TableCell>

                    <TableCell
                      sx={{
                        fontWeight:
                          "bold",
                        color:
                          "#5D4037",
                      }}
                    >
                      Data Type
                    </TableCell>
                  </TableRow>
                </TableHead>

                <TableBody>
                  {columns.map(
                    (
                      column,
                      columnIndex
                    ) => (
                      <TableRow
                        key={`${column?.name || "column"}-${columnIndex}`}
                      >
                        <TableCell>
                          {columnIndex +
                            1}
                        </TableCell>

                        <TableCell
                          sx={{
                            fontWeight:
                              600,
                            color:
                              "#5D4037",
                          }}
                        >
                          {column?.name ||
                            "-"}
                        </TableCell>

                        <TableCell>
                          {column?.data_type ||
                            "unknown"}
                        </TableCell>
                      </TableRow>
                    )
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </AccordionDetails>
      </Accordion>
    );
  };


  // ============================================================
  // LOADING
  // ============================================================

  if (loading) {
    return (
      <DashboardLayout>
        <Box
          sx={{
            minHeight:
              "70vh",
            display: "flex",
            justifyContent:
              "center",
            alignItems:
              "center",
            flexDirection:
              "column",
            gap: 2,
          }}
        >
          <CircularProgress
            sx={{
              color:
                "#6D4C41",
            }}
          />

          <Typography color="#6D4C41">
            Loading schema
            metadata...
          </Typography>
        </Box>
      </DashboardLayout>
    );
  }


  // ============================================================
  // MAIN UI
  // ============================================================

  return (
    <DashboardLayout>
      <Box
        sx={{
          minHeight: "100%",
          backgroundColor:
            "#FFFDF2",
          p: {
            xs: 2,
            md: 4,
          },
        }}
      >

        {/* HEADER */}

        <Box
          sx={{
            display: "flex",
            justifyContent:
              "space-between",
            alignItems: {
              xs: "flex-start",
              md: "center",
            },
            flexDirection: {
              xs: "column",
              md: "row",
            },
            gap: 2,
            mb: 3,
          }}
        >
          <Box>
            <Typography
              variant="h4"
              fontWeight="bold"
              color="#5D4037"
            >
              Schema Viewer
            </Typography>

            <Typography
              sx={{
                mt: 0.5,
                color:
                  "#8D6E63",
              }}
            >
              Explore your database
              structure, tables,
              collections, fields
              and relationships.
            </Typography>
          </Box>

          <Button
            variant="contained"
            startIcon={
              refreshing ? (
                <CircularProgress
                  size={18}
                  sx={{
                    color:
                      "#FFF",
                  }}
                />
              ) : (
                <RefreshIcon />
              )
            }
            onClick={
              handleRefresh
            }
            disabled={
              refreshing
            }
            sx={{
              backgroundColor:
                "#6D4C41",
              color: "#FFF",
              px: 2.5,
              py: 1.2,
              borderRadius: 2,
              fontWeight:
                "bold",

              "&:hover": {
                backgroundColor:
                  "#5D4037",
              },
            }}
          >
            {refreshing
              ? "Refreshing..."
              : "Refresh"}
          </Button>
        </Box>


        {/* DATABASE SELECTOR */}

        <Paper
          elevation={0}
          sx={{
            p: 3,
            mb: 3,
            borderRadius: 3,
            border:
              "1px solid #D7C29E",
            backgroundColor:
              "#FFF8D8",
          }}
        >
          <Stack
            direction={{
              xs: "column",
              md: "row",
            }}
            spacing={2}
            alignItems={{
              xs: "stretch",
              md: "center",
            }}
          >
            <Box
              sx={{
                flex: 1,
              }}
            >
              <Typography
                fontWeight="bold"
                color="#5D4037"
                sx={{ mb: 0.5 }}
              >
                Select Database
              </Typography>

              <Typography
                variant="body2"
                color="#8D6E63"
              >
                Choose which connected
                database metadata you want
                to view.
              </Typography>
            </Box>

            <TextField
              select
              value={
                selectedDatabaseType
              }
              onChange={
                handleDatabaseChange
              }
              sx={{
                minWidth: {
                  xs: "100%",
                  md: 220,
                },

                "& .MuiOutlinedInput-root":
                  {
                    backgroundColor:
                      "#FFFDF2",

                    "& fieldset": {
                      borderColor:
                        "#D7C29E",
                    },

                    "&:hover fieldset":
                      {
                        borderColor:
                          "#A1887F",
                      },

                    "&.Mui-focused fieldset":
                      {
                        borderColor:
                          "#6D4C41",
                      },
                  },
              }}
            >
              <MenuItem value="mongodb">
                MongoDB
              </MenuItem>

              <MenuItem value="postgresql">
                PostgreSQL
              </MenuItem>
            </TextField>
          </Stack>
        </Paper>


        {/* ERROR */}

        {error && (
          <Alert
            severity="error"
            sx={{
              mb: 3,
              borderRadius: 2,
            }}
          >
            {error}
          </Alert>
        )}


        {/* DATABASE SUMMARY */}

        <Paper
          elevation={0}
          sx={{
            p: 3,
            mb: 3,
            borderRadius: 3,
            border:
              "1px solid #D7C29E",
            backgroundColor:
              "#FFF8D8",
          }}
        >
          <Stack
            direction={{
              xs: "column",
              sm: "row",
            }}
            spacing={3}
            divider={
              <Divider
                orientation="vertical"
                flexItem
                sx={{
                  display: {
                    xs: "none",
                    sm: "block",
                  },
                }}
              />
            }
          >

            <Box sx={{ flex: 1 }}>
              <Stack
                direction="row"
                spacing={1}
                alignItems="center"
                sx={{ mb: 0.5 }}
              >
                <StorageIcon
                  sx={{
                    color:
                      "#6D4C41",
                  }}
                />

                <Typography
                  variant="body2"
                  color="#8D6E63"
                >
                  Database
                </Typography>
              </Stack>

              <Typography
                fontWeight="bold"
                color="#5D4037"
                sx={{
                  wordBreak:
                    "break-word",
                }}
              >
                {metadata.database_name ||
                  "Unknown"}
              </Typography>
            </Box>


            <Box sx={{ flex: 1 }}>
              <Typography
                variant="body2"
                color="#8D6E63"
                sx={{ mb: 0.5 }}
              >
                Database Type
              </Typography>

              <Chip
                label={
                  databaseTypeDisplay
                }
                sx={{
                  backgroundColor:
                    "#6D4C41",
                  color: "#FFF",
                  fontWeight:
                    "bold",
                }}
              />
            </Box>


            <Box sx={{ flex: 1 }}>
              <Typography
                variant="body2"
                color="#8D6E63"
                sx={{ mb: 0.5 }}
              >
                {isMongoDB
                  ? "Collections"
                  : "Tables"}
              </Typography>

              <Typography
                variant="h5"
                fontWeight="bold"
                color="#5D4037"
              >
                {tables.length}
              </Typography>
            </Box>


            <Box sx={{ flex: 1 }}>
              <Typography
                variant="body2"
                color="#8D6E63"
                sx={{ mb: 0.5 }}
              >
                Views
              </Typography>

              <Typography
                variant="h5"
                fontWeight="bold"
                color="#5D4037"
              >
                {views.length}
              </Typography>
            </Box>


            <Box sx={{ flex: 1 }}>
              <Typography
                variant="body2"
                color="#8D6E63"
                sx={{ mb: 0.5 }}
              >
                {isMongoDB
                  ? "Fields"
                  : "Columns"}
              </Typography>

              <Typography
                variant="h5"
                fontWeight="bold"
                color="#5D4037"
              >
                {totalColumns}
              </Typography>
            </Box>


            <Box sx={{ flex: 1 }}>
              <Typography
                variant="body2"
                color="#8D6E63"
                sx={{ mb: 0.5 }}
              >
                Indexes
              </Typography>

              <Typography
                variant="h5"
                fontWeight="bold"
                color="#5D4037"
              >
                {totalIndexes}
              </Typography>
            </Box>

          </Stack>
        </Paper>


        {/* SEARCH */}

        <Paper
          elevation={0}
          sx={{
            p: 2,
            mb: 3,
            borderRadius: 3,
            border:
              "1px solid #D7C29E",
            backgroundColor:
              "#FFFDF2",
          }}
        >
          <TextField
            fullWidth
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value
              )
            }
            placeholder={
              isMongoDB
                ? "Search collections, fields or data types..."
                : "Search tables, columns or data types..."
            }
            InputProps={{
              startAdornment: (
                <SearchIcon
                  sx={{
                    color:
                      "#8D6E63",
                    mr: 1,
                  }}
                />
              ),
            }}
            sx={{
              "& .MuiOutlinedInput-root":
                {
                  borderRadius: 2,

                  "& fieldset": {
                    borderColor:
                      "#D7C29E",
                  },

                  "&:hover fieldset":
                    {
                      borderColor:
                        "#A1887F",
                    },

                  "&.Mui-focused fieldset":
                    {
                      borderColor:
                        "#6D4C41",
                    },
                },
            }}
          />
        </Paper>


        {/* TABLES / COLLECTIONS */}

        <Box sx={{ mb: 4 }}>
          <Stack
            direction="row"
            spacing={1}
            alignItems="center"
            sx={{ mb: 2 }}
          >
            {isMongoDB ? (
              <StorageIcon
                sx={{
                  color:
                    "#6D4C41",
                }}
              />
            ) : (
              <TableChartIcon
                sx={{
                  color:
                    "#6D4C41",
                }}
              />
            )}

            <Typography
              variant="h5"
              fontWeight="bold"
              color="#5D4037"
            >
              {isMongoDB
                ? "Collections"
                : "Tables"}
            </Typography>

            <Chip
              label={
                filteredTables.length
              }
              size="small"
              sx={{
                backgroundColor:
                  "#E8D7A8",
                color:
                  "#5D4037",
                fontWeight:
                  "bold",
              }}
            />
          </Stack>


          {filteredTables.length ===
          0 ? (
            <Paper
              elevation={0}
              sx={{
                p: 5,
                textAlign:
                  "center",
                borderRadius: 3,
                border:
                  "1px dashed #D7C29E",
                backgroundColor:
                  "#FFFDF2",
              }}
            >
              <ViewColumnIcon
                sx={{
                  fontSize: 45,
                  color:
                    "#BCAAA4",
                  mb: 1,
                }}
              />

              <Typography
                fontWeight="bold"
                color="#6D4C41"
              >
                {search
                  ? "No matching results found"
                  : isMongoDB
                  ? "No collections found"
                  : "No tables found"}
              </Typography>

              <Typography
                variant="body2"
                color="#8D6E63"
                sx={{ mt: 0.5 }}
              >
                {search
                  ? "Try a different search term."
                  : isMongoDB
                  ? "The selected MongoDB database does not contain any collections."
                  : "No database tables are available."}
              </Typography>
            </Paper>
          ) : (
            filteredTables.map(
              renderTable
            )
          )}
        </Box>


        {/* VIEWS */}

        {views.length > 0 && (
          <Box>
            <Stack
              direction="row"
              spacing={1}
              alignItems="center"
              sx={{ mb: 2 }}
            >
              <ViewListIcon
                sx={{
                  color:
                    "#6D4C41",
                }}
              />

              <Typography
                variant="h5"
                fontWeight="bold"
                color="#5D4037"
              >
                Views
              </Typography>

              <Chip
                label={
                  filteredViews.length
                }
                size="small"
                sx={{
                  backgroundColor:
                    "#E8D7A8",
                  color:
                    "#5D4037",
                  fontWeight:
                    "bold",
                }}
              />
            </Stack>


            {filteredViews.length ===
            0 ? (
              <Alert
                severity="info"
                sx={{
                  backgroundColor:
                    "#FFF8E1",
                  color:
                    "#6D4C41",
                }}
              >
                No matching views
                found.
              </Alert>
            ) : (
              filteredViews.map(
                renderView
              )
            )}
          </Box>
        )}

      </Box>
    </DashboardLayout>
  );
}

export default SchemaViewer;