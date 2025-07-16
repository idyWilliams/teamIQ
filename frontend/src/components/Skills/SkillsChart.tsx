import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { ChartBarIcon, TrendingUpIcon, TrendingDownIcon } from '@heroicons/react/24/outline';
import { api } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';

interface SkillsChartProps {
  userId?: number;
  showProgression?: boolean;
}

const SkillsChart: React.FC<SkillsChartProps> = ({ userId, showProgression = false }) => {
  const { data: skills, isLoading, error } = useQuery({
    queryKey: ['skills', userId],
    queryFn: async () => {
      const endpoint = userId ? `/skills/user/${userId}/skills` : '/skills/my-skills';
      const response = await api.get(endpoint);
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
    return <ErrorMessage message="Failed to load skills data" />;
  }

  if (!skills || skills.length === 0) {
    return (
      <div className="text-center py-12">
        <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Skills Found</h3>
        <p className="text-gray-500">Add some skills to see your progress chart.</p>
      </div>
    );
  }

  // Group skills by category
  const skillsByCategory = skills.reduce((acc: any, skill: any) => {
    const category = skill.skill.category;
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(skill);
    return acc;
  }, {});

  const getSkillColor = (level: number) => {
    if (level >= 8) return 'bg-green-500';
    if (level >= 6) return 'bg-blue-500';
    if (level >= 4) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getTrendIcon = (skill: any) => {
    // This would come from analytics endpoint in real implementation
    const trend = 'up'; // Placeholder
    
    if (trend === 'up') {
      return <TrendingUpIcon className="h-4 w-4 text-green-500" />;
    } else if (trend === 'down') {
      return <TrendingDownIcon className="h-4 w-4 text-red-500" />;
    }
    return null;
  };

  return (
    <div className="space-y-6">
      {Object.entries(skillsByCategory).map(([category, categorySkills]: [string, any]) => (
        <div key={category} className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <h3 className="text-lg font-medium text-gray-900 mb-4 capitalize">
            {category} Skills
          </h3>
          
          <div className="space-y-4">
            {categorySkills.map((skill: any) => (
              <div key={skill.id} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900">
                      {skill.skill.name}
                    </span>
                    <div className="flex items-center">
                      {showProgression && getTrendIcon(skill)}
                      <span className="text-sm text-gray-600 ml-2">
                        {skill.proficiency_level}/10
                      </span>
                    </div>
                  </div>
                  
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${getSkillColor(skill.proficiency_level)}`}
                      style={{ width: `${(skill.proficiency_level / 10) * 100}%` }}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-xs text-gray-500">
                      Last updated: {new Date(skill.last_updated).toLocaleDateString()}
                    </span>
                    {skill.evidence_data && (
                      <span className="text-xs text-blue-600">
                        {Object.keys(skill.evidence_data).length} evidence points
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default SkillsChart;
