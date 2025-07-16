import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  UserGroupIcon, 
  ClipboardDocumentListIcon, 
  SparklesIcon,
  ArrowRightIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { api } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';
import { toast } from 'react-hot-toast';

interface TaskAllocationProps {
  projectId: number;
}

const TaskAllocation: React.FC<TaskAllocationProps> = ({ projectId }) => {
  const [selectedAssignments, setSelectedAssignments] = useState<{[key: number]: number}>({});
  const queryClient = useQueryClient();

  const { data: recommendations, isLoading, error } = useQuery({
    queryKey: ['task-recommendations', projectId],
    queryFn: async () => {
      const response = await api.post(`/tasks/allocate-recommendations/${projectId}`);
      return response.data;
    },
  });

  const { data: projectData } = useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => {
      const response = await api.get(`/projects/${projectId}`);
      return response.data;
    },
  });

  const bulkAssignMutation = useMutation({
    mutationFn: async (assignments: {task_id: number, user_id: number}[]) => {
      const response = await api.post('/tasks/bulk-assign', assignments);
      return response.data;
    },
    onSuccess: () => {
      toast.success('Tasks assigned successfully');
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['task-recommendations'] });
      setSelectedAssignments({});
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to assign tasks');
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
    return <ErrorMessage message="Failed to load task recommendations" />;
  }

  const recommendationsList = recommendations?.recommendations || [];

  const handleAssignmentChange = (taskId: number, userId: number) => {
    setSelectedAssignments(prev => ({
      ...prev,
      [taskId]: userId
    }));
  };

  const handleBulkAssign = () => {
    const assignments = Object.entries(selectedAssignments).map(([taskId, userId]) => ({
      task_id: parseInt(taskId),
      user_id: userId
    }));

    if (assignments.length === 0) {
      toast.error('Please select at least one task to assign');
      return;
    }

    bulkAssignMutation.mutate(assignments);
  };

  // Group recommendations by task
  const taskGroups = recommendationsList.reduce((acc: any, rec: any) => {
    if (!acc[rec.task_id]) {
      acc[rec.task_id] = [];
    }
    acc[rec.task_id].push(rec);
    return acc;
  }, {});

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-green-600';
    if (confidence >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getMatchScoreColor = (score: number) => {
    if (score >= 8) return 'bg-green-100 text-green-800';
    if (score >= 6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <SparklesIcon className="h-6 w-6 text-blue-600 mr-3" />
            <div>
              <h2 className="text-xl font-bold text-gray-900">AI Task Allocation</h2>
              <p className="text-gray-600">
                Project: {projectData?.name || 'Loading...'}
              </p>
            </div>
          </div>
          
          <button
            onClick={handleBulkAssign}
            disabled={Object.keys(selectedAssignments).length === 0 || bulkAssignMutation.isPending}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {bulkAssignMutation.isPending ? (
              <LoadingSpinner size="sm" />
            ) : (
              <>
                <CheckCircleIcon className="h-4 w-4 mr-2" />
                Assign Selected ({Object.keys(selectedAssignments).length})
              </>
            )}
          </button>
        </div>
      </div>

      {/* Task Recommendations */}
      {Object.keys(taskGroups).length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm p-12 border border-gray-200 text-center">
          <ClipboardDocumentListIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Tasks to Allocate</h3>
          <p className="text-gray-500">All tasks in this project have been assigned or there are no unassigned tasks.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(taskGroups).map(([taskId, taskRecommendations]: [string, any]) => {
            const topRecommendation = taskRecommendations[0];
            const selectedUserId = selectedAssignments[parseInt(taskId)];
            
            return (
              <div key={taskId} className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900 mb-2">
                        Task #{taskId}
                      </h3>
                      <p className="text-gray-600 mb-3">
                        {topRecommendation.rationale || 'No description available'}
                      </p>
                      
                      <div className="flex items-center space-x-4 text-sm text-gray-500">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getMatchScoreColor(topRecommendation.match_score)}`}>
                          Match: {topRecommendation.match_score}/10
                        </span>
                        <span className={`${getConfidenceColor(topRecommendation.confidence)}`}>
                          Confidence: {topRecommendation.confidence}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="p-6">
                  <h4 className="text-sm font-medium text-gray-900 mb-4">Recommended Assignees</h4>
                  <div className="space-y-3">
                    {taskRecommendations.slice(0, 3).map((rec: any, index: number) => (
                      <div 
                        key={rec.user_id} 
                        className={`flex items-center justify-between p-4 rounded-lg border-2 transition-colors cursor-pointer ${
                          selectedUserId === rec.user_id 
                            ? 'border-blue-500 bg-blue-50' 
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => handleAssignmentChange(parseInt(taskId), rec.user_id)}
                      >
                        <div className="flex items-center">
                          <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center mr-3">
                            <span className="text-sm font-semibold text-white">
                              {rec.user_name.split(' ').map((n: string) => n[0]).join('')}
                            </span>
                          </div>
                          <div>
                            <h5 className="font-medium text-gray-900">{rec.user_name}</h5>
                            <p className="text-sm text-gray-500">
                              Current workload: {rec.current_workload} tasks
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-3">
                          <div className="text-right">
                            <div className={`text-sm font-medium ${getConfidenceColor(rec.confidence)}`}>
                              {rec.confidence}%
                            </div>
                            <div className="text-xs text-gray-500">
                              Match: {rec.match_score}/10
                            </div>
                          </div>
                          
                          {index === 0 && (
                            <div className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
                              AI Recommended
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default TaskAllocation;
