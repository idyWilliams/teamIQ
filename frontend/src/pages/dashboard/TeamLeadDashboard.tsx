import React from "react";
import { useQuery } from "react-query";
import {
  Users,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Calendar,
  Brain,
  MessageSquare,
  Target,
} from "lucide-react";
import { dashboardApi } from "../../lib/api";
import { TeamDashboardData } from "../../types";
import DashboardCard from "../../components/dashboard/DashboardCard";
import TeamMetrics from "../../components/dashboard/TeamMetrics";
import SentimentChart from "../../components/dashboard/SentimentChart";
import Card, { CardHeader, CardContent } from "../../components/ui/Card";
import LoadingSpinner from "../../components/ui/LoadingSpinnerSpinner";
import Badge from "../../components/ui/Badge";
import { formatDate } from "../../lib/utils";

const TeamLeadDashboard: React.FC = () => {
  const { data, isLoading, error } = useQuery<TeamDashboardData>(
    "teamLeadDashboard",
    dashboardApi.getTeamLeadDashboard
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "success";
      case "active":
        return "primary";
      case "on_hold":
        return "warning";
      default:
        return "secondary";
    }
  };

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-primary text-white rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">
              Team Dashboard - {data.team_info.name}
            </h1>
            <p className="text-blue-100 mt-1">
              Monitor your team's progress and performance
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-blue-100">Team Health</p>
            <p className="text-3xl font-bold">
              {(data.team_sentiment.health_score * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardCard
          title="Team Members"
          value={data.team_metrics.total_members}
          icon={Users}
          iconColor="text-blue-600"
        />
        <DashboardCard
          title="Active Projects"
          value={data.team_metrics.active_projects}
          icon={Target}
          iconColor="text-green-600"
        />
        <DashboardCard
          title="Completion Rate"
          value={`${data.team_metrics.project_completion_rate.toFixed(1)}%`}
          icon={TrendingUp}
          iconColor="text-purple-600"
        />
        <DashboardCard
          title="Active Blockers"
          value={data.team_sentiment.blocker_count}
          icon={AlertTriangle}
          iconColor="text-red-600"
        />
      </div>

      {/* Team Metrics */}
      <TeamMetrics data={data.team_metrics} />

      {/* Team Sentiment */}
      <SentimentChart data={data.team_sentiment} />

      {/* Projects and Blockers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Project Status */}
        <Card>
          <CardHeader title="Project Status" />
          <CardContent>
            {data.project_status.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No projects found</p>
              </div>
            ) : (
              <div className="space-y-4">
                {data.project_status.map((project) => (
                  <div
                    key={project.id}
                    className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
                  >
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">
                        {project.name}
                      </h4>
                      <p className="text-sm text-gray-600 mt-1">
                        {project.description}
                      </p>
                      <div className="flex items-center text-sm text-gray-500 mt-2">
                        <Calendar className="h-4 w-4 mr-1" />
                        {project.start_date &&
                          formatDate(project.start_date, "short")}
                        {project.end_date &&
                          ` - ${formatDate(project.end_date, "short")}`}
                      </div>
                    </div>
                    <div className="flex flex-col items-end space-y-2">
                      <Badge variant={getStatusColor(project.status)} size="sm">
                        {project.status}
                      </Badge>
                      {project.github_repo && (
                        <span className="text-xs text-gray-500">GitHub</span>
                      )}
                      {project.jira_project_key && (
                        <span className="text-xs text-gray-500">Jira</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Active Blockers */}
        <Card>
          <CardHeader title="Active Blockers" />
          <CardContent>
            {data.blockers.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-2" />
                <p>No active blockers</p>
              </div>
            ) : (
              <div className="space-y-4">
                {data.blockers.map((blocker, index) => (
                  <div
                    key={index}
                    className="p-4 border border-gray-200 rounded-lg"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <Badge
                            variant={
                              blocker.severity === "high" ? "error" : "warning"
                            }
                            size="sm"
                          >
                            {blocker.severity}
                          </Badge>
                          <Badge variant="secondary" size="sm">
                            {blocker.type}
                          </Badge>
                        </div>
                        <p className="text-sm font-medium text-gray-900 mt-2">
                          {blocker.description}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Affects: {blocker.affected_users.join(", ")}
                        </p>
                      </div>
                      <div className="text-right">
                        <Badge
                          variant={
                            blocker.urgency === "immediate"
                              ? "error"
                              : "secondary"
                          }
                          size="sm"
                        >
                          {blocker.urgency}
                        </Badge>
                      </div>
                    </div>
                    <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-700">
                        <strong>Suggested Action:</strong>{" "}
                        {blocker.suggested_action}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader title="Quick Actions" />
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button className="p-4 text-left border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
              <Brain className="h-6 w-6 text-blue-600 mb-2" />
              <h4 className="font-medium text-gray-900">Allocate Tasks</h4>
              <p className="text-sm text-gray-600">
                Use AI to optimize task assignments
              </p>
            </button>
            <button className="p-4 text-left border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
              <MessageSquare className="h-6 w-6 text-green-600 mb-2" />
              <h4 className="font-medium text-gray-900">
                Generate Retrospective
              </h4>
              <p className="text-sm text-gray-600">
                Create automated sprint review
              </p>
            </button>
            <button className="p-4 text-left border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
              <TrendingUp className="h-6 w-6 text-purple-600 mb-2" />
              <h4 className="font-medium text-gray-900">View Analytics</h4>
              <p className="text-sm text-gray-600">
                Deep dive into team performance
              </p>
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default TeamLeadDashboard;
