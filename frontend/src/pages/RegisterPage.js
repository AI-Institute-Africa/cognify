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
import { GraduationCap, Mail, Lock, User, Eye, EyeOff, ArrowRight, ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'student'
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e) => {
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
      await register(formData.email, formData.password, formData.fullName, formData.role);
      toast.success('Account created successfully!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
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
          
          <div className="mb-8">
            <h2 className="text-2xl font-bold">Create your account</h2>
            <p className="text-zinc-500 mt-2">Join EduOS and start your learning journey</p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-5">
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
                </SelectContent>
              </Select>
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
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Creating account...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  Create account
                  <ArrowRight className="w-5 h-5" />
                </span>
              )}
            </Button>
          </form>
          
          <p className="text-center text-xs text-zinc-600 mt-8">
            By creating an account, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>
      
      {/* Right side - Hero */}
      <div className="hidden lg:flex lg:w-1/2 relative bg-[#0d0d0f] items-center justify-center p-12">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-[100px]" />
          <div className="absolute bottom-1/3 left-1/4 w-96 h-96 bg-violet-500/10 rounded-full blur-[100px]" />
        </div>
        
        <div className="relative z-10 max-w-lg text-center">
          <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center mx-auto mb-8 shadow-2xl shadow-blue-500/20">
            <GraduationCap className="w-10 h-10 text-white" />
          </div>
          
          <h2 className="text-4xl font-bold mb-6">
            Start Your Journey
          </h2>
          
          <p className="text-zinc-400 text-lg leading-relaxed">
            Join thousands of students, teachers, and parents who are already using EduOS to transform their educational experience.
          </p>
          
          <div className="grid grid-cols-3 gap-6 mt-12">
            <div className="glass-card p-4">
              <h4 className="text-2xl font-bold text-blue-400">5K+</h4>
              <p className="text-xs text-zinc-500 mt-1">Students</p>
            </div>
            <div className="glass-card p-4">
              <h4 className="text-2xl font-bold text-violet-400">200+</h4>
              <p className="text-xs text-zinc-500 mt-1">Courses</p>
            </div>
            <div className="glass-card p-4">
              <h4 className="text-2xl font-bold text-emerald-400">98%</h4>
              <p className="text-xs text-zinc-500 mt-1">Success Rate</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
