/**
 * Sidebar layout for authenticated staff users.
 * Responsive with collapsible sidebar on mobile.
 */

import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import {
  LayoutDashboard, Briefcase, Users, FileText, Calendar,
  Gift, Bell, Settings, LogOut, Menu, X, ChevronRight,
  Shield, ClipboardList, UserCircle,
} from 'lucide-react';

const staffNavItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', roles: ['admin', 'recruiter', 'hiring_manager'] },
  { to: '/jobs', icon: Briefcase, label: 'Jobs', roles: ['admin', 'recruiter', 'hiring_manager'] },
  { to: '/applications', icon: FileText, label: 'Applications', roles: ['admin', 'recruiter', 'hiring_manager'] },
  { to: '/candidates', icon: Users, label: 'Candidates', roles: ['admin', 'recruiter', 'hiring_manager'] },
  { to: '/interviews', icon: Calendar, label: 'Interviews', roles: ['admin', 'recruiter', 'hiring_manager', 'interviewer'] },
  { to: '/offers', icon: Gift, label: 'Offers', roles: ['admin', 'recruiter'] },
  { to: '/users', icon: Shield, label: 'Users', roles: ['admin'] },
];

const candidateNavItems = [
  { to: '/my-dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/careers', icon: Briefcase, label: 'Browse Jobs' },
  { to: '/my-applications', icon: ClipboardList, label: 'My Applications' },
  { to: '/my-interviews', icon: Calendar, label: 'Interviews' },
  { to: '/profile', icon: UserCircle, label: 'Profile' },
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navItems = user?.role === 'candidate' ? candidateNavItems : staffNavItems;
  const filteredNav = user?.role === 'candidate'
    ? navItems
    : navItems.filter((item) => 'roles' in item && (item as any).roles.includes(user?.role));

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const roleLabel: Record<string, string> = {
    admin: 'Administrator',
    recruiter: 'Recruiter',
    hiring_manager: 'Hiring Manager',
    interviewer: 'Interviewer',
    candidate: 'Candidate',
  };

  return (
    <div className="flex h-screen bg-surface-50">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/30 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-white border-r border-surface-100 
          flex flex-col transition-transform duration-300 lg:translate-x-0 lg:static
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-surface-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 gradient-primary rounded-lg flex items-center justify-center">
              <Briefcase className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold gradient-text">RecruitFlow</span>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="lg:hidden text-surface-400 hover:text-surface-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* User info */}
        <div className="px-4 py-4 border-b border-surface-100">
          <div className="flex items-center gap-3 px-2">
            <div className="w-10 h-10 gradient-primary rounded-full flex items-center justify-center text-white font-bold text-sm">
              {user?.name?.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-surface-900 truncate">{user?.name}</p>
              <p className="text-xs text-surface-500">{roleLabel[user?.role || ''] || user?.role}</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {filteredNav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                `nav-link ${isActive ? 'nav-link-active' : ''}`
              }
            >
              <item.icon className="w-5 h-5 shrink-0" />
              <span>{item.label}</span>
              <ChevronRight className="w-4 h-4 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-surface-100 space-y-1">
          <NavLink to="/settings" className="nav-link" onClick={() => setSidebarOpen(false)}>
            <Settings className="w-5 h-5" />
            <span>Settings</span>
          </NavLink>
          <button onClick={handleLogout} className="nav-link w-full text-danger hover:bg-red-50 hover:text-danger">
            <LogOut className="w-5 h-5" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-16 bg-white border-b border-surface-100 flex items-center justify-between px-6 shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden text-surface-500 hover:text-surface-700"
          >
            <Menu className="w-6 h-6" />
          </button>
          <div className="hidden lg:block" />
          <div className="flex items-center gap-4">
            <button className="relative text-surface-400 hover:text-surface-600 transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute -top-1 -right-1 w-2 h-2 bg-danger rounded-full" />
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
