/**
 * MSAL Configuration for Azure AD Authentication
 * 
 * This module configures the Microsoft Authentication Library (MSAL) for browser-based
 * authentication with Azure AD (Entra ID). All configuration is environment-driven.
 */

import { LogLevel } from "@azure/msal-browser";

/**
 * Validate that all required environment variables are present
 */
function validateEnvVariables() {
  const required = [
    "VITE_AZURE_CLIENT_ID",
    "VITE_AZURE_TENANT_ID",
    "VITE_AZURE_REDIRECT_URI",
  ];

  const missing = required.filter((key) => !import.meta.env[key]);

  if (missing.length > 0) {
    throw new Error(
      `Missing required environment variables: ${missing.join(", ")}. ` +
        `Please check your .env file and ensure all VITE_AZURE_* variables are set.`
    );
  }
}

/**
 * Get MSAL configuration from environment variables
 */
function getMsalConfig() {
  validateEnvVariables();

  const clientId = import.meta.env.VITE_AZURE_CLIENT_ID;
  const tenantId = import.meta.env.VITE_AZURE_TENANT_ID;
  const redirectUri = import.meta.env.VITE_AZURE_REDIRECT_URI;

  return {
    auth: {
      clientId,
      authority: `https://login.microsoftonline.com/${tenantId}`,
      redirectUri,
      postLogoutRedirectUri: "/",
      // SPA Configuration: Use Authorization Code Flow with PKCE
      // This is the proper flow for Single-Page Applications
      navigateToLoginRequestUrl: false,
    },
    cache: {
      cacheLocation: "localStorage",
      storeAuthStateInCookie: false,
    },
    system: {
      // Allow popup windows to communicate back
      allowRedirectInIframe: false,
      loggerOptions: {
        loggerCallback: (level, message, containsPii) => {
          if (containsPii) {
            return;
          }
          switch (level) {
            case LogLevel.Error:
              console.error("[MSAL Error]", message);
              break;
            case LogLevel.Warning:
              console.warn("[MSAL Warning]", message);
              break;
            case LogLevel.Info:
              console.info("[MSAL Info]", message);
              break;
            case LogLevel.Verbose:
              if (import.meta.env.DEV) {
                console.debug("[MSAL Verbose]", message);
              }
              break;
          }
        },
        piiLoggingEnabled: false,
      },
    },
  };
}

/**
 * Scopes for API access
 * The access token will have these scopes when calling the backend API
 */
export const API_SCOPES = [
  "openid",
  "profile", 
  "email",
];

/**
 * Scopes for login only (ID token)
 * Using minimal scopes for Azure AD B2C / Entra ID compatibility
 */
export const LOGIN_SCOPES = [
  "openid",
  "profile",
  "email",
  // Optional: Add your API's scope if you have one configured
  // Example: `api://${import.meta.env.VITE_AZURE_CLIENT_ID}/access_as_user`
];

/**
 * Create and export MSAL configuration
 */
export const msalConfig = getMsalConfig();

/**
 * Login request configuration
 * Can be customized with additional scopes if needed
 */
export const loginRequest = {
  scopes: LOGIN_SCOPES,
};

/**
 * Logout request configuration
 */
export const logoutRequest = {
  postLogoutRedirectUri: "/",
};

/**
 * Token request configuration for silent token acquisition
 */
export const tokenRequest = {
  scopes: API_SCOPES,
  forceRefresh: false,
};

export default msalConfig;
