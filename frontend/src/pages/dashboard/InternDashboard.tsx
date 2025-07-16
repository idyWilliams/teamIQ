import React from "react";
import { useQuery } from "react-query";
import {
  Brain,
  CheckSquare,
  TrendingUp,
  Calendar,
  Github,
  MessageSquare,
  Target,
  Award,
} from "lucide-react";
import { dashboardApi } from "../../lib/api";
import { DashboardData } from "../../types";
import DashboardCard from "../../components/dashboard/DashboardCard";
import SkillRadarChart from "../../components/dashboard/SkillRadarChart";
import TaskList from "../../components/dashboard/TaskList";
import Card, { CardHeader, CardContent } from "../../components/ui/Card";
import LoadingSpinner from "../../components/ui/LoadingSpinnerSpinner";
import Badge from "../../components/ui/Badge";
import { formatRelativeTime } from "../../lib/utils";

const InternDashboard: React.FC = () => {
  const { data, isLoading, error } = useQuery<DashboardData>(
    "internDashboard",
    dashboardApi.getInternDashboard
  );

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="large" text="Loading dashboard..." />
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

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-primary text-white rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">
              Welcome back, {data.user_info.full_name}!
            </h1>
            <p className="text-blue-100 mt-1">
              Here's what's happening with your projects today
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-blue-100">Overall Progress</p>
            <p className="text-3xl font-bold">
              {data.summary.completion_rate.toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardCard
          title="Active Projects"
          value={data.summary.active_projects}
          icon={Target}
          iconColor="text-blue-600"
        />
        <DashboardCard
          title="Completion Rate"
          value={`${data.summary.completion_rate.toFixed(1)}%`}
          icon={TrendingUp}
          iconColor="text-green-600"
        />
        <DashboardCard
          title="Skills Tracked"
          value={data.summary.skill_count}
          icon={Brain}
          iconColor="text-purple-600"
        />
        <DashboardCard
          title="Recent Activity"
          value={data.summary.recent_activity_count}
          icon={MessageSquare}
          iconColor="text-orange-600"
        />
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Skills Chart */}
        <SkillRadarChart data={data.skill_insights} />

        {/* Task Summary */}
        <Card>
          <CardHeader title="Task Overview" />
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Total Tasks</span>
                <span className="font-semibold">
                  {data.task_summary.total_tasks}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Completed</span>
                <span className="font-semibold text-green-600">
                  {data.task_summary.completed_tasks}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">In Progress</span>
                <span className="font-semibold text-blue-600">
                  {data.task_summary.in_progress_tasks}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Pending</span>
                <span className="font-semibold text-gray-600">
                  {data.task_summary.pending_tasks}
                </span>
              </div>
              {data.task_summary.overdue_tasks > 0 && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Overdue</span>
                  <span className="font-semibold text-red-600">
                    {data.task_summary.overdue_tasks}
                  </span>
                </div>
              )}
            </div>

            <div className="mt-6">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all duration-300"
                  style={{
                    width: `${
                      (data.task_summary.completed_tasks /
                        data.task_summary.total_tasks) *
                      100
                    }%`,
                  }}
                />
              </div>
              <p className="text-sm text-gray-500 mt-2">
                {data.task_summary.completed_tasks} of{" "}
                {data.task_summary.total_tasks} tasks completed
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity and Notifications */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <Card>
          <CardHeader title="Recent Activity" />
          <CardContent>
            {data.recent_activity.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No recent activity</p>
              </div>
            ) : (
              <div className="space-y-4">
                {data.recent_activity.map((activity, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      {activity.type === "commit" && (
                        <Github className="h-4 w-4 text-gray-500" />
                      )}
                      {activity.type === "pull_request" && (
                        <CheckSquare className="h-4 w-4 text-blue-500" />
                      )}
                      {activity.type === "task" && (
                        <Target className="h-4 w-4 text-green-500" />
                      )}
                      {activity.type === "review" && (
                        <MessageSquare className="h-4 w-4 text-purple-500" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {activity.title}
                      </p>
                      <div className="flex items-center text-sm text-gray-500 mt-1">
                        <span>{formatRelativeTime(activity.date)}</span>
                        {activity.repository && (
                          <span className="ml-2">• {activity.repository}</span>
                        )}
                        {activity.state && (
                          <Badge
                            variant={
                              activity.state === "merged"
                                ? "success"
                                : "secondary"
                            }
                            size="sm"
                            className="ml-2"
                          >
                            {activity.state}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Notifications */}
        <Card>
          <CardHeader title="Notifications" />
          <CardContent>
            {data.notifications.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No new notifications</p>
              </div>
            ) : (
              <div className="space-y-4">
                {data.notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`p-3 rounded-lg border ${
                      notification.is_read
                        ? "bg-gray-50"
                        : "bg-blue-50 border-blue-200"
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">
                          {notification.title}
                        </p>
                        <p className="text-sm text-gray-600 mt-1">
                          {notification.message}
                        </p>
                        <p className="text-xs text-gray-500 mt-2">
                          {formatRelativeTime(notification.created_at)}
                        </p>
                      </div>
                      <Badge
                        variant={
                          notification.type === "error" ? "error" : "secondary"
                        }
                        size="sm"
                      >
                        {notification.type}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default InternDashboard;
