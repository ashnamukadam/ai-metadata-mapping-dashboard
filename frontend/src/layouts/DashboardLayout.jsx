import { Box } from "@mui/material";
import Sidebar from "../components/Sidebar";
import Header from "../components/Header";

function DashboardLayout({ children }) {
  return (
    <Box
      sx={{
        display: "flex",
        minHeight: "100vh",
        bgcolor: "#FFF8DC", // Butter Yellow
      }}
    >
      {/* Sidebar */}
      <Sidebar />

      {/* Right Side */}
      <Box
        sx={{
          flexGrow: 1,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Header */}
        <Header />

        {/* Main Content */}
        <Box
          sx={{
            flexGrow: 1,
            p: 4,
          }}
        >
          {children}
        </Box>
      </Box>
    </Box>
  );
}

export default DashboardLayout;