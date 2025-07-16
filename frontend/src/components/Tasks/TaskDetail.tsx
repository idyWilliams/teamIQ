import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../../services/api";
import Card from "../ui/Card";
import Button from "../ui/Button";
import Loading from "../ui/LoadingSpinner";
import EmptyState from "../ui/EmptyState";
import {
  ClipboardDocumentListIcon,
  CalendarDaysIcon,
  ClockIcon,
  CheckCircleIcon,
  XMarkIcon,
  PencilIcon,
  ChartBarIcon,
  FolderIcon,
  UserIcon,
} from "@heroicons/react/24/outline";

const TaskDetail: React.FC = () => {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    title: "",
    description: "",
    status: "",
    priority: "",
    estimated_hours: "",
    actual_hours: "",
    due_date: "",
  });

  const { data: taskData, isLoading } = useQuery({
    queryKey: ["task", taskId],
    queryFn: () => api.get(`/tasks/${taskId}`),
    enabled: !!taskId,
  });

  const updateTaskMutation = useMutation({
    mutationFn: (data: any) => api.put(`/tasks/${taskId}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["task", taskId] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      setIsEditing(false);
    },
  });

  if (isLoading) {
    return <Loading />;
  }

  if (!taskData?.data) {
    return <EmptyState />;
    // return <EmptyState message="Task not found" />;
  }

  const { task } = taskData.data;

  const handleEditClick = () => {
    setEditForm({
      title: task.title || "",
      description: task.description || "",
      status: task.status || "",
      priority: task.priority || "",
      estimated_hours: task.estimated_hours?.toString() || "",
      actual_hours: task.actual_hours?.toString() || "",
      due_date: task.due_date
        ? new Date(task.due_date).toISOString().split("T")[0]
        : "",
    });
    setIsEditing(true);
  };

  const handleSave = () => {
    const updateData: any = {};

    if (editForm.title !== task.title) updateData.title = editForm.title;
    if (editForm.description !== task.description)
      updateData.description = editForm.description;
    if (editForm.status !== task.status) updateData.status = editForm.status;
    if (editForm.priority !== task.priority)
      updateData.priority = editForm.priority;
    if (editForm.estimated_hours !== task.estimated_hours?.toString()) {
      updateData.estimated_hours = editForm.estimated_hours
        ? parseFloat(editForm.estimated_hours)
        : null;
    }
    if (editForm.actual_hours !== task.actual_hours?.toString()) {
      updateData.actual_hours = editForm.actual_hours
        ? parseFloat(editForm.actual_hours)
        : null;
    }
    if (
      editForm.due_date !==
      (task.due_date ? new Date(task.due_date).toISOString().split("T")[0] : "")
    ) {
      updateData.due_date = editForm.due_date
        ? new Date(editForm.due_date).toISOString()
        : null;
    }

    if (Object.keys(updateData).length > 0) {
      updateTaskMutation.mutate(updateData);
    } else {
      setIsEditing(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "done":
        return "bg-green-100 text-green-700";
      case "in_progress":
        return "bg-blue-100 text-blue-700";
      case "in_review":
        return "bg-purple-100 text-purple-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "urgent":
        return "bg-red-100 text-red-700";
      case "high":
        return "bg-orange-100 text-orange-700";
      case "medium":
        return "bg-yellow-100 text-yellow-700";
      default:
        return "bg-green-100 text-green-700";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            onClick={() => navigate("/tasks")}
            className="p-2"
          >
            <XMarkIcon className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{task.title}</h1>
            <p className="text-gray-600">Task Details</p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {isEditing ? (
            <>
              <Button
                variant="ghost"
                onClick={() => setIsEditing(false)}
                disabled={updateTaskMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={updateTaskMutation.isPending}
              >
                Save Changes
              </Button>
            </>
          ) : (
            <Button
              variant="ghost"
              onClick={handleEditClick}
              className="flex items-center space-x-2"
            >
              <PencilIcon className="w-4 h-4" />
              <span>Edit</span>
            </Button>
          )}
        </div>
      </div>

      {/* Task Information */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Task Details */}
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">Task Information</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Title
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editForm.title}
                    onChange={(e) =>
                      setEditForm({ ...editForm, title: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">{task.title}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                {isEditing ? (
                  <textarea
                    value={editForm.description}
                    onChange={(e) =>
                      setEditForm({ ...editForm, description: e.target.value })
                    }
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">
                    {task.description || "No description provided"}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Status
                  </label>
                  {isEditing ? (
                    <select
                      value={editForm.status}
                      onChange={(e) =>
                        setEditForm({ ...editForm, status: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="to_do">To Do</option>
                      <option value="in_progress">In Progress</option>
                      <option value="in_review">In Review</option>
                      <option value="done">Done</option>
                    </select>
                  ) : (
                    <span
                      className={`inline-block px-3 py-1 text-sm rounded-full ${getStatusColor(
                        task.status
                      )}`}
                    >
                      {task.status.replace("_", " ")}
                    </span>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Priority
                  </label>
                  {isEditing ? (
                    <select
                      value={editForm.priority}
                      onChange={(e) =>
                        setEditForm({ ...editForm, priority: e.target.value })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  ) : (
                    <span
                      className={`inline-block px-3 py-1 text-sm rounded-full ${getPriorityColor(
                        task.priority
                      )}`}
                    >
                      {task.priority}
                    </span>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Due Date
                </label>
                {isEditing ? (
                  <input
                    type="date"
                    value={editForm.due_date}
                    onChange={(e) =>
                      setEditForm({ ...editForm, due_date: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">
                    {task.due_date
                      ? formatDate(task.due_date)
                      : "No due date set"}
                  </p>
                )}
              </div>
            </div>
          </Card>

          {/* Time Tracking */}
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">Time Tracking</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Estimated Hours
                </label>
                {isEditing ? (
                  <input
                    type="number"
                    step="0.5"
                    value={editForm.estimated_hours}
                    onChange={(e) =>
                      setEditForm({
                        ...editForm,
                        estimated_hours: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">
                    {task.estimated_hours || 0} hours
                  </p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Actual Hours
                </label>
                {isEditing ? (
                  <input
                    type="number"
                    step="0.5"
                    value={editForm.actual_hours}
                    onChange={(e) =>
                      setEditForm({ ...editForm, actual_hours: e.target.value })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">
                    {task.actual_hours || 0} hours
                  </p>
                )}
              </div>
            </div>

            {task.time_tracking && (
              <div className="mt-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600">Time Progress</span>
                  <span className="text-sm text-gray-600">
                    {task.time_tracking.remaining_hours} hours remaining
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{
                      width: `${Math.min(
                        100,
                        (task.time_tracking.actual_hours /
                          task.time_tracking.estimated_hours) *
                          100
                      )}%`,
                    }}
                  ></div>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Progress */}
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">Progress</h2>
            <div className="space-y-4">
              {task.progress && (
                <>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Completion</span>
                    <span className="text-sm font-semibold">
                      {task.progress.completion_percentage}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{
                        width: `${task.progress.completion_percentage}%`,
                      }}
                    ></div>
                  </div>
                </>
              )}

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Status</span>
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${getStatusColor(
                      task.status
                    )}`}
                  >
                    {task.status.replace("_", " ")}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Priority</span>
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${getPriorityColor(
                      task.priority
                    )}`}
                  >
                    {task.priority}
                  </span>
                </div>
                {task.story_points && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Story Points</span>
                    <span className="text-sm font-semibold">
                      {task.story_points}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Additional Information */}
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4">Additional Info</h2>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <ClipboardDocumentListIcon className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-sm text-gray-600">Task ID</p>
                  <p className="text-sm font-medium">{task.id}</p>
                </div>
              </div>

              {task.jira_key && (
                <div className="flex items-center space-x-3">
                  <FolderIcon className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-600">Jira Key</p>
                    <p className="text-sm font-medium">{task.jira_key}</p>
                  </div>
                </div>
              )}

              {task.github_pr_url && (
                <div className="flex items-center space-x-3">
                  <div className="w-5 h-5 text-gray-400">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Pull Request</p>
                    <a
                      href={task.github_pr_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm font-medium text-blue-600 hover:text-blue-800"
                    >
                      View PR
                    </a>
                  </div>
                </div>
              )}

              <div className="flex items-center space-x-3">
                <CalendarDaysIcon className="w-5 h-5 text-gray-400" />
                <div>
                  <p className="text-sm text-gray-600">Created</p>
                  <p className="text-sm font-medium">
                    {formatDate(task.created_at)}
                  </p>
                </div>
              </div>

              {task.completed_at && (
                <div className="flex items-center space-x-3">
                  <CheckCircleIcon className="w-5 h-5 text-green-500" />
                  <div>
                    <p className="text-sm text-gray-600">Completed</p>
                    <p className="text-sm font-medium">
                      {formatDate(task.completed_at)}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default TaskDetail;
