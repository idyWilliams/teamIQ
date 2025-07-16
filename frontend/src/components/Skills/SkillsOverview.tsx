import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../../hooks/useAuth";
import { api } from "../../services/api";
import Card from "../ui/Card";
import Loading from "../ui/LoadingSpinner";
import EmptyState from "../ui/EmptyState";
import SkillRadarChart from "./SkillRadarChart";
import SkillProgressChart from "./SkillProgressChart";
import {
  AcademicCapIcon,

  ChartBarIcon,
  ClockIcon,
  LightBulbIcon,
  ArrowTrendingUpIcon,
} from "@heroicons/react/24/outline";
import { TrendingUpIcon } from "lucide-react";

const SkillsOverview: React.FC = () => {
  const { user } = useAuth();
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  const { data: skillsData, isLoading } = useQuery({
    queryKey: ["skills", "me"],
    queryFn: () => api.get("/skills/me"),
  });

  const { data: analyticsData } = useQuery({
    queryKey: ["skills", "analytics", "growth"],
    queryFn: () => api.get("/skills/analytics/growth"),
  });

  const { data: recommendationsData } = useQuery({
    queryKey: ["skills", "recommendations"],
    queryFn: () => api.get("/skills/recommendations"),
  });

  if (isLoading) {
    return <Loading />;
  }

  if (!skillsData?.data) {
    return <EmptyState />;
  }
  // if (!skillsData?.data) {
  //   return <EmptyState message="Unable to load skills data" />;
  // }

  const { skills, skills_by_category, radar_data, statistics } =
    skillsData.data;
  const analytics = analyticsData?.data || {};
  const recommendations = recommendationsData?.data?.recommendations || [];

  const categories = Object.keys(skills_by_category);

  const filteredSkills =
    selectedCategory === "all"
      ? skills
      : skills_by_category[selectedCategory] || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Skills</h1>
          <p className="text-gray-600">
            Track your skill development and growth
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg">
              <AcademicCapIcon className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Total Skills</p>
              <p className="text-2xl font-semibold">
                {statistics.total_skills}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-lg">
              <ChartBarIcon className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Avg Proficiency</p>
              <p className="text-2xl font-semibold">
                {statistics.average_proficiency.toFixed(1)}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-purple-100 rounded-lg">
              <TrendingUpIcon
                className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Growing Skills</p>
              <p className="text-2xl font-semibold">
                {analytics.summary?.improving_skills || 0}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="p-3 bg-orange-100 rounded-lg">
              <LightBulbIcon className="w-6 h-6 text-orange-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600">Recommendations</p>
              <p className="text-2xl font-semibold">{recommendations.length}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Skills Radar Chart */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Skills Radar</h2>
          <SkillRadarChart data={radar_data} />
        </Card>

        {/* Skills Progress Chart */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Skill Growth (30 days)</h2>
          <SkillProgressChart data={analytics.skill_growth || []} />
        </Card>
      </div>

      {/* Skills List and Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Skills List */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">
            {selectedCategory === "all"
              ? "All Skills"
              : `${
                  selectedCategory.charAt(0).toUpperCase() +
                  selectedCategory.slice(1)
                } Skills`}
          </h2>
          <div className="space-y-3">
            {filteredSkills.length === 0 ? (
              <EmptyState  />
              // <EmptyState message="No skills found" />
            ) : (
              filteredSkills.map((skill: any) => (
                <div
                  key={skill.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <p className="font-medium">{skill.name}</p>
                      <span className="text-sm text-gray-600">
                        {skill.proficiency_level.toFixed(1)}/5
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{
                          width: `${(skill.proficiency_level / 5) * 100}%`,
                        }}
                      ></div>
                    </div>
                    <div className="flex items-center justify-between mt-1">
                      <p className="text-xs text-gray-500 capitalize">
                        {skill.category}
                      </p>
                      <p className="text-xs text-gray-500">
                        {skill.evidence_count} evidence
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>

        {/* Recommendations */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Skill Recommendations</h2>
          <div className="space-y-3">
            {recommendations.length === 0 ? (
              <EmptyState  />
              // <EmptyState message="No recommendations available" />
            ) : (
              recommendations.map((recommendation: any, index: number) => (
                <div key={index} className="p-3 bg-blue-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-medium">{recommendation.skill_name}</p>
                    <span
                      className={`px-2 py-1 text-xs rounded-full ${
                        recommendation.priority === "high"
                          ? "bg-red-100 text-red-700"
                          : recommendation.priority === "medium"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-green-100 text-green-700"
                      }`}
                    >
                      {recommendation.priority}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">
                    Current: {recommendation.current_level} → Target:{" "}
                    {recommendation.target_level}
                  </p>
                  <div className="space-y-1">
                    {recommendation.suggested_actions?.map(
                      (action: string, actionIndex: number) => (
                        <p key={actionIndex} className="text-xs text-gray-500">
                          • {action}
                        </p>
                      )
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {/* Top Skills */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">Top Skills</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {statistics.top_skills.map((skill: any) => (
            <div key={skill.id} className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium">{skill.name}</h3>
                <span className="text-sm text-gray-600">
                  {skill.proficiency_level.toFixed(1)}/5
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${(skill.proficiency_level / 5) * 100}%` }}
                ></div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500 capitalize">
                  {skill.category}
                </span>
                <span className="text-xs text-gray-500">
                  Last assessed:{" "}
                  {new Date(skill.last_assessed).toLocaleDateString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default SkillsOverview;
