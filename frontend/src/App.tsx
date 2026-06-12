import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./auth/AuthProvider";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Dashboard } from "./pages/Dashboard";
import { Clients } from "./pages/Clients";
import { Upload } from "./pages/Upload";
import { Reconciliation } from "./pages/Reconciliation";
import { VendorAnalysis } from "./pages/VendorAnalysis";
import { Reports } from "./pages/Reports";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/clients" element={<Clients />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/reconcile" element={<Reconciliation />} />
            <Route path="/vendors" element={<VendorAnalysis />} />
            <Route path="/reports" element={<Reports />} />
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
