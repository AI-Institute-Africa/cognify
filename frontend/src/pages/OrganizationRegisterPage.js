import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { registerOrganization } from '../services/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { 
  Building2, 
  Mail, 
  Phone, 
  MapPin, 
  Globe, 
  User,
  Lock,
  ArrowRight,
  ArrowLeft,
  CheckCircle,
  FileText
} from 'lucide-react';
import { toast } from 'sonner';

const ORG_TYPES = [
  { value: 'school', label: 'School (K-12)' },
  { value: 'university', label: 'University / College' },
  { value: 'government', label: 'Government Agency' },
  { value: 'institution', label: 'Training Institution' },
  { value: 'corporate', label: 'Corporate / Enterprise' }
];

const STEPS = ['Organization Info', 'Admin Account', 'Review'];

export default function OrganizationRegisterPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    org_type: 'school',
    country: '',
    address: '',
    phone: '',
    email: '',
    website: '',
    registration_number: '',
    admin_name: '',
    admin_email: '',
    admin_password: '',
    confirm_password: ''
  });

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const validateStep = () => {
    if (step === 0) {
      if (!formData.name || !formData.country || !formData.address || !formData.phone || !formData.email) {
        toast.error('Please fill in all required fields');
        return false;
      }
    } else if (step === 1) {
      if (!formData.admin_name || !formData.admin_email || !formData.admin_password) {
        toast.error('Please fill in all admin details');
        return false;
      }
      if (formData.admin_password !== formData.confirm_password) {
        toast.error('Passwords do not match');
        return false;
      }
      if (formData.admin_password.length < 6) {
        toast.error('Password must be at least 6 characters');
        return false;
      }
    }
    return true;
  };

  const handleNext = () => {
    if (validateStep()) {
      setStep(prev => Math.min(prev + 1, STEPS.length - 1));
    }
  };

  const handleBack = () => {
    setStep(prev => Math.max(prev - 1, 0));
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const result = await registerOrganization(formData);
      localStorage.setItem('eduos_token', result.access_token);
      toast.success('Organization registered successfully!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090B] flex items-center justify-center p-8">
      <div className="w-full max-w-2xl">
        <Link 
          to="/login" 
          className="inline-flex items-center gap-2 text-zinc-500 hover:text-white transition-colors mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to login
        </Link>
        
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center mx-auto mb-4">
            <Building2 className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold">Register Your Organization</h1>
          <p className="text-zinc-500 mt-2">Join EduOS with your school, university, or institution</p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-4 mb-8">
          {STEPS.map((stepName, index) => (
            <div key={stepName} className="flex items-center">
              <div className={`flex items-center gap-2 ${index <= step ? 'text-blue-400' : 'text-zinc-600'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  index < step ? 'bg-blue-500 text-white' :
                  index === step ? 'bg-blue-500/20 text-blue-400 border border-blue-500' :
                  'bg-zinc-800 text-zinc-500'
                }`}>
                  {index < step ? <CheckCircle className="w-4 h-4" /> : index + 1}
                </div>
                <span className="text-sm hidden md:block">{stepName}</span>
              </div>
              {index < STEPS.length - 1 && (
                <div className={`w-12 h-0.5 mx-2 ${index < step ? 'bg-blue-500' : 'bg-zinc-800'}`} />
              )}
            </div>
          ))}
        </div>

        <div className="glass-card p-8">
          {/* Step 1: Organization Info */}
          {step === 0 && (
            <div className="space-y-5">
              <h2 className="text-xl font-semibold mb-6">Organization Details</h2>
              
              <div className="space-y-2">
                <Label>Organization Name *</Label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <Input
                    placeholder="Springfield University"
                    value={formData.name}
                    onChange={(e) => handleChange('name', e.target.value)}
                    data-testid="org-name-input"
                    className="pl-11 bg-zinc-900/50 border-white/10 h-12"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Organization Type *</Label>
                <Select value={formData.org_type} onValueChange={(value) => handleChange('org_type', value)}>
                  <SelectTrigger data-testid="org-type-select" className="h-12 bg-zinc-900/50 border-white/10">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-white/10">
                    {ORG_TYPES.map(type => (
                      <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Country *</Label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      placeholder="Zimbabwe"
                      value={formData.country}
                      onChange={(e) => handleChange('country', e.target.value)}
                      data-testid="org-country-input"
                      className="pl-11 bg-zinc-900/50 border-white/10 h-12"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Phone *</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      placeholder="+263 123 456 789"
                      value={formData.phone}
                      onChange={(e) => handleChange('phone', e.target.value)}
                      data-testid="org-phone-input"
                      className="pl-11 bg-zinc-900/50 border-white/10 h-12"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Address *</Label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-3 w-5 h-5 text-zinc-500" />
                  <Textarea
                    placeholder="123 Education Street, Harare"
                    value={formData.address}
                    onChange={(e) => handleChange('address', e.target.value)}
                    data-testid="org-address-input"
                    className="pl-11 bg-zinc-900/50 border-white/10 min-h-[80px]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Email *</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      type="email"
                      placeholder="info@university.edu"
                      value={formData.email}
                      onChange={(e) => handleChange('email', e.target.value)}
                      data-testid="org-email-input"
                      className="pl-11 bg-zinc-900/50 border-white/10 h-12"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Website</Label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                    <Input
                      placeholder="https://university.edu"
                      value={formData.website}
                      onChange={(e) => handleChange('website', e.target.value)}
                      data-testid="org-website-input"
                      className="pl-11 bg-zinc-900/50 border-white/10 h-12"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Registration Number</Label>
                <div className="relative">
                  <FileText className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <Input
                    placeholder="REG-12345"
                    value={formData.registration_number}
                    onChange={(e) => handleChange('registration_number', e.target.value)}
                    data-testid="org-reg-number-input"
                    className="pl-11 bg-zinc-900/50 border-white/10 h-12"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Admin Account */}
          {step === 1 && (
            <div className="space-y-5">
              <h2 className="text-xl font-semibold mb-6">Admin Account</h2>
              <p className="text-zinc-500 text-sm mb-4">Create the administrator account for your organization</p>
              
              <div className="space-y-2">
                <Label>Admin Full Name *</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <Input
                    placeholder="John Doe"
                    value={formData.admin_name}
                    onChange={(e) => handleChange('admin_name', e.target.value)}
                    data-testid="admin-name-input"
                    className="pl-11 bg-zinc-900/50 border-white/10 h-12"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Admin Email *</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <Input
                    type="email"
                    placeholder="admin@university.edu"
                    value={formData.admin_email}
                    onChange={(e) => handleChange('admin_email', e.target.value)}
                    data-testid="admin-email-input"
                    className="pl-11 bg-zinc-900/50 border-white/10 h-12"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Password *</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <Input
                    type="password"
                    placeholder="••••••••"
                    value={formData.admin_password}
                    onChange={(e) => handleChange('admin_password', e.target.value)}
                    data-testid="admin-password-input"
                    className="pl-11 bg-zinc-900/50 border-white/10 h-12"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Confirm Password *</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
                  <Input
                    type="password"
                    placeholder="••••••••"
                    value={formData.confirm_password}
                    onChange={(e) => handleChange('confirm_password', e.target.value)}
                    data-testid="admin-confirm-password-input"
                    className="pl-11 bg-zinc-900/50 border-white/10 h-12"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Review */}
          {step === 2 && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold mb-6">Review & Submit</h2>
              
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-zinc-800/50 border border-white/5">
                  <h3 className="font-medium text-blue-400 mb-3">Organization</h3>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-zinc-500">Name:</span>
                      <p className="font-medium">{formData.name}</p>
                    </div>
                    <div>
                      <span className="text-zinc-500">Type:</span>
                      <p className="font-medium">{ORG_TYPES.find(t => t.value === formData.org_type)?.label}</p>
                    </div>
                    <div>
                      <span className="text-zinc-500">Country:</span>
                      <p className="font-medium">{formData.country}</p>
                    </div>
                    <div>
                      <span className="text-zinc-500">Email:</span>
                      <p className="font-medium">{formData.email}</p>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-zinc-800/50 border border-white/5">
                  <h3 className="font-medium text-violet-400 mb-3">Administrator</h3>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-zinc-500">Name:</span>
                      <p className="font-medium">{formData.admin_name}</p>
                    </div>
                    <div>
                      <span className="text-zinc-500">Email:</span>
                      <p className="font-medium">{formData.admin_email}</p>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
                  <p className="text-sm text-amber-400">
                    After registration, your organization will be in pending status until verification documents are reviewed.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8 pt-6 border-t border-white/5">
            {step > 0 ? (
              <Button variant="ghost" onClick={handleBack}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
            ) : (
              <div />
            )}
            
            {step < STEPS.length - 1 ? (
              <Button onClick={handleNext} data-testid="next-step-btn" className="bg-blue-500 hover:bg-blue-600">
                Next
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            ) : (
              <Button 
                onClick={handleSubmit} 
                disabled={loading}
                data-testid="submit-org-btn"
                className="bg-blue-500 hover:bg-blue-600"
              >
                {loading ? 'Registering...' : 'Register Organization'}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
