import React from 'react'
import { Calendar, Clock, User, AlertCircle } from 'lucide-react'
import { Task } from '../../types'
import { formatDate, formatRelativeTime } from '../../lib/utils'
import Card, { CardHeader, CardContent } from '../ui/Card'
import Badge from '../ui/Badge'

interface TaskListProps {
  tasks: Task[]
  title?: string
  showAssignee?: boolean
  limit?: number
  className?: string
  onTaskClick?: (task: Task) => void
}

const TaskList: React.FC<TaskListProps> = ({
  tasks,
  title = 'Recent Tasks',
  showAssignee = false,
  limit,
  className,
  onTaskClick,
}) => {
  const displayTasks = limit ? tasks.slice(0, limit) : tasks

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'done':
        return 'success'
      case 'in_progress':
        return 'warning'
      case 'todo':
        return 'secondary'
      default:
        return 'default'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'error'
      case 'medium':
        return 'warning'
      case 'low':
        return 'success'
      default:
        return 'default'
    }
  }

  if (displayTasks.length === 0) {
    return (
      <Card className={className}>
        <CardHeader title={title} />
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            <p>No tasks available</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={className}>
      <CardHeader title={title} />
      <CardContent>
        <div className="space-y-4">
          {displayTasks.map((task) => (
            <div
              key={task.id}
              className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => onTaskClick?.(task)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900 mb-2">
                    {task.title}
                  </h4>
                  
                  {task.description && (
                    <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                      {task.description}
                    </p>
                  )}
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <div className="flex items-center">
                      <Clock className="h-4 w-4 mr-1" />
                      {formatRelativeTime(task.created_at)}
                    </div>
                    
                    {task.due_date && (
                      <div className="flex items-center">
                        <Calendar className="h-4 w-4 mr-1" />
                        Due {formatDate(task.due_date, 'short')}
                      </div>
                    )}
                    
                    {showAssignee && task.assignee_name && (
                      <div className="flex items-center">
                        <User className="h-4 w-4 mr-1" />
                        {task.assignee_name}
                      </div>
                    )}
                    
                    {task.story_points && (
                      <div className="flex items-center">
                        <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                          {task.story_points} pts
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="flex flex-col items-end space-y-2">
                  <div className="flex space-x-2">
                    <Badge
                      variant={getStatusColor(task.status)}
                      size="sm"
                    >
                      {task.status.replace('_', ' ')}
                    </Badge>
                    <Badge
                      variant={getPriorityColor(task.priority)}
                      size="sm"
                    >
                      {task.priority}
                    </Badge>
                  </div>
                  
                  {task.due_date && new Date(task.due_date) < new Date() && task.status !== 'done' && (
                    <div className="flex items-center text-red-500 text-xs">
                      <AlertCircle className="h-3 w-3 mr-1" />
                      Overdue
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export default TaskList
