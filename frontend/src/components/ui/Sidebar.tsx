import React from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { 
  Home, 
  Users, 
  CheckSquare, 
  FolderOpen, 
  BarChart3, 
  Heart, 
  Settings, 
  User,
  Shield,
  Target,
  Brain,
  MessageSquare
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { useAuth } from '../../contexts/AuthContext'

interface SidebarProps {
  isCollapsed: boolean
  onToggle: () => void
}

interface NavItem {
  name: string
  href: string
  icon: React.ComponentType<any>
  roles?: string[]
}

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, onToggle }) => {
  const { user } = useAuth()
  const location = useLocation()

  const navigation: NavItem[] = [
    {
      name: 'Dashboard',
      href: '/',
      icon: Home,
    },
    {
      name: 'Skills',
      href: '/skills',
      icon: Brain,
    },
    {
      name: 'Tasks',
      href: '/tasks',
      icon: CheckSquare,
    },
    {
      name: 'Task Allocation',
      href: '/tasks/allocation',
      icon: Target,
      roles: ['team_lead', 'manager', 'admin'],
    },
    {
      name: 'Projects',
      href: '/projects',
      icon: FolderOpen,
    },
    {
      name: 'Analytics',
      href: '/analytics',
      icon: BarChart3,
    },
    {
      name: 'Sentiment',
      href: '/sentiment',
      icon: MessageSquare,
      roles: ['team_lead', 'manager', 'hr', 'admin'],
    },
    {
      name: 'Profile',
      href: '/profile',
      icon: User,
    },
    {
      name: 'Admin',
      href: '/admin',
      icon: Shield,
      roles: ['admin'],
    },
  ]

  const filteredNavigation = navigation.filter(item => {
    if (!item.roles) return true
    return user && item.roles.includes(user.role)
  })

  return (
    <div className={cn(
      'bg-primary-800 text-white h-full flex flex-col transition-all duration-300',
      isCollapsed ? 'w-16' : 'w-64'
    )}>
      {/* Logo */}
      <div className="p-4 border-b border-primary-700">
        <div className="flex items-center">
          <div className="bg-white rounded-lg p-2">
            <Shield className="h-6 w-6 text-primary-600" />
          </div>
          {!isCollapsed && (
            <div className="ml-3">
              <h1 className="text-lg font-bold">iSentry</h1>
              <p className="text-sm text-primary-200">TeamIQ</p>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {filteredNavigation.map((item) => {
          const Icon = item.icon
          const isActive = location.pathname === item.href || 
                          (item.href !== '/' && location.pathname.startsWith(item.href))
          
          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={cn(
                'group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors',
                isActive
                  ? 'bg-primary-700 text-white'
                  : 'text-primary-200 hover:bg-primary-700 hover:text-white'
              )}
              title={isCollapsed ? item.name : undefined}
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              {!isCollapsed && (
                <span className="ml-3">{item.name}</span>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* User Info */}
      <div className="p-4 border-t border-primary-700">
        <div className="flex items-center">
          <div className="bg-primary-600 rounded-full p-2">
            <User className="h-4 w-4" />
          </div>
          {!isCollapsed && user && (
            <div className="ml-3 min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user.full_name}
              </p>
              <p className="text-xs text-primary-200 truncate">
                {user.role.replace('_', ' ').toUpperCase()}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Sidebar
