import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  CheckCircle,
  AlertCircle,
  Loader2,
  GraduationCap,
  BookOpen,
  Building2,
  Lock,
  User
} from 'lucide-react';
import { toast } from 'sonner';

export default function AcceptInvitePage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [inviteData, setInviteData] = useState(null);
  
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const token = searchParams.get('token');
  const API = process.env.REACT_APP_BACKEND_URL;
  
  useEffect(() => {
    if (!token) {
      setError('No invitation token provided');
      setLoading(false);
      return;
    }
    
    verifyToken();
  }, [token]);
  
  const verifyToken = async () => {
    try {
      const response = await fetch(`${API}/api/auth/verify-magic-link?token=${token}`);
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Invalid invitation');
      }
      
      setInviteData(data);
    } catch (err) {
      setError(err.message || 'Invalid or expired invitation');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    
    if (password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    if (!fullName.trim()) {
      toast.error('Please enter your full name');
      return;
    }
    
    setSubmitting(true);
    
    try {
      const response = await fetch(
        `${API}/api/auth/accept-magic-link?token=${token}&password=${encodeURIComponent(password)}&full_name=${encodeURIComponent(fullName)}`,
        { method: 'POST' }
      );
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to create account');
      }
      
      // Auto-login with returned token
      localStorage.setItem('token', data.access_token);
      
      toast.success('Account created successfully! Welcome to Cognify!');
      
      // Navigate to dashboard
      window.location.href = '/dashboard';
      
    } catch (err) {
      toast.error(err.message || 'Failed to create account');
    } finally {
      setSubmitting(false);
    }
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto" />
          <p className="text-zinc-400 mt-4">Verifying invitation...</p>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-4">
        <div className="max-w-md w-full">
          <div className="bg-zinc-900/50 border border-red-500/30 rounded-2xl p-8 text-center">
            <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-8 h-8 text-red-400" />
            </div>
            <h1 className="text-xl font-bold text-white mb-2">Invalid Invitation</h1>
            <p className="text-zinc-400 mb-6">{error}</p>
            <p className="text-zinc-500 text-sm mb-6">
              The invitation link may have expired or already been used.
              Please contact your organization administrator for a new invitation.
            </p>
            <Link to="/login">
              <Button className="bg-blue-500 hover:bg-blue-600">
                Go to Login
              </Button>
            </Link>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-4">
      <div className="max-w-lg w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <GraduationCap className="w-10 h-10 text-blue-500" />
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">
              Cognify
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">
            You're Invited!
          </h1>
          <p className="text-zinc-400">
            Set up your account to start learning
          </p>
        </div>
        
        {/* Invite Details Card */}
        <div className="bg-zinc-900/50 border border-white/10 rounded-2xl p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-emerald-500/20 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="text-sm text-zinc-400">Invitation verified</p>
              <p className="text-white font-medium">{inviteData?.email}</p>
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-blue-400" />
              <div>
                <p className="text-xs text-zinc-500">Organization</p>
                <p className="text-sm text-white">{inviteData?.org_name || 'Cognify'}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-violet-400" />
              <div>
                <p className="text-xs text-zinc-500">Course</p>
                <p className="text-sm text-white">{inviteData?.course_name || 'Course'}</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Setup Form */}
        <form onSubmit={handleSubmit} className="bg-zinc-900/50 border border-white/10 rounded-2xl p-6 space-y-5">
          <h2 className="text-lg font-semibold text-white mb-4">Create Your Account</h2>
          
          <div className="space-y-2">
            <Label htmlFor="fullName" className="text-zinc-300">Full Name</Label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <Input
                id="fullName"
                type="text"
                placeholder="Enter your full name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="pl-10 bg-zinc-800 border-white/10"
                required
                data-testid="invite-fullname-input"
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="password" className="text-zinc-300">Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <Input
                id="password"
                type="password"
                placeholder="Create a password (min 6 characters)"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-10 bg-zinc-800 border-white/10"
                required
                minLength={6}
                data-testid="invite-password-input"
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="confirmPassword" className="text-zinc-300">Confirm Password</Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Confirm your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="pl-10 bg-zinc-800 border-white/10"
                required
                data-testid="invite-confirm-password-input"
              />
            </div>
          </div>
          
          <Button
            type="submit"
            disabled={submitting}
            className="w-full bg-gradient-to-r from-blue-500 to-violet-500 hover:from-blue-600 hover:to-violet-600 text-white py-3"
            data-testid="invite-submit-btn"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Creating Account...
              </>
            ) : (
              <>
                <CheckCircle className="w-4 h-4 mr-2" />
                Create Account & Start Learning
              </>
            )}
          </Button>
          
          <p className="text-xs text-center text-zinc-500 mt-4">
            By creating an account, you agree to our Terms of Service and Privacy Policy.
          </p>
        </form>
        
        <p className="text-center text-zinc-500 text-sm mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-blue-400 hover:text-blue-300">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
