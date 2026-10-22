import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { GraduationCap, Mail, Lock, Eye, EyeOff, ArrowRight, Sparkles, Loader2, Phone, MessageSquare, Info, ExternalLink } from 'lucide-react';
import { toast } from 'sonner';
import { processGoogleSession, requestPhoneOtp, initiateGoogleLogin, getErrorMessage } from '../services/api';
import PhoneInputWithCountry from '../components/PhoneInputWithCountry';

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
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loginMethod, setLoginMethod] = useState('password'); // 'password' | 'otp'
  const [otpChannel, setOtpChannel] = useState('sms'); // 'sms' | 'whatsapp'
  const [otpCode, setOtpCode] = useState('');
  const [otpCooldown, setOtpCooldown] = useState(0);
  const [otpSending, setOtpSending] = useState(false);
  const [devOtpCode, setDevOtpCode] = useState('');
  const [whatsAppLink, setWhatsAppLink] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const { login, loginWithToken, loginWithPhoneAuth } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Handle Google OAuth callback if session_id is in URL
  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    if (sessionId) {
      setGoogleLoading(true);
      processGoogleSession(sessionId)
        .then((res) => {
          if (res?.token) {
            loginWithToken(res.token, res.user);
            toast.success('Successfully signed in with Google!');
            navigate('/dashboard');
          }
        })
        .catch((err) => {
          toast.error(getErrorMessage(err, 'Google sign-in failed'));
        })
        .finally(() => {
          setGoogleLoading(false);
        });
    }
  }, [searchParams, loginWithToken, navigate]);

  const handleGoogleSignIn = () => {
    initiateGoogleLogin('/dashboard');
  };

  useEffect(() => {
    let timer;
    if (otpCooldown > 0) {
      timer = setInterval(() => {
        setOtpCooldown((prev) => (prev > 0 ? prev - 1 : 0));
      }, 1000);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [otpCooldown]);

  const handleRequestOtp = async () => {
    if (!identifier || identifier.trim().length < 8) {
      toast.error('Please enter your mobile phone number first');
      return;
    }
    setOtpSending(true);
    try {
      const res = await requestPhoneOtp(identifier.trim(), otpChannel);
      toast.success(res.message || `OTP sent via ${otpChannel.toUpperCase()}!`);
      if (res.dev_simulator_code) {
        setDevOtpCode(res.dev_simulator_code);
        toast.info(`Sandbox Simulator: OTP code is ${res.dev_simulator_code}`, { duration: 10000 });
      }
      if (res.whatsapp_link) {
        setWhatsAppLink(res.whatsapp_link);
      }
      setOtpCooldown(60);
    } catch (error) {
      toast.error(getErrorMessage(error, 'Failed to send OTP code'));
    } finally {
      setOtpSending(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!identifier) {
      toast.error('Please enter your email or phone number');
      return;
    }

    setLoading(true);
    try {
      if (loginMethod === 'otp') {
        if (!otpCode || otpCode.length !== 6) {
          toast.error('Please enter the 6-digit OTP code');
          setLoading(false);
          return;
        }
        await loginWithPhoneAuth(identifier.trim(), null, otpCode.trim());
        toast.success('Welcome back!');
        navigate('/dashboard');
      } else {
        if (!password) {
          toast.error('Please enter your password');
          setLoading(false);
          return;
        }
        // Try phone/email login with password
        if (loginWithPhoneAuth && identifier.replace(/\D/g, '').length >= 8) {
          await loginWithPhoneAuth(identifier.trim(), password);
        } else {
          await login(identifier.trim(), password);
        }
        toast.success('Welcome back!');
        navigate('/dashboard');
      }
    } catch (error) {
      toast.error(getErrorMessage(error, 'Login failed'));
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
              <h1 className="text-3xl font-bold">Cognify</h1>
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
      <div className="w-full lg:w-1/2 flex items-center justify-center p-4 sm:p-8 bg-[#09090B]">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-3 mb-6 sm:mb-8 justify-center">
            <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-xl bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center">
              <GraduationCap className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
            </div>
            <h1 className="text-xl sm:text-2xl font-bold">Cognify</h1>
          </div>
          
          <div className="mb-6 sm:mb-8 text-center lg:text-left">
            <h2 className="text-xl sm:text-2xl font-bold">Welcome back</h2>
            <p className="text-zinc-500 mt-2 text-sm sm:text-base">Enter your credentials to access your account</p>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Google Sign In */}
            <Button
              type="button"
              onClick={handleGoogleSignIn}
              disabled={googleLoading}
              variant="outline"
              className="w-full h-12 border-white/10 hover:bg-white/5 hover:border-white/20 transition-all"
              data-testid="google-signin-btn"
            >
              {googleLoading ? (
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              ) : (
                <GoogleIcon />
              )}
              <span className="ml-2">Continue with Google</span>
            </Button>
            
            {/* Login Method Toggle */}
            <div className="grid grid-cols-2 p-1 bg-zinc-900 border border-white/10 rounded-xl mb-4">
              <button
                type="button"
                onClick={() => setLoginMethod('password')}
                className={`py-2 px-3 text-sm font-medium rounded-lg transition-all flex items-center justify-center gap-2 ${
                  loginMethod === 'password'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                <Lock className="w-4 h-4" />
                Password
              </button>
              <button
                type="button"
                onClick={() => setLoginMethod('otp')}
                className={`py-2 px-3 text-sm font-medium rounded-lg transition-all flex items-center justify-center gap-2 ${
                  loginMethod === 'otp'
                    ? 'bg-blue-600 text-white shadow-md'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                <MessageSquare className="w-4 h-4" />
                Phone OTP
              </button>
            </div>

            {loginMethod === 'otp' ? (
              <div className="space-y-3">
                <div className="space-y-2">
                  <Label htmlFor="identifier" className="text-zinc-400">
                    Mobile Phone Number
                  </Label>
                  <PhoneInputWithCountry
                    id="identifier"
                    value={identifier}
                    onChange={(full) => setIdentifier(full)}
                    required
                  />
                </div>

                <div className="flex items-center justify-between text-xs text-zinc-400">
                  <span>Send OTP via:</span>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setOtpChannel('sms')}
                      className={`px-2.5 py-1 rounded text-xs transition-colors ${
                        otpChannel === 'sms'
                          ? 'bg-blue-500/20 text-blue-400 border border-blue-500/40'
                          : 'text-zinc-400 hover:text-zinc-200'
                      }`}
                    >
                      SMS
                    </button>
                    <button
                      type="button"
                      onClick={() => setOtpChannel('whatsapp')}
                      className={`px-2.5 py-1 rounded text-xs transition-colors ${
                        otpChannel === 'whatsapp'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                          : 'text-zinc-400 hover:text-zinc-200'
                      }`}
                    >
                      WhatsApp
                    </button>
                  </div>
                </div>

                {/* Dev/Demo Simulator Helper Box — only shown when real delivery not confirmed */}
                {devOtpCode && (
                  <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-xs space-y-1.5 animate-in fade-in duration-300">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-amber-400 flex items-center gap-1.5">
                        <Info className="w-3.5 h-3.5" /> Delivery Fallback Notice
                      </span>
                      <span className="text-[10px] bg-amber-500/20 text-amber-300 px-1.5 py-0.5 rounded font-mono">
                        FALLBACK
                      </span>
                    </div>
                    <p className="text-zinc-400 text-[11px] leading-relaxed">
                      OTP could not be confirmed as delivered. Use this code to continue:
                    </p>
                    <div className="flex items-center justify-between pt-1">
                      <span className="text-base font-mono font-bold text-amber-400 tracking-widest">{devOtpCode}</span>
                      <div className="flex gap-2">
                        {whatsAppLink && (
                          <a
                            href={whatsAppLink}
                            target="_blank"
                            rel="noreferrer"
                            className="px-2 py-1 bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 rounded text-xs transition-colors flex items-center gap-1"
                          >
                            <ExternalLink className="w-3 h-3" /> WhatsApp
                          </a>
                        )}
                        <button
                          type="button"
                          onClick={() => {
                            setOtpCode(devOtpCode);
                            toast.success('Verification code auto-filled!');
                          }}
                          className="px-2 py-1 bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 rounded text-xs transition-colors font-medium"
                        >
                          Auto-fill Code
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <MessageSquare className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      id="otpCode"
                      type="text"
                      placeholder="6-digit OTP code"
                      maxLength={6}
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      data-testid="login-otp-input"
                      className="pl-11 bg-zinc-900/50 border-white/10 h-12 focus:border-blue-500/50 font-mono tracking-wider"
                    />
                  </div>
                  <Button
                    type="button"
                    onClick={handleRequestOtp}
                    disabled={otpSending || otpCooldown > 0}
                    className="h-12 px-4 bg-zinc-800 hover:bg-zinc-700 text-white font-medium border border-white/10"
                  >
                    {otpSending ? 'Sending...' : otpCooldown > 0 ? `${otpCooldown}s` : 'Send OTP'}
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <div className="space-y-2">
                  <Label htmlFor="identifier" className="text-zinc-400">
                    Email or Phone Number
                  </Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      id="identifier"
                      type="text"
                      placeholder="you@school.edu or +263 77 123 4567"
                      value={identifier}
                      onChange={(e) => setIdentifier(e.target.value)}
                      data-testid="login-identifier-input"
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
              </>
            )}
            
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
                <span className="px-4 bg-[#09090B] text-zinc-500">New to Cognify?</span>
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
