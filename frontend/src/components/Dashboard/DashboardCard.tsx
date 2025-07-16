import React from 'react'
import { LucideIcon } from 'lucide-react'
import { cn } from '../../lib/utils'
import Card from '../ui/Card'

interface DashboardCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  iconColor?: string
  change?: {
    value: number
    label: string
    positive?: boolean
  }
  className?: string
  onClick?: () => void
}

const DashboardCard: React.FC<DashboardCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  iconColor = 'text-primary-600',
  change,
  className,
  onClick,
}) => {
  return (
    <Card
      className={cn('cursor-pointer hover:shadow-lg transition-shadow', className)}
      onClick={onClick}
    >
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <div className={cn('w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center')}>
            <Icon className={cn('h-5 w-5', iconColor)} />
          </div>
        </div>
        
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subtitle && (
            <p className="text-sm text-gray-500">{subtitle}</p>
          )}
        </div>
      </div>
      
      {change && (
        <div className="mt-4 flex items-center">
          <span
            className={cn(
              'text-sm font-medium',
              change.positive ? 'text-green-600' : 'text-red-600'
            )}
          >
            {change.positive ? '+' : ''}{change.value}%
          </span>
          <span className="text-sm text-gray-500 ml-1">{change.label}</span>
        </div>
      )}
    </Card>
  )
}

export default DashboardCard
