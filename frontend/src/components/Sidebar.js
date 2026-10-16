import React, { useState } from 'react';
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
  Building2,
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
  FileText,
  X,
  ChevronDown,
  FolderOpen,
  Import,
  Share2,
  Zap,
  Award,
  BarChart3,
  Shield,
  UserCheck,
  Newspaper
} from 'lucide-react';

const navItems = {
  student: [
    { path: '/dashboard', icon: LayoutDashboard, labelKey: 'dashboard' },
    { 
      icon: FolderOpen, 
      label: 'My Courses',
      subItems: [
        { path: '/courses', icon: BookOpen, label: 'Standard Courses' },
        { path: '/create-custom-course', icon: FileUp, label: 'Customized Courses' },
        { path: '/premade-courses', icon: FolderOpen, label: 'Premade Courses' },
        { path: '/org-catalog', icon: Building2, label: 'Organization Catalog', orgOnly: true },
      ]
    },
    { 
      icon: Globe, 
      label: 'Public Library & Summits',
      subItems: [
        { path: '/public', icon: Globe, label: 'Browse Public Library' },
        { path: '/public?tab=summit', icon: Award, label: 'Summit Presentations' },
        { path: '/public?tab=keynote', icon: Sparkles, label: 'Keynotes & Workshops' },
      ]
    },
    { path: '/multi-subject', icon: Layers, label: 'Multi-Subject Learning' },
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
    { path: '/ai-training-engine', icon: Zap, label: 'AI Q&A Generator' },
    { path: '/learning-journey', icon: TrendingUp, labelKey: 'learningJourney' },
    { path: '/study-groups', icon: UsersRound, labelKey: 'studyGroups' },
    { divider: true, label: 'Share & Collaborate' },
    { path: '/share-content', icon: Share2, label: 'Share Content' },
    { path: '/certificate-gallery', icon: Award, label: 'Certificate Gallery' },
    { path: '/virtual-classroom', icon: Video, labelKey: 'virtualClassroom' },
    { path: '/live-research', icon: Search, labelKey: 'liveResearch' },
    { path: '/career', icon: Sparkles, labelKey: 'careerGuidance' },
  ],
  teacher: [
    { path: '/dashboard', icon: LayoutDashboard, labelKey: 'dashboard' },
    { 
      icon: FolderOpen, 
      label: 'My Courses',
      subItems: [
        { path: '/courses', icon: BookOpen, label: 'Standard Courses' },
        { path: '/create-custom-course', icon: FileUp, label: 'Customized Courses' },
        { path: '/premade-courses', icon: FolderOpen, label: 'Premade Courses' },
        { path: '/org-catalog', icon: Building2, label: 'Organization Catalog', orgOnly: true },
      ]
    },
    { 
      icon: Globe, 
      label: 'Public Library & Summits',
      subItems: [
        { path: '/public', icon: Globe, label: 'Browse Public Library' },
        { path: '/public?tab=summit', icon: Award, label: 'Summit Presentations' },
        { path: '/public?tab=keynote', icon: Sparkles, label: 'Keynotes & Workshops' },
      ]
    },
    { path: '/multi-subject', icon: Layers, label: 'Multi-Subject' },
    { path: '/exams', icon: ClipboardList, labelKey: 'exams' },
    { path: '/students', icon: Users, label: 'Students' },
    { path: '/grades', icon: GraduationCap, label: 'Grading' },
    { path: '/attendance', icon: Calendar, labelKey: 'attendance' },
    { path: '/teacher-messaging', icon: MessageSquare, label: 'Messaging' },
    { path: '/course-analytics', icon: BarChart3, label: 'Course Analytics' },
    { divider: true, label: 'AI Tools' },
    { path: '/lesson-planner', icon: Sparkles, label: 'AI Planner' },
    { path: '/syllabus-ingestion', icon: FileUp, label: 'Content Ingestion' },
    { path: '/assignment-generator', icon: FileCheck, label: 'Assignment Gen' },
    { path: '/ai-training-engine', icon: Zap, label: 'AI Q&A Generator' },
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
    { 
      icon: FolderOpen, 
      label: 'My Courses',
      subItems: [
        { path: '/courses', icon: BookOpen, label: 'Standard Courses' },
        { path: '/create-custom-course', icon: FileUp, label: 'Customized Courses' },
        { path: '/premade-courses', icon: FolderOpen, label: 'Premade Courses' },
        { path: '/org-catalog', icon: Building2, label: 'Organization Catalog' },
      ]
    },
    { 
      icon: Globe, 
      label: 'Public Library & Summits',
      subItems: [
        { path: '/public', icon: Globe, label: 'Browse Public Library' },
        { path: '/public?tab=summit', icon: Award, label: 'Summit Presentations' },
        { path: '/public?tab=keynote', icon: Sparkles, label: 'Keynotes & Workshops' },
      ]
    },
    { path: '/multi-subject', icon: Layers, label: 'Multi-Subject' },
    { path: '/exams', icon: ClipboardList, label: 'Exams' },
    { path: '/assignments', icon: FileText, label: 'Assignments' },
    { path: '/grades', icon: GraduationCap, label: 'Grading' },
    { path: '/fees', icon: CreditCard, label: 'Finance' },
    { path: '/achievements', icon: Trophy, labelKey: 'achievements' },
    { path: '/credentials', icon: FileCheck, labelKey: 'credentials' },
    { path: '/course-analytics', icon: BarChart3, label: 'Course Analytics' },
    { divider: true, label: 'AI Tools' },
    { path: '/ai-training-engine', icon: Zap, label: 'AI Q&A Generator' },
    { path: '/lesson-planner', icon: Sparkles, label: 'AI Planner' },
    { path: '/syllabus-ingestion', icon: FileUp, label: 'Content Ingestion' },
    { path: '/assignment-generator', icon: FileCheck, label: 'Assignment Gen' },
    { path: '/question-analysis', icon: HelpCircle, label: 'Question Analysis' },
    { path: '/ai-mentor', icon: Brain, labelKey: 'aiMentor' },
    { path: '/student-risk', icon: AlertTriangle, labelKey: 'riskPrediction' },
    { path: '/learn-by-teaching', icon: Mic, label: 'Learn by Teaching' },
    { path: '/knowledge-graph', icon: Network, label: 'Knowledge Graph' },
    { divider: true, label: 'Smart Campus' },
    { path: '/virtual-classroom', icon: Video, labelKey: 'virtualClassroom' },
    { path: '/rfid-attendance', icon: Wifi, label: 'RFID Attendance' },
    { path: '/biometric-attendance', icon: Fingerprint, label: 'Biometric' },
    { path: '/share-content', icon: Share2, label: 'Share Content' },
  ],
  org_admin: [
    { path: '/dashboard', icon: LayoutDashboard, labelKey: 'dashboard' },
    { path: '/org-admin', icon: Users, label: 'Org Dashboard' },
    { path: '/org-admin/members', icon: UserCheck, label: 'Members & Join Link' },
    { path: '/organization-settings', icon: Settings, label: 'Organization Settings' },
    { path: '/students', icon: Users, labelKey: 'participants' },
    { path: '/teachers', icon: GraduationCap, label: 'Staff' },
    { 
      icon: FolderOpen, 
      label: 'My Courses',
      subItems: [
        { path: '/courses', icon: BookOpen, label: 'Standard Courses' },
        { path: '/create-custom-course', icon: FileUp, label: 'Add Course' },
        { path: '/premade-courses', icon: FolderOpen, label: 'Premade Courses' },
        { path: '/org-catalog', icon: Building2, label: 'Organization Catalog' },
      ]
    },
    { 
      icon: Globe, 
      label: 'Public Library & Summits',
      subItems: [
        { path: '/public', icon: Globe, label: 'Browse Public Library' },
        { path: '/public?tab=summit', icon: Award, label: 'Summit Presentations' },
        { path: '/public?tab=keynote', icon: Sparkles, label: 'Keynotes & Workshops' },
      ]
    },
    { path: '/multi-subject', icon: Layers, label: 'Multi-Subject' },
    { path: '/exams', icon: ClipboardList, label: 'Exams' },
    { path: '/assignments', icon: FileText, label: 'Assignments' },
    { path: '/grades', icon: GraduationCap, label: 'Grading' },
    { path: '/attendance', icon: Calendar, label: 'Attendance' },
    { path: '/teacher-messaging', icon: MessageSquare, label: 'Messaging' },
    { path: '/course-analytics', icon: BarChart3, label: 'Course Analytics' },
    { path: '/fees', icon: CreditCard, label: 'Finance' },
    { path: '/credentials', icon: FileCheck, labelKey: 'credentials' },
    { divider: true, label: 'AI Tools' },
    { path: '/ai-training-engine', icon: Zap, label: 'AI Q&A Generator' },
    { path: '/lesson-planner', icon: Sparkles, label: 'AI Planner' },
    { path: '/syllabus-ingestion', icon: FileUp, label: 'Content Ingestion' },
    { path: '/assignment-generator', icon: FileCheck, label: 'Assignment Gen' },
    { path: '/question-analysis', icon: HelpCircle, label: 'Question Analysis' },
    { path: '/ai-mentor', icon: Brain, labelKey: 'aiMentor' },
    { path: '/student-risk', icon: AlertTriangle, labelKey: 'riskPrediction' },
    { path: '/learn-by-teaching', icon: Mic, label: 'Learn by Teaching' },
    { path: '/knowledge-graph', icon: Network, label: 'Knowledge Graph' },
    { divider: true, label: 'Smart Campus' },
    { path: '/virtual-classroom', icon: Video, labelKey: 'virtualClassroom' },
    { path: '/rfid-attendance', icon: Wifi, label: 'RFID Attendance' },
    { path: '/biometric-attendance', icon: Fingerprint, label: 'Biometric' },
    { path: '/share-content', icon: Share2, label: 'Share Content' },
  ],
  parent: [
    { path: '/dashboard', icon: LayoutDashboard, labelKey: 'dashboard' },
    { path: '/parent-portal', icon: Users, labelKey: 'myChildren' },
    { path: '/fees', icon: CreditCard, labelKey: 'fees' },
    { path: '/attendance', icon: Calendar, labelKey: 'attendance' },
  ],
  super_admin: [
    { path: '/super-admin', icon: Shield, label: 'Super Admin Console' },
    { path: '/super-admin/payment-management', icon: CreditCard, label: 'Payment Management' },
    { path: '/super-admin/publishing', icon: Newspaper, label: 'Publishing Config' },
    { divider: true, label: 'System' },
    { path: '/public', icon: Globe, label: 'Public Library' },
    { path: '/courses', icon: BookOpen, label: 'All Courses' },
    { path: '/premade-courses', icon: FolderOpen, label: 'Premade Docs' },
    { divider: true, label: 'Tools' },
    { path: '/ai-mentor', icon: Brain, labelKey: 'aiMentor' },
    { path: '/settings', icon: Settings, labelKey: 'settings' },
  ],
};

export const Sidebar = ({ isOpen, onClose, isMobile }) => {
  const { user, logout } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [expandedMenus, setExpandedMenus] = useState({});
  const items = navItems[user?.role] || navItems.student;

  const handleLogout = () => {
    logout();
    navigate('/login');
    if (onClose) onClose();
  };

  const handleNavClick = () => {
    if (isMobile && onClose) {
      onClose();
    }
  };

  const toggleSubmenu = (index) => {
    setExpandedMenus(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const shouldShowItem = (item) => {
    // Check if item is org-only and user has organization_id
    if (item.orgOnly) {
      return !!user?.organization_id;
    }
    return true;
  };

  const renderNavItem = (item, index) => {
    const Icon = item.icon;
    const label = item.labelKey ? t(item.labelKey) : item.label;
    
    // Handle nested subItems (My Courses menu)
    if (item.subItems) {
      const isExpanded = expandedMenus[index];
      const hasOrgCatalog = item.subItems.some(sub => sub.path === '/org-catalog');
      const visibleSubItems = item.subItems.filter(shouldShowItem);
      
      return (
        <div key={index}>
          <button
            onClick={() => toggleSubmenu(index)}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-zinc-400 hover:text-white hover:bg-white/5 transition-all"
            data-testid={`nav-submenu-${index}`}
          >
            <Icon className="w-5 h-5" />
            <span className="flex-1 text-left text-sm font-medium">{label}</span>
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </button>
          {isExpanded && (
            <div className="ml-4 pl-4 border-l border-white/10 space-y-1 mt-1">
              {visibleSubItems.map((subItem, subIndex) => {
                const SubIcon = subItem.icon;
                const isActive = window.location.pathname === subItem.path;
                return (
                  <NavLink
                    key={subIndex}
                    to={subItem.path}
                    onClick={handleNavClick}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-all ${
                      isActive
                        ? 'bg-blue-500/10 text-blue-400'
                        : 'text-zinc-500 hover:text-white hover:bg-white/5'
                    }`}
                    data-testid={`nav-link-${subItem.path.replace('/', '')}`}
                  >
                    <SubIcon className="w-4 h-4" />
                    <span className="text-sm">{subItem.label}</span>
                  </NavLink>
                );
              })}
            </div>
          )}
        </div>
      );
    }
    
    // Regular nav item
    return null; // Will be handled by existing logic
  };

  return (
    <aside className={`
      fixed left-0 top-0 h-screen w-64 bg-[#0d0d0f] border-r border-white/5 flex flex-col z-50
      transition-transform duration-300 ease-in-out
      ${isMobile ? (isOpen ? 'translate-x-0' : '-translate-x-full') : 'translate-x-0'}
    `}>
      {/* Logo */}
      <div className="p-6 border-b border-white/5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center">
              <GraduationCap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-lg tracking-tight">Cognify</h1>
              <p className="text-xs text-zinc-500">2026 Platform</p>
            </div>
          </div>
          {isMobile && (
            <button 
              onClick={onClose}
              className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-white/5 transition-colors"
              data-testid="close-sidebar-btn"
            >
              <X className="w-5 h-5" />
            </button>
          )}
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
          ) : item.subItems ? (
            <div key={`submenu-${index}`} className="space-y-1">
              <button
                onClick={() => toggleSubmenu(index)}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-zinc-400 hover:text-white hover:bg-white/5 transition-all duration-200"
                data-testid={`nav-${item.label.toLowerCase().replace(/\s/g, '-')}`}
              >
                <item.icon className="w-5 h-5" />
                <span className="flex-1">{item.label}</span>
                {expandedMenus[index] ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </button>
              {expandedMenus[index] && (
                <div className="ml-4 space-y-1">
                  {item.subItems.filter(shouldShowItem).map((subItem) => (
                    <NavLink
                      key={subItem.path}
                      to={subItem.path}
                      onClick={handleNavClick}
                      data-testid={`nav-${subItem.label.toLowerCase().replace(/\s/g, '-')}`}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 group ${
                          isActive
                            ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                            : 'text-zinc-400 hover:text-white hover:bg-white/5'
                        }`
                      }
                    >
                      <subItem.icon className="w-4 h-4" />
                      <span className="flex-1">{subItem.label}</span>
                    </NavLink>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={handleNavClick}
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
          onClick={handleNavClick}
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
