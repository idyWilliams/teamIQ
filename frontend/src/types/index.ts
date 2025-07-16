export interface User {
  id: number
  email: string
  username: string
  full_name: string
  role: 'intern' | 'engineer' | 'team_lead' | 'manager' | 'hr' | 'recruiter' | 'admin'
  is_active: boolean
  avatar_url?: string
  bio?: string
  linkedin_url?: string
  github_username?: string
  slack_user_id?: string
  created_at: string
  updated_at: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  full_name: string
  role: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface Team {
  id: number
  name: string
  description?: string
  team_lead_id?: number
  created_at: string
  updated_at: string
}

export interface Skill {
  id: number
  name: string
  category: 'technical' | 'soft' | 'domain'
  description?: string
  proficiency_score: number
  trend: 'improving' | 'stable' | 'declining'
  confidence: number
  evidence_count: number
  last_updated: string
}

export interface Project {
  id: number
  name: string
  description?: string
  status: 'active' | 'completed' | 'on_hold'
  team_id?: number
  team_name?: string
  github_repo?: string
  jira_project_key?: string
  start_date?: string
  end_date?: string
  created_at: string
  updated_at: string
}

export interface Task {
  id: number
  title: string
  description?: string
  status: 'todo' | 'in_progress' | 'done'
  priority: 'low' | 'medium' | 'high'
  assigned_to?: number
  assignee_name?: string
  project_id?: number
  project_name?: string
  jira_ticket_id?: string
  story_points?: number
  due_date?: string
  created_at: string
  updated_at: string
}

export interface Notification {
  id: number
  title: string
  message: string
  type: 'info' | 'warning' | 'error' | 'success'
  is_read: boolean
  action_url?: string
  created_at: string
}

export interface DashboardData {
  user_info: {
    id: number
    full_name: string
    role: string
    avatar_url?: string
    github_username?: string
  }
  summary: {
    active_projects: number
    completion_rate: number
    skill_count: number
    recent_activity_count: number
  }
  recent_activity: ActivityItem[]
  skill_insights: SkillInsights
  task_summary: TaskSummary
  notifications: Notification[]
}

export interface ActivityItem {
  type: 'commit' | 'pull_request' | 'task' | 'review'
  title: string
  date: string
  url?: string
  repository?: string
  state?: string
}

export interface SkillInsights {
  categories: Record<string, number>
  detailed_skills: Record<string, Skill[]>
  overall_score: number
}

export interface TaskSummary {
  total_tasks: number
  completed_tasks: number
  in_progress_tasks: number
  pending_tasks: number
  overdue_tasks: number
}

export interface TeamDashboardData {
  team_info: {
    id: number
    name: string
    description?: string
    team_lead: string
  }
  team_metrics: {
    total_members: number
    active_projects: number
    completed_projects: number
    project_completion_rate: number
  }
  team_sentiment: {
    overall_sentiment: string
    trend: string
    blocker_count: number
    health_score: number
  }
  skill_matrix: {
    skill_coverage: Record<string, number>
    team_strengths: SkillStrength[]
    team_weaknesses: SkillWeakness[]
  }
  project_status: Project[]
  blockers: Blocker[]
}

export interface SkillStrength {
  skill: string
  average_score: number
  coverage: number
}

export interface SkillWeakness {
  skill: string
  average_score: number
  coverage: number
}

export interface Blocker {
  type: 'technical' | 'process' | 'communication' | 'resource'
  description: string
  severity: 'high' | 'medium' | 'low'
  urgency: 'immediate' | 'soon' | 'later'
  affected_users: string[]
  evidence: string
  suggested_action: string
  timestamp: string
}

export interface SkillAnalysis {
  user_id: number
  skills: Skill[]
  skill_radar: SkillRadarData
  skill_gaps: SkillGap[]
  recommendations: string[]
}

export interface SkillRadarData {
  categories: Record<string, number>
  detailed_skills: Record<string, Skill[]>
  overall_score: number
}

export interface SkillGap {
  skill: string
  current_level: number
  required_level: number
  gap_severity: 'high' | 'medium' | 'low'
  recommendation: string
}

export interface TaskAllocation {
  task_assignments: TaskAssignment[]
  team_metrics: {
    total_tasks: number
    assigned_tasks: number
    assignment_rate: number
    workload_distribution: Record<string, WorkloadInfo>
  }
  optimization_notes: string[]
}

export interface TaskAssignment {
  task_id: string
  task_title: string
  recommended_assignees: RecommendedAssignee[]
  priority: string
  estimated_hours: number
  required_skills: string[]
  assignment_reasoning: string
}

export interface RecommendedAssignee {
  member_id: string
  member_name: string
  match_score: number
  skill_match: number
  workload_impact: WorkloadImpact
  growth_potential: number
  availability: number
  recommendation_reason: string
}

export interface WorkloadImpact {
  current_hours: number
  new_hours: number
  current_utilization: number
  new_utilization: number
  impact_level: 'high' | 'medium' | 'low'
}

export interface WorkloadInfo {
  name: string
  assigned_tasks: number
  current_workload: number
  utilization: number
}

export interface Analytics {
  productivity_metrics: {
    task_completion_rate: number
    total_tasks: number
    completed_tasks: number
    code_commits: number
    lines_of_code: number
    commit_frequency: number
  }
  code_quality_metrics: {
    total_commits: number
    total_pull_requests: number
    merged_pull_requests: number
    pr_merge_rate: number
    avg_commit_size: number
  }
  collaboration_metrics: {
    code_reviews_given: number
    messages_sent: number
    collaboration_score: number
  }
  time_analysis: {
    total_logged_hours: number
    avg_hours_per_day: number
    worklog_entries: number
  }
}

export interface SentimentAnalysis {
  overall_sentiment: string
  trend: string
  sentiment_timeline: SentimentTimelinePoint[]
  blocker_frequency: number
  team_health_score: number
  total_messages: number
  analyzed_messages: number
  blocker_count: number
  recommendations: string[]
}

export interface SentimentTimelinePoint {
  date: string
  sentiment_score: number
  message_count: number
}

export interface Integration {
  id: number
  name: string
  is_active: boolean
  status: 'connected' | 'disconnected' | 'error'
  last_sync?: string
  config_summary: Record<string, any>
}

export interface IntegrationStatus {
  status: 'connected' | 'not_configured' | 'error'
  message?: string
  user?: string
  team?: string
  server?: string
  last_tested?: string
}

export interface ChartData {
  labels: string[]
  datasets: {
    label: string
    data: number[]
    backgroundColor?: string | string[]
    borderColor?: string | string[]
    borderWidth?: number
    fill?: boolean
  }[]
}

export interface ChartOptions {
  responsive?: boolean
  maintainAspectRatio?: boolean
  plugins?: {
    legend?: {
      display?: boolean
      position?: 'top' | 'bottom' | 'left' | 'right'
    }
    tooltip?: {
      enabled?: boolean
    }
  }
  scales?: {
    x?: {
      display?: boolean
      grid?: {
        display?: boolean
      }
    }
    y?: {
      display?: boolean
      grid?: {
        display?: boolean
      }
      beginAtZero?: boolean
    }
  }
}

export interface ApiError {
  message: string
  status?: number
  details?: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface FilterOptions {
  search?: string
  status?: string
  priority?: string
  assigned_to?: number
  project_id?: number
  team_id?: number
  date_from?: string
  date_to?: string
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface TableColumn {
  key: string
  label: string
  sortable?: boolean
  render?: (value: any, row: any) => React.ReactNode
  className?: string
}

export interface TableProps {
  columns: TableColumn[]
  data: any[]
  loading?: boolean
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  onSort?: (column: string) => void
  onRowClick?: (row: any) => void
  className?: string
}

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
}

export interface FormField {
  name: string
  label: string
  type: 'text' | 'email' | 'password' | 'number' | 'select' | 'textarea' | 'date' | 'checkbox'
  required?: boolean
  placeholder?: string
  options?: { value: string; label: string }[]
  validation?: {
    required?: boolean
    minLength?: number
    maxLength?: number
    pattern?: RegExp
    custom?: (value: any) => string | null
  }
}

export interface FormConfig {
  fields: FormField[]
  onSubmit: (data: any) => void | Promise<void>
  initialValues?: Record<string, any>
  submitText?: string
  cancelText?: string
  onCancel?: () => void
}
