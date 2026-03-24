/**
 * useAuth Hook
 * 
 * Custom hook to access authentication context throughout the application.
 * Must be called within a component that is a child of AuthProvider.
 */

import { useContext } from "react";
import { AuthContext } from "./AuthContext";

/**
 * Hook to access authentication context
 * 
 * @returns Authentication context with user, login, logout, etc.
 * @throws Error if used outside of AuthProvider
 * 
 * @example
 * ```jsx
 * const { user, isAuthenticated, login, logout } = useAuth();
 * ```
 */
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used within an AuthProvider. " +
        "Make sure your component is wrapped by AuthProvider."
    );
  }

  return context;
}

export default useAuth;
