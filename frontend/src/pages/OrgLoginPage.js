import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Building2, Mail, Lock, Eye, EyeOff, ArrowRight, Loader2, Users, BookOpen, Award, UserPlus } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export default function OrgLoginPage() {
  const { orgSlug } = useParams();
  const [tab, setTab] = useState('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [role, setRole] = useState('student');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [orgData, setOrgData] = useState(null);
  const [loadingOrg, setLoadingOrg] = useState(true);
  const { login } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (orgSlug) loadOrganization();
  }, [orgSlug]);

  const loadOrganization = async () => {
    try {
      const { data } = await axios.get(`${API}/api/org/public/${orgSlug}`);
      setOrgData(data);
    } catch (error) {
      toast.error('Organization not found');
      navigate('/login');
    } finally {
      setLoadingOrg(false);
    }
  };

  const handleLogin = async (e) => {
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
      const msg = error.response?.data?.detail || error.message || 'Login failed';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (!email || !password || !fullName) {
      toast.error('Please fill in all fields');
      return;
    }
    if (password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/auth/org-register`, {
        email,
        password,
        full_name: fullName,
        role,
        org_slug: orgSlug
      });
      toast.success(data.message || 'Registration submitted! Awaiting admin approval.');
      setTab('login');
      setPassword('');
      setFullName('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
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
          <div className="flex items-center gap-4 mb-8">
            {orgData?.logo_url ? (
              <img src={orgData.logo_url} alt={orgData.name}
                className="w-16 h-16 rounded-2xl object-cover shadow-lg" />
            ) : (
              <div className="w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg"
                style={{ background: `linear-gradient(135deg, ${primaryColor}, ${secondaryColor})` }}>
                <Building2 className="w-8 h-8 text-white" />
              </div>
            )}
            <div>
              <h1 className="text-3xl font-bold">{orgData?.name || 'Organization'}</h1>
              <p className="text-zinc-500 text-sm">Learning Portal</p>
            </div>
          </div>
          
          {orgData?.description && (
            <p className="text-zinc-400 mb-8 leading-relaxed">{orgData.description}</p>
          )}

          <div className="grid grid-cols-3 gap-4 mb-8">
            {[
              { icon: Users, label: 'Staff & Students', value: orgData?.member_count || '100+' },
              { icon: BookOpen, label: 'Courses', value: orgData?.course_count || '50+' },
              { icon: Award, label: 'Certificates', value: orgData?.cert_count || '200+' },
            ].map((stat, i) => (
              <div key={i} className="glass-card p-4 text-center">
                <stat.icon className="w-5 h-5 mx-auto mb-2" style={{ color: primaryColor }} />
                <p className="text-lg font-bold">{stat.value}</p>
                <p className="text-xs text-zinc-500">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right side - Login/Register Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-[#09090B]">
        <div className="w-full max-w-md space-y-6">
          {/* Mobile org header */}
          <div className="lg:hidden flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center"
              style={{ background: `linear-gradient(135deg, ${primaryColor}, ${secondaryColor})` }}>
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold">{orgData?.name || 'Organization'}</h1>
              <p className="text-xs text-zinc-500">Learning Portal</p>
            </div>
          </div>

          {/* Tab Switcher */}
          <div className="flex rounded-xl bg-zinc-900 p-1 border border-white/5">
            <button
              onClick={() => setTab('login')}
              className={`flex-1 py-2.5 text-sm font-medium rounded-lg transition-all ${
                tab === 'login' ? 'bg-white/10 text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'
              }`}
              data-testid="org-tab-login"
            >
              Sign In
            </button>
            <button
              onClick={() => setTab('register')}
              className={`flex-1 py-2.5 text-sm font-medium rounded-lg transition-all ${
                tab === 'register' ? 'bg-white/10 text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-300'
              }`}
              data-testid="org-tab-register"
            >
              Register
            </button>
          </div>

          {/* Login Form */}
          {tab === 'login' && (
            <form onSubmit={handleLogin} className="space-y-4" data-testid="org-login-form">
              <div className="text-center mb-4">
                <h2 className="text-2xl font-bold">Welcome Back</h2>
                <p className="text-sm text-zinc-500 mt-1">
                  Sign in to {orgData?.name || 'your organization'}
                </p>
              </div>

              <div className="space-y-2">
                <Label>Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                    placeholder="your.email@organization.com"
                    className="pl-10 bg-zinc-800 border-white/10"
                    data-testid="org-login-email-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    value={password} onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password"
                    className="pl-10 pr-10 bg-zinc-800 border-white/10"
                    data-testid="org-login-password-input"
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300">
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <Button type="submit" disabled={loading} className="w-full"
                style={{ background: `linear-gradient(135deg, ${primaryColor}, ${secondaryColor})` }}
                data-testid="org-login-submit-btn"
              >
                {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <ArrowRight className="w-4 h-4 mr-2" />}
                Sign In
              </Button>

              <p className="text-center text-sm text-zinc-500">
                Don't have an account?{' '}
                <button type="button" onClick={() => setTab('register')} className="text-blue-400 hover:underline">
                  Register here
                </button>
              </p>
            </form>
          )}

          {/* Registration Form */}
          {tab === 'register' && (
            <form onSubmit={handleRegister} className="space-y-4" data-testid="org-register-form">
              <div className="text-center mb-4">
                <h2 className="text-2xl font-bold">Join {orgData?.name || 'Organization'}</h2>
                <p className="text-sm text-zinc-500 mt-1">
                  Create your account. Requires admin approval.
                </p>
              </div>

              <div className="space-y-2">
                <Label>Full Name</Label>
                <div className="relative">
                  <UserPlus className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    type="text" value={fullName} onChange={(e) => setFullName(e.target.value)}
                    placeholder="Enter your full name"
                    className="pl-10 bg-zinc-800 border-white/10"
                    data-testid="org-register-name-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                    placeholder="your.email@organization.com"
                    className="pl-10 bg-zinc-800 border-white/10"
                    data-testid="org-register-email-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                  <Input
                    type={showPassword ? 'text' : 'password'}
                    value={password} onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min 6 characters"
                    className="pl-10 pr-10 bg-zinc-800 border-white/10"
                    data-testid="org-register-password-input"
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300">
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Role</Label>
                <Select value={role} onValueChange={setRole}>
                  <SelectTrigger className="bg-zinc-800 border-white/10" data-testid="org-register-role-select">
                    <SelectValue placeholder="Select your role" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="student">Student / Participant</SelectItem>
                    <SelectItem value="teacher">Staff / Instructor</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Button type="submit" disabled={loading} className="w-full"
                style={{ background: `linear-gradient(135deg, ${primaryColor}, ${secondaryColor})` }}
                data-testid="org-register-submit-btn"
              >
                {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <UserPlus className="w-4 h-4 mr-2" />}
                Submit Registration
              </Button>

              <p className="text-center text-xs text-zinc-500">
                Your account will be reviewed by the organization admin before activation.
              </p>

              <p className="text-center text-sm text-zinc-500">
                Already have an account?{' '}
                <button type="button" onClick={() => setTab('login')} className="text-blue-400 hover:underline">
                  Sign in
                </button>
              </p>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
