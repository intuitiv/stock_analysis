import React, { createContext, useContext, useState, ReactNode } from 'react';
import { api } from '../utils/api';

// Define the shape of the user object
export interface User {
  id: number;
  username: string;
  email?: string;
}

// Define the shape of the login response
export interface LoginResponse {
  token: string;
  user: User | null;
}

export interface AuthContextType {
  token: string | null;
  user: User | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  getToken: () => string | null;
}

// Provide a default value that matches the AuthContextType
const defaultAuthContextValue: AuthContextType = {
  token: null,
  user: null,
  login: async () => { throw new Error('AuthProvider not found'); },
  logout: () => { throw new Error('AuthProvider not found'); },
  isAuthenticated: false,
  getToken: () => null,
};

export const AuthContext = createContext<AuthContextType>(defaultAuthContextValue);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('authToken'));
  const [user, setUser] = useState<User | null>(() => {
    const storedUser = localStorage.getItem('user');
    return storedUser ? JSON.parse(storedUser) : null;
  });

  const getToken = () => token || localStorage.getItem('authToken');

  const login = async (username: string, password: string) => {
    try {
      const response = await api.auth.login({ username, password });
      const loginResponse = response as LoginResponse;

      setToken(loginResponse.token);
      localStorage.setItem('authToken', loginResponse.token);
      
      if (loginResponse.user) {
        setUser(loginResponse.user);
        localStorage.setItem('user', JSON.stringify(loginResponse.user));
      } else {
        setUser(null);
        localStorage.removeItem('user');
      }
    } catch (error) {
      setToken(null);
      setUser(null);
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      throw error;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
  };

  const isAuthenticated = !!token;

  return (
    <AuthContext.Provider value={{ 
      token, 
      user,
      login, 
      logout, 
      isAuthenticated,
      getToken
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  return context;
};
