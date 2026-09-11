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

import {
  Link as RouterLink,
  useNavigate,
} from "react-router-dom";

import {
  loginUser,
  forgotPassword,
} from "../services/authService";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const [loading, setLoading] = useState(false);

  // Forgot Password state
  const [showForgotPassword, setShowForgotPassword] =
    useState(false);

  const [newPassword, setNewPassword] = useState("");
  const [resetLoading, setResetLoading] = useState(false);

  // =========================
  // LOGIN
  // =========================

  const handleLogin = async (event) => {
    event.preventDefault();

    console.log("1. LOGIN FUNCTION STARTED");
    console.log("Email:", email);

    setError("");
    setSuccess("");
    setLoading(true);

    try {
      console.log("2. CALLING loginUser()");

      const response = await loginUser(email, password);

      console.log("3. LOGIN RESPONSE:", response);

      localStorage.setItem(
        "token",
        response.access_token
      );

      console.log("4. TOKEN SAVED");

      setSuccess("Login Successful!");

      setTimeout(() => {
        console.log("5. NAVIGATING TO DASHBOARD");
        navigate("/dashboard");
      }, 800);
    } catch (err) {
      console.error("LOGIN ERROR:", err);

      const message =
        err?.response?.data?.detail ||
        err?.message ||
        "Login Failed";

      setError(String(message));
    } finally {
      console.log("6. LOGIN FINISHED");
      setLoading(false);
    }
  };

  // =========================
  // FORGOT PASSWORD
  // =========================

  const handleForgotPassword = async (event) => {
    event.preventDefault();

    setError("");
    setSuccess("");

    if (!email) {
      setError("Please enter your email address.");
      return;
    }

    if (!newPassword) {
      setError("Please enter a new password.");
      return;
    }

    if (newPassword.length < 6) {
      setError(
        "New password must be at least 6 characters."
      );
      return;
    }

    setResetLoading(true);

    try {
      console.log("RESET PASSWORD STARTED");

      const response = await forgotPassword(
        email,
        newPassword
      );

      console.log(
        "RESET PASSWORD RESPONSE:",
        response
      );

      setSuccess(
        "Password updated successfully! You can now login with your new password."
      );

      setNewPassword("");
    } catch (err) {
      console.error(
        "FORGOT PASSWORD ERROR:",
        err
      );

      const message =
        err?.response?.data?.detail ||
        err?.message ||
        "Password reset failed.";

      setError(String(message));
    } finally {
      setResetLoading(false);
    }
  };

  // =========================
  // SWITCH TO FORGOT PASSWORD
  // =========================

  const handleShowForgotPassword = () => {
    setShowForgotPassword(true);
    setError("");
    setSuccess("");
    setNewPassword("");
  };

  // =========================
  // BACK TO LOGIN
  // =========================

  const handleBackToLogin = () => {
    setShowForgotPassword(false);
    setError("");
    setSuccess("");
    setNewPassword("");
  };

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        backgroundColor: "#FFF8DC",
        padding: 2,
      }}
    >
      <Card
        sx={{
          width: "100%",
          maxWidth: 450,
          borderRadius: 3,
          boxShadow: 4,
        }}
      >
        <CardContent sx={{ p: 4 }}>

          {/* =========================
              TITLE
          ========================= */}

          <Typography
            variant="h4"
            align="center"
            gutterBottom
            fontWeight="bold"
          >
            {showForgotPassword
              ? "Reset Password 🔐"
              : "Welcome Back 👋"}
          </Typography>

          <Typography
            align="center"
            color="text.secondary"
            mb={4}
          >
            AI Metadata Mapping Dashboard
          </Typography>

          {/* =========================
              SUCCESS MESSAGE
          ========================= */}

          {success && (
            <Alert
              severity="success"
              sx={{ mb: 2 }}
            >
              {success}
            </Alert>
          )}

          {/* =========================
              ERROR MESSAGE
          ========================= */}

          {error && (
            <Alert
              severity="error"
              sx={{ mb: 2 }}
            >
              {error}
            </Alert>
          )}

          {/* =========================
              FORGOT PASSWORD FORM
          ========================= */}

          {showForgotPassword ? (
            <Box
              component="form"
              onSubmit={handleForgotPassword}
            >

              <Typography
                sx={{
                  color: "#795548",
                  mb: 2,
                }}
              >
                Enter your registered email and create
                a new password.
              </Typography>

              {/* EMAIL */}

              <TextField
                fullWidth
                required
                label="Email"
                type="email"
                margin="normal"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
              />

              {/* NEW PASSWORD */}

              <TextField
                fullWidth
                required
                label="New Password"
                type="password"
                margin="normal"
                value={newPassword}
                onChange={(event) =>
                  setNewPassword(event.target.value)
                }
              />

              {/* RESET BUTTON */}

              <Button
                fullWidth
                type="submit"
                variant="contained"
                disabled={resetLoading}
                sx={{
                  mt: 3,
                  py: 1.4,
                  borderRadius: 2,
                  bgcolor: "#6D4C41",
                  "&:hover": {
                    bgcolor: "#5D4037",
                  },
                }}
              >
                {resetLoading
                  ? "Updating Password..."
                  : "Reset Password"}
              </Button>

              {/* BACK TO LOGIN */}

              <Box
                sx={{
                  display: "flex",
                  justifyContent: "center",
                  mt: 3,
                }}
              >
                <Link
                  component="button"
                  type="button"
                  onClick={handleBackToLogin}
                  underline="hover"
                  sx={{
                    color: "#6D4C41",
                    fontWeight: 600,
                    border: "none",
                    background: "none",
                    cursor: "pointer",
                    fontSize: "inherit",
                  }}
                >
                  ← Back to Login
                </Link>
              </Box>
            </Box>
          ) : (

            /* =========================
               LOGIN FORM
            ========================= */

            <Box
              component="form"
              onSubmit={handleLogin}
            >

              {/* EMAIL */}

              <TextField
                fullWidth
                required
                label="Email"
                type="email"
                margin="normal"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
              />

              {/* PASSWORD */}

              <TextField
                fullWidth
                required
                label="Password"
                type="password"
                margin="normal"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
              />

              {/* FORGOT PASSWORD */}

              <Box
                sx={{
                  display: "flex",
                  justifyContent: "flex-end",
                  mt: 1,
                }}
              >
                <Link
                  component="button"
                  type="button"
                  onClick={handleShowForgotPassword}
                  underline="hover"
                  sx={{
                    color: "#6D4C41",
                    fontWeight: 600,
                    border: "none",
                    background: "none",
                    cursor: "pointer",
                    fontSize: "0.875rem",
                  }}
                >
                  Forgot Password?
                </Link>
              </Box>

              {/* LOGIN BUTTON */}

              <Button
                fullWidth
                type="submit"
                variant="contained"
                disabled={loading}
                sx={{
                  mt: 3,
                  py: 1.4,
                  borderRadius: 2,
                  bgcolor: "#6D4C41",
                  "&:hover": {
                    bgcolor: "#5D4037",
                  },
                }}
              >
                {loading
                  ? "Logging in..."
                  : "Login"}
              </Button>
            </Box>
          )}

          {/* =========================
              REGISTER LINK
          ========================= */}

          {!showForgotPassword && (
            <Box
              sx={{
                display: "flex",
                justifyContent: "center",
                mt: 3,
              }}
            >
              <Typography
                variant="body2"
                color="text.secondary"
              >
                Don't have an account?{" "}

                <Link
                  component={RouterLink}
                  to="/register"
                  underline="hover"
                  sx={{
                    color: "#6D4C41",
                    fontWeight: 600,
                  }}
                >
                  Register
                </Link>
              </Typography>
            </Box>
          )}

        </CardContent>
      </Card>
    </Box>
  );
}

export default Login;
              