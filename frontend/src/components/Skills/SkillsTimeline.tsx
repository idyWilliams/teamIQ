import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { ClockIcon, TrendingUpIcon, TrendingDownIcon } from '@heroicons/react/24/outline';
import { api } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';

interface SkillsTimelineProps {
  skillId?: number;
  days?: number;
}

const SkillsTimeline: React.FC<SkillsTimelineProps> = ({ skillId, days = 30 }) => {
  const { data: analytics, isLoading, error } = useQuery({
    queryKey: ['skills-analytics', skillId, days],
    queryFn: async () => {
      const response = await api.get(`/skills/analytics?days=${days}`);
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage message="Failed to load skills timeline" />;
  }

  if (!analytics || analytics.length === 0) {
    return (
      <div className="text-center py-12">
        <ClockIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Analytics Data</h3>
        <p className="text-gray-500">Skill analytics will appear here once you start working on tasks.</p>
      </div>
    );
  }

  // Group analytics by skill
  const skillAnalytics = analytics.reduce((acc: any, item: any) => {
    const skillName = item.skill.name;
    if (!acc[skillName]) {
      acc[skillName] = [];
    }
    acc[skillName].push(item);
    return acc;
  }, {});

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUpIcon className="h-4 w-4 text-green-500" />;
      case 'down':
        return <TrendingDownIcon className="h-4 w-4 text-red-500" />;
      default:
        return <div className="h-4 w-4 bg-gray-400 rounded-full" />;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-blue-600';
    if (score >= 4) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {Object.entries(skillAnalytics).map(([skillName, skillData]: [string, any]) => (
        <div key={skillName} className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 mb-4">{skillName}</h3>
          
          <div className="space-y-4">
            {skillData
              .sort((a: any, b: any) => new Date(b.date).getTime() - new Date(a.date).getTime())
              .map((item: any, index: number) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 mr-4">
                      {getTrendIcon(item.trend)}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        Score: <span className={getScoreColor(item.score)}>{item.score}/10</span>
                      </p>
                      <p className="text-xs text-gray-500">
                        {item.evidence_count} evidence points
                      </p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <p className="text-sm text-gray-600">
                      {new Date(item.date).toLocaleDateString()}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(item.date).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default SkillsTimeline;
