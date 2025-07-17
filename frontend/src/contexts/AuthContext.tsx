import React, { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../lib/api'
import { getToken, setToken, removeToken, getUserFromToken, isAuthenticated } from '../lib/auth'
import { User, LoginCredentials, RegisterData, AuthResponse } from '../types'
import toast from 'react-hot-toast'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (credentials: LoginCredentials) => Promise<void>
  register: (userData: RegisterData) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: React.ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = getToken()
        if (token && isAuthenticated()) {
          // Get user from token first (faster)
          const tokenUser = getUserFromToken()
          if (tokenUser) {
            setUser({
              id: tokenUser.id,
              email: tokenUser.email,
              username: tokenUser.username,
              full_name: tokenUser.username, // Temporary fallback
              role: tokenUser.role as User['role'],
              is_active: true,
              created_at: '',
              updated_at: '',
            })
          }

          // Then fetch full user data
          await refreshUser()
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
        removeToken()
      } finally {
        setLoading(false)
      }
    }

    initializeAuth()
  }, [])

  const login = async (credentials: LoginCredentials) => {
    try {
      setLoading(true)
      const response = await authApi.login(credentials)
      const authData: AuthResponse = response.data

      setToken(authData.access_token)
      setUser(authData.user)

      toast.success('Welcome back!')

      // Navigate to appropriate dashboard based on role
      const dashboardRoute = getDashboardRoute(authData.user.role)
      navigate(dashboardRoute)
    } catch (error: any) {
      toast.error(error.message || 'Login failed')
      throw error
    } finally {
      setLoading(false)
    }
  }

  const register = async (userData: RegisterData) => {
    try {
      setLoading(true)
      const response = await authApi.register(userData)
      const authData: AuthResponse = response.data

      setToken(authData.access_token)
      setUser(authData.user)

      toast.success('Account created successfully!')

      // Navigate to appropriate dashboard based on role
      const dashboardRoute = getDashboardRoute(authData.user.role)
      navigate(dashboardRoute)
    } catch (error: any) {
      toast.error(error.message || 'Registration failed')
      throw error
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    removeToken()
    setUser(null)
    toast.success('Logged out successfully')
    navigate('/login')
  }

  const refreshUser = async () => {
    try {
      const response = await authApi.getCurrentUser()
      setUser(response.data)
    } catch (error) {
      console.error('Failed to refresh user:', error)
      logout()
    }
  }

   const getDashboardRoute = (role: string): string => {
    switch (role) {
      case 'intern':
      case 'engineer':
        return '/dashboard/intern'
      case 'team_lead':
      case 'manager':
        return '/dashboard/team-lead'
      case 'hr':
        return '/dashboard/hr'
      case 'admin':
        return '/dashboard/admin'
      default:
        return '/dashboard/intern'
    }
  }

  const value: AuthContextType = {
    user,
    loading,
    login,
    register,
    logout,
    refreshUser,
    isAuthenticated: !!user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
