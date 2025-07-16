import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  ChartBarIcon, 
  ClipboardDocumentListIcon, 
  FolderIcon,
  TrendingUpIcon,
  ClockIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

import { api } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';
import SkillsChart from '../Skills/SkillsChart';
import TaskList from '../Tasks/TaskList';

const InternDashboard: React.FC = () => {
  const { data: dashboardData, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const response = await api.get('/dashboard/stats');
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
    return <ErrorMessage message="Failed to load dashboard data" />;
  }

  const stats = dashboardData?.stats || {};
  const recentTasks = dashboardData?.recent_tasks || [];
  const topSkills = dashboardData?.top_skills || [];
  const activeProjects = dashboardData?.active_projects || [];

  const statCards = [
    {
      title: 'Total Tasks',
      value: stats.total_tasks || 0,
      icon: ClipboardDocumentListIcon,
      color: 'bg-blue-600',
      change: null,
    },
    {
      title: 'Completed Tasks',
      value: stats.completed_tasks || 0,
      icon: CheckCircleIcon,
      color: 'bg-green-600',
      change: null,
    },
    {
      title: 'Active Projects',
      value: stats.active_projects || 0,
      icon: FolderIcon,
      color: 'bg-purple-600',
      change: null,
    },
    {
      title: 'Skills Improved',
      value: stats.skills_improved || 0,
      icon: TrendingUpIcon,
      color: 'bg-orange-600',
      change: '+2 this week',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                  {stat.change && (
                    <p className="text-sm text-green-600 mt-1">{stat.change}</p>
                  )}
                </div>
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <Icon className="h-6 w-6 text-white" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Skills Overview */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">My Skills</h3>
            <ChartBarIcon className="h-5 w-5 text-gray-400" />
          </div>
          
          {topSkills.length > 0 ? (
            <div className="space-y-4">
              {topSkills.map((skill: any, index: number) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="text-sm font-medium text-gray-900">{skill.name}</span>
                    <span className="ml-2 text-xs text-gray-500 capitalize">({skill.category})</span>
                  </div>
                  <div className="flex items-center">
                    <div className="w-24 bg-gray-200 rounded-full h-2 mr-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${(skill.proficiency_level / 10) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-600">{skill.proficiency_level}/10</span>
                    {skill.trend === 'up' && (
                      <TrendingUpIcon className="h-4 w-4 text-green-500 ml-1" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <ChartBarIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
              <p>No skills data available</p>
            </div>
          )}
        </div>

        {/* Recent Tasks */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Recent Tasks</h3>
            <ClipboardDocumentListIcon className="h-5 w-5 text-gray-400" />
          </div>
          
          {recentTasks.length > 0 ? (
            <div className="space-y-3">
              {recentTasks.slice(0, 5).map((task: any) => (
                <div key={task.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-gray-900">{task.title}</h4>
                    <div className="flex items-center mt-1">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        task.status === 'done' 
                          ? 'bg-green-100 text-green-800'
                          : task.status === 'in_progress'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {task.status.replace('_', ' ')}
                      </span>
                      <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        task.priority === 'high'
                          ? 'bg-red-100 text-red-800'
                          : task.priority === 'medium'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {task.priority}
                      </span>
                    </div>
                  </div>
                  {task.due_date && (
                    <div className="text-sm text-gray-500 ml-4">
                      <ClockIcon className="h-4 w-4 inline mr-1" />
                      {new Date(task.due_date).toLocaleDateString()}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <ClipboardDocumentListIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
              <p>No recent tasks</p>
            </div>
          )}
        </div>
      </div>

      {/* Active Projects */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Active Projects</h3>
          <FolderIcon className="h-5 w-5 text-gray-400" />
        </div>
        
        {activeProjects.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {activeProjects.map((project: any) => (
              <div key={project.id} className="p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium text-gray-900">{project.name}</h4>
                <p className="text-sm text-gray-600 mt-1">{project.team_name}</p>
                <div className="mt-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Progress</span>
                    <span className="font-medium">{Math.round(project.completion_percentage)}%</span>
                  </div>
                  <div className="mt-1 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${project.completion_percentage}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <FolderIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
            <p>No active projects</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default InternDashboard;
