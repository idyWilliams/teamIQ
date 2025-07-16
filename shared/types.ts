export interface AuthUser {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: 'intern' | 'team_lead' | 'hr' | 'recruiter' | 'admin';
  profile_picture?: string;
  bio?: string;
  linkedin_profile?: string;
  is_active: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterUser {
  username: string;
  email: string;
  password: string;
  full_name: string;
  role: 'intern' | 'team_lead' | 'hr' | 'recruiter' | 'admin';
}

export interface SkillData {
  id: number;
  name: string;
  category: string;
  proficiency_level: number;
  trend: 'up' | 'down' | 'stable';
  evidence_count: number;
  last_updated: string;
}

export interface TaskData {
  id: number;
  title: string;
  description?: string;
  status: 'todo' | 'in_progress' | 'done';
  priority: 'low' | 'medium' | 'high';
  project_name?: string;
  assignee_name?: string;
  due_date?: string;
  external_id?: string;
}

export interface ProjectData {
  id: number;
  name: string;
  description?: string;
  status: 'active' | 'completed' | 'on_hold';
  start_date?: string;
  end_date?: string;
  team_name?: string;
  task_count?: number;
  completion_percentage?: number;
}

export interface TeamMemberData {
  id: number;
  full_name: string;
  role: string;
  profile_picture?: string;
  key_skills: string[];
  current_tasks: number;
  sentiment_score: number;
  productivity_score: number;
}

export interface SentimentData {
  user_id: number;
  user_name: string;
  sentiment_score: number;
  confidence: number;
  has_blockers: boolean;
  blocker_keywords: string[];
  trend: 'improving' | 'declining' | 'stable';
  analyzed_at: string;
}

export interface RetrospectiveData {
  id: number;
  title: string;
  period_start: string;
  period_end: string;
  project_name?: string;
  team_name?: string;
  summary: string;
  achievements: string[];
  challenges: string[];
  action_items: string[];
  skill_insights: any;
  performance_metrics: any;
  created_at: string;
}

export interface NotificationData {
  id: number;
  title: string;
  message: string;
  type: 'task' | 'mention' | 'alert' | 'system';
  is_read: boolean;
  data?: any;
  created_at: string;
}

export interface DashboardStats {
  total_tasks: number;
  completed_tasks: number;
  active_projects: number;
  team_members: number;
  avg_sentiment: number;
  skills_improved: number;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface TaskAllocationRecommendation {
  task_id: number;
  recommended_assignee: number;
  assignee_name: string;
  confidence: number;
  reasons: string[];
  skill_match: number;
  workload_factor: number;
  growth_opportunity: number;
}

export interface IntegrationStatus {
  platform: 'github' | 'jira' | 'slack';
  is_connected: boolean;
  username?: string;
  last_sync?: string;
  error?: string;
}
