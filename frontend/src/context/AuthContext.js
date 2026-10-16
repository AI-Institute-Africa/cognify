import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => {
    // Initialize token from localStorage on mount
    const storedToken = localStorage.getItem('cognify_token');
    return storedToken || null;
  });
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async (authToken) => {
    if (!authToken) {
      setLoading(false);
      return;
    }
    
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
      // Clear invalid token
      localStorage.removeItem('cognify_token');
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Check token on mount and fetch user
    const storedToken = localStorage.getItem('cognify_token');
    if (storedToken) {
      setToken(storedToken);
      fetchUser(storedToken);
    } else {
      setLoading(false);
    }
  }, [fetchUser]);

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { access_token, user: userData } = response.data;
    localStorage.setItem('cognify_token', access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (email, password, fullName, role = 'student') => {
    const response = await axios.post(`${API}/auth/register`, {
      email,
      password,
      full_name: fullName,
      role
    });
    const { access_token, user: userData } = response.data;
    localStorage.setItem('cognify_token', access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const loginWithPhoneAuth = async (identifier, password = null, otpCode = null) => {
    const payload = { identifier };
    if (password) payload.password = password;
    if (otpCode) payload.otp_code = otpCode;
    const response = await axios.post(`${API}/auth/phone/login`, payload);
    const { access_token, user: userData } = response.data;
    localStorage.setItem('cognify_token', access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  };

  const loginWithToken = async (authToken, userData = null) => {
    localStorage.setItem('cognify_token', authToken);
    setToken(authToken);
    if (userData) {
      setUser(userData);
    } else {
      await fetchUser(authToken);
    }
  };

  const refreshUser = useCallback(async () => {
    const storedToken = localStorage.getItem('cognify_token');
    if (storedToken) {
      await fetchUser(storedToken);
    }
  }, [fetchUser]);

  const logout = () => {
    localStorage.removeItem('cognify_token');
    setToken(null);
    setUser(null);
  };

  // isAuthenticated should check both token and user for proper auth state
  const isAuthenticated = !!token && !!user;

  const value = {
    user,
    token,
    loading,
    login,
    register,
    loginWithPhoneAuth,
    loginWithToken,
    logout,
    refreshUser,
    isAuthenticated
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
