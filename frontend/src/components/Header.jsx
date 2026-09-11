import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Avatar,
  IconButton,
  Tooltip,
} from "@mui/material";

import NotificationsNoneIcon from "@mui/icons-material/NotificationsNone";
import AccountCircleIcon from "@mui/icons-material/AccountCircle";

function Header() {
  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        bgcolor: "#FFFDF2",
        color: "#6D4C41",
        borderBottom: "2px solid #E6D5A8",
      }}
    >
      <Toolbar
        sx={{
          display: "flex",
          justifyContent: "space-between",
          minHeight: 80,
          px: 4,
        }}
      >
        {/* Left Side */}
        <Box>
          <Typography
            variant="h5"
            sx={{
              fontWeight: 700,
              color: "#6D4C41",
            }}
          >
            AI Metadata Mapping Dashboard
          </Typography>

          <Typography
            variant="body2"
            sx={{
              color: "#8D6E63",
              mt: 0.5,
            }}
          >
            Welcome back 👋
          </Typography>
        </Box>

        {/* Right Side */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 2,
          }}
        >
          <Tooltip title="Notifications">
            <IconButton
              sx={{
                bgcolor: "#FFF3CD",
                "&:hover": {
                  bgcolor: "#E9D5B5",
                },
              }}
            >
              <NotificationsNoneIcon sx={{ color: "#6D4C41" }} />
            </IconButton>
          </Tooltip>

          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1.5,
            }}
          >
            <Avatar
              sx={{
                bgcolor: "#8B5E3C",
                width: 42,
                height: 42,
              }}
            >
              <AccountCircleIcon />
            </Avatar>

            <Box>
              <Typography
                sx={{
                  fontWeight: 600,
                  color: "#6D4C41",
                  lineHeight: 1.2,
                }}
              >
                Numa
              </Typography>

              <Typography
                variant="caption"
                sx={{
                  color: "#8D6E63",
                }}
              >
                Administrator
              </Typography>
            </Box>
          </Box>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default Header;