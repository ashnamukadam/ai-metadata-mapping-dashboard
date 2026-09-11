import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  Box,
  Grid,
  Paper,
  Typography,
  Button,
} from "@mui/material";

import api from "../services/api";


function Dashboard() {
  const navigate = useNavigate();

  const [stats, setStats] = useState({
    databases: 0,
    schemas: 0,
    tables: 0,
    mapped_tables: 0,
    columns: 0,
    views: 0,
    relationships: 0,
    last_mapping_date: null,
  });

  const [loading, setLoading] = useState(true);


  // ============================================================
  // FETCH DASHBOARD STATS
  // ============================================================

  useEffect(() => {
    const fetchDashboardStats = async () => {
      const token = localStorage.getItem("token");

      if (!token) {
        navigate("/login");
        return;
      }

      try {
        const response = await api.get(
          "/dashboard/stats",
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        console.log(
          "Dashboard Stats:",
          response.data
        );

        setStats({
          databases:
            response.data.databases || 0,

          schemas:
            response.data.schemas || 0,

          tables:
            response.data.tables || 0,

          mapped_tables:
            response.data.mapped_tables || 0,

          columns:
            response.data.columns || 0,

          views:
            response.data.views || 0,

          relationships:
            response.data.relationships || 0,

          last_mapping_date:
            response.data.last_mapping_date || null,
        });

      } catch (error) {
        console.error(
          "Failed to fetch dashboard stats:",
          error
        );

        if (
          error.response?.status === 401
        ) {
          localStorage.removeItem("token");
          navigate("/login");
        }

      } finally {
        setLoading(false);
      }
    };

    fetchDashboardStats();
  }, [navigate]);


  // ============================================================
  // FORMAT LAST MAPPING DATE
  // ============================================================

  const formatLastMappingDate = () => {
    if (!stats.last_mapping_date) {
      return "No mappings yet";
    }

    const date = new Date(
      stats.last_mapping_date
    );

    if (Number.isNaN(date.getTime())) {
      return "No mappings yet";
    }

    return date.toLocaleString();
  };


  // ============================================================
  // STATISTICS CARDS
  // ============================================================

  const statCards = [
    {
      title: "Databases",
      value: stats.databases,
    },
    {
      title: "Schemas",
      value: stats.schemas,
    },
    {
      title: "Tables",
      value: stats.tables,
    },
    {
      title: "Mapped Tables",
      value: stats.mapped_tables,
    },
    {
      title: "Columns",
      value: stats.columns,
    },
    {
      title: "Views",
      value: stats.views,
    },
    {
      title: "Relationships",
      value: stats.relationships,
    },
  ];


  // ============================================================
  // MAIN DASHBOARD
  // ============================================================

  return (
    <Box
      sx={{
        minHeight: "100vh",
        backgroundColor: "#FFF8D6",

        p: {
          xs: 2,
          sm: 3,
          md: 4,
        },
      }}
    >

      {/* ================================================== */}
      {/* HEADER */}
      {/* ================================================== */}

      <Box
        sx={{
          display: "flex",

          justifyContent:
            "space-between",

          alignItems: {
            xs: "flex-start",
            sm: "center",
          },

          flexDirection: {
            xs: "column",
            sm: "row",
          },

          gap: 2,
          mb: 4,
        }}
      >

        <Box>

          <Typography
            variant="h4"
            sx={{
              fontWeight: "bold",
              color: "#6D4C41",

              fontSize: {
                xs: "28px",
                sm: "32px",
                md: "36px",
              },
            }}
          >
            AI Metadata Mapping Dashboard
          </Typography>


          <Typography
            variant="body1"
            sx={{
              color: "#795548",
              mt: 1,
            }}
          >
            Overview of your database metadata
          </Typography>

        </Box>


        <Button
          variant="contained"
          onClick={() =>
            navigate(
              "/connect-database"
            )
          }
          sx={{
            backgroundColor: "#6D4C41",

            "&:hover": {
              backgroundColor: "#5D4037",
            },

            borderRadius: 2,
            px: 3,
            py: 1.2,

            whiteSpace: "nowrap",
          }}
        >
          Connect New Database
        </Button>

      </Box>


      {/* ================================================== */}
      {/* DATABASE STATUS */}
      {/* ================================================== */}

      <Paper
        elevation={0}
        sx={{
          p: 3,
          mb: 4,

          borderRadius: 3,

          backgroundColor: "#FFFDF2",

          border:
            "1px solid #E6D9A8",
        }}
      >

        <Typography
          variant="h6"
          sx={{
            fontWeight: "bold",
            color: "#6D4C41",
            mb: 1,
          }}
        >
          Database Status
        </Typography>


        <Typography
          variant="body1"
          sx={{
            color:
              stats.databases > 0
                ? "#4E6B50"
                : "#A94442",

            fontWeight: "bold",
          }}
        >
          {stats.databases > 0
            ? "● Database Connected"
            : "● No Database Connected"}
        </Typography>

      </Paper>


      {/* ================================================== */}
      {/* MAPPING SUMMARY */}
      {/* ================================================== */}

      <Grid
        container
        spacing={3}
        sx={{ mb: 4 }}
      >

        {/* LAST MAPPING DATE */}

        <Grid
          item
          xs={12}
          md={6}
        >

          <Paper
            elevation={0}
            sx={{
              p: 3,

              borderRadius: 3,

              backgroundColor:
                "#FFFDF2",

              border:
                "1px solid #E6D9A8",

              minHeight: 140,

              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
            }}
          >

            <Typography
              variant="body1"
              sx={{
                color: "#795548",
                fontWeight: 600,
                mb: 1,
              }}
            >
              Last Mapping Date
            </Typography>


            <Typography
              variant="h5"
              sx={{
                color: "#6D4C41",
                fontWeight: "bold",
              }}
            >
              {loading
                ? "..."
                : formatLastMappingDate()}
            </Typography>

          </Paper>

        </Grid>


        {/* MAPPING PROGRESS */}

        <Grid
          item
          xs={12}
          md={6}
        >

          <Paper
            elevation={0}
            sx={{
              p: 3,

              borderRadius: 3,

              backgroundColor:
                "#FFFDF2",

              border:
                "1px solid #E6D9A8",

              minHeight: 140,

              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
            }}
          >

            <Typography
              variant="body1"
              sx={{
                color: "#795548",
                fontWeight: 600,
                mb: 1,
              }}
            >
              Mapping Progress
            </Typography>


            <Typography
              variant="h5"
              sx={{
                color: "#6D4C41",
                fontWeight: "bold",
              }}
            >
              {loading
                ? "..."
                : `${stats.mapped_tables} / ${stats.tables} Tables Mapped`}
            </Typography>

          </Paper>

        </Grid>

      </Grid>


      {/* ================================================== */}
      {/* STATISTICS CARDS */}
      {/* ================================================== */}

      <Grid
        container
        spacing={3}
      >

        {statCards.map((card) => (

          <Grid
            item
            xs={12}
            sm={6}
            md={4}
            key={card.title}
          >

            <Paper
              elevation={0}
              sx={{
                p: 3,

                borderRadius: 3,

                backgroundColor:
                  "#FFFDF2",

                border:
                  "1px solid #E6D9A8",

                minHeight: 140,

                display: "flex",
                flexDirection:
                  "column",

                justifyContent:
                  "center",

                transition: "0.2s",

                "&:hover": {
                  transform:
                    "translateY(-3px)",

                  boxShadow:
                    "0 6px 15px rgba(109, 76, 65, 0.12)",
                },
              }}
            >

              <Typography
                variant="body1"
                sx={{
                  color: "#795548",
                  fontWeight: 600,
                  mb: 1,
                }}
              >
                {card.title}
              </Typography>


              <Typography
                variant="h3"
                sx={{
                  color: "#6D4C41",
                  fontWeight: "bold",
                }}
              >
                {loading
                  ? "..."
                  : card.value}
              </Typography>

            </Paper>

          </Grid>

        ))}

      </Grid>


      {/* ================================================== */}
      {/* QUICK ACTIONS */}
      {/* ================================================== */}

      <Paper
        elevation={0}
        sx={{
          p: 3,
          mt: 4,

          borderRadius: 3,

          backgroundColor:
            "#FFFDF2",

          border:
            "1px solid #E6D9A8",
        }}
      >

        <Typography
          variant="h6"
          sx={{
            color: "#6D4C41",
            fontWeight: "bold",
            mb: 2,
          }}
        >
          Quick Actions
        </Typography>


        <Box
          sx={{
            display: "flex",
            gap: 2,

            flexWrap: "wrap",

            alignItems:
              "center",
          }}
        >

          {/* CONNECT NEW DATABASE */}

          <Button
            variant="contained"
            onClick={() =>
              navigate(
                "/connect-database"
              )
            }
            sx={{
              backgroundColor:
                "#6D4C41",

              "&:hover": {
                backgroundColor:
                  "#5D4037",
              },

              borderRadius: 2,

              px: 3,
              py: 1.2,

              minWidth: 180,

              whiteSpace:
                "nowrap",
            }}
          >
            Connect New Database
          </Button>


          {/* VIEW EXISTING MAPPINGS */}

          <Button
            variant="outlined"
            onClick={() =>
              navigate(
                "/metadata-mapping"
              )
            }
            sx={{
              color: "#6D4C41",

              borderColor:
                "#6D4C41",

              borderRadius: 2,

              px: 3,
              py: 1.2,

              minWidth: 190,

              whiteSpace:
                "nowrap",

              "&:hover": {
                borderColor:
                  "#5D4037",

                backgroundColor:
                  "#FFF8D6",
              },
            }}
          >
            View Existing Mappings
          </Button>


          {/* EXPORT MAPPING */}

          <Button
            variant="outlined"
            onClick={() =>
              navigate(
                "/metadata-mapping"
              )
            }
            sx={{
              color: "#6D4C41",

              borderColor:
                "#6D4C41",

              borderRadius: 2,

              px: 3,
              py: 1.2,

              minWidth: 160,

              whiteSpace:
                "nowrap",

              "&:hover": {
                borderColor:
                  "#5D4037",

                backgroundColor:
                  "#FFF8D6",
              },
            }}
          >
            Export Mapping
          </Button>


          {/* VIEW SCHEMA */}

          <Button
            variant="outlined"
            onClick={() =>
              navigate(
                "/schema-viewer"
              )
            }
            sx={{
              color: "#6D4C41",

              borderColor:
                "#6D4C41",

              borderRadius: 2,

              px: 3,
              py: 1.2,

              minWidth: 140,

              whiteSpace:
                "nowrap",

              "&:hover": {
                borderColor:
                  "#5D4037",

                backgroundColor:
                  "#FFF8D6",
              },
            }}
          >
            View Schema
          </Button>


          {/* EXTRACT METADATA */}

          <Button
            variant="outlined"
            onClick={() =>
              navigate(
                "/connect-database"
              )
            }
            sx={{
              color: "#6D4C41",

              borderColor:
                "#6D4C41",

              borderRadius: 2,

              px: 3,
              py: 1.2,

              minWidth: 170,

              whiteSpace:
                "nowrap",

              "&:hover": {
                borderColor:
                  "#5D4037",

                backgroundColor:
                  "#FFF8D6",
              },
            }}
          >
            Extract Metadata
          </Button>


          {/* VIEW RELATIONSHIPS */}

          <Button
            variant="outlined"
            onClick={() =>
              navigate(
                "/relationships"
              )
            }
            sx={{
              color: "#6D4C41",

              borderColor:
                "#6D4C41",

              borderRadius: 2,

              px: 3,
              py: 1.2,

              minWidth: 180,

              whiteSpace:
                "nowrap",

              "&:hover": {
                borderColor:
                  "#5D4037",

                backgroundColor:
                  "#FFF8D6",
              },
            }}
          >
            View Relationships
          </Button>

        </Box>

      </Paper>

    </Box>
  );
}


export default Dashboard;