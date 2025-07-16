import { pgTable, serial, varchar, text, timestamp, integer, boolean, jsonb, decimal } from 'drizzle-orm/pg-core';
import { relations } from 'drizzle-orm';

export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  email: varchar('email', { length: 255 }).unique().notNull(),
  username: varchar('username', { length: 100 }).unique().notNull(),
  password_hash: varchar('password_hash', { length: 255 }).notNull(),
  first_name: varchar('first_name', { length: 100 }).notNull(),
  last_name: varchar('last_name', { length: 100 }).notNull(),
  role: varchar('role', { length: 50 }).notNull().default('intern'),
  profile_picture: varchar('profile_picture', { length: 255 }),
  bio: text('bio'),
  linkedin_profile: varchar('linkedin_profile', { length: 255 }),
  github_username: varchar('github_username', { length: 100 }),
  jira_username: varchar('jira_username', { length: 100 }),
  slack_user_id: varchar('slack_user_id', { length: 100 }),
  is_active: boolean('is_active').default(true),
  created_at: timestamp('created_at').defaultNow(),
  updated_at: timestamp('updated_at').defaultNow(),
});

export const teams = pgTable('teams', {
  id: serial('id').primaryKey(),
  name: varchar('name', { length: 100 }).notNull(),
  description: text('description'),
  team_lead_id: integer('team_lead_id').references(() => users.id),
  created_at: timestamp('created_at').defaultNow(),
  updated_at: timestamp('updated_at').defaultNow(),
});

export const team_members = pgTable('team_members', {
  id: serial('id').primaryKey(),
  team_id: integer('team_id').references(() => teams.id),
  user_id: integer('user_id').references(() => users.id),
  joined_at: timestamp('joined_at').defaultNow(),
});

export const projects = pgTable('projects', {
  id: serial('id').primaryKey(),
  name: varchar('name', { length: 100 }).notNull(),
  description: text('description'),
  team_id: integer('team_id').references(() => teams.id),
  status: varchar('status', { length: 50 }).default('active'),
  start_date: timestamp('start_date'),
  end_date: timestamp('end_date'),
  github_repo: varchar('github_repo', { length: 255 }),
  jira_project_key: varchar('jira_project_key', { length: 50 }),
  created_at: timestamp('created_at').defaultNow(),
  updated_at: timestamp('updated_at').defaultNow(),
});

export const skills = pgTable('skills', {
  id: serial('id').primaryKey(),
  name: varchar('name', { length: 100 }).unique().notNull(),
  category: varchar('category', { length: 50 }).notNull(),
  description: text('description'),
  created_at: timestamp('created_at').defaultNow(),
});

export const user_skills = pgTable('user_skills', {
  id: serial('id').primaryKey(),
  user_id: integer('user_id').references(() => users.id),
  skill_id: integer('skill_id').references(() => skills.id),
  proficiency_level: decimal('proficiency_level', { precision: 3, scale: 2 }).notNull(),
  evidence: jsonb('evidence'),
  last_updated: timestamp('last_updated').defaultNow(),
});

export const tasks = pgTable('tasks', {
  id: serial('id').primaryKey(),
  external_id: varchar('external_id', { length: 100 }).notNull(),
  title: varchar('title', { length: 255 }).notNull(),
  description: text('description'),
  project_id: integer('project_id').references(() => projects.id),
  assignee_id: integer('assignee_id').references(() => users.id),
  reporter_id: integer('reporter_id').references(() => users.id),
  status: varchar('status', { length: 50 }).notNull(),
  priority: varchar('priority', { length: 50 }),
  story_points: integer('story_points'),
  due_date: timestamp('due_date'),
  created_at: timestamp('created_at').defaultNow(),
  updated_at: timestamp('updated_at').defaultNow(),
});

export const commits = pgTable('commits', {
  id: serial('id').primaryKey(),
  sha: varchar('sha', { length: 100 }).unique().notNull(),
  user_id: integer('user_id').references(() => users.id),
  project_id: integer('project_id').references(() => projects.id),
  message: text('message').notNull(),
  additions: integer('additions').default(0),
  deletions: integer('deletions').default(0),
  files_changed: integer('files_changed').default(0),
  languages: jsonb('languages'),
  commit_date: timestamp('commit_date').notNull(),
  created_at: timestamp('created_at').defaultNow(),
});

export const pull_requests = pgTable('pull_requests', {
  id: serial('id').primaryKey(),
  external_id: integer('external_id').notNull(),
  title: varchar('title', { length: 255 }).notNull(),
  author_id: integer('author_id').references(() => users.id),
  project_id: integer('project_id').references(() => projects.id),
  status: varchar('status', { length: 50 }).notNull(),
  additions: integer('additions').default(0),
  deletions: integer('deletions').default(0),
  files_changed: integer('files_changed').default(0),
  review_comments: integer('review_comments').default(0),
  created_at: timestamp('created_at').defaultNow(),
  merged_at: timestamp('merged_at'),
});

export const messages = pgTable('messages', {
  id: serial('id').primaryKey(),
  external_id: varchar('external_id', { length: 100 }).notNull(),
  user_id: integer('user_id').references(() => users.id),
  channel_id: varchar('channel_id', { length: 100 }).notNull(),
  content: text('content').notNull(),
  sentiment_score: decimal('sentiment_score', { precision: 3, scale: 2 }),
  is_blocker: boolean('is_blocker').default(false),
  mentions: jsonb('mentions'),
  reactions: jsonb('reactions'),
  message_date: timestamp('message_date').notNull(),
  created_at: timestamp('created_at').defaultNow(),
});

export const retrospectives = pgTable('retrospectives', {
  id: serial('id').primaryKey(),
  title: varchar('title', { length: 255 }).notNull(),
  project_id: integer('project_id').references(() => projects.id),
  team_id: integer('team_id').references(() => teams.id),
  period_start: timestamp('period_start').notNull(),
  period_end: timestamp('period_end').notNull(),
  summary: text('summary'),
  achievements: jsonb('achievements'),
  challenges: jsonb('challenges'),
  action_items: jsonb('action_items'),
  metrics: jsonb('metrics'),
  created_by: integer('created_by').references(() => users.id),
  created_at: timestamp('created_at').defaultNow(),
});

export const notifications = pgTable('notifications', {
  id: serial('id').primaryKey(),
  user_id: integer('user_id').references(() => users.id),
  title: varchar('title', { length: 255 }).notNull(),
  message: text('message').notNull(),
  type: varchar('type', { length: 50 }).notNull(),
  is_read: boolean('is_read').default(false),
  metadata: jsonb('metadata'),
  created_at: timestamp('created_at').defaultNow(),
});

export const integration_configs = pgTable('integration_configs', {
  id: serial('id').primaryKey(),
  type: varchar('type', { length: 50 }).notNull(),
  config: jsonb('config').notNull(),
  is_active: boolean('is_active').default(true),
  created_at: timestamp('created_at').defaultNow(),
  updated_at: timestamp('updated_at').defaultNow(),
});

// Relations
export const usersRelations = relations(users, ({ many }) => ({
  teamMemberships: many(team_members),
  ledTeams: many(teams),
  assignedTasks: many(tasks),
  reportedTasks: many(tasks),
  skills: many(user_skills),
  commits: many(commits),
  pullRequests: many(pull_requests),
  messages: many(messages),
  notifications: many(notifications),
  retrospectives: many(retrospectives),
}));

export const teamsRelations = relations(teams, ({ one, many }) => ({
  teamLead: one(users, { fields: [teams.team_lead_id], references: [users.id] }),
  members: many(team_members),
  projects: many(projects),
  retrospectives: many(retrospectives),
}));

export const team_membersRelations = relations(team_members, ({ one }) => ({
  team: one(teams, { fields: [team_members.team_id], references: [teams.id] }),
  user: one(users, { fields: [team_members.user_id], references: [users.id] }),
}));

export const projectsRelations = relations(projects, ({ one, many }) => ({
  team: one(teams, { fields: [projects.team_id], references: [teams.id] }),
  tasks: many(tasks),
  commits: many(commits),
  pullRequests: many(pull_requests),
  retrospectives: many(retrospectives),
}));

export const skillsRelations = relations(skills, ({ many }) => ({
  userSkills: many(user_skills),
}));

export const user_skillsRelations = relations(user_skills, ({ one }) => ({
  user: one(users, { fields: [user_skills.user_id], references: [users.id] }),
  skill: one(skills, { fields: [user_skills.skill_id], references: [skills.id] }),
}));

export const tasksRelations = relations(tasks, ({ one }) => ({
  project: one(projects, { fields: [tasks.project_id], references: [projects.id] }),
  assignee: one(users, { fields: [tasks.assignee_id], references: [users.id] }),
  reporter: one(users, { fields: [tasks.reporter_id], references: [users.id] }),
}));

export const commitsRelations = relations(commits, ({ one }) => ({
  user: one(users, { fields: [commits.user_id], references: [users.id] }),
  project: one(projects, { fields: [commits.project_id], references: [projects.id] }),
}));

export const pull_requestsRelations = relations(pull_requests, ({ one }) => ({
  author: one(users, { fields: [pull_requests.author_id], references: [users.id] }),
  project: one(projects, { fields: [pull_requests.project_id], references: [projects.id] }),
}));

export const messagesRelations = relations(messages, ({ one }) => ({
  user: one(users, { fields: [messages.user_id], references: [users.id] }),
}));

export const retrospectivesRelations = relations(retrospectives, ({ one }) => ({
  project: one(projects, { fields: [retrospectives.project_id], references: [projects.id] }),
  team: one(teams, { fields: [retrospectives.team_id], references: [teams.id] }),
  creator: one(users, { fields: [retrospectives.created_by], references: [users.id] }),
}));

export const notificationsRelations = relations(notifications, ({ one }) => ({
  user: one(users, { fields: [notifications.user_id], references: [users.id] }),
}));

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;
export type Team = typeof teams.$inferSelect;
export type InsertTeam = typeof teams.$inferInsert;
export type Project = typeof projects.$inferSelect;
export type InsertProject = typeof projects.$inferInsert;
export type Skill = typeof skills.$inferSelect;
export type InsertSkill = typeof skills.$inferInsert;
export type UserSkill = typeof user_skills.$inferSelect;
export type InsertUserSkill = typeof user_skills.$inferInsert;
export type Task = typeof tasks.$inferSelect;
export type InsertTask = typeof tasks.$inferInsert;
export type Commit = typeof commits.$inferSelect;
export type InsertCommit = typeof commits.$inferInsert;
export type PullRequest = typeof pull_requests.$inferSelect;
export type InsertPullRequest = typeof pull_requests.$inferInsert;
export type Message = typeof messages.$inferSelect;
export type InsertMessage = typeof messages.$inferInsert;
export type Retrospective = typeof retrospectives.$inferSelect;
export type InsertRetrospective = typeof retrospectives.$inferInsert;
export type Notification = typeof notifications.$inferSelect;
export type InsertNotification = typeof notifications.$inferInsert;
export type IntegrationConfig = typeof integration_configs.$inferSelect;
export type InsertIntegrationConfig = typeof integration_configs.$inferInsert;
