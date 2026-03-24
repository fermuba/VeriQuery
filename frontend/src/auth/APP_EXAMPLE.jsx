/**
 * Example App.jsx with Authentication Integration
 * 
 * This shows how to integrate the auth module into your React app.
 * Copy the relevant parts to your own App.jsx
 */

import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { MsalAuthProvider, AuthGuard, Login } from "@/auth";

// Example components
import Dashboard from "./pages/Dashboard";
import Profile from "./pages/Profile";
import AdminPanel from "./pages/AdminPanel";
import Navbar from "./components/Navbar";

/**
 * App Routes
 * 
 * Usage:
 * 1. Wrap App with BrowserRouter in main.jsx
 * 2. Replace @/auth imports with your auth path
 * 3. Replace page imports with your actual pages
 * 4. Customize routes as needed
 */
function AppRoutes() {
  return (
    <Routes>
      {/* Public route */}
      <Route path="/login" element={<Login />} />

      {/* Protected routes */}
      <Route
        path="/dashboard"
        element={
          <AuthGuard>
            <Dashboard />
          </AuthGuard>
        }
      />

      <Route
        path="/profile"
        element={
          <AuthGuard>
            <Profile />
          </AuthGuard>
        }
      />

      {/* Admin-only route */}
      <Route
        path="/admin"
        element={
          <AuthGuard requiredRoles={["admin"]}>
            <AdminPanel />
          </AuthGuard>
        }
      />

      {/* Redirect to dashboard */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* 404 */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

/**
 * Main App Component
 */
export default function App() {
  return (
    <BrowserRouter>
      <MsalAuthProvider>
        <div className="min-h-screen bg-gray-100">
          <Navbar />
          <main className="container mx-auto py-8">
            <AppRoutes />
          </main>
        </div>
      </MsalAuthProvider>
    </BrowserRouter>
  );
}
