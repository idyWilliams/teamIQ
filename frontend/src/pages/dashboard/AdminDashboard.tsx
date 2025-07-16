/* eslint-disable @typescript-eslint/no-explicit-any */
import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Shield,
  Server,
  Users,
  Activity,
  Database,
  AlertCircle,
  CheckCircle,
  Clock,

} from "lucide-react";
import { dashboardApi } from "../../lib/api";

import Card, { CardHeader, CardContent } from "../../components/ui/Card";
import LoadingSpinner from "../../components/ui/LoadingSpinner";
import Badge from "../../components/ui/Badge";
import { LineChart, BarChart } from "../../components/ui/Chart";
import { ChartData } from "../../types";
import DashboardCard from "../../components/Dashboard/DashboardCard";

const AdminDashboard: React.FC = () => {
  const { data, isLoading, error } = useQuery(
    "adminDashboard",
    dashboardApi.getAdminDashboard
  );

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" text="Loading dashboard..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">Failed to load dashboard data</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">No dashboard data available</p>
      </div>
    );
  }

  // Mock data for admin dashboard
  const mockData = {
    system_health: {
      uptime: "99.9%",
      active_users: 48,
      api_response_time: "120ms",
      database_status: "healthy",
    },
    user_management: {
      total_users: 52,
      active_users: 48,
      pending_approvals: 3,
      recent_registrations: [
        {
          name: "John Doe",
          email: "john@example.com",
          role: "intern",
          date: "2024-01-15",
        },
        {
          name: "Jane Smith",
          email: "jane@example.com",
          role: "engineer",
          date: "2024-01-14",
        },
      ],
    },
    integrations: {
      github_status: "connected",
      jira_status: "connected",
      slack_status: "connected",
      openai_status: "connected",
    },
    security: {
      failed_login_attempts: 5,
      security_alerts: [
        {
          type: "info",
          message: "System backup completed successfully",
          time: "2 hours ago",
        },
        {
          type: "warning",
          message: "API rate limit approaching for GitHub",
          time: "5 hours ago",
        },
      ],
      last_backup: new Date().toISOString(),
    },
  };

  const systemMetricsData: ChartData = {
    labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
    datasets: [
      {
        label: "Active Users",
        data: [35, 38, 42, 45, 47, 48],
        borderColor: "rgba(30, 64, 175, 1)",
        backgroundColor: "rgba(30, 64, 175, 0.1)",
        borderWidth: 2,
        fill: true,
      },
      {
        label: "API Calls (x1000)",
        data: [120, 135, 150, 165, 180, 195],
        borderColor: "rgba(34, 197, 94, 1)",
        backgroundColor: "rgba(34, 197, 94, 0.1)",
        borderWidth: 2,
        fill: true,
      },
    ],
  };

  const integrationStatusData: ChartData = {
    labels: ["GitHub", "Jira", "Slack", "OpenAI"],
    datasets: [
      {
        label: "Uptime %",
        data: [99.9, 99.5, 99.8, 99.2],
        backgroundColor: "rgba(34, 197, 94, 0.8)",
        borderColor: "rgba(34, 197, 94, 1)",
        borderWidth: 1,
      },
    ],
  };

  const getIntegrationStatus = (status: string) => {
    switch (status) {
      case "connected":
        return { color: "success", icon: CheckCircle };
      case "disconnected":
        return { color: "error", icon: AlertCircle };
      default:
        return { color: "warning", icon: Clock };
    }
  };

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-primary text-white rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">System Administration</h1>
            <p className="text-blue-100 mt-1">
              Monitor system health, users, and integrations
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-blue-100">System Uptime</p>
            <p className="text-3xl font-bold">
              {mockData.system_health.uptime}
            </p>
          </div>
        </div>
      </div>

      {/* System Health Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardCard
          title="Active Users"
          value={mockData.system_health.active_users}
          icon={Users}
          iconColor="text-blue-600"
        />
        <DashboardCard
          title="API Response Time"
          value={mockData.system_health.api_response_time}
          icon={Activity}
          iconColor="text-green-600"
        />
        <DashboardCard
          title="Database Status"
          value="Healthy"
          icon={Database}
          iconColor="text-purple-600"
        />
        <DashboardCard
          title="Security Alerts"
          value={mockData.security.security_alerts.length}
          icon={Shield}
          iconColor="text-red-600"
        />
      </div>

      {/* System Metrics */}
      <Card>
        <CardHeader title="System Metrics" />
        <CardContent>
          <div className="h-64">
            <LineChart data={systemMetricsData} />
          </div>
        </CardContent>
      </Card>

      {/* User Management & Integrations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="User Management" />
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Total Users</span>
                <span className="font-semibold">
                  {mockData.user_management.total_users}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Active Users</span>
                <span className="font-semibold text-green-600">
                  {mockData.user_management.active_users}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Pending Approvals</span>
                <span className="font-semibold text-orange-600">
                  {mockData.user_management.pending_approvals}
                </span>
              </div>
            </div>

            <div className="mt-6">
              <h4 className="font-medium text-gray-900 mb-3">
                Recent Registrations
              </h4>
              <div className="space-y-2">
                {mockData.user_management.recent_registrations.map(
                  (user, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-2 bg-gray-50 rounded"
                    >
                      <div>
                        <p className="text-sm font-medium">{user.name}</p>
                        <p className="text-xs text-gray-500">{user.email}</p>
                      </div>
                      <Badge variant="secondary" size="sm">
                        {user.role}
                      </Badge>
                    </div>
                  )
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Integration Status" />
          <CardContent>
            <div className="space-y-4">
              {Object.entries(mockData.integrations).map(
                ([integration, status]) => {
                  const statusConfig = getIntegrationStatus(status);
                  const StatusIcon = statusConfig.icon;

                  return (
                    <div
                      key={integration}
                      className="flex items-center justify-between p-3 border border-gray-200 rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        <StatusIcon
                          className={`h-5 w-5 ${
                            statusConfig.color === "success"
                              ? "text-green-600"
                              : statusConfig.color === "error"
                              ? "text-red-600"
                              : "text-yellow-600"
                          }`}
                        />
                        <span className="font-medium capitalize">
                          {integration.replace("_", " ")}
                        </span>
                      </div>
                      <Badge variant={statusConfig.color as any} size="sm">
                        {status}
                      </Badge>
                    </div>
                  );
                }
              )}
            </div>

            <div className="mt-6">
              <h4 className="font-medium text-gray-900 mb-3">
                Integration Performance
              </h4>
              <div className="h-48">
                <BarChart data={integrationStatusData} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Security & Alerts */}
      <Card>
        <CardHeader title="Security & Alerts" />
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 mb-3">
                Security Summary
              </h4>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                  <span className="text-sm text-gray-700">
                    Failed Login Attempts
                  </span>
                  <Badge variant="error" size="sm">
                    {mockData.security.failed_login_attempts}
                  </Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                  <span className="text-sm text-gray-700">Last Backup</span>
                  <span className="text-sm text-gray-600">2 hours ago</span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-3">Recent Alerts</h4>
              <div className="space-y-3">
                {mockData.security.security_alerts.map((alert, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg ${
                      alert.type === "warning" ? "bg-yellow-50" : "bg-blue-50"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <p className="text-sm text-gray-700">{alert.message}</p>
                      <Badge
                        variant={
                          alert.type === "warning" ? "warning" : "primary"
                        }
                        size="sm"
                      >
                        {alert.type}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{alert.time}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader title="Quick Actions" />
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <button className="p-4 text-left border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
              <Users className="h-6 w-6 text-blue-600 mb-2" />
              <h4 className="font-medium text-gray-900">Manage Users</h4>
              <p className="text-sm text-gray-600">
                Add, edit, or deactivate users
              </p>
            </button>
            <button className="p-4 text-left border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
              <Server className="h-6 w-6 text-green-600 mb-2" />
              <h4 className="font-medium text-gray-900">System Settings</h4>
              <p className="text-sm text-gray-600">
                Configure system parameters
              </p>
            </button>
            <button className="p-4 text-left border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
              <Database className="h-6 w-6 text-purple-600 mb-2" />
              <h4 className="font-medium text-gray-900">Backup & Restore</h4>
              <p className="text-sm text-gray-600">Manage data backups</p>
            </button>
            <button className="p-4 text-left border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
              <Shield className="h-6 w-6 text-red-600 mb-2" />
              <h4 className="font-medium text-gray-900">Security Logs</h4>
              <p className="text-sm text-gray-600">Review security events</p>
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminDashboard;
