import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LanguageProvider } from './context/LanguageContext';

// Phase 1 Pages
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import CoursesPage from './pages/CoursesPage';
import GradesPage from './pages/GradesPage';
import AttendancePage from './pages/AttendancePage';
import FeesPage from './pages/FeesPage';
import AchievementsPage from './pages/AchievementsPage';
import CareerGuidancePage from './pages/CareerGuidancePage';
import StudentsPage from './pages/StudentsPage';
import TeachersPage from './pages/TeachersPage';
import LessonPlannerPage from './pages/LessonPlannerPage';
import SettingsPage from './pages/SettingsPage';

// Phase 2 Pages
import AIMentorPage from './pages/AIMentorPage';
import KnowledgeGraphPage from './pages/KnowledgeGraphPage';
import OrganizationRegisterPage from './pages/OrganizationRegisterPage';
import SyllabusIngestionPage from './pages/SyllabusIngestionPage';
import LearnByTeachingPage from './pages/LearnByTeachingPage';
import LiveResearchPage from './pages/LiveResearchPage';
import LearningJourneyPage from './pages/LearningJourneyPage';
import ParentPortalPage from './pages/ParentPortalPage';
import RFIDAttendancePage from './pages/RFIDAttendancePage';
import CredentialsPage from './pages/CredentialsPage';

// Phase 3 Pages
import HomePage from './pages/HomePage';
import StudyGroupsPage from './pages/StudyGroupsPage';
import BiometricAttendancePage from './pages/BiometricAttendancePage';
import VirtualClassroomPage from './pages/VirtualClassroomPage';
import StudentRiskPage from './pages/StudentRiskPage';

// Phase 4 - Advanced AI Pages
import QuestionAnalysisPage from './pages/QuestionAnalysisPage';
import OutcomeLearningPage from './pages/OutcomeLearningPage';
import MultidisciplinaryPage from './pages/MultidisciplinaryPage';
import AssignmentGeneratorPage from './pages/AssignmentGeneratorPage';
import CourseViewPage from './pages/CourseViewPage';
import AvatarSettingsPage from './pages/AvatarSettingsPage';
import ExamPage from './pages/ExamPage';
import VRLearningPage from './pages/VRLearningPage';
import PaymentPage from './pages/PaymentPage';
import OrgAdminDashboardPage from './pages/OrgAdminDashboardPage';
import OrganizationSettingsPage from './pages/OrganizationSettingsPage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';
import StudentAssignmentsPage from './pages/StudentAssignmentsPage';
import KTCELearningPage from './pages/KTCELearningPage';
import AvatarTrialPage from './pages/AvatarTrialPage';
import CreateCustomCoursePage from './pages/CreateCustomCoursePage';
import AcceptInvitePage from './pages/AcceptInvitePage';
import BulkEnrollmentPage from './pages/BulkEnrollmentPage';
import TeacherMessagingPage from './pages/TeacherMessagingPage';
import OrgLoginPage from './pages/OrgLoginPage';
import OrganizationCatalogPage from './pages/OrganizationCatalogPage';
import CertificateViewPage, { CertificateVerifyPage } from './pages/CertificateViewPage';
import MultiSubjectPage from './pages/MultiSubjectPage';
import MultiSubjectLearningPage from './pages/MultiSubjectLearningPage';
import ShareContentPage from './pages/ShareContentPage';
import AITrainingEnginePage from './pages/AITrainingEnginePage';
import CertificateGalleryPage from './pages/CertificateGalleryPage';
import CourseManagePage from './pages/CourseManagePage';
import PremadeCoursesPage from './pages/PremadeCoursesPage';
import CourseAnalyticsDashboardPage from './pages/CourseAnalyticsDashboardPage';

import './App.css';

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  const { user, loading, isAuthenticated } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-zinc-500 mt-4">Loading...</p>
        </div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  if (allowedRoles.length > 0 && !allowedRoles.includes(user?.role)) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

// Public Route Component (redirect to dashboard if authenticated)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={
        <PublicRoute>
          <LoginPage />
        </PublicRoute>
      } />
      <Route path="/register" element={
        <PublicRoute>
          <RegisterPage />
        </PublicRoute>
      } />
      <Route path="/forgot-password" element={
        <PublicRoute>
          <ForgotPasswordPage />
        </PublicRoute>
      } />
      <Route path="/accept-invite" element={<AcceptInvitePage />} />
      <Route path="/org/:orgSlug/login" element={<OrgLoginPage />} />
      <Route path="/org/:orgSlug" element={<OrgLoginPage />} />
      
      {/* Protected Routes */}
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <DashboardPage />
        </ProtectedRoute>
      } />
      
      <Route path="/courses" element={
        <ProtectedRoute>
          <CoursesPage />
        </ProtectedRoute>
      } />
      
      <Route path="/course/:courseId" element={
        <ProtectedRoute>
          <CourseViewPage />
        </ProtectedRoute>
      } />
      
      <Route path="/payment/:courseId" element={
        <ProtectedRoute>
          <PaymentPage />
        </ProtectedRoute>
      } />
      
      <Route path="/grades" element={
        <ProtectedRoute>
          <GradesPage />
        </ProtectedRoute>
      } />
      
      <Route path="/attendance" element={
        <ProtectedRoute>
          <AttendancePage />
        </ProtectedRoute>
      } />
      
      <Route path="/fees" element={
        <ProtectedRoute>
          <FeesPage />
        </ProtectedRoute>
      } />
      
      <Route path="/achievements" element={
        <ProtectedRoute allowedRoles={['student', 'admin']}>
          <AchievementsPage />
        </ProtectedRoute>
      } />
      
      <Route path="/career" element={
        <ProtectedRoute allowedRoles={['student']}>
          <CareerGuidancePage />
        </ProtectedRoute>
      } />
      
      <Route path="/students" element={
        <ProtectedRoute allowedRoles={['admin', 'teacher', 'org_admin']}>
          <StudentsPage />
        </ProtectedRoute>
      } />
      
      <Route path="/lesson-planner" element={
        <ProtectedRoute allowedRoles={['teacher', 'admin', 'org_admin']}>
          <LessonPlannerPage />
        </ProtectedRoute>
      } />
      
      <Route path="/teachers" element={
        <ProtectedRoute allowedRoles={['admin', 'org_admin']}>
          <TeachersPage />
        </ProtectedRoute>
      } />
      
      <Route path="/settings" element={
        <ProtectedRoute>
          <SettingsPage />
        </ProtectedRoute>
      } />
      
      {/* Phase 2 Routes */}
      <Route path="/ai-mentor" element={
        <ProtectedRoute>
          <AIMentorPage />
        </ProtectedRoute>
      } />
      
      <Route path="/knowledge-graph" element={
        <ProtectedRoute>
          <KnowledgeGraphPage />
        </ProtectedRoute>
      } />
      
      <Route path="/syllabus-ingestion" element={
        <ProtectedRoute allowedRoles={['admin', 'teacher', 'org_admin']}>
          <SyllabusIngestionPage />
        </ProtectedRoute>
      } />
      
      <Route path="/learn-by-teaching" element={
        <ProtectedRoute>
          <LearnByTeachingPage />
        </ProtectedRoute>
      } />
      
      <Route path="/live-research" element={
        <ProtectedRoute>
          <LiveResearchPage />
        </ProtectedRoute>
      } />
      
      <Route path="/learning-journey" element={
        <ProtectedRoute>
          <LearningJourneyPage />
        </ProtectedRoute>
      } />
      
      <Route path="/ktce/:courseId" element={
        <ProtectedRoute>
          <KTCELearningPage />
        </ProtectedRoute>
      } />
      
      <Route path="/parent-portal" element={
        <ProtectedRoute allowedRoles={['parent']}>
          <ParentPortalPage />
        </ProtectedRoute>
      } />
      
      <Route path="/rfid-attendance" element={
        <ProtectedRoute allowedRoles={['admin', 'org_admin', 'teacher']}>
          <RFIDAttendancePage />
        </ProtectedRoute>
      } />
      
      <Route path="/credentials" element={
        <ProtectedRoute allowedRoles={['admin', 'org_admin', 'teacher']}>
          <CredentialsPage />
        </ProtectedRoute>
      } />
      
      {/* Phase 3 Routes */}
      <Route path="/study-groups" element={
        <ProtectedRoute>
          <StudyGroupsPage />
        </ProtectedRoute>
      } />
      
      <Route path="/biometric-attendance" element={
        <ProtectedRoute allowedRoles={['admin', 'org_admin', 'teacher']}>
          <BiometricAttendancePage />
        </ProtectedRoute>
      } />
      
      <Route path="/virtual-classroom" element={
        <ProtectedRoute>
          <VirtualClassroomPage />
        </ProtectedRoute>
      } />
      
      <Route path="/student-risk" element={
        <ProtectedRoute allowedRoles={['admin', 'org_admin', 'teacher']}>
          <StudentRiskPage />
        </ProtectedRoute>
      } />
      
      {/* Organization Registration (Public) */}
      <Route path="/register-organization" element={
        <PublicRoute>
          <OrganizationRegisterPage />
        </PublicRoute>
      } />
      
      {/* Phase 4 - Advanced AI Features */}
      <Route path="/question-analysis" element={
        <ProtectedRoute>
          <QuestionAnalysisPage />
        </ProtectedRoute>
      } />
      
      <Route path="/outcome-learning" element={
        <ProtectedRoute>
          <OutcomeLearningPage />
        </ProtectedRoute>
      } />
      
      <Route path="/create-custom-course" element={
        <ProtectedRoute>
          <CreateCustomCoursePage />
        </ProtectedRoute>
      } />
      
      <Route path="/multidisciplinary" element={
        <ProtectedRoute allowedRoles={['admin', 'teacher', 'org_admin']}>
          <MultidisciplinaryPage />
        </ProtectedRoute>
      } />
      
      <Route path="/assignment-generator" element={
        <ProtectedRoute allowedRoles={['admin', 'teacher', 'org_admin']}>
          <AssignmentGeneratorPage />
        </ProtectedRoute>
      } />
      
      <Route path="/avatar-settings" element={
        <ProtectedRoute>
          <AvatarSettingsPage />
        </ProtectedRoute>
      } />
      
      <Route path="/exams" element={
        <ProtectedRoute>
          <ExamPage />
        </ProtectedRoute>
      } />
      
      <Route path="/assignments" element={
        <ProtectedRoute>
          <StudentAssignmentsPage />
        </ProtectedRoute>
      } />
      
      <Route path="/vr-learning" element={
        <ProtectedRoute>
          <VRLearningPage />
        </ProtectedRoute>
      } />
      
      <Route path="/org-admin" element={
        <ProtectedRoute allowedRoles={['org_admin', 'admin']}>
          <OrgAdminDashboardPage />
        </ProtectedRoute>
      } />
      
      <Route path="/organization-settings" element={
        <ProtectedRoute allowedRoles={['org_admin', 'admin']}>
          <OrganizationSettingsPage />
        </ProtectedRoute>
      } />
      
      <Route path="/bulk-enrollment" element={
        <ProtectedRoute allowedRoles={['org_admin', 'admin', 'teacher']}>
          <BulkEnrollmentPage />
        </ProtectedRoute>
      } />
      
      <Route path="/teacher-messaging" element={
        <ProtectedRoute allowedRoles={['teacher', 'admin', 'org_admin']}>
          <TeacherMessagingPage />
        </ProtectedRoute>
      } />

      <Route path="/course-analytics" element={
        <ProtectedRoute allowedRoles={['teacher', 'admin', 'org_admin']}>
          <CourseAnalyticsDashboardPage />
        </ProtectedRoute>
      } />
      
      {/* Multi-Subject Learning */}
      <Route path="/multi-subject" element={
        <ProtectedRoute>
          <MultiSubjectPage />
        </ProtectedRoute>
      } />
      <Route path="/multi-subject/:pathId" element={
        <ProtectedRoute>
          <MultiSubjectLearningPage />
        </ProtectedRoute>
      } />
      
      {/* Share Content */}
      <Route path="/share-content" element={
        <ProtectedRoute>
          <ShareContentPage />
        </ProtectedRoute>
      } />
      
      {/* AI Training Intelligence Engine */}
      <Route path="/ai-training-engine" element={
        <ProtectedRoute>
          <AITrainingEnginePage />
        </ProtectedRoute>
      } />
      
      {/* Organization Catalog */}
      <Route path="/org-catalog" element={
        <ProtectedRoute>
          <OrganizationCatalogPage />
        </ProtectedRoute>
      } />
      
      {/* Certificate Routes */}
      <Route path="/certificate/:certificateId" element={
        <ProtectedRoute>
          <CertificateViewPage />
        </ProtectedRoute>
      } />
      
      {/* Certificate Gallery */}
      <Route path="/certificate-gallery" element={
        <ProtectedRoute>
          <CertificateGalleryPage />
        </ProtectedRoute>
      } />
      <Route path="/certificate-gallery/:userId" element={
        <ProtectedRoute>
          <CertificateGalleryPage />
        </ProtectedRoute>
      } />
      
      {/* Course Management */}
      <Route path="/course-manage/:courseId" element={
        <ProtectedRoute>
          <CourseManagePage />
        </ProtectedRoute>
      } />
      
      {/* Premade Courses */}
      <Route path="/premade-courses" element={
        <ProtectedRoute>
          <PremadeCoursesPage />
        </ProtectedRoute>
      } />
      
      {/* Public Certificate Verification */}
      <Route path="/verify-certificate/:verificationCode" element={<CertificateVerifyPage />} />
      
      {/* Avatar Trial (Public - No account needed) */}
      <Route path="/avatar-trial" element={<AvatarTrialPage />} />
      
      {/* Home Page (Public) */}
      <Route path="/" element={<HomePage />} />
      
      {/* 404 - Redirect to home */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <LanguageProvider>
        <AuthProvider>
          <AppRoutes />
          <Toaster 
            position="top-right" 
            toastOptions={{
              style: {
                background: '#18181B',
                border: '1px solid rgba(255,255,255,0.1)',
                color: '#FAFAFA',
              },
            }}
          />
        </AuthProvider>
      </LanguageProvider>
    </BrowserRouter>
  );
}

export default App;
