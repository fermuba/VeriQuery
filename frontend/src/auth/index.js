/**
 * Auth Module Exports
 * 
 * Central export point for all authentication-related components and hooks.
 */

// Configuration
export { msalConfig, loginRequest, logoutRequest, tokenRequest, API_SCOPES } from "./authConfig";

// Context
export { AuthContext, AuthProvider } from "./AuthContext";

// Hooks
export { useAuth } from "./useAuth";
export { useApi } from "./useApi";

// Components
export { AuthGuard } from "./AuthGuard";
export { Login } from "./Login";
export { MsalAuthProvider, getMsalInstance } from "./authProvider";
