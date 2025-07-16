import React from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../../hooks/useAuth";
import { api } from "../../services/api";
import Card from "../ui/Card";
import Loading from "../ui/LoadingSpinner";
import EmptyState from "../ui/EmptyState";
import {
  UsersIcon,
  AcademicCapIcon,
  DocumentChartBarIcon,
  ChartBarIcon,
  ClockIcon,
  TrendingUpIcon,
  UserGroupIcon,
  BriefcaseIcon,
} from "@heroicons/react/24/outline";

const RecruiterDashboard: React.FC = () => {
  const { user } = useAuth();

  const { data: dashboardData, isLoading } = useQuery({
    queryKey: ["dashboard", "recruiter"],
    queryFn: () => api.get("/dashboard/recruiter"),
  });

  if (isLoading) {
    return <Loading />;
  }

  if (!dashboardData?.data) {
    return <EmptyState message="Unable to load dashboard data" />;
  }

  const { dashboard } = dashboardData.data;

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-lg p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">Recruiter Dashboard</h1>
        <p className="text-blue-100">
          Manage candidates, track hiring pipeline, and analyze recruitment
          metrics.
        </p>
      </div>

      {/* Pipeline Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg">
              <UsersIcon className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Total Candidates</p>
              <p className="text-2xl font-semibold">
                {dashboard.candidate_pipeline.total_candidates}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-lg">
              <DocumentChartBarIcon className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Active Interviews</p>
              <p className="text-2xl font-semibold">
                {dashboard.candidate_pipeline.active_interviews}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-purple-100 rounded-lg">
              <BriefcaseIcon className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Pending Offers</p>
              <p className="text-2xl font-semibold">
                {dashboard.candidate_pipeline.pending_offers}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-orange-100 rounded-lg">
              <ClockIcon className="w-6 h-6 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Time to Hire</p>
              <p className="text-2xl font-semibold">
                {dashboard.hiring_metrics.time_to_hire} days
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Skill Demand and Hiring Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Demanded Skills */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Top Demanded Skills</h2>
          <div className="space-y-3">
            {dashboard.skill_demand.top_demanded_skills.length === 0 ? (
              <EmptyState message="No skill demand data available" />
            ) : (
              dashboard.skill_demand.top_demanded_skills.map(
                (skill: any, index: number) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <AcademicCapIcon className="w-5 h-5 text-gray-400" />
                      <div>
                        <p className="font-medium">{skill.name}</p>
                        <p className="text-sm text-gray-600">
                          {skill.category}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">
                        {skill.demand_score}
                      </p>
                      <p className="text-xs text-gray-500">demand score</p>
                    </div>
                  </div>
                )
              )
            )}
          </div>
        </Card>

        {/* Hiring Metrics */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Hiring Metrics</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">
                Offer Acceptance Rate
              </span>
              <span className="font-semibold">
                {dashboard.hiring_metrics.offer_acceptance_rate}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full"
                style={{
                  width: `${dashboard.hiring_metrics.offer_acceptance_rate}%`,
                }}
              ></div>
            </div>
            <div className="space-y-3">
              {Object.entries(
                dashboard.hiring_metrics.source_effectiveness
              ).map(([source, effectiveness]: [string, any]) => (
                <div key={source} className="flex items-center justify-between">
                  <span className="text-sm capitalize">{source}</span>
                  <span className="font-medium">{effectiveness}%</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </div>

      {/* Team Needs and Candidate Profiles */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Team Needs */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Team Needs</h2>
          <div className="space-y-3">
            {dashboard.team_needs.open_positions.length === 0 ? (
              <EmptyState message="No open positions" />
            ) : (
              dashboard.team_needs.open_positions.map(
                (position: any, index: number) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <p className="font-medium">{position.title}</p>
                      <p className="text-sm text-gray-600">
                        {position.department}
                      </p>
                    </div>
                    <div className="text-right">
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${
                          position.urgency === "high"
                            ? "bg-red-100 text-red-700"
                            : position.urgency === "medium"
                            ? "bg-yellow-100 text-yellow-700"
                            : "bg-green-100 text-green-700"
                        }`}
                      >
                        {position.urgency}
                      </span>
                    </div>
                  </div>
                )
              )
            )}
          </div>
        </Card>

        {/* Top Candidates */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Top Candidates</h2>
          <div className="space-y-3">
            {dashboard.candidate_profiles.top_candidates.length === 0 ? (
              <EmptyState message="No candidates available" />
            ) : (
              dashboard.candidate_profiles.top_candidates.map(
                (candidate: any, index: number) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
                        {candidate.name.charAt(0)}
                      </div>
                      <div>
                        <p className="font-medium">{candidate.name}</p>
                        <p className="text-sm text-gray-600">
                          {candidate.position}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">
                        {candidate.match_score}%
                      </p>
                      <p className="text-xs text-gray-500">match</p>
                    </div>
                  </div>
                )
              )
            )}
          </div>
        </Card>
      </div>

      {/* Skill Gap Analysis and Recent Hires */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Skill Gap Analysis */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Skill Gap Analysis</h2>
          <div className="space-y-3">
            {dashboard.skill_demand.skill_gap_analysis.length === 0 ? (
              <EmptyState message="No skill gaps identified" />
            ) : (
              dashboard.skill_demand.skill_gap_analysis.map(
                (gap: any, index: number) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg"
                  >
                    <div>
                      <p className="font-medium">{gap.skill}</p>
                      <p className="text-sm text-gray-600">{gap.department}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium">{gap.gap_size}</p>
                      <p className="text-xs text-gray-500">gap size</p>
                    </div>
                  </div>
                )
              )
            )}
          </div>
        </Card>

        {/* Recent Hires */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Recent Hires</h2>
          <div className="space-y-3">
            {dashboard.candidate_pipeline.recent_hires.length === 0 ? (
              <EmptyState message="No recent hires" />
            ) : (
              dashboard.candidate_pipeline.recent_hires.map(
                (hire: any, index: number) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-green-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center text-white font-medium">
                        {hire.name.charAt(0)}
                      </div>
                      <div>
                        <p className="font-medium">{hire.name}</p>
                        <p className="text-sm text-gray-600">{hire.position}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm">{hire.start_date}</p>
                      <p className="text-xs text-gray-500">start date</p>
                    </div>
                  </div>
                )
              )
            )}
          </div>
        </Card>
      </div>

      {/* Market Trends */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">Market Trends</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {dashboard.skill_demand.market_trends.length === 0 ? (
            <EmptyState message="No market trends data available" />
          ) : (
            dashboard.skill_demand.market_trends.map(
              (trend: any, index: number) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium">{trend.skill}</h3>
                    <TrendingUpIcon className="w-4 h-4 text-green-500" />
                  </div>
                  <p className="text-sm text-gray-600">{trend.trend}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {trend.market_demand}% demand
                  </p>
                </div>
              )
            )
          )}
        </div>
      </Card>
    </div>
  );
};

export default RecruiterDashboard;
