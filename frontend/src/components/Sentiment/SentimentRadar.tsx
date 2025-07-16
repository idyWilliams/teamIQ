import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  FaceSmileIcon, 
  ExclamationTriangleIcon,
  UsersIcon,
  ClockIcon,
  ChartBarIcon,
  FunnelIcon
} from '@heroicons/react/24/outline';
import { api } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';

interface SentimentRadarProps {
  teamId?: number;
  showFilters?: boolean;
}

const SentimentRadar: React.FC<SentimentRadarProps> = ({ teamId, showFilters = true }) => {
  const [selectedPeriod, setSelectedPeriod] = useState<number>(7);
  const [selectedPlatform, setSelectedPlatform] = useState<string>('');

  const { data: teamSentiment, isLoading, error } = useQuery({
    queryKey: ['team-sentiment', teamId, selectedPeriod],
    queryFn: async () => {
      const endpoint = teamId ? `/sentiment/team/${teamId}` : '/sentiment/summary';
      const params = new URLSearchParams({ days: selectedPeriod.toString() });
      const response = await api.get(`${endpoint}?${params.toString()}`);
      return response.data;
    },
  });

  const { data: sentimentAlerts } = useQuery({
    queryKey: ['sentiment-alerts'],
    queryFn: async () => {
      const response = await api.get('/sentiment/alerts');
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
    return <ErrorMessage message="Failed to load sentiment data" />;
  }

  const getSentimentColor = (score: number) => {
    if (score > 20) return 'text-green-600';
    if (score > -20) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getSentimentBg = (score: number) => {
    if (score > 20) return 'bg-green-100';
    if (score > -20) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-green-100 text-green-800';
    }
  };

  const alerts = sentimentAlerts || [];
  const sentiment = teamSentiment || {};

  return (
    <div className="space-y-6">
      {/* Filters */}
      {showFilters && (
        <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
          <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <ClockIcon className="h-5 w-5 text-gray-400 mr-2" />
                <select
                  value={selectedPeriod}
                  onChange={(e) => setSelectedPeriod(Number(e.target.value))}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value={7}>Last 7 days</option>
                  <option value={14}>Last 14 days</option>
                  <option value={30}>Last 30 days</option>
                </select>
              </div>
              
              <div className="flex items-center">
                <FunnelIcon className="h-5 w-5 text-gray-400 mr-2" />
                <select
                  value={selectedPlatform}
                  onChange={(e) => setSelectedPlatform(e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">All Platforms</option>
                  <option value="slack">Slack</option>
                  <option value="discord">Discord</option>
                  <option value="teams">Teams</option>
                </select>
              </div>
            </div>
            
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              Analyze Team
            </button>
          </div>
        </div>
      )}

      {/* Sentiment Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <FaceSmileIcon className="h-8 w-8 text-blue-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Avg Sentiment</p>
              <p className={`text-2xl font-bold ${getSentimentColor(sentiment.average_sentiment || 0)}`}>
                {sentiment.average_sentiment > 0 ? '+' : ''}{Math.round(sentiment.average_sentiment || 0)}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <ChartBarIcon className="h-8 w-8 text-green-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Positive</p>
              <p className="text-2xl font-bold text-gray-900">
                {sentiment.sentiment_distribution?.positive || 0}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-8 w-8 text-red-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">At Risk</p>
              <p className="text-2xl font-bold text-gray-900">
                {sentiment.users_at_risk || 0}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center">
            <UsersIcon className="h-8 w-8 text-purple-600 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Blockers</p>
              <p className="text-2xl font-bold text-gray-900">
                {sentiment.blockers_identified || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Sentiment Alerts */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Sentiment Alerts</h3>
          <ExclamationTriangleIcon className="h-5 w-5 text-gray-400" />
        </div>
        
        {alerts.length > 0 ? (
          <div className="space-y-4">
            {alerts.map((alert: any, index: number) => (
              <div key={index} className={`p-4 rounded-lg border-l-4 ${
                alert.severity === 'high' 
                  ? 'bg-red-50 border-red-400'
                  : alert.severity === 'medium'
                  ? 'bg-yellow-50 border-yellow-400'
                  : 'bg-blue-50 border-blue-400'
              }`}>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center mb-2">
                      <h4 className="font-medium text-gray-900">{alert.user_name}</h4>
                      <span className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        alert.severity === 'high'
                          ? 'bg-red-100 text-red-800'
                          : alert.severity === 'medium'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}>
                        {alert.severity}
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-3">{alert.description}</p>
                    
                    <div className="flex items-center space-x-4 text-sm">
                      <span className={`${getSentimentColor(alert.sentiment_score)}`}>
                        Sentiment: {alert.sentiment_score}
                      </span>
                      {alert.blockers?.length > 0 && (
                        <span className="text-red-600">
                          Blockers: {alert.blockers.join(', ')}
                        </span>
                      )}
                    </div>
                    
                    <div className="mt-3 flex flex-wrap gap-2">
                      {alert.recommendations.map((rec: string, idx: number) => (
                        <span key={idx} className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                          {rec}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  <div className="ml-4 flex-shrink-0">
                    <button className="text-sm text-blue-600 hover:text-blue-800">
                      Take Action
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <FaceSmileIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No sentiment alerts at this time</p>
          </div>
        )}
      </div>

      {/* Team Members At Risk */}
      {teamSentiment?.members_at_risk && teamSentiment.members_at_risk.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">Members At Risk</h3>
            <UsersIcon className="h-5 w-5 text-gray-400" />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {teamSentiment.members_at_risk.map((member: any) => (
              <div key={member.user_id} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-gray-900">{member.user_name}</h4>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRiskLevelColor(member.risk_level)}`}>
                    {member.risk_level} risk
                  </span>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Sentiment:</span>
                    <span className={getSentimentColor(member.average_sentiment)}>
                      {Math.round(member.average_sentiment)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Blockers:</span>
                    <span className="text-red-600">{member.blockers_count}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SentimentRadar;
