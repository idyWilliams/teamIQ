import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  UsersIcon, 
  ChartBarIcon, 
  ExclamationTriangleIcon,
  TrendingUpIcon,
  ClipboardDocumentListIcon,
  FolderIcon,
  FaceSmileIcon
} from '@heroicons/react/24/outline';

import { api } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';
import SentimentRadar from '../Sentiment/SentimentRadar';

const TeamLeadDashboard: React.FC = () => {
  const { data: dashboardData, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const response = await api.get('/dashboard/stats');
      return response.data;
    },
  });

  const { data: sentimentAlerts } = useQuery({
    queryKey: ['sentiment-alerts'],
    queryFn: async () => {
      const response = await api.get('/dashboard/sentiment-alerts');
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
  const teamMembers = dashboardData?.team_members || [];
  const activeProjects = dashboardData?.active_projects || [];
  const alerts = sentimentAlerts?.alerts || [];

  const statCards = [
    {
      title: 'Team Members',
      value: stats.team_members || 0,
      icon: UsersIcon,
      color: 'bg-blue-600',
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
      title: 'Total Tasks',
      value: stats.total_tasks || 0,
      icon: ClipboardDocumentListIcon,
      color: 'bg-green-600',
      change: null,
    },
    {
      title: 'Avg Sentiment',
      value: stats.avg_sentiment ? `${stats.avg_sentiment > 0 ? '+' : ''}${Math.round(stats.avg_sentiment)}` : '0',
      icon: FaceSmileIcon,
      color: stats.avg_sentiment > 0 ? 'bg-green-600' : stats.avg_sentiment < 0 ? 'bg-red-600' : 'bg-gray-600',
      change: null,
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

      {/* Alerts Section */}
      {alerts.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Attention Required</h3>
            <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
          </div>
          
          <div className="space-y-3">
            {alerts.slice(0, 5).map((alert: any, index: number) => (
              <div key={index} className={`p-4 rounded-lg border-l-4 ${
                alert.severity === 'high' 
                  ? 'bg-red-50 border-red-400'
                  : alert.severity === 'medium'
                  ? 'bg-yellow-50 border-yellow-400'
                  : 'bg-blue-50 border-blue-400'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">{alert.user_name}</h4>
                    <p className="text-sm text-gray-600">{alert.description}</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {alert.recommendations.map((rec: string, idx: number) => (
                        <span key={idx} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                          {rec}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      alert.severity === 'high'
                        ? 'bg-red-100 text-red-800'
                        : alert.severity === 'medium'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {alert.severity}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Team Members */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Team Members</h3>
            <UsersIcon className="h-5 w-5 text-gray-400" />
          </div>
          
          {teamMembers.length > 0 ? (
            <div className="space-y-4">
              {teamMembers.map((member: any) => (
                <div key={member.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center mr-3">
                      <span className="text-sm font-semibold text-white">
                        {member.full_name.split(' ').map((n: string) => n[0]).join('')}
                      </span>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{member.full_name}</h4>
                      <p className="text-xs text-gray-500 capitalize">{member.role.replace('_', ' ')}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600">{member.current_tasks} tasks</span>
                      <div className={`w-3 h-3 rounded-full ${
                        member.sentiment_score > 20 
                          ? 'bg-green-500'
                          : member.sentiment_score > -20
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <UsersIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
              <p>No team members</p>
            </div>
          )}
        </div>

        {/* Active Projects */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Active Projects</h3>
            <FolderIcon className="h-5 w-5 text-gray-400" />
          </div>
          
          {activeProjects.length > 0 ? (
            <div className="space-y-4">
              {activeProjects.map((project: any) => (
                <div key={project.id} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-gray-900">{project.name}</h4>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      project.status === 'active' 
                        ? 'bg-green-100 text-green-800'
                        : project.status === 'completed'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {project.status}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-500">Progress</span>
                    <span className="font-medium">{Math.round(project.completion_percentage)}%</span>
                  </div>
                  <div className="mt-2 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${project.completion_percentage}%` }}
                    />
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

      {/* Team Sentiment Overview */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Team Sentiment Overview</h3>
          <FaceSmileIcon className="h-5 w-5 text-gray-400" />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">
              {stats.avg_sentiment > 0 ? '+' : ''}{Math.round(stats.avg_sentiment || 0)}
            </div>
            <p className="text-sm text-gray-600">Average Sentiment</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">
              {teamMembers.filter((m: any) => m.sentiment_score > 20).length}
            </div>
            <p className="text-sm text-gray-600">Positive Members</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-red-600">
              {teamMembers.filter((m: any) => m.sentiment_score < -20).length}
            </div>
            <p className="text-sm text-gray-600">At Risk Members</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TeamLeadDashboard;
