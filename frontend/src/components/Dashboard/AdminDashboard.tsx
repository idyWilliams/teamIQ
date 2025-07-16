import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  UsersIcon, 
  ChartBarIcon, 
  ServerIcon,
  ShieldCheckIcon,
  CogIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  DatabaseIcon
} from '@heroicons/react/24/outline';

import { api } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';

const AdminDashboard: React.FC = () => {
  const { data: dashboardData, isLoading, error } = useQuery({
    queryKey: ['admin-dashboard'],
    queryFn: async () => {
      const response = await api.get('/dashboard/stats');
      return response.data;
    },
  });

  const { data: systemHealth } = useQuery({
    queryKey: ['system-health'],
    queryFn: async () => {
      const response = await api.get('/health');
      return response.data;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const { data: integrationStatus } = useQuery({
    queryKey: ['integration-status'],
    queryFn: async () => {
      const response = await api.get('/integrations/admin/all');
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
    return <ErrorMessage message="Failed to load admin dashboard data" />;
  }

  const stats = dashboardData?.stats || {};
  const integrations = integrationStatus || [];

  const statCards = [
    {
      title: 'Total Users',
      value: stats.team_members || 0,
      icon: UsersIcon,
      color: 'bg-blue-600',
      change: '+5 this month',
    },
    {
      title: 'Active Projects',
      value: stats.active_projects || 0,
      icon: ChartBarIcon,
      color: 'bg-green-600',
      change: '+2 this week',
    },
    {
      title: 'System Health',
      value: systemHealth?.status === 'healthy' ? 'Healthy' : 'Warning',
      icon: ServerIcon,
      color: systemHealth?.status === 'healthy' ? 'bg-green-600' : 'bg-yellow-600',
      change: null,
    },
    {
      title: 'Active Integrations',
      value: integrations.filter((i: any) => i.is_active).length,
      icon: DatabaseIcon,
      color: 'bg-purple-600',
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

      {/* System Status */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">System Status</h3>
          <ShieldCheckIcon className="h-5 w-5 text-gray-400" />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">99.9%</div>
            <p className="text-sm text-gray-600">Uptime</p>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">45ms</div>
            <p className="text-sm text-gray-600">Avg Response Time</p>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">2.1GB</div>
            <p className="text-sm text-gray-600">Memory Usage</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Integration Status */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Integration Status</h3>
            <CogIcon className="h-5 w-5 text-gray-400" />
          </div>
          
          <div className="space-y-4">
            {integrations.slice(0, 10).map((integration: any, index: number) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div className={`w-3 h-3 rounded-full mr-3 ${
                    integration.is_active ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">
                      {integration.platform.charAt(0).toUpperCase() + integration.platform.slice(1)}
                    </h4>
                    <p className="text-xs text-gray-500">{integration.user_name}</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    integration.is_active
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {integration.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
            <ClockIcon className="h-5 w-5 text-gray-400" />
          </div>
          
          <div className="space-y-3">
            {[
              { action: 'New user registered', user: 'John Doe', time: '2 minutes ago', type: 'success' },
              { action: 'GitHub integration updated', user: 'Jane Smith', time: '15 minutes ago', type: 'info' },
              { action: 'Project created', user: 'Mike Johnson', time: '1 hour ago', type: 'success' },
              { action: 'Failed login attempt', user: 'Unknown', time: '2 hours ago', type: 'warning' },
              { action: 'System backup completed', user: 'System', time: '3 hours ago', type: 'info' },
            ].map((activity, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <div className={`w-2 h-2 rounded-full mr-3 ${
                    activity.type === 'success' ? 'bg-green-500' :
                    activity.type === 'warning' ? 'bg-yellow-500' :
                    'bg-blue-500'
                  }`} />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{activity.action}</p>
                    <p className="text-xs text-gray-500">{activity.user}</p>
                  </div>
                </div>
                <div className="text-xs text-gray-500">{activity.time}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* User Management Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
          <CogIcon className="h-5 w-5 text-gray-400" />
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="p-4 bg-blue-50 rounded-lg border border-blue-200 hover:bg-blue-100 transition-colors">
            <UsersIcon className="h-6 w-6 text-blue-600 mb-2" />
            <p className="text-sm font-medium text-blue-900">Manage Users</p>
            <p className="text-xs text-blue-600">Add, edit, or deactivate users</p>
          </button>
          
          <button className="p-4 bg-green-50 rounded-lg border border-green-200 hover:bg-green-100 transition-colors">
            <DatabaseIcon className="h-6 w-6 text-green-600 mb-2" />
            <p className="text-sm font-medium text-green-900">System Backup</p>
            <p className="text-xs text-green-600">Create or restore backups</p>
          </button>
          
          <button className="p-4 bg-purple-50 rounded-lg border border-purple-200 hover:bg-purple-100 transition-colors">
            <ShieldCheckIcon className="h-6 w-6 text-purple-600 mb-2" />
            <p className="text-sm font-medium text-purple-900">Security Settings</p>
            <p className="text-xs text-purple-600">Configure security policies</p>
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
