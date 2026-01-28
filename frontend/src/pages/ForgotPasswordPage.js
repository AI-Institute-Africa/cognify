import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { GraduationCap, Mail, ArrowLeft, Key, Check, Loader2, Lock } from 'lucide-react';
import { toast } from 'sonner';
import { forgotPasswordV2, resetPasswordV2 } from '../services/api';

export default function ForgotPasswordPage() {
  const [step, setStep] = useState(1); // 1: email, 2: code + new password
  const [email, setEmail] = useState('');
  const [resetCode, setResetCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSendCode = async (e) => {
    e.preventDefault();
    if (!email) {
      toast.error('Please enter your email');
      return;
    }
    
    setLoading(true);
    try {
      await forgotPasswordV2(email);
      toast.success('If this email exists, a reset code has been sent!');
      setStep(2);
    } catch (error) {
      toast.error('Failed to send reset code');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    
    if (!resetCode || resetCode.length !== 6) {
      toast.error('Please enter the 6-digit reset code');
      return;
    }
    
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    
    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    setLoading(true);
    try {
      await resetPasswordV2(email, resetCode, newPassword);
      toast.success('Password reset successfully!');
      setStep(3);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#09090B] p-8">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center">
            <GraduationCap className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold">EduOS</h1>
        </div>
        
        {/* Step 1: Enter Email */}
        {step === 1 && (
          <div className="glass-card p-8">
            <Link to="/login" className="flex items-center gap-2 text-zinc-500 hover:text-white mb-6 transition-colors">
              <ArrowLeft className="w-4 h-4" />
              Back to login
            </Link>
            
            <h2 className="text-2xl font-bold mb-2">Forgot Password</h2>
            <p className="text-zinc-500 mb-6">Enter your email and we&apos;ll send you a reset code</p>
            
            <form onSubmit={handleSendCode} className="space-y-6">
              <div className="space-y-2">
                <Label>Email Address</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <Input
                    type="email"
                    placeholder="you@school.edu"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-11 bg-zinc-900/50 border-white/10 h-12"
                    data-testid="forgot-email-input"
                  />
                </div>
              </div>
              
              <Button
                type="submit"
                disabled={loading}
                className="w-full h-12 bg-blue-500 hover:bg-blue-600"
                data-testid="send-code-btn"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  'Send Reset Code'
                )}
              </Button>
            </form>
          </div>
        )}
        
        {/* Step 2: Enter Code & New Password */}
        {step === 2 && (
          <div className="glass-card p-8">
            <button 
              onClick={() => setStep(1)} 
              className="flex items-center gap-2 text-zinc-500 hover:text-white mb-6 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Change email
            </button>
            
            <h2 className="text-2xl font-bold mb-2">Reset Password</h2>
            <p className="text-zinc-500 mb-6">Enter the code sent to {email}</p>
            
            {sentCode && (
              <div className="p-3 mb-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <p className="text-sm text-amber-400">
                  <strong>Demo Mode:</strong> Your reset code is <code className="bg-amber-500/20 px-2 py-1 rounded">{sentCode}</code>
                </p>
              </div>
            )}
            
            <form onSubmit={handleResetPassword} className="space-y-4">
              <div className="space-y-2">
                <Label>Reset Code</Label>
                <div className="relative">
                  <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <Input
                    type="text"
                    placeholder="Enter code"
                    value={resetCode}
                    onChange={(e) => setResetCode(e.target.value.toUpperCase())}
                    className="pl-11 bg-zinc-900/50 border-white/10 h-12 font-mono tracking-wider"
                    data-testid="reset-code-input"
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label>New Password</Label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="bg-zinc-900/50 border-white/10 h-12"
                  data-testid="new-password-input"
                />
              </div>
              
              <div className="space-y-2">
                <Label>Confirm New Password</Label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="bg-zinc-900/50 border-white/10 h-12"
                />
              </div>
              
              <Button
                type="submit"
                disabled={loading}
                className="w-full h-12 bg-blue-500 hover:bg-blue-600"
                data-testid="reset-password-btn"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  'Reset Password'
                )}
              </Button>
            </form>
          </div>
        )}
        
        {/* Step 3: Success */}
        {step === 3 && (
          <div className="glass-card p-8 text-center">
            <div className="w-16 h-16 rounded-full bg-emerald-500/20 flex items-center justify-center mx-auto mb-6">
              <Check className="w-8 h-8 text-emerald-400" />
            </div>
            
            <h2 className="text-2xl font-bold mb-2">Password Reset!</h2>
            <p className="text-zinc-500 mb-6">Your password has been reset successfully</p>
            
            <Link to="/login">
              <Button className="w-full h-12 bg-blue-500 hover:bg-blue-600">
                Sign In with New Password
              </Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
