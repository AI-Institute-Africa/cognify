import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { GraduationCap, Mail, Lock, Eye, EyeOff, ArrowRight, Sparkles, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { processGoogleSession } from '../services/api';

// Google icon SVG
const GoogleIcon = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24">
    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
  </svg>
);

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const { login, loginWithToken } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Handle Google OAuth callback
  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    if (sessionId) {
      handleGoogleCallback(sessionId);
    }
  }, [searchParams]);

  const handleGoogleCallback = async (sessionId) => {
    setGoogleLoading(true);
    try {
      const result = await processGoogleSession(sessionId);
      if (result.access_token) {
        localStorage.setItem('eduos_token', result.access_token);
        localStorage.setItem('eduos_user', JSON.stringify(result.user));
        if (loginWithToken) {
          await loginWithToken(result.access_token);
        }
        toast.success(`Welcome, ${result.user.full_name || 'User'}!`);
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Google auth error:', error);
      toast.error('Google sign-in failed. Please try again.');
    } finally {
      setGoogleLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    // Redirect to Emergent Google OAuth
    const clientId = 'emergent-eduos-client';
    const redirectUri = encodeURIComponent(`${window.location.origin}/login`);
    const authUrl = `https://demobackend.emergentagent.com/auth/v1/env/oauth/google?client_id=${clientId}&redirect_uri=${redirectUri}`;
    window.location.href = authUrl;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }
    
    setLoading(true);
    try {
      await login(email, password);
      toast.success('Welcome back!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Hero */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-[#0d0d0f] items-center justify-center p-12">
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[100px]" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-violet-500/10 rounded-full blur-[100px]" />
        </div>
        
        <div className="relative z-10 max-w-lg">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <GraduationCap className="w-7 h-7 text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">EduOS</h1>
              <p className="text-zinc-500 text-sm">2026 Platform</p>
            </div>
          </div>
          
          <h2 className="text-4xl font-bold leading-tight mb-6">
            The Future of
            <span className="block text-gradient">Educational Intelligence</span>
          </h2>
          
          <p className="text-zinc-400 text-lg leading-relaxed mb-8">
            A unified platform managing the complete learner lifecycle - from admission to career success. 
            Powered by AI-driven insights and real-time analytics.
          </p>
          
          <div className="flex items-center gap-4">
            <div className="flex -space-x-3">
              <img src="https://images.pexels.com/photos/35590598/pexels-photo-35590598.jpeg" alt="User" className="w-10 h-10 rounded-full border-2 border-[#0d0d0f] object-cover" />
              <img src="https://images.pexels.com/photos/35584277/pexels-photo-35584277.jpeg" alt="User" className="w-10 h-10 rounded-full border-2 border-[#0d0d0f] object-cover" />
              <div className="w-10 h-10 rounded-full border-2 border-[#0d0d0f] bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-xs font-bold">
                5K+
              </div>
            </div>
            <p className="text-sm text-zinc-400">
              <span className="text-white font-semibold">5,000+</span> students already enrolled
            </p>
          </div>
        </div>
      </div>
      
      {/* Right side - Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-[#09090B]">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-8 justify-center">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center">
              <GraduationCap className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold">EduOS</h1>
          </div>
          
          <div className="mb-8">
            <h2 className="text-2xl font-bold">Welcome back</h2>
            <p className="text-zinc-500 mt-2">Enter your credentials to access your account</p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-zinc-400">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@school.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  data-testid="login-email-input"
                  className="pl-11 bg-zinc-900/50 border-white/10 h-12 focus:border-blue-500/50"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-zinc-400">Password</Label>
                <Link to="/forgot-password" className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
                  Forgot password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  data-testid="login-password-input"
                  className="pl-11 pr-11 bg-zinc-900/50 border-white/10 h-12 focus:border-blue-500/50"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>
            
            <Button
              type="submit"
              data-testid="login-submit-btn"
              disabled={loading}
              className="w-full h-12 bg-blue-500 hover:bg-blue-600 text-white font-medium shadow-lg shadow-blue-500/20 transition-all duration-200"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Signing in...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  Sign in
                  <ArrowRight className="w-5 h-5" />
                </span>
              )}
            </Button>
          </form>
          
          <div className="mt-8">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/10" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-[#09090B] text-zinc-500">New to EduOS?</span>
              </div>
            </div>
            
            <Link to="/register">
              <Button
                variant="outline"
                data-testid="go-to-register-btn"
                className="w-full mt-6 h-12 border-white/10 hover:bg-white/5 hover:border-white/20 transition-all"
              >
                <Sparkles className="w-4 h-4 mr-2 text-blue-400" />
                Create an account
              </Button>
            </Link>
          </div>
          
          <p className="text-center text-xs text-zinc-600 mt-8">
            By signing in, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>
    </div>
  );
}
