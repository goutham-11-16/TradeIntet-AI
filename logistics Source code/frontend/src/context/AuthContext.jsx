import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api, formatApiError } from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // null=loading, false=unauth, obj=auth
  const [ready, setReady] = useState(false);

  const check = useCallback(async () => {
    try {
      const { data } = await api.me();
      setUser(data);
    } catch {
      setUser(false);
    } finally {
      setReady(true);
    }
  }, []);

  useEffect(() => { check(); }, [check]);

  const login = async (creds) => {
    const { data } = await api.login(creds);
    if (data.access_token) localStorage.setItem("ts_token", data.access_token);
    setUser(data);
    return data;
  };

  const register = async (payload) => {
    const { data } = await api.register(payload);
    if (data.access_token) localStorage.setItem("ts_token", data.access_token);
    setUser(data);
    return data;
  };

  const logout = async () => {
    try { await api.logout(); } catch {}
    localStorage.removeItem("ts_token");
    setUser(false);
  };

  const hasRole = (...roles) => user && roles.includes(user.role);
  const canManage = () => hasRole("admin", "manager");

  return (
    <AuthContext.Provider value={{ user, ready, login, register, logout, hasRole, canManage, refresh: check, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
export { formatApiError };
