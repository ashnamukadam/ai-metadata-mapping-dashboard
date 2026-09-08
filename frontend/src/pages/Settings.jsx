import { useState } from "react";

import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Divider,
  Alert,
} from "@mui/material";

import DashboardLayout from "../layouts/DashboardLayout";

function Settings() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");

  const handleSave = () => {
    setMessage("Settings saved successfully.");
  };

  return (
    <DashboardLayout>
      <Box
        sx={{
          minHeight: "100vh",
          backgroundColor: "#FFF8D6",
          p: { xs: 2, md: 4 },
        }}
      >
        <Typography
          variant="h4"
          sx={{
            color: "#6D4C41",
            fontWeight: "bold",
            mb: 1,
          }}
        >
          Settings
        </Typography>

        <Typography
          sx={{
            color: "#795548",
            mb: 3,
          }}
        >
          Manage your dashboard settings and account information.
        </Typography>

        <Paper
          elevation={0}
          sx={{
            maxWidth: 700,
            p: 4,
            borderRadius: 3,
            backgroundColor: "#FFFDF2",
            border: "1px solid #E6D9A8",
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
            Account Settings
          </Typography>

          <Divider sx={{ mb: 3 }} />

          <TextField
            fullWidth
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            margin="normal"
          />

          <TextField
            fullWidth
            label="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            margin="normal"
          />

          {message && (
            <Alert
              severity="success"
              sx={{ mt: 2 }}
            >
              {message}
            </Alert>
          )}

          <Button
            variant="contained"
            onClick={handleSave}
            sx={{
              mt: 3,
              backgroundColor: "#6D4C41",
              "&:hover": {
                backgroundColor: "#5D4037",
              },
            }}
          >
            Save Settings
          </Button>
        </Paper>
      </Box>
    </DashboardLayout>
  );
}

export default Settings;