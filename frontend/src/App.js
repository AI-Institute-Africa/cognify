import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './context/AuthContext';

// Pages
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
import LessonPlannerPage from './pages/LessonPlannerPage';

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
        <ProtectedRoute allowedRoles={['admin', 'teacher']}>
          <StudentsPage />
        </ProtectedRoute>
      } />
      
      <Route path="/lesson-planner" element={
        <ProtectedRoute allowedRoles={['teacher', 'admin']}>
          <LessonPlannerPage />
        </ProtectedRoute>
      } />
      
      {/* Redirect root to login or dashboard */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      
      {/* 404 - Redirect to dashboard */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
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
    </BrowserRouter>
  );
}

export default App;
