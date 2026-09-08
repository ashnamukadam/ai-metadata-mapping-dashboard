import { useState } from "react";
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Typography,
  Link,
  Alert,
} from "@mui/material";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { registerUser } from "../services/authService";

function Register() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleRegister = async () => {
    try {
      setLoading(true);
      setMessage("");
      setError("");

      await registerUser(formData);

      setMessage("Registration Successful!");

      setTimeout(() => {
        navigate("/login");
      }, 1500);
    } catch (err) {
      console.error(err);

      setError(
        err.response?.data?.detail ||
          "Registration Failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        bgcolor: "background.default",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        p: 3,
      }}
    >
      <Card
        sx={{
          width: 450,
          borderRadius: 4,
          boxShadow: 6,
        }}
      >
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h4" align="center" gutterBottom>
            Create Account
          </Typography>

          <Typography align="center" color="text.secondary" mb={4}>
            Join AI Metadata Mapping Dashboard
          </Typography>

          <TextField
            fullWidth
            label="Full Name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            margin="normal"
          />

          <TextField
            fullWidth
            label="Email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            margin="normal"
          />

          <TextField
            fullWidth
            label="Password"
            name="password"
            type="password"
            value={formData.password}
            onChange={handleChange}
            margin="normal"
          />

          {message && (
            <Alert severity="success" sx={{ mt: 2 }}>
              {message}
            </Alert>
          )}

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}

          <Button
            fullWidth
            variant="contained"
            sx={{
              mt: 3,
              py: 1.5,
            }}
            onClick={handleRegister}
            disabled={loading}
          >
            {loading ? "Registering..." : "Register"}
          </Button>

          <Typography align="center" mt={3}>
            Already have an account?{" "}
            <Link component={RouterLink} to="/login">
              Login
            </Link>
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
}

export default Register;