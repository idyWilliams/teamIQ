import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  DocumentTextIcon, 
  CalendarIcon,
  UsersIcon,
  FolderIcon,
  PlusIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import { api } from '../../services/api';
import LoadingSpinner from '../Common/LoadingSpinner';
import ErrorMessage from '../Common/ErrorMessage';
import Modal from '../Common/Modal';
import RetrospectiveReport from './RetrospectiveReport';

interface RetrospectivesListProps {
  teamId?: number;
  projectId?: number;
  showActions?: boolean;
}

const RetrospectivesList: React.FC<RetrospectivesListProps> = ({ 
  teamId, 
  projectId, 
  showActions = true 
}) => {
  const [selectedRetrospective, setSelectedRetrospective] = useState<any>(null);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const { data: retrospectives, isLoading, error } = useQuery({
    queryKey: ['retrospectives', teamId, projectId],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (teamId) params.append('team_id', teamId.toString());
      if (projectId) params.append('project_id', projectId.toString());
      
      const response = await api.get(`/retrospectives/?${params.toString()}`);
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
    return <ErrorMessage message="Failed to load retrospectives" />;
  }

  const filteredRetrospectives = retrospectives?.filter((retro: any) => 
    retro.title.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getTimeSince = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return '1 day ago';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    return `${Math.floor(diffDays / 30)} months ago`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
        <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
          <div className="flex-1">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search retrospectives..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>
          
          {showActions && (
            <button
              onClick={() => setShowGenerateModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center"
            >
              <PlusIcon className="h-4 w-4 mr-2" />
              Generate Retrospective
            </button>
          )}
        </div>
      </div>

      {/* Retrospectives List */}
      {filteredRetrospectives.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm p-12 border border-gray-200 text-center">
          <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Retrospectives Found</h3>
          <p className="text-gray-500">
            {searchTerm 
              ? 'Try adjusting your search term'
              : 'Generate your first retrospective to get started'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredRetrospectives.map((retrospective: any) => (
            <div 
              key={retrospective.id} 
              className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => setSelectedRetrospective(retrospective)}
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <DocumentTextIcon className="h-8 w-8 text-blue-600 mr-3 flex-shrink-0" />
                  <div className="flex-1">
                    <h3 className="text-lg font-medium text-gray-900 mb-1">
                      {retrospective.title}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {getTimeSince(retrospective.created_at)}
                    </p>
                  </div>
                </div>
                
                <div className="space-y-3">
                  <div className="flex items-center text-sm text-gray-600">
                    <CalendarIcon className="h-4 w-4 mr-2" />
                    <span>
                      {formatDate(retrospective.period_start)} - {formatDate(retrospective.period_end)}
                    </span>
                  </div>
                  
                  {retrospective.team_name && (
                    <div className="flex items-center text-sm text-gray-600">
                      <UsersIcon className="h-4 w-4 mr-2" />
                      <span>{retrospective.team_name}</span>
                    </div>
                  )}
                  
                  {retrospective.project_name && (
                    <div className="flex items-center text-sm text-gray-600">
                      <FolderIcon className="h-4 w-4 mr-2" />
                      <span>{retrospective.project_name}</span>
                    </div>
                  )}
                </div>
                
                {retrospective.summary && (
                  <p className="text-sm text-gray-600 mt-4 line-clamp-3">
                    {retrospective.summary}
                  </p>
                )}
                
                <div className="mt-4 flex items-center justify-between">
                  <span className="text-xs text-gray-500">
                    By {retrospective.created_by_name}
                  </span>
                  
                  <div className="flex items-center space-x-2">
                    {retrospective.achievements?.length > 0 && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {retrospective.achievements.length} wins
                      </span>
                    )}
                    {retrospective.challenges?.length > 0 && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        {retrospective.challenges.length} challenges
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Retrospective Detail Modal */}
      <Modal
        isOpen={!!selectedRetrospective}
        onClose={() => setSelectedRetrospective(null)}
        title={selectedRetrospective?.title}
        size="lg"
      >
        {selectedRetrospective && (
          <RetrospectiveReport retrospective={selectedRetrospective} />
        )}
      </Modal>

      {/* Generate Retrospective Modal */}
      <Modal
        isOpen={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
        title="Generate Retrospective"
      >
        <GenerateRetrospectiveForm 
          teamId={teamId}
          projectId={projectId}
          onClose={() => setShowGenerateModal(false)}
        />
      </Modal>
    </div>
  );
};

// Generate Retrospective Form Component
const GenerateRetrospectiveForm: React.FC<{
  teamId?: number;
  projectId?: number;
  onClose: () => void;
}> = ({ teamId, projectId, onClose }) => {
  const [formData, setFormData] = useState({
    title: '',
    period_start: '',
    period_end: '',
    team_id: teamId || 0,
    project_id: projectId || 0,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/retrospectives/generate', formData);
      onClose();
    } catch (error) {
      console.error('Failed to generate retrospective:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="title" className="block text-sm font-medium text-gray-700">
          Title
        </label>
        <input
          type="text"
          id="title"
          value={formData.title}
          onChange={(e) => setFormData({ ...formData, title: e.target.value })}
          className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
          required
        />
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="period_start" className="block text-sm font-medium text-gray-700">
            Start Date
          </label>
          <input
            type="date"
            id="period_start"
            value={formData.period_start}
            onChange={(e) => setFormData({ ...formData, period_start: e.target.value })}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            required
          />
        </div>
        
        <div>
          <label htmlFor="period_end" className="block text-sm font-medium text-gray-700">
            End Date
          </label>
          <input
            type="date"
            id="period_end"
            value={formData.period_end}
            onChange={(e) => setFormData({ ...formData, period_end: e.target.value })}
            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            required
          />
        </div>
      </div>
      
      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={onClose}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700"
        >
          Generate
        </button>
      </div>
    </form>
  );
};

export default RetrospectivesList;
