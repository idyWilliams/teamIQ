import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  UsersIcon, 
  ChartBarIcon, 
  ExclamationTriangleIcon,
  TrendingUpIcon,
  BriefcaseIcon,
  AcademicCapIcon,
  HeartIcon
} from '@heroicons/react/24/outline';

import { api } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';

const HRDashboard: React.FC = () => {
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
  const alerts = sentimentAlerts?.alerts || [];

  const statCards = [
    {
      title: 'Total Employees',
      value: stats.team_members || 0,
      icon: UsersIcon,
      color: 'bg-blue-600',
      change: '+3 this month',
    },
    {
      title: 'At Risk',
      value: alerts.filter((a: any) => a.severity === 'high').length,
      icon: ExclamationTriangleIcon,
      color: 'bg-red-600',
      change: '-2 from last week',
    },
    {
      title: 'Avg Performance',
      value: '8.2/10',
      icon: ChartBarIcon,
      color: 'bg-green-600',
      change: '+0.3 from last month',
    },
    {
      title: 'Retention Rate',
      value: '94%',
      icon: HeartIcon,
      color: 'bg-purple-600',
      change: '+2% from last quarter',
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
                    <p className={`text-sm mt-1 ${
                      stat.change.startsWith('+') ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {stat.change}
                    </p>
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

      {/* Critical Alerts */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Critical Alerts</h3>
          <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
        </div>
        
        {alerts.length > 0 ? (
          <div className="space-y-3">
            {alerts.filter((a: any) => a.severity === 'high').slice(0, 3).map((alert: any, index: number) => (
              <div key={index} className="p-4 bg-red-50 rounded-lg border-l-4 border-red-400">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">{alert.user_name}</h4>
                    <p className="text-sm text-gray-600">{alert.description}</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {alert.recommendations.slice(0, 2).map((rec: string, idx: number) => (
                        <span key={idx} className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">
                          {rec}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      HIGH
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <ExclamationTriangleIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
            <p>No critical alerts</p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Overview */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Performance Overview</h3>
            <ChartBarIcon className="h-5 w-5 text-gray-400" />
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">High Performers</span>
              <span className="text-sm font-medium text-green-600">
                {teamMembers.filter((m: any) => m.productivity_score > 80).length} members
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Average Performers</span>
              <span className="text-sm font-medium text-yellow-600">
                {teamMembers.filter((m: any) => m.productivity_score > 60 && m.productivity_score <= 80).length} members
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Needs Improvement</span>
              <span className="text-sm font-medium text-red-600">
                {teamMembers.filter((m: any) => m.productivity_score <= 60).length} members
              </span>
            </div>
          </div>

          <div className="mt-6">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Performance Distribution</h4>
            <div className="space-y-2">
              <div className="flex items-center">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{ width: '65%' }} />
                </div>
                <span className="ml-2 text-sm text-gray-600">65%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Skill Development */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Skill Development</h3>
            <AcademicCapIcon className="h-5 w-5 text-gray-400" />
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Skills Improved (30d)</span>
              <span className="text-sm font-medium text-green-600">
                +{stats.skills_improved || 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Training Completed</span>
              <span className="text-sm font-medium text-blue-600">
                {Math.floor(Math.random() * 50) + 20} sessions
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Certifications</span>
              <span className="text-sm font-medium text-purple-600">
                {Math.floor(Math.random() * 10) + 5} earned
              </span>
            </div>
          </div>

          <div className="mt-6">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Top Skills Being Developed</h4>
            <div className="space-y-2">
              {['React', 'Python', 'Project Management', 'Communication'].map((skill, index) => (
                <div key={index} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">{skill}</span>
                  <span className="text-sm font-medium text-blue-600">
                    {Math.floor(Math.random() * 10) + 5} members
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Team Wellbeing */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Team Wellbeing</h3>
          <HeartIcon className="h-5 w-5 text-gray-400" />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">
              {Math.round(stats.avg_sentiment || 0)}
            </div>
            <p className="text-sm text-gray-600">Average Sentiment</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">
              {teamMembers.filter((m: any) => m.sentiment_score > 20).length}
            </div>
            <p className="text-sm text-gray-600">Happy Members</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-600">
              {teamMembers.filter((m: any) => m.sentiment_score >= -20 && m.sentiment_score <= 20).length}
            </div>
            <p className="text-sm text-gray-600">Neutral Members</p>
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

export default HRDashboard;
