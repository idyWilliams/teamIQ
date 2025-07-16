export const ROLES = {
  INTERN: 'intern',
  TEAM_LEAD: 'team_lead',
  HR: 'hr',
  RECRUITER: 'recruiter',
  ADMIN: 'admin',
} as const;

export const TASK_STATUS = {
  TODO: 'todo',
  IN_PROGRESS: 'in_progress',
  DONE: 'done',
} as const;

export const TASK_PRIORITY = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
} as const;

export const PROJECT_STATUS = {
  ACTIVE: 'active',
  COMPLETED: 'completed',
  ON_HOLD: 'on_hold',
} as const;

export const SKILL_CATEGORIES = {
  TECHNICAL: 'technical',
  SOFT: 'soft',
  DOMAIN: 'domain',
} as const;

export const SENTIMENT_THRESHOLDS = {
  POSITIVE: 20,
  NEUTRAL: -20,
  NEGATIVE: -20,
} as const;

export const INTEGRATION_PLATFORMS = {
  GITHUB: 'github',
  JIRA: 'jira',
  SLACK: 'slack',
} as const;

export const NOTIFICATION_TYPES = {
  TASK: 'task',
  MENTION: 'mention',
  ALERT: 'alert',
  SYSTEM: 'system',
} as const;

export const ALERT_SEVERITIES = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
} as const;

export const TRENDS = {
  UP: 'up',
  DOWN: 'down',
  STABLE: 'stable',
} as const;

export const COLORS = {
  PRIMARY: '#1e40af', // blue-700
  SUCCESS: '#16a34a', // green-600
  WARNING: '#ca8a04', // yellow-600
  ERROR: '#dc2626', // red-600
  INFO: '#2563eb', // blue-600
  GRAY: '#6b7280', // gray-500
} as const;

export const CHART_COLORS = [
  '#3b82f6', // blue-500
  '#10b981', // emerald-500
  '#f59e0b', // amber-500
  '#ef4444', // red-500
  '#8b5cf6', // violet-500
  '#06b6d4', // cyan-500
  '#84cc16', // lime-500
  '#f97316', // orange-500
  '#ec4899', // pink-500
  '#6366f1', // indigo-500
];

export const DATE_FORMATS = {
  SHORT: 'MMM d, yyyy',
  LONG: 'MMMM d, yyyy',
  WITH_TIME: 'MMM d, yyyy h:mm a',
  TIME_ONLY: 'h:mm a',
} as const;
