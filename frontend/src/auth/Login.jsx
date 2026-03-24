/**
 * Login Component
 * 
 * Displays login page with Azure AD authentication option.
 * Automatically redirects to dashboard if already authenticated.
 */

import React, { useEffect, useRef, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "./useAuth";

/**
 * Login Page Component
 * 
 * Shows login UI and handles the authentication flow.
 * If user is already authenticated, redirects to dashboard.
 * 
 * @example
 * ```jsx
 * <Route path="/login" element={<Login />} />
 * ```
 */
export const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, isLoading, login, error } = useAuth();
  const redirectTimeoutRef = useRef(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  // Handle redirect after authentication
  useEffect(() => {
    console.log("🔍 Login component effect:", {
      isAuthenticated,
      isLoading,
      isCallbackPage: location.pathname === "/callback",
      checkingAuth,
    });

    // If on callback page, check if we got a code from Microsoft
    if (location.pathname === "/callback") {
      const params = new URLSearchParams(location.search);
      const hashParams = new URLSearchParams(location.hash.substring(1));
      
      const hasCode = params.has("code") || hashParams.has("code");
      const hasError = params.has("error") || hashParams.has("error");
      
      console.log("📍 On callback page");
      console.log("   - hasCode:", hasCode);
      console.log("   - hasError:", hasError);
      console.log("   - isLoading:", isLoading);
      console.log("   - isAuthenticated:", isAuthenticated);
      console.log("   - Search params:", {code: params.get("code"), error: params.get("error")});
      console.log("   - Hash params:", {code: hashParams.get("code"), error: hashParams.get("error")});
      
      // If Microsoft returned an error, show it and go back to login
      if (hasError) {
        const error = params.get("error") || hashParams.get("error");
        const errorDesc = params.get("error_description") || hashParams.get("error_description");
        console.error("❌ Microsoft returned error:", error, errorDesc);
        setCheckingAuth(false);
        // Don't redirect, just stay on callback which shows Login component
        return;
      }
      
      // If no code and not loading, Microsoft rejected the login
      if (!hasCode && !isLoading) {
        console.log("⚠️ No code from Microsoft, staying on login");
        setCheckingAuth(false);
        return;
      }
      
      // If loading finished and authenticated, redirect to dashboard
      if (!isLoading) {
        if (isAuthenticated) {
          console.log("✅ Authenticated on callback - redirecting to dashboard");
          redirectTimeoutRef.current = setTimeout(() => {
            navigate("/dashboard", { replace: true });
          }, 300);
        } else {
          console.log("⚠️ Still not authenticated on callback page");
          setCheckingAuth(false);
        }
      }
      return;
    }

    // If on login page and authenticated, redirect
    if (location.pathname === "/login" && isAuthenticated && !isLoading) {
      console.log("✅ Authenticated on login page - redirecting to dashboard");
      redirectTimeoutRef.current = setTimeout(() => {
        navigate("/dashboard", { replace: true });
      }, 100);
      return;
    }

    // Not loading anymore
    if (!isLoading) {
      setCheckingAuth(false);
    }
  }, [isAuthenticated, isLoading, navigate, location.pathname, checkingAuth]);

  const handleLogin = async () => {
    try {
      console.log("🔐 Starting login...");
      setCheckingAuth(true);
      
      // Si estamos en callback, vuelve a /login primero
      if (location.pathname === "/callback") {
        console.log("Redirecting from callback to login to retry...");
        navigate("/login", { replace: true });
        setCheckingAuth(false);
        return;
      }
      
      await login();
      console.log("✅ Login completed");
    } catch (err) {
      console.error("❌ Login failed:", err);
      setCheckingAuth(false);
    }
  };

  // Show loading while checking auth on callback
  if (checkingAuth || (location.pathname === "/callback" && isLoading)) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center px-4">
        <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 text-sm">Completando autenticación...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center px-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-8">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <div className="text-4xl font-bold text-blue-600 mb-2">🔐</div>
          <h1 className="text-3xl font-bold text-gray-900">
            ForensicGuardian
          </h1>
          <p className="text-gray-600 mt-2">Platform de Análisis Forense</p>
        </div>

        {/* Error State */}
        {error && !isLoading && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800 text-sm font-medium">
              <span className="font-bold">Error:</span> {error}
            </p>
          </div>
        )}

        {/* Login Form */}
        {!checkingAuth && (
          <>
            <p className="text-gray-600 text-center mb-6">
              Inicia sesión con tu cuenta Microsoft Entra ID para continuar
            </p>

            <button
              onClick={handleLogin}
              disabled={isLoading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded-lg transition duration-200 flex items-center justify-center gap-2"
            >
              <svg
                className="w-5 h-5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M10.5 1.5H4a2.5 2.5 0 0 0-2.5 2.5v9A2.5 2.5 0 0 0 4 15.5h6.5m0 0H16a2.5 2.5 0 0 0 2.5-2.5v-9A2.5 2.5 0 0 0 16 1.5h-5.5m0 0v12m0 0L7 10m3.5 3.5l3.5-3.5" />
              </svg>
              Iniciar sesión con Microsoft
            </button>

            <div className="mt-6 pt-6 border-t border-gray-200">
              <p className="text-gray-500 text-xs text-center">
                Tus datos están protegidos con seguridad de clase empresarial
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default Login;
