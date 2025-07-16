import React from 'react';
import { 
  DocumentTextIcon, 
  CalendarIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClipboardDocumentListIcon,
  ChartBarIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline';

interface RetrospectiveReportProps {
  retrospective: any;
}

const RetrospectiveReport: React.FC<RetrospectiveReportProps> = ({ retrospective }) => {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const handleExport = () => {
    // This would generate and download a PDF or other format
    console.log('Exporting retrospective:', retrospective.id);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{retrospective.title}</h1>
            <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
              <div className="flex items-center">
                <CalendarIcon className="h-4 w-4 mr-1" />
                <span>
                  {formatDate(retrospective.period_start)} - {formatDate(retrospective.period_end)}
                </span>
              </div>
              <span>Created by {retrospective.created_by_name}</span>
              <span>Created on {formatDate(retrospective.created_at)}</span>
            </div>
          </div>
          
          <button
            onClick={handleExport}
            className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
          >
            <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Context Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {retrospective.team_name && (
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-medium text-blue-900">Team</h3>
            <p className="text-blue-700">{retrospective.team_name}</p>
          </div>
        )}
        
        {retrospective.project_name && (
          <div className="bg-purple-50 p-4 rounded-lg">
            <h3 className="font-medium text-purple-900">Project</h3>
            <p className="text-purple-700">{retrospective.project_name}</p>
          </div>
        )}
      </div>

      {/* Summary */}
      {retrospective.summary && (
        <div className="bg-gray-50 p-6 rounded-lg">
          <div className="flex items-center mb-3">
            <DocumentTextIcon className="h-5 w-5 text-gray-600 mr-2" />
            <h2 className="text-lg font-medium text-gray-900">Summary</h2>
          </div>
          <p className="text-gray-700 leading-relaxed">{retrospective.summary}</p>
        </div>
      )}

      {/* Achievements */}
      {retrospective.achievements && retrospective.achievements.length > 0 && (
        <div className="bg-green-50 p-6 rounded-lg">
          <div className="flex items-center mb-4">
            <CheckCircleIcon className="h-5 w-5 text-green-600 mr-2" />
            <h2 className="text-lg font-medium text-green-900">Achievements</h2>
          </div>
          <ul className="space-y-2">
            {retrospective.achievements.map((achievement: string, index: number) => (
              <li key={index} className="flex items-start">
                <CheckCircleIcon className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                <span className="text-green-800">{achievement}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Challenges */}
      {retrospective.challenges && retrospective.challenges.length > 0 && (
        <div className="bg-red-50 p-6 rounded-lg">
          <div className="flex items-center mb-4">
            <ExclamationCircleIcon className="h-5 w-5 text-red-600 mr-2" />
            <h2 className="text-lg font-medium text-red-900">Challenges</h2>
          </div>
          <ul className="space-y-2">
            {retrospective.challenges.map((challenge: string, index: number) => (
              <li key={index} className="flex items-start">
                <ExclamationCircleIcon className="h-4 w-4 text-red-500 mr-2 mt-0.5 flex-shrink-0" />
                <span className="text-red-800">{challenge}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Action Items */}
      {retrospective.action_items && retrospective.action_items.length > 0 && (
        <div className="bg-yellow-50 p-6 rounded-lg">
          <div className="flex items-center mb-4">
            <ClipboardDocumentListIcon className="h-5 w-5 text-yellow-600 mr-2" />
            <h2 className="text-lg font-medium text-yellow-900">Action Items</h2>
          </div>
          <ul className="space-y-2">
            {retrospective.action_items.map((actionItem: string, index: number) => (
              <li key={index} className="flex items-start">
                <ClipboardDocumentListIcon className="h-4 w-4 text-yellow-500 mr-2 mt-0.5 flex-shrink-0" />
                <span className="text-yellow-800">{actionItem}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Performance Metrics */}
      {retrospective.performance_metrics && Object.keys(retrospective.performance_metrics).length > 0 && (
        <div className="bg-blue-50 p-6 rounded-lg">
          <div className="flex items-center mb-4">
            <ChartBarIcon className="h-5 w-5 text-blue-600 mr-2" />
            <h2 className="text-lg font-medium text-blue-900">Performance Metrics</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(retrospective.performance_metrics).map(([key, value]: [string, any]) => (
              <div key={key} className="bg-white p-4 rounded-lg shadow-sm">
                <h3 className="font-medium text-gray-900 capitalize">
                  {key.replace(/_/g, ' ')}
                </h3>
                <p className="text-2xl font-bold text-blue-600 mt-1">
                  {typeof value === 'number' ? value.toLocaleString() : value}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Skill Insights */}
      {retrospective.skill_insights && Object.keys(retrospective.skill_insights).length > 0 && (
        <div className="bg-purple-50 p-6 rounded-lg">
          <div className="flex items-center mb-4">
            <ChartBarIcon className="h-5 w-5 text-purple-600 mr-2" />
            <h2 className="text-lg font-medium text-purple-900">Skill Insights</h2>
          </div>
          <div className="space-y-4">
            {Object.entries(retrospective.skill_insights).map(([skill, insight]: [string, any]) => (
              <div key={skill} className="bg-white p-4 rounded-lg shadow-sm">
                <h3 className="font-medium text-gray-900">{skill}</h3>
                <p className="text-sm text-gray-600 mt-1">
                  {typeof insight === 'string' ? insight : JSON.stringify(insight)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="border-t border-gray-200 pt-4">
        <p className="text-sm text-gray-500 text-center">
          This retrospective was generated automatically by iSentry TeamIQ AI.
        </p>
      </div>
    </div>
  );
};

export default RetrospectiveReport;
