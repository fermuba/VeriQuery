/**
 * Debug Panel Component
 * 
 * Shows current authentication state, URL parameters, and localStorage for debugging
 */

import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

export default function DebugPanel() {
  const location = useLocation();
  const [debugInfo, setDebugInfo] = useState({});

  useEffect(() => {
    try {
      const params = new URLSearchParams(location.search);
      const hash = new URLSearchParams(location.hash.substring(1));

      const info = {
        currentPath: location.pathname,
        currentSearch: location.search,
        currentHash: location.hash,
        urlParams: {
          code: params.get("code"),
          state: params.get("state"),
          session_state: params.get("session_state"),
          error: params.get("error"),
          error_description: params.get("error_description"),
        },
        hashParams: {
          access_token: hash.get("access_token")?.substring(0, 20) + "..." || null,
          id_token: hash.get("id_token")?.substring(0, 20) + "..." || null,
          error: hash.get("error"),
          error_description: hash.get("error_description"),
        },
        localStorage: {
          msalAccountsCount: (localStorage.getItem("msal.account.keys") || "").split(",").filter(Boolean).length,
          allMsalKeys: Object.keys(localStorage)
            .filter(k => k.startsWith("msal"))
            .map(k => ({ key: k, valueLength: localStorage.getItem(k)?.length || 0 })),
        },
      };

      setDebugInfo(info);

      // Log everything
      console.log("🐛 DEBUG PANEL INFO:");
      console.log("Current Path:", info.currentPath);
      console.log("URL Params:", info.urlParams);
      console.log("Hash Params:", info.hashParams);
      console.log("localStorage MSAL keys:", info.localStorage.allMsalKeys);
    } catch (err) {
      console.error("Debug panel error:", err);
      setDebugInfo({ error: err.message });
    }
  }, [location]);

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      background: "#1e1e1e",
      color: "#00ff00",
      padding: "8px",
      fontSize: "8px",
      fontFamily: "monospace",
      maxWidth: "350px",
      maxHeight: "200px",
      overflow: "auto",
      border: "2px solid #00ff00",
      zIndex: 9999,
    }}>
      <div style={{ marginBottom: "5px", fontWeight: "bold", fontSize: "9px" }}>🐛 DEBUG</div>

      <div>
        <strong>Path:</strong> {debugInfo?.currentPath || "..."}
      </div>

      <div style={{ marginTop: "5px" }}>
        <strong>Code:</strong> {debugInfo?.urlParams?.code ? "✅ YES" : "❌ NO"}
      </div>

      <div style={{ marginTop: "5px" }}>
        <strong>Error:</strong> {debugInfo?.urlParams?.error || "none"}
      </div>

      <div style={{ marginTop: "5px" }}>
        <strong>MSAL Accounts:</strong> {debugInfo?.localStorage?.msalAccountsCount || 0}
      </div>

      {debugInfo?.error && (
        <div style={{ marginTop: "5px", color: "#ff0000" }}>
          ⚠️ {debugInfo.error}
        </div>
      )}
    </div>
  );
}
