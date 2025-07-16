import React from "react";
import { useQuery } from "react-query";
import {
  Users,
  TrendingUp,
  Heart,
  Award,
  AlertTriangle,
  UserPlus,
  UserMinus,
  Star,
} from "lucide-react";
import { dashboardApi } from "../../lib/api";
import DashboardCard from "../../components/dashboard/DashboardCard";
import Card, { CardHeader, CardContent } from "../../components/ui/Card";
import LoadingSpinner from "../../components/ui/LoadingSpinnerSpinner";
import Badge from "../../components/ui/Badge";
import { BarChart, DoughnutChart } from "../../components/ui/Chart";
import { ChartData } from "../../types";

const HRDashboard: React.FC = () => {
  const { data, isLoading, error } = useQuery(
    "hrDashboard",
    dashboardApi.getHRDashboard
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

  // Mock data for HR dashboard
  const mockData = {
    talent_overview: {
      total_employees: 48,
      active_interns: 12,
      retention_rate: 85,
      avg_performance_score: 4.2,
    },
    hiring_pipeline: {
      open_positions: 8,
      candidates_in_process: 15,
      interviews_scheduled: 6,
      offers_pending: 3,
    },
    performance_insights: {
      top_performers: [
        { name: "Sarah Johnson", score: 4.8, role: "Senior Engineer" },
        { name: "Mike Chen", score: 4.7, role: "Team Lead" },
        { name: "Emily Davis", score: 4.5, role: "Engineer" },
      ],
      improvement_needed: [
        { name: "John Smith", score: 3.2, role: "Intern" },
        { name: "Lisa Wong", score: 3.4, role: "Engineer" },
      ],
      skill_gaps: ["React", "Machine Learning", "DevOps"],
    },
    attrition_insights: {
      at_risk_employees: [
        { name: "Alex Turner", risk_score: 0.8, reason: "Low satisfaction" },
        { name: "Maria Garcia", risk_score: 0.7, reason: "Workload concerns" },
      ],
      predicted_turnover: 12,
      retention_recommendations: [
        "Implement flexible work arrangements",
        "Increase mentorship programs",
        "Review compensation packages",
      ],
    },
  };

  const performanceData: ChartData = {
    labels: ["5 Star", "4 Star", "3 Star", "2 Star", "1 Star"],
    datasets: [
      {
        label: "Performance Distribution",
        data: [15, 20, 10, 2, 1],
        backgroundColor: [
          "rgba(34, 197, 94, 0.8)",
          "rgba(59, 130, 246, 0.8)",
          "rgba(251, 191, 36, 0.8)",
          "rgba(239, 68, 68, 0.8)",
          "rgba(156, 163, 175, 0.8)",
        ],
        borderColor: [
          "rgba(34, 197, 94, 1)",
          "rgba(59, 130, 246, 1)",
          "rgba(251, 191, 36, 1)",
          "rgba(239, 68, 68, 1)",
          "rgba(156, 163, 175, 1)",
        ],
        borderWidth: 1,
      },
    ],
  };

  const skillGapsData: ChartData = {
    labels: mockData.performance_insights.skill_gaps,
    datasets: [
      {
        label: "Skill Gap Severity",
        data: [30, 25, 20],
        backgroundColor: "rgba(239, 68, 68, 0.8)",
        borderColor: "rgba(239, 68, 68, 1)",
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-primary text-white rounded-lg p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">HR Dashboard</h1>
            <p className="text-blue-100 mt-1">
              Monitor talent, performance, and team health
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-blue-100">Average Performance</p>
            <p className="text-3xl font-bold">
              {mockData.talent_overview.avg_performance_score}/5
            </p>
          </div>
        </div>
      </div>

      {/* Talent Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <DashboardCard
          title="Total Employees"
          value={mockData.talent_overview.total_employees}
          icon={Users}
          iconColor="text-blue-600"
        />
        <DashboardCard
          title="Active Interns"
          value={mockData.talent_overview.active_interns}
          icon={UserPlus}
          iconColor="text-green-600"
        />
        <DashboardCard
          title="Retention Rate"
          value={`${mockData.talent_overview.retention_rate}%`}
          icon={Heart}
          iconColor="text-purple-600"
        />
        <DashboardCard
          title="Avg Performance"
          value={mockData.talent_overview.avg_performance_score}
          icon={Star}
          iconColor="text-yellow-600"
        />
      </div>

      {/* Hiring Pipeline */}
      <Card>
        <CardHeader title="Hiring Pipeline" />
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {mockData.hiring_pipeline.open_positions}
              </div>
              <div className="text-sm text-gray-600">Open Positions</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {mockData.hiring_pipeline.candidates_in_process}
              </div>
              <div className="text-sm text-gray-600">Candidates in Process</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">
                {mockData.hiring_pipeline.interviews_scheduled}
              </div>
              <div className="text-sm text-gray-600">Interviews Scheduled</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {mockData.hiring_pipeline.offers_pending}
              </div>
              <div className="text-sm text-gray-600">Offers Pending</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Performance Distribution" />
          <CardContent>
            <div className="h-64">
              <DoughnutChart data={performanceData} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Skill Gap Analysis" />
          <CardContent>
            <div className="h-64">
              <BarChart data={skillGapsData} />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Lists */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="Top Performers" />
          <CardContent>
            <div className="space-y-4">
              {mockData.performance_insights.top_performers.map(
                (performer, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-green-50 rounded-lg"
                  >
                    <div>
                      <p className="font-medium text-gray-900">
                        {performer.name}
                      </p>
                      <p className="text-sm text-gray-600">{performer.role}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="success" size="sm">
                        {performer.score}/5
                      </Badge>
                      <Award className="h-4 w-4 text-green-600" />
                    </div>
                  </div>
                )
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Needs Improvement" />
          <CardContent>
            <div className="space-y-4">
              {mockData.performance_insights.improvement_needed.map(
                (performer, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg"
                  >
                    <div>
                      <p className="font-medium text-gray-900">
                        {performer.name}
                      </p>
                      <p className="text-sm text-gray-600">{performer.role}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge variant="warning" size="sm">
                        {performer.score}/5
                      </Badge>
                      <TrendingUp className="h-4 w-4 text-yellow-600" />
                    </div>
                  </div>
                )
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Attrition Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader title="At-Risk Employees" />
          <CardContent>
            <div className="space-y-4">
              {mockData.attrition_insights.at_risk_employees.map(
                (employee, index) => (
                  <div
                    key={index}
                    className="p-4 border border-red-200 rounded-lg bg-red-50"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900">
                          {employee.name}
                        </p>
                        <p className="text-sm text-gray-600">
                          {employee.reason}
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant="error" size="sm">
                          {(employee.risk_score * 100).toFixed(0)}% risk
                        </Badge>
                        <AlertTriangle className="h-4 w-4 text-red-600" />
                      </div>
                    </div>
                  </div>
                )
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader title="Retention Recommendations" />
          <CardContent>
            <div className="space-y-4">
              {mockData.attrition_insights.retention_recommendations.map(
                (recommendation, index) => (
                  <div key={index} className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-gray-700">{recommendation}</p>
                  </div>
                )
              )}
            </div>
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">
                <strong>Predicted Turnover:</strong>{" "}
                {mockData.attrition_insights.predicted_turnover}% over next 6
                months
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default HRDashboard;
