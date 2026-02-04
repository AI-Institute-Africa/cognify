import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { GraduationCap, Mail, Lock, User, Eye, EyeOff, ArrowRight, ArrowLeft, CheckCircle, RefreshCw, Linkedin } from 'lucide-react';
import { toast } from 'sonner';
import { registerWithVerification, verifyEmail, resendVerification, initiateGoogleLogin } from '../services/api';

export default function RegisterPage() {
  const [step, setStep] = useState('register'); // 'register' | 'verify'
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'student',
    linkedinUrl: ''
  });
  const [verificationCode, setVerificationCode] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    
    if (!formData.fullName || !formData.email || !formData.password) {
      toast.error('Please fill in all fields');
      return;
    }
    
    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    
    if (formData.password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    setLoading(true);
    try {
      await registerWithVerification(formData.email, formData.password, formData.fullName, formData.role, formData.linkedinUrl);
      toast.success('Verification code sent to your email!');
      setStep('verify');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e) => {
    e.preventDefault();
    
    if (!verificationCode || verificationCode.length !== 6) {
      toast.error('Please enter the 6-digit verification code');
      return;
    }
    
    setLoading(true);
    try {
      const result = await verifyEmail(formData.email, verificationCode);
      // Auto-login after verification
      if (result.access_token) {
        localStorage.setItem('token', result.access_token);
        localStorage.setItem('user', JSON.stringify(result.user));
        toast.success('Account verified successfully!');
        navigate('/dashboard');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setLoading(true);
    try {
      await resendVerification(formData.email);
      toast.success('New verification code sent!');
    } catch (error) {
      toast.error('Failed to resend code');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignUp = () => {
    initiateGoogleLogin('/dashboard');
  };

  return (
    <div className="min-h-screen flex">
      {/* Left side - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-[#09090B]">
        <div className="w-full max-w-md">
          <Link 
            to="/login" 
            className="inline-flex items-center gap-2 text-zinc-500 hover:text-white transition-colors mb-8"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to login
          </Link>
          
          {step === 'register' ? (
            <>
              <div className="mb-8">
                <h2 className="text-2xl font-bold">Create your account</h2>
                <p className="text-zinc-500 mt-2">Join EduOS and start your learning journey</p>
              </div>
              
              {/* Google Sign Up Button */}
              <Button
                type="button"
                onClick={handleGoogleSignUp}
                variant="outline"
                className="w-full h-12 mb-6 border-white/20 hover:bg-white/5 flex items-center justify-center gap-3"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Sign up with Google
              </Button>
              
              <div className="relative mb-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/10"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-[#09090B] text-zinc-500">or register with email</span>
                </div>
              </div>
              
              <form onSubmit={handleRegister} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="fullName" className="text-zinc-400">Full Name</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      id="fullName"
                      type="text"
                      placeholder="John Doe"
                      value={formData.fullName}
                      onChange={(e) => handleChange('fullName', e.target.value)}
                      data-testid="register-name-input"
                      className="pl-11 bg-zinc-900/50 border-white/10 h-12 focus:border-blue-500/50"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-zinc-400">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="you@school.edu"
                      value={formData.email}
                      onChange={(e) => handleChange('email', e.target.value)}
                      data-testid="register-email-input"
                      className="pl-11 bg-zinc-900/50 border-white/10 h-12 focus:border-blue-500/50"
                    />
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="role" className="text-zinc-400">I am a</Label>
                  <Select value={formData.role} onValueChange={(value) => handleChange('role', value)}>
                    <SelectTrigger 
                      data-testid="register-role-select"
                      className="h-12 bg-zinc-900/50 border-white/10 focus:border-blue-500/50"
                    >
                      <SelectValue placeholder="Select your role" />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-white/10">
                      <SelectItem value="student">Student</SelectItem>
                      <SelectItem value="teacher">Teacher</SelectItem>
                      <SelectItem value="parent">Parent</SelectItem>
                      <SelectItem value="org_admin">Organization Admin</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                {/* LinkedIn Profile - Optional */}
                <div className="space-y-2">
                  <Label htmlFor="linkedinUrl" className="text-zinc-400">
                    LinkedIn Profile <span className="text-zinc-600">(optional)</span>
                  </Label>
                  <div className="relative">
                    <Linkedin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      id="linkedinUrl"
                      type="url"
                      placeholder="https://linkedin.com/in/yourprofile"
                      value={formData.linkedinUrl}
                      onChange={(e) => handleChange('linkedinUrl', e.target.value)}
                      data-testid="register-linkedin-input"
                      className="pl-11 bg-zinc-900/50 border-white/10 h-12 focus:border-blue-500/50"
                    />
                  </div>
                  <p className="text-xs text-zinc-600">
                    Add your LinkedIn to get personalized learning recommendations from our AI Mentor
                  </p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="password" className="text-zinc-400">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={(e) => handleChange('password', e.target.value)}
                      data-testid="register-password-input"
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
                
                <div className="space-y-2">
                  <Label htmlFor="confirmPassword" className="text-zinc-400">Confirm Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      id="confirmPassword"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      value={formData.confirmPassword}
                      onChange={(e) => handleChange('confirmPassword', e.target.value)}
                      data-testid="register-confirm-password-input"
                      className="pl-11 bg-zinc-900/50 border-white/10 h-12 focus:border-blue-500/50"
                    />
                  </div>
                </div>
                
                <Button
                  type="submit"
                  data-testid="register-submit-btn"
                  disabled={loading}
                  className="w-full h-12 bg-blue-500 hover:bg-blue-600 text-white font-medium shadow-lg shadow-blue-500/20 transition-all duration-200 mt-4"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Creating account...
                    </span>
                  ) : (
                    <span className="flex items-center justify-center gap-2">
                      Create Account
                      <ArrowRight className="w-5 h-5" />
                    </span>
                  )}
                </Button>
              </form>
            </>
          ) : (
            // Verification Step
            <>
              <div className="mb-8 text-center">
                <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Mail className="w-8 h-8 text-blue-400" />
                </div>
                <h2 className="text-2xl font-bold">Verify your email</h2>
                <p className="text-zinc-500 mt-2">
                  We sent a 6-digit code to<br />
                  <span className="text-white">{formData.email}</span>
                </p>
              </div>
              
              <form onSubmit={handleVerify} className="space-y-5">
                <div className="space-y-2">
                  <Label htmlFor="code" className="text-zinc-400">Verification Code</Label>
                  <Input
                    id="code"
                    type="text"
                    placeholder="000000"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                    data-testid="verification-code-input"
                    className="text-center text-2xl tracking-widest bg-zinc-900/50 border-white/10 h-14 focus:border-blue-500/50"
                    maxLength={6}
                  />
                </div>
                
                <Button
                  type="submit"
                  data-testid="verify-submit-btn"
                  disabled={loading || verificationCode.length !== 6}
                  className="w-full h-12 bg-blue-500 hover:bg-blue-600 text-white font-medium shadow-lg shadow-blue-500/20 transition-all duration-200"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Verifying...
                    </span>
                  ) : (
                    <span className="flex items-center justify-center gap-2">
                      <CheckCircle className="w-5 h-5" />
                      Verify Email
                    </span>
                  )}
                </Button>
                
                <div className="text-center">
                  <button
                    type="button"
                    onClick={handleResend}
                    disabled={loading}
                    className="text-zinc-400 hover:text-white transition-colors inline-flex items-center gap-2"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Resend code
                  </button>
                </div>
                
                <button
                  type="button"
                  onClick={() => setStep('register')}
                  className="w-full text-center text-zinc-500 hover:text-white transition-colors"
                >
                  Use a different email
                </button>
              </form>
            </>
          )}
          
          <p className="text-center text-zinc-500 mt-8">
            Already have an account?{' '}
            <Link to="/login" className="text-blue-400 hover:text-blue-300 transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </div>
      
      {/* Right side - Visual */}
      <div className="hidden lg:flex w-1/2 bg-gradient-to-br from-blue-900/20 via-purple-900/20 to-blue-900/20 items-center justify-center p-12 relative overflow-hidden">
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/30 rounded-full filter blur-3xl animate-pulse" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/30 rounded-full filter blur-3xl animate-pulse delay-1000" />
        </div>
        <div className="relative z-10 text-center">
          <div className="w-24 h-24 bg-gradient-to-br from-blue-400 to-purple-500 rounded-2xl flex items-center justify-center mx-auto mb-8 shadow-2xl">
            <GraduationCap className="w-12 h-12 text-white" />
          </div>
          <h1 className="text-4xl font-bold mb-4">
            Welcome to <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">EduOS 2026</span>
          </h1>
          <p className="text-xl text-zinc-400 max-w-md">
            The most advanced AI-powered education platform. Learn smarter, not harder.
          </p>
          <div className="mt-12 grid grid-cols-3 gap-6">
            <div className="glass-card p-4 text-center">
              <div className="text-2xl font-bold text-blue-400">AI</div>
              <div className="text-sm text-zinc-500">Powered</div>
            </div>
            <div className="glass-card p-4 text-center">
              <div className="text-2xl font-bold text-purple-400">24/7</div>
              <div className="text-sm text-zinc-500">Learning</div>
            </div>
            <div className="glass-card p-4 text-center">
              <div className="text-2xl font-bold text-green-400">100+</div>
              <div className="text-sm text-zinc-500">Courses</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
