import React, { createContext, useState, useEffect, useCallback } from 'react';
import { login as loginApi, getProfile } from '../api/auth';
import { setTokens, clearTokens, getAccessToken } from '../utils/storage';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    if (!getAccessToken()) {
      setLoading(false);
      return;
    }
    try {
      const { data } = await getProfile();
      setUser(data);
    } catch {
      clearTokens();
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = async (email, password) => {
    const { data } = await loginApi(email, password);
    setTokens(data.access, data.refresh);
    setUser(data.user);
    return data.user;
  };

  const logout = () => {
    clearTokens();
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    logout,
    isAuthenticated: !!user,
    isAdmin: user?.is_staff || false,
    refreshUser: loadUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
