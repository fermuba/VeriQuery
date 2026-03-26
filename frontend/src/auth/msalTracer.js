/**
 * MSAL Event Tracer
 * 
 * Captura TODOS los eventos de MSAL para debuggear el flujo completo
 * Esto nos mostrará exactamente qué está pasando en cada paso
 */

export function setupMsalTracer(msalInstance) {
  if (!msalInstance) {
    console.error("❌ MSAL instance is null");
    return;
  }

  console.log("🔍 Setting up MSAL Event Tracer...");

  // Escuchar TODOS los eventos de MSAL
  msalInstance.addEventCallback((event) => {
    console.group(`📡 MSAL EVENT: ${event.eventName}`);
    console.log("Event Type:", event.eventName);
    console.log("Interaction Type:", event.interactionType);
    console.log("Event Payload:", event.payload);
    
    switch (event.eventName) {
      case "msal:acquireTokenStart":
        console.log("🔑 Token acquisition started");
        console.log("   - InteractionType:", event.interactionType);
        console.log("   - Scopes:", event.payload?.scopes);
        break;

      case "msal:acquireTokenSuccess":
        console.log("✅ Token acquisition successful");
        console.log("   - Account:", event.payload?.account);
        console.log("   - Access Token (first 50 chars):", event.payload?.accessToken?.substring(0, 50));
        break;

      case "msal:acquireTokenFailure":
        console.error("❌ Token acquisition failed");
        console.error("   - Error:", event.payload?.error);
        console.error("   - Error Description:", event.payload?.errorDescription);
        console.error("   - Correlation ID:", event.payload?.correlationId);
        break;

      case "msal:loginStart":
        console.log("🔐 Login started");
        console.log("   - Interaction Type:", event.interactionType);
        console.log("   - Authority:", event.payload?.authority);
        console.log("   - Redirect URI:", event.payload?.redirectUri);
        console.log("   - Scopes:", event.payload?.scopes);
        console.log("   - Client ID:", event.payload?.clientId);
        break;

      case "msal:loginSuccess":
        console.log("✅ Login successful");
        console.log("   - Account:", event.payload?.account);
        console.log("   - ID Token Claims:", event.payload?.idToken?.claims);
        break;

      case "msal:loginFailure":
        console.error("❌ Login failed");
        console.error("   - Error:", event.payload?.error);
        console.error("   - Error Description:", event.payload?.errorDescription);
        console.error("   - Correlation ID:", event.payload?.correlationId);
        break;

      case "msal:handleRedirectStart":
        console.log("🔄 Handle redirect started");
        break;

      case "msal:handleRedirectEnd":
        console.log("✅ Handle redirect completed");
        break;

      default:
        console.log("Other event:", event.eventName);
    }
    
    console.groupEnd();
  });

  // Crear wrapper para capturar llamadas HTTP
  console.log("🟢 MSAL Tracer iniciado - todos los eventos serán registrados");
}

export default setupMsalTracer;
