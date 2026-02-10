import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Building2, Mail, Lock, Eye, EyeOff, ArrowRight, Loader2, Users, BookOpen, Award } from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

export default function OrgLoginPage() {
  const { orgSlug } = useParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [orgData, setOrgData] = useState(null);
  const [loadingOrg, setLoadingOrg] = useState(true);
  const { login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (orgSlug) {
      loadOrganization();
    }
  }, [orgSlug]);

  const loadOrganization = async () => {
    try {
      const response = await fetch(`${API}/api/org/public/${orgSlug}`);
      if (response.ok) {
        const data = await response.json();
        setOrgData(data);
      } else {
        toast.error('Organization not found');
        navigate('/login');
      }
    } catch (error) {
      console.error('Failed to load organization:', error);
      navigate('/login');
    } finally {
      setLoadingOrg(false);
    }
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
      toast.success(`Welcome to ${orgData?.name || 'the organization'}!`);
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  if (loadingOrg) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  // Get organization branding colors
  const primaryColor = orgData?.branding?.primary_color || '#3B82F6';
  const secondaryColor = orgData?.branding?.secondary_color || '#8B5CF6';

  return (
    <div className="min-h-screen flex">
      {/* Left side - Organization Hero */}
      <div 
        className="hidden lg:flex lg:w-1/2 relative items-center justify-center p-12"
        style={{
          background: `linear-gradient(135deg, ${primaryColor}15, ${secondaryColor}15)`,
          backgroundColor: '#0d0d0f'
        }}
      >
        {/* Background decoration */}
        <div className="absolute inset-0 overflow-hidden">
          <div 
            className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full blur-[100px]"
            style={{ backgroundColor: `${primaryColor}20` }}
          />
          <div 
            className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full blur-[100px]"
            style={{ backgroundColor: `${secondaryColor}20` }}
          />
        </div>
        
        <div className="relative z-10 max-w-lg">
          {/* Organization Logo/Name */}
          <div className="flex items-center gap-4 mb-8">
            {orgData?.logo_url ? (
              <img 
                src={orgData.logo_url} 
                alt={orgData.name}
                className="w-16 h-16 rounded-2xl object-cover shadow-lg"
              />
            ) : (
              <div 
                className="w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg"
                style={{ background: `linear-gradient(135deg, ${primaryColor}, ${secondaryColor})` }}
              >
                <Building2 className="w-8 h-8 text-white" />
              </div>
            )}
            <div>
              <h1 className="text-3xl font-bold">{orgData?.name || 'Organization'}</h1>
              <p className="text-zinc-500 text-sm">Learning Portal</p>
            </div>
          </div>
          
          <h2 className="text-4xl font-bold leading-tight mb-6">
            Welcome to
            <span 
              className="block"
              style={{ color: primaryColor }}
            >
              {orgData?.name || 'Our Learning Platform'}
            </span>
          </h2>
          
          <p className="text-zinc-400 text-lg leading-relaxed mb-8">
            {orgData?.description || 'Access your courses, track your progress, and achieve your learning goals with our comprehensive platform.'}
          </p>
          
          {/* Organization Stats */}
          <div className="grid grid-cols-3 gap-4">
            <div className="glass-card p-4 text-center">
              <Users className="w-6 h-6 mx-auto mb-2" style={{ color: primaryColor }} />
              <p className="text-2xl font-bold">{orgData?.stats?.students || '500+'}</p>
              <p className="text-xs text-zinc-500">Students</p>
            </div>
            <div className="glass-card p-4 text-center">
              <BookOpen className="w-6 h-6 mx-auto mb-2" style={{ color: primaryColor }} />
              <p className="text-2xl font-bold">{orgData?.stats?.courses || '50+'}</p>
              <p className="text-xs text-zinc-500">Courses</p>
            </div>
            <div className="glass-card p-4 text-center">
              <Award className="w-6 h-6 mx-auto mb-2" style={{ color: primaryColor }} />
              <p className="text-2xl font-bold">{orgData?.stats?.certificates || '200+'}</p>
              <p className="text-xs text-zinc-500">Certificates</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Right side - Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-4 sm:p-8 bg-[#09090B]">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-6 sm:mb-8 justify-center">
            {orgData?.logo_url ? (
              <img 
                src={orgData.logo_url} 
                alt={orgData.name}
                className="w-12 h-12 rounded-xl object-cover"
              />
            ) : (
              <div 
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{ background: `linear-gradient(135deg, ${primaryColor}, ${secondaryColor})` }}
              >
                <Building2 className="w-6 h-6 text-white" />
              </div>
            )}
            <h1 className="text-xl sm:text-2xl font-bold">{orgData?.name || 'Organization'}</h1>
          </div>
          
          <div className="mb-6 sm:mb-8 text-center lg:text-left">
            <h2 className="text-xl sm:text-2xl font-bold">Sign in to your account</h2>
            <p className="text-zinc-500 mt-2 text-sm sm:text-base">
              Enter your credentials to access {orgData?.name || 'the organization'}'s learning portal
            </p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-zinc-400">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                <Input
                  id="email"
                  type="email"
                  placeholder={`you@${orgData?.domain || 'organization.edu'}`}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  data-testid="org-login-email-input"
                  className="pl-11 bg-zinc-900/50 border-white/10 h-12 focus:border-blue-500/50"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-zinc-400">Password</Label>
                <Link to="/forgot-password" className="text-sm hover:underline" style={{ color: primaryColor }}>
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
                  data-testid="org-login-password-input"
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
              data-testid="org-login-submit-btn"
              disabled={loading}
              className="w-full h-12 text-white font-medium shadow-lg transition-all duration-200"
              style={{ 
                backgroundColor: primaryColor,
                boxShadow: `0 4px 14px ${primaryColor}40`
              }}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin" />
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
          
          <div className="mt-8 text-center">
            <p className="text-zinc-500 text-sm">
              Not a member of {orgData?.name || 'this organization'}?
            </p>
            <Link 
              to="/login" 
              className="text-sm mt-2 inline-block hover:underline"
              style={{ color: primaryColor }}
            >
              Sign in with a different account
            </Link>
          </div>
          
          <p className="text-center text-xs text-zinc-600 mt-8">
            Powered by <span className="text-zinc-400">Cognify</span> • {new Date().getFullYear()}
          </p>
        </div>
      </div>
    </div>
  );
}
