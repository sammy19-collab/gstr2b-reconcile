import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import { login as apiLogin } from "../api/endpoints";
import type { User, TokenResponse } from "../types";

interface AuthContextValue {
  user: User | null;
  accessToken: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  accessToken: null,
  login: async () => {},
  logout: () => {},
  isAuthenticated: false,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(
    () => sessionStorage.getItem("access_token")
  );
  const [user, setUser] = useState<User | null>(null);

  // On mount, restore token from sessionStorage
  useEffect(() => {
    const token = sessionStorage.getItem("access_token");
    if (token) {
      setAccessToken(token);
      // Decode basic info from JWT payload
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        setUser({
          id: parseInt(payload.sub),
          email: payload.email || "",
          full_name: payload.full_name || "",
          role: payload.role || "USER",
          is_active: true,
          created_at: "",
        });
      } catch {
        // ignore decode errors
      }
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const data: TokenResponse = await apiLogin(email, password);
    sessionStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    setAccessToken(data.access_token);

    // Decode user info from JWT
    try {
      const payload = JSON.parse(atob(data.access_token.split(".")[1]));
      setUser({
        id: parseInt(payload.sub),
        email: payload.email || email,
        full_name: payload.full_name || "",
        role: payload.role || "USER",
        is_active: true,
        created_at: "",
      });
    } catch {
      setUser({ id: 0, email, full_name: "", role: "USER", is_active: true, created_at: "" });
    }
  }, []);

  const logout = useCallback(() => {
    sessionStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setAccessToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken,
        login,
        logout,
        isAuthenticated: !!accessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  return useContext(AuthContext);
}
