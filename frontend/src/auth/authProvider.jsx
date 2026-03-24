/**
 * MSAL Provider Wrapper
 * 
 * Sets up MSAL and AuthProvider for the entire application.
 * This is the root authentication layer.
 */

import React from "react";
import { MsalProvider } from "@azure/msal-react";
import { PublicClientApplication } from "@azure/msal-browser";
import { AuthProvider } from "./AuthContext";
import { msalConfig } from "./authConfig";

/**
 * Initialize MSAL with the configuration
 */
let msalInstance = null;

export function getMsalInstance() {
  if (!msalInstance) {
    try {
      msalInstance = new PublicClientApplication(msalConfig);
      console.log("✅ MSAL instance created");
      console.log("🔧 MSAL Configuration:");
      console.log("   - Client ID:", msalConfig.auth.clientId);
      console.log("   - Authority:", msalConfig.auth.authority);
      console.log("   - Redirect URI:", msalConfig.auth.redirectUri);
    } catch (err) {
      console.error("❌ Error creating MSAL instance:", err);
    }
  }
  return msalInstance;
}

/**
 * MSAL Auth Provider Component
 * 
 * Combines MsalProvider (for MSAL browser SDK) and AuthProvider (for custom auth context)
 * into a single wrapper component for convenience.
 * 
 * @param children - Application components
 * 
 * @example
 * ```jsx
 * import { MsalAuthProvider } from "@/auth/authProvider";
 * 
 * ReactDOM.render(
 *   <MsalAuthProvider>
 *     <App />
 *   </MsalAuthProvider>,
 *   document.getElementById("root")
 * );
 * ```
 */
export const MsalAuthProvider = ({ children }) => {
  const msalInstance = getMsalInstance();

  return (
    <MsalProvider instance={msalInstance}>
      <AuthProvider>{children}</AuthProvider>
    </MsalProvider>
  );
};

export default MsalAuthProvider;
