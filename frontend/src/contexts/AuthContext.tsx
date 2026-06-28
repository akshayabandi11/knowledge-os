import React, { createContext, useContext, useState, useEffect } from 'react';
import api, { setAccessToken, getAccessToken } from '../services/api';
import { UserResponse, UserLoginRequest, UserRegisterRequest } from '../services/types';

interface AuthContextType {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: UserLoginRequest) => Promise<void>;
  register: (credentials: UserRegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  updateUser: (fullName: string) => Promise<void>;
  triggerSessionExpired: () => void;
  showExpiredAlert: boolean;
  clearExpiredAlert: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showExpiredAlert, setShowExpiredAlert] = useState(false);

  const fetchProfile = async () => {
    try {
      const response = await api.get<UserResponse>('/auth/me');
      setUser(response.data);
    } catch {
      setUser(null);
      setAccessToken('');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const token = getAccessToken();
    if (token) {
      fetchProfile();
    } else {
      setIsLoading(false);
    }

    // Bind event listener to intercept expired session tokens
    const handleExpired = () => {
      setUser(null);
      setShowExpiredAlert(true);
    };
    window.addEventListener('session-expired', handleExpired);
    return () => window.removeEventListener('session-expired', handleExpired);
  }, []);

  const login = async (credentials: UserLoginRequest) => {
    setIsLoading(true);
    try {
      const response = await api.post<{ access_token: string }>('/auth/login', credentials);
      setAccessToken(response.data.access_token);
      await fetchProfile();
      setShowExpiredAlert(false);
    } catch (err) {
      setIsLoading(false);
      throw err;
    }
  };

  const register = async (credentials: UserRegisterRequest) => {
    setIsLoading(true);
    try {
      await api.post<UserResponse>('/auth/register', credentials);
      // Automatically log in user on registration completion (or redirect to login)
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Allow cleaning client state even if backend network request fails
    } finally {
      setUser(null);
      setAccessToken('');
    }
  };

  const logoutAll = async () => {
    try {
      await api.post('/auth/logout-all');
    } finally {
      setUser(null);
      setAccessToken('');
    }
  };

  const updateUser = async (fullName: string) => {
    const response = await api.patch<UserResponse>('/auth/me', { full_name: fullName });
    setUser(response.data);
  };

  const triggerSessionExpired = () => {
    setUser(null);
    setAccessToken('');
    setShowExpiredAlert(true);
  };

  const clearExpiredAlert = () => setShowExpiredAlert(false);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
    logoutAll,
    updateUser,
    triggerSessionExpired,
    showExpiredAlert,
    clearExpiredAlert,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
