import { Routes, Route, Navigate } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import ConnectDatabase from "./pages/ConnectDatabase";
import MongoDB from "./pages/MongoDB";
import SchemaViewer from "./pages/SchemaViewer";
import Relationships from "./pages/Relationships";
import MetadataMapping from "./pages/MetadataMapping";
import Settings from "./pages/Settings";

import ProtectedRoute from "./routes/ProtectedRoute";

function App() {
  return (
    <Routes>

      {/* =========================================
          DEFAULT ROUTE
      ========================================= */}
      <Route
        path="/"
        element={<Navigate to="/login" replace />}
      />


      {/* =========================================
          LOGIN
      ========================================= */}
      <Route
        path="/login"
        element={<Login />}
      />


      {/* =========================================
          REGISTER
      ========================================= */}
      <Route
        path="/register"
        element={<Register />}
      />


      {/* =========================================
          DASHBOARD
      ========================================= */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />


      {/* =========================================
          CONNECT DATABASE
      ========================================= */}
      <Route
        path="/connect-database"
        element={
          <ProtectedRoute>
            <ConnectDatabase />
          </ProtectedRoute>
        }
      />


      {/* =========================================
          MONGODB
      ========================================= */}
      <Route
        path="/mongodb"
        element={
          <ProtectedRoute>
            <MongoDB />
          </ProtectedRoute>
        }
      />


      {/* =========================================
          SCHEMA VIEWER
      ========================================= */}
      <Route
        path="/schema-viewer"
        element={
          <ProtectedRoute>
            <SchemaViewer />
          </ProtectedRoute>
        }
      />


      {/* =========================================
          RELATIONSHIPS
      ========================================= */}
      <Route
        path="/relationships"
        element={
          <ProtectedRoute>
            <Relationships />
          </ProtectedRoute>
        }
      />


      {/* =========================================
          METADATA MAPPING
      ========================================= */}
      <Route
        path="/metadata-mapping"
        element={
          <ProtectedRoute>
            <MetadataMapping />
          </ProtectedRoute>
        }
      />


      {/* =========================================
          SETTINGS
      ========================================= */}
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Settings />
          </ProtectedRoute>
        }
      />


      {/* =========================================
          UNKNOWN ROUTE
      ========================================= */}
      <Route
        path="*"
        element={<Navigate to="/dashboard" replace />}
      />

    </Routes>
  );
}

export default App;