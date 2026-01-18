import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  LayoutDashboard, 
  BookOpen, 
  GraduationCap, 
  Calendar, 
  CreditCard, 
  Trophy, 
  MessageSquare, 
  Users, 
  Settings,
  LogOut,
  ChevronRight,
  Sparkles,
  Brain,
  Network,
  FileUp,
  Search,
  Mic,
  TrendingUp,
  FileCheck,
  Wifi,
  Fingerprint,
  Video,
  AlertTriangle,
  UsersRound
} from 'lucide-react';

const navItems = {
  student: [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/courses', icon: BookOpen, label: 'My Courses' },
    { path: '/grades', icon: GraduationCap, label: 'Grades' },
    { path: '/attendance', icon: Calendar, label: 'Attendance' },
    { path: '/fees', icon: CreditCard, label: 'Fees' },
    { path: '/achievements', icon: Trophy, label: 'Achievements' },
    { divider: true, label: 'AI Learning' },
    { path: '/ai-mentor', icon: Brain, label: 'AI Mentor' },
    { path: '/knowledge-graph', icon: Network, label: 'Knowledge Graph' },
    { path: '/learn-by-teaching', icon: Mic, label: 'Learn by Teaching' },
    { path: '/learning-journey', icon: TrendingUp, label: 'Learning Journey' },
    { path: '/study-groups', icon: UsersRound, label: 'AI Study Groups' },
    { path: '/live-research', icon: Search, label: 'Live Research' },
    { divider: true, label: 'Classes' },
    { path: '/virtual-classroom', icon: Video, label: 'Virtual Classroom' },
    { path: '/career', icon: Sparkles, label: 'Career Guide' },
  ],
  teacher: [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/courses', icon: BookOpen, label: 'My Classes' },
    { path: '/students', icon: Users, label: 'Students' },
    { path: '/grades', icon: GraduationCap, label: 'Grading' },
    { path: '/attendance', icon: Calendar, label: 'Attendance' },
    { divider: true, label: 'AI Tools' },
    { path: '/lesson-planner', icon: Sparkles, label: 'AI Planner' },
    { path: '/syllabus-ingestion', icon: FileUp, label: 'Syllabus Ingestion' },
    { path: '/student-risk', icon: AlertTriangle, label: 'Risk Prediction' },
    { path: '/ai-mentor', icon: Brain, label: 'AI Mentor' },
    { divider: true, label: 'Smart Campus' },
    { path: '/virtual-classroom', icon: Video, label: 'Virtual Classroom' },
    { path: '/rfid-attendance', icon: Wifi, label: 'RFID Attendance' },
    { path: '/biometric-attendance', icon: Fingerprint, label: 'Biometric' },
    { path: '/credentials', icon: FileCheck, label: 'Credentials' },
  ],
  admin: [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/students', icon: Users, label: 'Students' },
    { path: '/teachers', icon: GraduationCap, label: 'Teachers' },
    { path: '/courses', icon: BookOpen, label: 'Courses' },
    { path: '/fees', icon: CreditCard, label: 'Finance' },
    { path: '/achievements', icon: Trophy, label: 'Achievements' },
    { divider: true, label: 'AI Tools' },
    { path: '/syllabus-ingestion', icon: FileUp, label: 'Syllabus Ingestion' },
    { path: '/student-risk', icon: AlertTriangle, label: 'Risk Prediction' },
    { path: '/ai-mentor', icon: Brain, label: 'AI Mentor' },
    { divider: true, label: 'Smart Campus' },
    { path: '/virtual-classroom', icon: Video, label: 'Virtual Classroom' },
    { path: '/rfid-attendance', icon: Wifi, label: 'RFID Attendance' },
    { path: '/biometric-attendance', icon: Fingerprint, label: 'Biometric' },
    { path: '/credentials', icon: FileCheck, label: 'Credentials' },
  ],
  org_admin: [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/students', icon: Users, label: 'Participants' },
    { path: '/teachers', icon: GraduationCap, label: 'Staff' },
    { path: '/courses', icon: BookOpen, label: 'Programs' },
    { path: '/fees', icon: CreditCard, label: 'Finance' },
    { divider: true, label: 'AI Tools' },
    { path: '/syllabus-ingestion', icon: FileUp, label: 'Syllabus Ingestion' },
    { path: '/student-risk', icon: AlertTriangle, label: 'Risk Prediction' },
    { path: '/ai-mentor', icon: Brain, label: 'AI Mentor' },
    { divider: true, label: 'Smart Campus' },
    { path: '/virtual-classroom', icon: Video, label: 'Virtual Classroom' },
    { path: '/rfid-attendance', icon: Wifi, label: 'RFID Attendance' },
    { path: '/biometric-attendance', icon: Fingerprint, label: 'Biometric' },
    { path: '/credentials', icon: FileCheck, label: 'Credentials' },
  ],
  parent: [
    { path: '/parent-portal', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/children', icon: Users, label: 'My Children' },
    { path: '/fees', icon: CreditCard, label: 'Fees' },
    { path: '/attendance', icon: Calendar, label: 'Attendance' },
  ],
};

export const Sidebar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const items = navItems[user?.role] || navItems.student;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-[#0d0d0f] border-r border-white/5 flex flex-col z-50">
      {/* Logo */}
      <div className="p-6 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center">
            <GraduationCap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight">EduOS</h1>
            <p className="text-xs text-zinc-500">2026 Platform</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {items.map((item, index) => (
          item.divider ? (
            <div key={`divider-${index}`} className="pt-4 pb-2">
              <p className="px-4 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                {item.label}
              </p>
            </div>
          ) : (
            <NavLink
              key={item.path}
              to={item.path}
              data-testid={`nav-${item.label.toLowerCase().replace(/\s/g, '-')}`}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 group ${
                  isActive
                    ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                    : 'text-zinc-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span className="flex-1">{item.label}</span>
              <ChevronRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
            </NavLink>
          )
        ))}
      </nav>

      {/* User section */}
      <div className="p-4 border-t border-white/5">
        <NavLink
          to="/settings"
          data-testid="nav-settings"
          className="flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-zinc-400 hover:text-white hover:bg-white/5 transition-all"
        >
          <Settings className="w-5 h-5" />
          <span>Settings</span>
        </NavLink>
        <button
          onClick={handleLogout}
          data-testid="logout-btn"
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-zinc-400 hover:text-red-400 hover:bg-red-500/10 transition-all mt-1"
        >
          <LogOut className="w-5 h-5" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
};
