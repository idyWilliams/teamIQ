import React from 'react'
import { NavLink } from 'react-router-dom'
import { cn } from '../../lib/utils'

interface NavigationItem {
  name: string
  href: string
  current?: boolean
}

interface NavigationProps {
  items: NavigationItem[]
  className?: string
}

const Navigation: React.FC<NavigationProps> = ({ items, className }) => {
  return (
    <nav className={cn('flex space-x-8', className)}>
      {items.map((item) => (
        <NavLink
          key={item.name}
          to={item.href}
          className={({ isActive }) =>
            cn(
              'whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm transition-colors',
              isActive
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            )
          }
        >
          {item.name}
        </NavLink>
      ))}
    </nav>
  )
}

export default Navigation
