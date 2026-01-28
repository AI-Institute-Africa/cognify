import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
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
  UsersRound,
  Languages,
  HelpCircle,
  Target,
  Layers,
  Volume2,
  Globe,
  User,
  ClipboardList,
  Glasses,
  FileText
} from 'lucide-react';

const navItems = {
  student: [
    { path: '/dashboard', icon: LayoutDashboard, labelKey: 'dashboard' },
    { path: '/courses', icon: BookOpen, labelKey: 'myCourses' },
    { path: '/assignments', icon: FileText, labelKey: 'assignments' },
    { path: '/exams', icon: ClipboardList, labelKey: 'exams' },
    { path: '/grades', icon: GraduationCap, labelKey: 'grades' },
    { path: '/attendance', icon: Calendar, labelKey: 'attendance' },
    { path: '/fees', icon: CreditCard, labelKey: 'fees' },
    { path: '/achievements', icon: Trophy, labelKey: 'achievements' },
    { divider: true, labelKey: 'aiMentor' },
    { path: '/ai-mentor', icon: Brain, labelKey: 'aiMentor' },
    { path: '/avatar-settings', icon: User, labelKey: 'myAvatar' },
    { path: '/vr-learning', icon: Glasses, labelKey: 'vrLearning' },
    { path: '/knowledge-graph', icon: Network, labelKey: 'knowledgeGraph' },
    { path: '/learn-by-teaching', icon: Mic, labelKey: 'learnByTeaching' },
    { path: '/question-analysis', icon: HelpCircle, label: 'Question Analysis' },
    { path: '/learning-journey', icon: TrendingUp, labelKey: 'learningJourney' },
    { path: '/study-groups', icon: UsersRound, labelKey: 'studyGroups' },
    { path: '/outcome-learning', icon: Target, label: 'Outcome Learning' },
    { divider: true, label: 'Classes' },
    { path: '/virtual-classroom', icon: Video, labelKey: 'virtualClassroom' },
    { path: '/live-research', icon: Search, labelKey: 'liveResearch' },
    { path: '/career', icon: Sparkles, labelKey: 'careerGuidance' },
  ],
  teacher: [
    { path: '/dashboard', icon: LayoutDashboard, labelKey: 'dashboard' },
    { path: '/courses', icon: BookOpen, label: 'My Classes' },
    { path: '/exams', icon: ClipboardList, labelKey: 'exams' },
    { path: '/students', icon: Users, label: 'Students' },
    { path: '/grades', icon: GraduationCap, label: 'Grading' },
    { path: '/attendance', icon: Calendar, labelKey: 'attendance' },
    { divider: true, label: 'AI Tools' },
    { path: '/lesson-planner', icon: Sparkles, label: 'AI Planner' },
    { path: '/syllabus-ingestion', icon: FileUp, label: 'Syllabus Ingestion' },
    { path: '/assignment-generator', icon: FileCheck, label: 'Assignment Gen' },
    { path: '/multidisciplinary', icon: Layers, label: 'Multi-Subject' },
    { path: '/student-risk', icon: AlertTriangle, labelKey: 'riskPrediction' },
    { path: '/ai-mentor', icon: Brain, labelKey: 'aiMentor' },
    { divider: true, label: 'Smart Campus' },
    { path: '/virtual-classroom', icon: Video, labelKey: 'virtualClassroom' },
    { path: '/rfid-attendance', icon: Wifi, label: 'RFID Attendance' },
    { path: '/biometric-attendance', icon: Fingerprint, label: 'Biometric' },
    { path: '/credentials', icon: FileCheck, labelKey: 'credentials' },
  ],
  admin: [
    { path: '/dashboard', icon: LayoutDashboard, labelKey: 'dashboard' },
    { path: '/students', icon: Users, label: 'Students' },
    { path: '/teachers', icon: GraduationCap, label: 'Teachers' },
    { path: '/courses', icon: BookOpen, labelKey: 'courses' },
    { path: '/fees', icon: CreditCard, label: 'Finance' },
    { path: '/achievements', icon: Trophy, labelKey: 'achievements' },
    { divider: true, label: 'AI Tools' },
    { path: '/syllabus-ingestion', icon: FileUp, label: 'Syllabus Ingestion' },
    { path: '/student-risk', icon: AlertTriangle, labelKey: 'riskPrediction' },
    { path: '/ai-mentor', icon: Brain, labelKey: 'aiMentor' },
    { divider: true, label: 'Smart Campus' },
    { path: '/virtual-classroom', icon: Video, labelKey: 'virtualClassroom' },
    { path: '/rfid-attendance', icon: Wifi, label: 'RFID Attendance' },
    { path: '/biometric-attendance', icon: Fingerprint, label: 'Biometric' },
    { path: '/credentials', icon: FileCheck, labelKey: 'credentials' },
  ],
  org_admin: [
    { path: '/dashboard', icon: LayoutDashboard, labelKey: 'dashboard' },
    { path: '/students', icon: Users, labelKey: 'participants' },
    { path: '/teachers', icon: GraduationCap, label: 'Staff' },
    { path: '/courses', icon: BookOpen, label: 'Programs' },
    { path: '/fees', icon: CreditCard, label: 'Finance' },
    { divider: true, label: 'AI Tools' },
    { path: '/syllabus-ingestion', icon: FileUp, label: 'Syllabus Ingestion' },
    { path: '/student-risk', icon: AlertTriangle, labelKey: 'riskPrediction' },
    { path: '/ai-mentor', icon: Brain, labelKey: 'aiMentor' },
    { divider: true, label: 'Smart Campus' },
    { path: '/virtual-classroom', icon: Video, labelKey: 'virtualClassroom' },
    { path: '/rfid-attendance', icon: Wifi, label: 'RFID Attendance' },
    { path: '/biometric-attendance', icon: Fingerprint, label: 'Biometric' },
    { path: '/credentials', icon: FileCheck, labelKey: 'credentials' },
  ],
  parent: [
    { path: '/dashboard', icon: LayoutDashboard, labelKey: 'dashboard' },
    { path: '/parent-portal', icon: Users, labelKey: 'myChildren' },
    { path: '/fees', icon: CreditCard, labelKey: 'fees' },
    { path: '/attendance', icon: Calendar, labelKey: 'attendance' },
  ],
};

export const Sidebar = () => {
  const { user, logout } = useAuth();
  const { t } = useLanguage();
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
                {item.labelKey ? t(item.labelKey) : item.label}
              </p>
            </div>
          ) : (
            <NavLink
              key={item.path}
              to={item.path}
              data-testid={`nav-${(item.labelKey || item.label).toLowerCase().replace(/\s/g, '-')}`}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 group ${
                  isActive
                    ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                    : 'text-zinc-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <item.icon className="w-5 h-5" />
              <span className="flex-1">{item.labelKey ? t(item.labelKey) : item.label}</span>
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
          <span>{t('settings')}</span>
        </NavLink>
        <button
          onClick={handleLogout}
          data-testid="logout-btn"
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm text-zinc-400 hover:text-red-400 hover:bg-red-500/10 transition-all mt-1"
        >
          <LogOut className="w-5 h-5" />
          <span>{t('logout')}</span>
        </button>
      </div>
    </aside>
  );
};
