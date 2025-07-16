import axios, { AxiosResponse, AxiosError } from 'axios'
import { getToken, removeToken } from './auth'

// Create axios instance with default config
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    // Handle 401 errors (unauthorized)
    if (error.response?.status === 401) {
      removeToken()
      window.location.href = '/login'
    }
    
    // Handle network errors
    if (!error.response) {
      console.error('Network error:', error.message)
      return Promise.reject(new Error('Network error. Please check your connection.'))
    }
    
    // Handle other errors
    const errorMessage = error.response?.data?.detail || error.message
    return Promise.reject(new Error(errorMessage))
  }
)

// Auth API
export const authApi = {
  login: (credentials: { email: string; password: string }) =>
    api.post('/auth/login', credentials),
  
  register: (userData: {
    email: string
    username: string
    password: string
    full_name: string
    role: string
  }) => api.post('/auth/register', userData),
  
  requestPasswordReset: (email: string) =>
    api.post('/auth/password-reset', { email }),
  
  confirmPasswordReset: (token: string, new_password: string) =>
    api.post('/auth/password-reset/confirm', { token, new_password }),
  
  getCurrentUser: () => api.get('/auth/me'),
  
  logout: () => api.post('/auth/logout'),
  
  refreshToken: () => api.post('/auth/refresh'),
}

// Users API
export const usersApi = {
  getProfile: () => api.get('/users/profile'),
  
  updateProfile: (userData: {
    full_name?: string
    bio?: string
    linkedin_url?: string
    github_username?: string
    avatar_url?: string
  }) => api.put('/users/profile', userData),
  
  getUsers: () => api.get('/users/'),
  
  getUserById: (id: number) => api.get(`/users/${id}`),
  
  createUser: (userData: {
    email: string
    username: string
    full_name: string
    role: string
    password: string
  }) => api.post('/users/', userData),
  
  activateUser: (id: number) => api.put(`/users/${id}/activate`),
  
  deactivateUser: (id: number) => api.put(`/users/${id}/deactivate`),
  
  deleteUser: (id: number) => api.delete(`/users/${id}`),
}

// Dashboard API
export const dashboardApi = {
  getInternDashboard: () => api.get('/dashboard/intern'),
  
  getTeamLeadDashboard: () => api.get('/dashboard/team-lead'),
  
  getHRDashboard: () => api.get('/dashboard/hr'),
  
  getAdminDashboard: () => api.get('/dashboard/admin'),
  
  getAnalytics: () => api.get('/dashboard/analytics'),
}

// Skills API
export const skillsApi = {
  getUserSkills: () => api.get('/skills/'),
  
  getSkillAnalysis: () => api.get('/skills/analysis'),
  
  getTeamSkillMatrix: (teamId: number) => api.get(`/skills/team/${teamId}`),
  
  createSkill: (skillData: {
    name: string
    category: string
    description?: string
  }) => api.post('/skills/', skillData),
  
  updateSkill: (id: number, skillData: {
    name?: string
    category?: string
    description?: string
  }) => api.put(`/skills/${id}`, skillData),
  
  deleteSkill: (id: number) => api.delete(`/skills/${id}`),
  
  refreshSkills: () => api.post('/skills/refresh'),
}

// Tasks API
export const tasksApi = {
  getTasks: (params?: {
    project_id?: number
    assigned_to?: number
    status?: string
  }) => api.get('/tasks/', { params }),
  
  getTask: (id: number) => api.get(`/tasks/${id}`),
  
  createTask: (taskData: {
    title: string
    description?: string
    priority?: string
    project_id?: number
    assigned_to?: number
    jira_ticket_id?: string
    story_points?: number
    due_date?: string
  }) => api.post('/tasks/', taskData),
  
  updateTask: (id: number, taskData: {
    title?: string
    description?: string
    status?: string
    priority?: string
    assigned_to?: number
    story_points?: number
    due_date?: string
  }) => api.put(`/tasks/${id}`, taskData),
  
  deleteTask: (id: number) => api.delete(`/tasks/${id}`),
  
  allocateTasks: (allocationData: {
    project_id?: number
    team_id?: number
    constraints?: Record<string, any>
  }) => api.post('/tasks/allocate', allocationData),
  
  assignTask: (id: number, assigneeId: number) =>
    api.post(`/tasks/${id}/assign`, { assignee_id: assigneeId }),
  
  unassignTask: (id: number) => api.post(`/tasks/${id}/unassign`),
  
  getTaskSummary: () => api.get('/tasks/my/summary'),
}

// Projects API
export const projectsApi = {
  getProjects: (params?: {
    team_id?: number
    status?: string
  }) => api.get('/projects/', { params }),
  
  getProject: (id: number) => api.get(`/projects/${id}`),
  
  createProject: (projectData: {
    name: string
    description?: string
    team_id?: number
    github_repo?: string
    jira_project_key?: string
    start_date?: string
    end_date?: string
  }) => api.post('/projects/', projectData),
  
  updateProject: (id: number, projectData: {
    name?: string
    description?: string
    status?: string
    github_repo?: string
    jira_project_key?: string
    start_date?: string
    end_date?: string
  }) => api.put(`/projects/${id}`, projectData),
  
  deleteProject: (id: number) => api.delete(`/projects/${id}`),
  
  getProjectAnalytics: (id: number) => api.get(`/projects/${id}/analytics`),
  
  getProjectTasks: (id: number) => api.get(`/projects/${id}/tasks`),
  
  generateRetrospective: (id: number) => api.post(`/projects/${id}/retrospective`),
  
  getProjectHealth: (id: number) => api.get(`/projects/${id}/health`),
}

// Analytics API
export const analyticsApi = {
  getUserSkillAnalytics: (userId: number, days: number = 30) =>
    api.get(`/analytics/user/${userId}/skills`, { params: { days } }),
  
  getUserProductivityAnalytics: (userId: number, days: number = 30) =>
    api.get(`/analytics/user/${userId}/productivity`, { params: { days } }),
  
  getTeamAnalytics: (teamId: number, days: number = 30) =>
    api.get(`/analytics/team/${teamId}/analytics`, { params: { days } }),
  
  getBlockerInsights: (teamId?: number, days: number = 7) =>
    api.get('/analytics/insights/blockers', { params: { team_id: teamId, days } }),
  
  getSentimentInsights: (teamId?: number, days: number = 30) =>
    api.get('/analytics/insights/sentiment', { params: { team_id: teamId, days } }),
  
  getPerformanceReport: (params: {
    user_id?: number
    team_id?: number
    days?: number
  }) => api.get('/analytics/reports/performance', { params }),
}

// Integrations API
export const integrationsApi = {
  getIntegrations: () => api.get('/integrations/'),
  
  getIntegrationStatus: (name: string) => api.get(`/integrations/${name}/status`),
  
  testIntegration: (integrationData: {
    name: string
    config: Record<string, any>
  }) => api.post('/integrations/test', integrationData),
  
  syncIntegration: (name: string) => api.post(`/integrations/sync/${name}`),
  
  updateIntegrationConfig: (name: string, config: Record<string, any>) =>
    api.put(`/integrations/${name}/config`, config),
  
  removeIntegration: (name: string) => api.delete(`/integrations/${name}`),
  
  getGitHubRepos: () => api.get('/integrations/github/repos'),
  
  getJiraProjects: () => api.get('/integrations/jira/projects'),
  
  getSlackChannels: () => api.get('/integrations/slack/channels'),
}

export default api
