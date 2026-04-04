/**
 * useApi Hook
 * 
 * Custom hook for making authenticated API calls to the backend.
 * Automatically includes the JWT token from Azure AD in the Authorization header.
 */

import { useCallback } from "react";
import { useAuth } from "./useAuth";

/**
 * useApi Hook
 * 
 * Provides methods to make authenticated API calls to the backend.
 * Automatically handles token acquisition and includes it in headers.
 * 
 * @returns Object with api functions (get, post, put, delete)
 * 
 * @example
 * ```jsx
 * const { api } = useApi();
 * 
 * // GET request
 * const { data, error } = await api.get("/api/profile");
 * 
 * // POST request with body
 * const response = await api.post("/api/queries", { query: "SELECT ..." });
 * ```
 */
export function useApi() {
  const { getAccessToken } = useAuth();

  /**
   * Make an authenticated API request
   */
  const request = useCallback(
    async (endpoint, options = {}) => {
      try {
        // Get access token from Azure AD
        const token = await getAccessToken();

        if (!token) {
          return {
            ok: false,
            status: 401,
            error: "No access token available. Please login.",
          };
        }

        // Prepare headers with Bearer token
        const headers = {
          ...options.headers,
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        };

        // Make the request
        const response = await fetch(endpoint, {
          ...options,
          headers,
        });

        // Parse response
        let data;
        try {
          data = await response.json();
        } catch {
          // Response is not JSON, that's OK
        }

        const errorMsg =
          !response.ok && typeof data === "object" && data !== null
            ? data?.error || response.statusText
            : undefined;

        return {
          ok: response.ok,
          status: response.status,
          data,
          error: errorMsg,
        };
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "Unknown error";
        return {
          ok: false,
          status: 0,
          error: errorMessage,
        };
      }
    },
    [getAccessToken]
  );

  /**
   * GET request
   */
  const get = useCallback(
    async (endpoint, options) => {
      return request(endpoint, {
        ...options,
        method: "GET",
      });
    },
    [request]
  );

  /**
   * POST request
   */
  const post = useCallback(
    async (endpoint, body, options) => {
      return request(endpoint, {
        ...options,
        method: "POST",
        body: body ? JSON.stringify(body) : undefined,
      });
    },
    [request]
  );

  /**
   * PUT request
   */
  const put = useCallback(
    async (endpoint, body, options) => {
      return request(endpoint, {
        ...options,
        method: "PUT",
        body: body ? JSON.stringify(body) : undefined,
      });
    },
    [request]
  );

  /**
   * DELETE request
   */
  const delete_ = useCallback(
    async (endpoint, options) => {
      return request(endpoint, {
        ...options,
        method: "DELETE",
      });
    },
    [request]
  );

  return {
    request,
    get,
    post,
    put,
    delete: delete_,
  };
}

export default useApi;
