import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  HomeIcon, 
  ChartBarIcon, 
  ClipboardDocumentListIcon,
  FolderIcon,
  UsersIcon,
  FaceSmileIcon,
  DocumentTextIcon,
  UserIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon
} from '@heroicons/react/24/outline';

import { useAuth } from '../../hooks/useAuth';

const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const navigationItems = [
    { name: 'Dashboard', href: '/dashboard', icon: HomeIcon, roles: ['intern', 'team_lead', 'hr', 'recruiter', 'admin'] },
    { name: 'Skills', href: '/skills', icon: ChartBarIcon, roles: ['intern', 'team_lead', 'hr', 'recruiter', 'admin'] },
    { name: 'Tasks', href: '/tasks', icon: ClipboardDocumentListIcon, roles: ['intern', 'team_lead', 'hr', 'admin'] },
    { name: 'Projects', href: '/projects', icon: FolderIcon, roles: ['intern', 'team_lead', 'hr', 'admin'] },
    { name: 'Team Members', href: '/team-members', icon: UsersIcon, roles: ['team_lead', 'hr', 'admin'] },
    { name: 'Sentiment', href: '/sentiment', icon: FaceSmileIcon, roles: ['team_lead', 'hr', 'admin'] },
    { name: 'Retrospectives', href: '/retrospectives', icon: DocumentTextIcon, roles: ['team_lead', 'hr', 'admin'] },
    { name: 'Profile', href: '/profile', icon: UserIcon, roles: ['intern', 'team_lead', 'hr', 'recruiter', 'admin'] },
    { name: 'Admin', href: '/admin', icon: Cog6ToothIcon, roles: ['admin'] },
  ];

  const filteredNavigation = navigationItems.filter(item => 
    item.roles.includes(user?.role || '')
  );

  const handleLogout = async () => {
    await logout();
  };

  return (
    <div className="flex flex-col h-full bg-blue-900 text-white">
      {/* Logo */}
      <div className="flex items-center justify-center h-16 bg-blue-800 border-b border-blue-700">
        <div className="flex items-center">
          <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center mr-3">
            <span className="text-blue-900 font-bold text-lg">iS</span>
          </div>
          <span className="text-xl font-bold">iSentry TeamIQ</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {filteredNavigation.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.href;
          
          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={`flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors duration-200 ${
                isActive
                  ? 'bg-blue-800 text-white'
                  : 'text-blue-100 hover:bg-blue-800 hover:text-white'
              }`}
            >
              <Icon className="w-5 h-5 mr-3" />
              {item.name}
            </NavLink>
          );
        })}
      </nav>

      {/* User section */}
      <div className="p-4 border-t border-blue-700">
        <div className="flex items-center mb-4">
          <div className="w-10 h-10 bg-blue-700 rounded-full flex items-center justify-center mr-3">
            <span className="text-sm font-semibold">
              {user?.full_name.split(' ').map(n => n[0]).join('')}
            </span>
          </div>
          <div>
            <p className="text-sm font-medium">{user?.full_name}</p>
            <p className="text-xs text-blue-200 capitalize">{user?.role.replace('_', ' ')}</p>
          </div>
        </div>
        
        <button
          onClick={handleLogout}
          className="flex items-center w-full px-4 py-2 text-sm font-medium text-blue-100 rounded-lg hover:bg-blue-800 hover:text-white transition-colors duration-200"
        >
          <ArrowRightOnRectangleIcon className="w-5 h-5 mr-3" />
          Logout
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
