/**
 * Authentication Context
 * 
 * Provides global authentication state and methods throughout the application.
 * This is the single source of truth for authentication in the frontend.
 */

import React, { createContext, useCallback, useEffect, useState } from "react";
import {
  useIsAuthenticated,
  useMsal,
  useAccount,
} from "@azure/msal-react";
import { LOGIN_SCOPES, API_SCOPES } from "./authConfig";

/**
 * Create the auth context
 */
export const AuthContext = createContext(undefined);

/**
 * Auth Provider Component
 * 
 * Wraps the application and provides authentication context.
 * Must be used after MsalProvider in the component tree.
 */
export const AuthProvider = ({ children }) => {
  const { instance, accounts, inProgress } = useMsal();
  const isAuthenticated = useIsAuthenticated();
  const account = useAccount();
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Extract user information from the account
   */
  const extractUserFromAccount = useCallback((account) => {
    if (!account) return null;
    
    // Extract roles from idTokenClaims
    const idTokenClaims = account.idTokenClaims || {};
    const roles = idTokenClaims.roles || [];

    return {
      id: account.localAccountId,
      email: account.username || account.homeAccountId || "",
      name: account.name || "User",
      roles,
      tenantId: idTokenClaims.tid,
      oid: idTokenClaims.oid,
    };
  }, []);

  /**
   * Update user state when account changes
   * Also handle initial state when MSAL finishes initializing
   */
  useEffect(() => {
    console.log("📊 Auth state update:", {
      isAuthenticated,
      inProgress,
      accountExists: !!account,
      accountsCount: accounts?.length || 0,
      userExists: !!user,
    });

    // Wait for MSAL to finish initializing
    if (inProgress && inProgress !== "none") {
      console.log("⏳ MSAL still initializing...", inProgress);
      setIsLoading(true);
      return;
    }

    // MSAL finished initializing - now check auth state
    console.log("✅ MSAL initialization complete");
    console.log("   - isAuthenticated:", isAuthenticated);
    console.log("   - account:", account);
    console.log("   - accounts array:", accounts);
    
    // Get all accounts directly from MSAL instance
    const allAccounts = instance.getAllAccounts();
    console.log("   - Trying getAllAccounts():", allAccounts);
    
    // Use either the account from hook or the first account from getAllAccounts
    const activeAccount = account || (allAccounts && allAccounts[0]);
    
    if (activeAccount) {
      try {
        const userData = extractUserFromAccount(activeAccount);
        setUser(userData);
        setError(null);
        setIsLoading(false);
        console.log("✅ User authenticated and loaded:", userData);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Failed to extract user info";
        setError(errorMessage);
        setUser(null);
        setIsLoading(false);
      }
    } else {
      console.log("ℹ️ Not authenticated or no account found");
      console.log("   - isAuthenticated:", isAuthenticated);
      console.log("   - account:", account);
      console.log("   - Accounts in MSAL:", accounts);
      console.log("   - All Accounts:", allAccounts);
      setUser(null);
      setError(null);
      setIsLoading(false);
    }
  }, [isAuthenticated, account, inProgress, extractUserFromAccount, accounts]);

  /**
   * Login with redirect
   * 
   * Use redirect flow instead of popup for better SPA compatibility
   * This is more reliable with Azure AD SPA platform configuration
   */
  const login = useCallback(async () => {
    try {
      setError(null);
      setIsLoading(true);
      console.log("🔐 Starting login redirect...");

      // Use loginRedirect for SPA - more reliable than popup
      await instance.loginRedirect({
        scopes: ["openid", "profile", "email"],
      });
    } catch (err) {
      console.error("❌ Login redirect error:", err);
      const errorMessage =
        err?.errorMessage || 
        err?.message || 
        "Login failed";
      setError(errorMessage);
      setIsLoading(false);
    }
  }, [instance]);

  /**
   * Logout
   */
  const logout = useCallback(async () => {
    try {
      setError(null);
      setIsLoading(true);
      setUser(null);
      console.log("🚪 Logging out...");

      await instance.logoutPopup({
        postLogoutRedirectUri: "/",
        mainWindowRedirectUri: "/",
      });
      
      console.log("✅ Logout completed");
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Logout failed";
      setError(errorMessage);
      console.error("❌ Logout error:", err);
    } finally {
      setIsLoading(false);
    }
  }, [instance]);

  /**
   * Get access token for API calls
   * Tries silent acquisition first, falls back to popup
   */
  const getAccessToken = useCallback(async () => {
    // If still loading, wait a moment for auth to complete
    if (isLoading) {
      console.log("⏳ Auth still loading, waiting...");
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    if (!isAuthenticated || !account) {
      console.warn("⚠️ Cannot get token: not authenticated");
      return null;
    }

    try {
      console.log("🔑 Acquiring token silently...");
      
      // Try silent token acquisition first
      const response = await instance.acquireTokenSilent({
        scopes: LOGIN_SCOPES,
        account,
        forceRefresh: false,
      });

      console.log("✅ Token acquired (silent)");
      return response.accessToken;
    } catch (err) {
      console.warn("⚠️ Silent token acquisition failed, trying popup...");
      
      try {
        // Fall back to popup
        const response = await instance.acquireTokenPopup({
          scopes: LOGIN_SCOPES,
        });

        console.log("✅ Token acquired (popup)");
        return response.accessToken;
      } catch (popupErr) {
        console.error("❌ Failed to acquire token:", popupErr);
        return null;
      }
    }
  }, [isAuthenticated, isLoading, account, instance]);

  const value = {
    user,
    isAuthenticated: isAuthenticated && user !== null,
    isLoading,
    login,
    logout,
    getAccessToken,
    error,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;
