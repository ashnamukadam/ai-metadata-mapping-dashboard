import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

import {
  Box,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Button,
  Collapse,
} from "@mui/material";

import DashboardIcon from "@mui/icons-material/Dashboard";
import StorageIcon from "@mui/icons-material/Storage";
import SchemaIcon from "@mui/icons-material/Schema";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import SettingsIcon from "@mui/icons-material/Settings";
import LogoutIcon from "@mui/icons-material/Logout";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import StorageRoundedIcon from "@mui/icons-material/StorageRounded";

function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const [databaseOpen, setDatabaseOpen] = useState(
    location.pathname === "/connect-database" ||
    location.pathname === "/mongodb"
  );

  const menuItems = [
    {
      text: "Dashboard",
      icon: <DashboardIcon />,
      path: "/dashboard",
    },
    {
      text: "Schema Viewer",
      icon: <SchemaIcon />,
      path: "/schema-viewer",
    },
    {
      text: "Relationships",
      icon: <AccountTreeIcon />,
      path: "/relationships",
    },
    {
      text: "Metadata Mapping",
      icon: <AutoAwesomeIcon />,
      path: "/metadata-mapping",
    },
    {
      text: "Settings",
      icon: <SettingsIcon />,
      path: "/settings",
    },
  ];

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  return (
    <Box
      sx={{
        width: 300,
        minHeight: "100vh",
        bgcolor: "#FFF3CD",
        borderRight: "1px solid #E6D9A8",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {/* =========================================
          LOGO / TITLE
      ========================================= */}
      <Box
        sx={{
          px: 3,
          py: 3,
          textAlign: "center",
        }}
      >
        <Typography
          variant="h5"
          fontWeight="bold"
          sx={{
            color: "#6D4C41",
            letterSpacing: 0.5,
          }}
        >
          AI Metadata
        </Typography>

        <Typography
          variant="body2"
          sx={{
            color: "#795548",
            mt: 0.5,
          }}
        >
          Mapping Dashboard
        </Typography>
      </Box>

      <Divider sx={{ borderColor: "#E6D9A8" }} />

      {/* =========================================
          MENU
      ========================================= */}
      <List sx={{ px: 1.5, py: 2 }}>

        {/* DASHBOARD */}
        <ListItemButton
          onClick={() => navigate("/dashboard")}
          selected={location.pathname === "/dashboard"}
          sx={{
            borderRadius: 2,
            mb: 0.8,
            minHeight: 48,

            color: "#6D4C41",

            "& .MuiListItemIcon-root": {
              color: "#6D4C41",
              minWidth: 42,
            },

            "&.Mui-selected": {
              bgcolor: "#D7B899",
              color: "#5D4037",
              fontWeight: "bold",

              "& .MuiListItemIcon-root": {
                color: "#5D4037",
              },
            },

            "&.Mui-selected:hover": {
              bgcolor: "#D7B899",
            },

            "&:hover": {
              bgcolor: "#E9D5B5",
            },
          }}
        >
          <ListItemIcon>
            <DashboardIcon />
          </ListItemIcon>

          <ListItemText
            primary="Dashboard"
            primaryTypographyProps={{
              fontSize: 15,
              fontWeight: location.pathname === "/dashboard" ? 700 : 500,
            }}
          />
        </ListItemButton>


        {/* =========================================
            CONNECT DATABASE
        ========================================= */}
        <ListItemButton
          onClick={() => setDatabaseOpen(!databaseOpen)}
          sx={{
            borderRadius: 2,
            mb: 0.5,
            minHeight: 48,

            color: "#6D4C41",

            "& .MuiListItemIcon-root": {
              color: "#6D4C41",
              minWidth: 42,
            },

            "&:hover": {
              bgcolor: "#E9D5B5",
            },
          }}
        >
          <ListItemIcon>
            <StorageIcon />
          </ListItemIcon>

          <ListItemText
            primary="Connect Database"
            primaryTypographyProps={{
              fontSize: 15,
              fontWeight: 600,
              whiteSpace: "nowrap",
            }}
          />

          {databaseOpen ? (
            <ExpandLessIcon sx={{ color: "#6D4C41" }} />
          ) : (
            <ExpandMoreIcon sx={{ color: "#6D4C41" }} />
          )}
        </ListItemButton>


        {/* =========================================
            DATABASE SUBMENU
        ========================================= */}
        <Collapse in={databaseOpen} timeout="auto" unmountOnExit>
          <List component="div" disablePadding>

            {/* POSTGRESQL */}
            <ListItemButton
              onClick={() => navigate("/connect-database")}
              selected={location.pathname === "/connect-database"}
              sx={{
                ml: 2,
                mr: 1,
                mb: 0.5,
                borderRadius: 2,
                minHeight: 44,

                color: "#795548",

                "& .MuiListItemIcon-root": {
                  color: "#795548",
                  minWidth: 38,
                },

                "&.Mui-selected": {
                  bgcolor: "#D7B899",
                  color: "#5D4037",
                  fontWeight: "bold",

                  "& .MuiListItemIcon-root": {
                    color: "#5D4037",
                  },
                },

                "&.Mui-selected:hover": {
                  bgcolor: "#D7B899",
                },

                "&:hover": {
                  bgcolor: "#E9D5B5",
                },
              }}
            >
              <ListItemIcon>
                <StorageRoundedIcon fontSize="small" />
              </ListItemIcon>

              <ListItemText
                primary="PostgreSQL"
                primaryTypographyProps={{
                  fontSize: 14,
                  fontWeight:
                    location.pathname === "/connect-database"
                      ? 700
                      : 500,
                }}
              />
            </ListItemButton>


            {/* MONGODB */}
            <ListItemButton
              onClick={() => navigate("/mongodb")}
              selected={location.pathname === "/mongodb"}
              sx={{
                ml: 2,
                mr: 1,
                mb: 0.8,
                borderRadius: 2,
                minHeight: 44,

                color: "#795548",

                "& .MuiListItemIcon-root": {
                  color: "#795548",
                  minWidth: 38,
                },

                "&.Mui-selected": {
                  bgcolor: "#D7B899",
                  color: "#5D4037",
                  fontWeight: "bold",

                  "& .MuiListItemIcon-root": {
                    color: "#5D4037",
                  },
                },

                "&.Mui-selected:hover": {
                  bgcolor: "#D7B899",
                },

                "&:hover": {
                  bgcolor: "#E9D5B5",
                },
              }}
            >
              <ListItemIcon>
                <StorageRoundedIcon fontSize="small" />
              </ListItemIcon>

              <ListItemText
                primary="MongoDB"
                primaryTypographyProps={{
                  fontSize: 14,
                  fontWeight:
                    location.pathname === "/mongodb"
                      ? 700
                      : 500,
                }}
              />
            </ListItemButton>

          </List>
        </Collapse>


        {/* =========================================
            OTHER MENU ITEMS
        ========================================= */}
        {menuItems.slice(1).map((item) => {
          const isSelected = location.pathname === item.path;

          return (
            <ListItemButton
              key={item.text}
              onClick={() => navigate(item.path)}
              selected={isSelected}
              sx={{
                borderRadius: 2,
                mb: 0.8,
                minHeight: 48,

                color: "#6D4C41",

                "& .MuiListItemIcon-root": {
                  color: "#6D4C41",
                  minWidth: 42,
                },

                "&.Mui-selected": {
                  bgcolor: "#D7B899",
                  color: "#5D4037",
                  fontWeight: "bold",

                  "& .MuiListItemIcon-root": {
                    color: "#5D4037",
                  },
                },

                "&.Mui-selected:hover": {
                  bgcolor: "#D7B899",
                },

                "&:hover": {
                  bgcolor: "#E9D5B5",
                },
              }}
            >
              <ListItemIcon>
                {item.icon}
              </ListItemIcon>

              <ListItemText
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: 15,
                  fontWeight: isSelected ? 700 : 500,
                  whiteSpace: "nowrap",
                }}
              />
            </ListItemButton>
          );
        })}
      </List>


      {/* =========================================
          SPACER
      ========================================= */}
      <Box sx={{ flexGrow: 1 }} />

      <Divider sx={{ borderColor: "#E6D9A8" }} />


      {/* =========================================
          LOGOUT
      ========================================= */}
      <Box sx={{ p: 2 }}>
        <Button
          fullWidth
          variant="outlined"
          startIcon={<LogoutIcon />}
          onClick={handleLogout}
          sx={{
            color: "#6D4C41",
            borderColor: "#BCAAA4",
            borderRadius: 2,
            py: 1.2,
            textTransform: "none",
            fontWeight: 600,

            "&:hover": {
              borderColor: "#6D4C41",
              bgcolor: "#E9D5B5",
            },
          }}
        >
          Logout
        </Button>
      </Box>
    </Box>
  );
}

export default Sidebar;