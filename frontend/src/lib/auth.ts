import { jwtDecode } from 'jwt-decode'

const TOKEN_KEY = 'isentry_token'

export interface DecodedToken {
  user_id: number
  email: string
  username: string
  role: string
  exp: number
  iat: number
}

export const getToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY)
}

export const setToken = (token: string): void => {
  localStorage.setItem(TOKEN_KEY, token)
}

export const removeToken = (): void => {
  localStorage.removeItem(TOKEN_KEY)
}

export const isTokenValid = (token: string): boolean => {
  try {
    const decoded: DecodedToken = jwtDecode(token)
    const currentTime = Date.now() / 1000
    return decoded.exp > currentTime
  } catch {
    return false
  }
}

export const getDecodedToken = (): DecodedToken | null => {
  const token = getToken()
  if (!token) return null
  
  try {
    return jwtDecode(token)
  } catch {
    return null
  }
}

export const getUserFromToken = (): {
  id: number
  email: string
  username: string
  role: string
} | null => {
  const decoded = getDecodedToken()
  if (!decoded) return null
  
  return {
    id: decoded.user_id,
    email: decoded.email,
    username: decoded.username,
    role: decoded.role,
  }
}

export const hasRole = (requiredRoles: string[]): boolean => {
  const user = getUserFromToken()
  if (!user) return false
  
  return requiredRoles.includes(user.role)
}

export const isAuthenticated = (): boolean => {
  const token = getToken()
  return token !== null && isTokenValid(token)
}

export const getRoleDisplayName = (role: string): string => {
  const roleMap: Record<string, string> = {
    intern: 'Intern',
    engineer: 'Engineer',
    team_lead: 'Team Lead',
    manager: 'Manager',
    hr: 'HR Personnel',
    recruiter: 'Recruiter',
    admin: 'Administrator',
  }
  
  return roleMap[role] || role
}

export const getRoleColor = (role: string): string => {
  const colorMap: Record<string, string> = {
    intern: 'bg-blue-100 text-blue-800',
    engineer: 'bg-green-100 text-green-800',
    team_lead: 'bg-purple-100 text-purple-800',
    manager: 'bg-purple-100 text-purple-800',
    hr: 'bg-orange-100 text-orange-800',
    recruiter: 'bg-pink-100 text-pink-800',
    admin: 'bg-red-100 text-red-800',
  }
  
  return colorMap[role] || 'bg-gray-100 text-gray-800'
}

export const canAccessRoute = (route: string, userRole: string): boolean => {
  const routePermissions: Record<string, string[]> = {
    '/dashboard/intern': ['intern', 'engineer'],
    '/dashboard/team-lead': ['team_lead', 'manager'],
    '/dashboard/hr': ['hr'],
    '/dashboard/admin': ['admin'],
    '/tasks/allocation': ['team_lead', 'manager', 'admin'],
    '/sentiment': ['team_lead', 'manager', 'hr', 'admin'],
    '/admin': ['admin'],
  }
  
  const allowedRoles = routePermissions[route]
  if (!allowedRoles) return true // Route accessible to all authenticated users
  
  return allowedRoles.includes(userRole)
}
