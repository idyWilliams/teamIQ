/* eslint-disable no-useless-catch */
import React, { createContext, useContext, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { authService } from "../services/auth";
import { AuthResponse, User as AuthUser, RegisterData } from "../types";
import { authApi } from "../lib/api";
import toast from "react-hot-toast";

interface AuthContextType {
  user: AuthUser | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  // const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const initAuth = async () => {
      try {
        const token = authService.getToken();
        if (token) {
          const currentUser = await authService.getCurrentUser();
          setUser(currentUser);
        }
      } catch (error) {
        console.error("Failed to initialize auth:", error);
        authService.removeToken();
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (username: string, password: string) => {
    // eslint-disable-next-line no-useless-catch
    try {
      const response = await authService.login(username, password);
      setUser(response.user);
      navigate("/dashboard");
    } catch (error) {
      throw error;
    }
  };

  // const register = async (email: string, username: string, password: string, fullName: string) => {
  //   try {
  //     const response = await authService.register(email, username, password, fullName);
  //     setUser(response.user);
  //     navigate('/dashboard');
  //   } catch (error) {
  //     throw error;
  //   }
  // };

  const register = async (userData: RegisterData) => {
    try {
      setIsLoading(true);
      const response = await authApi.register(userData);
      const authData: AuthResponse = response.data;

      // setToken(authData.access_token);
      setUser(authData.user);

      toast.success("Account created successfully!");

      // Navigate to appropriate dashboard based on role
      const dashboardRoute = getDashboardRoute(authData.user.role);
      navigate(dashboardRoute);
    } catch (error: unknown) {
  
      toast.error(error.message || "Registration failed");
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      await authService.logout();
      setUser(null);
      navigate("/login");
    } catch (error) {
      console.error("Logout error:", error);
      // Force logout even if API call fails
      authService.removeToken();
      setUser(null);
      navigate("/login");
    }
  };

  const refreshToken = async () => {
    try {
      const response = await authService.refreshToken();
      setUser(response.user);
    } catch (error) {
      console.error("Token refresh failed:", error);
      await logout();
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    login,
    logout,
    refreshToken,
    register,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

const getDashboardRoute = (role: string): string => {
  switch (role) {
    case "intern":
    case "engineer":
      return "/dashboard/intern";
    case "team_lead":
    case "manager":
      return "/dashboard/team-lead";
    case "hr":
      return "/dashboard/hr";
    case "admin":
      return "/dashboard/admin";
    default:
      return "/dashboard/intern";
  }
};
