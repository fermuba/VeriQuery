/**
 * AuthGuard Component
 * 
 * Protects routes by ensuring user is authenticated.
 * If not authenticated, shows login message (doesn't auto-login).
 */

import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./useAuth";

/**
 * Loading fallback component
 */
const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen bg-gray-50">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
      <p className="text-gray-600 font-medium">Validando autenticación...</p>
    </div>
  </div>
);

/**
 * Unauthorized fallback component
 */
const UnauthorizedFallback = ({ requiredRoles }) => (
  <div className="flex items-center justify-center min-h-screen bg-gray-50">
    <div className="text-center max-w-md">
      <div className="text-red-600 text-4xl mb-4">🔒</div>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">
        Acceso Denegado
      </h1>
      <p className="text-gray-600 mb-4">
        No tienes los permisos necesarios para acceder a esta página.
      </p>
      <p className="text-sm text-gray-500">
        Roles requeridos: <span className="font-mono">{requiredRoles.join(", ")}</span>
      </p>
    </div>
  </div>
);

/**
 * AuthGuard Component
 * 
 * Protects routes and enforces role-based access control.
 * Redirects to login if not authenticated (no auto-login loop).
 * 
 * @param children - Component(s) to render if authenticated
 * @param requiredRoles - Optional array of roles that user must have
 * @param fallback - Optional custom loading fallback
 * 
 * @example
 * ```jsx
 * <AuthGuard>
 *   <Dashboard />
 * </AuthGuard>
 * 
 * <AuthGuard requiredRoles={["admin", "moderator"]}>
 *   <AdminPanel />
 * </AuthGuard>
 * ```
 */
export const AuthGuard = ({
  children,
  requiredRoles,
  fallback,
}) => {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading, user } = useAuth();

  // Show loading state while checking authentication
  if (isLoading) {
    return fallback || <LoadingFallback />;
  }

  // User not authenticated - redirect to login (no auto-login)
  if (!isAuthenticated) {
    useEffect(() => {
      navigate("/login", { replace: true });
    }, [navigate]);
    
    return fallback || <LoadingFallback />;
  }

  // Check role-based access if required
  if (requiredRoles && requiredRoles.length > 0) {
    const hasRequiredRole = user?.roles?.some((role) =>
      requiredRoles.includes(role)
    );

    if (!hasRequiredRole) {
      return <UnauthorizedFallback requiredRoles={requiredRoles} />;
    }
  }

  return <>{children}</>;
};

export default AuthGuard;
