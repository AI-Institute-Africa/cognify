import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Switch } from './ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { 
  Zap, 
  Brain, 
  Users, 
  Target, 
  Layers, 
  Globe, 
  Sparkles,
  GraduationCap,
  User,
  Building2,
  Shield,
  CheckCircle,
  DollarSign,
  ArrowRight
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

// AI Features Configuration - Based on requirements
const AI_FEATURES = [
  { 
    id: 'ktce', 
    name: 'KTCE (Knowledge Time Compression)', 
    description: 'Compress learning time with AI-optimized content delivery',
    icon: Zap,
    color: 'violet',
    extraFee: 9.99
  },
  { 
    id: 'outcome_based', 
    name: 'Outcome Based Learning', 
    description: 'Goal-oriented learning with measurable outcomes',
    icon: Target,
    color: 'emerald',
    extraFee: 7.99
  },
  { 
    id: 'adaptive', 
    name: 'Adaptive Learning', 
    description: 'Personalized learning paths based on student performance',
    icon: Brain,
    color: 'blue',
    extraFee: 12.99
  },
  { 
    id: 'avatar_tutor', 
    name: 'Avatar Tutor', 
    description: 'Virtual AI instructor for interactive lessons',
    icon: Users,
    color: 'amber',
    extraFee: 14.99
  },
  { 
    id: 'multidisciplinary', 
    name: 'Multi-disciplinary', 
    description: 'Cross-subject learning integration',
    icon: Layers,
    color: 'cyan',
    extraFee: 8.99
  },
  { 
    id: 'multilingual', 
    name: 'Multilingual Support', 
    description: 'Auto-translate content to multiple languages',
    icon: Globe,
    color: 'pink',
    extraFee: 5.99
  },
  { 
    id: 'ai_mentor', 
    name: 'AI Mentor', 
    description: 'Personal AI mentor for guidance and support',
    icon: Sparkles,
    color: 'orange',
    extraFee: 11.99
  }
];

// User Role Options
const USER_ROLES = [
  { id: 'student', label: 'Student', icon: GraduationCap, description: 'Learning and studying' },
  { id: 'teacher', label: 'Teacher', icon: User, description: 'Teaching and creating content' },
  { id: 'org_admin', label: 'Organization Admin', icon: Building2, description: 'Managing organization' },
  { id: 'org_staff', label: 'Organization Staff', icon: Shield, description: 'Supporting organization' }
];

export default function AIFeaturesGridModal({ 
  isOpen, 
  onClose, 
  onComplete,
  courseType = 'standard', // 'standard' or 'customized'
  initialFeatures = {},
  showRoleSelection = true
}) {
  const { user } = useAuth();
  const [selectedFeatures, setSelectedFeatures] = useState(initialFeatures);
  const [selectedRole, setSelectedRole] = useState(user?.role || 'student');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(showRoleSelection ? 1 : 2); // 1: Role, 2: Features

  useEffect(() => {
    if (isOpen) {
      // Load saved preferences if any
      loadSavedPreferences();
    }
  }, [isOpen]);

  const loadSavedPreferences = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/user/ai-preferences`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        if (data.preferences) {
          setSelectedFeatures(data.preferences.features || {});
          if (data.preferences.role) {
            setSelectedRole(data.preferences.role);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load preferences:', error);
    }
  };

  const toggleFeature = (featureId) => {
    setSelectedFeatures(prev => ({
      ...prev,
      [featureId]: !prev[featureId]
    }));
  };

  const calculateTotalFee = () => {
    return AI_FEATURES.reduce((total, feature) => {
      if (selectedFeatures[feature.id]) {
        return total + feature.extraFee;
      }
      return total;
    }, 0);
  };

  const handleContinue = async () => {
    if (step === 1) {
      setStep(2);
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('cognify_token');
      
      // Save preferences to backend
      await fetch(`${API}/api/user/ai-preferences`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          features: selectedFeatures,
          role: selectedRole,
          course_type: courseType,
          total_fee: calculateTotalFee()
        })
      });

      // Call completion callback
      if (onComplete) {
        onComplete({
          features: selectedFeatures,
          role: selectedRole,
          totalFee: calculateTotalFee()
        });
      }

      toast.success('AI features configured successfully!');
      onClose();
    } catch (error) {
      console.error('Failed to save preferences:', error);
      toast.error('Failed to save preferences');
    } finally {
      setLoading(false);
    }
  };

  const selectedCount = Object.values(selectedFeatures).filter(Boolean).length;
  const totalFee = calculateTotalFee();

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-zinc-900 border-white/10 max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-violet-400" />
            AI Features Selection
          </DialogTitle>
          <DialogDescription className="text-zinc-500">
            {step === 1 
              ? 'Select your role to personalize your experience'
              : 'Choose AI capabilities for your learning journey. Features attract additional fees.'}
          </DialogDescription>
        </DialogHeader>

        {/* Step 1: Role Selection */}
        {step === 1 && showRoleSelection && (
          <div className="space-y-4 mt-4">
            <p className="text-sm text-zinc-400">I am a:</p>
            <div className="grid grid-cols-2 gap-3">
              {USER_ROLES.map(role => {
                const Icon = role.icon;
                const isSelected = selectedRole === role.id;
                return (
                  <button
                    key={role.id}
                    onClick={() => setSelectedRole(role.id)}
                    className={`p-4 rounded-xl border transition-all text-left ${
                      isSelected
                        ? 'border-violet-500 bg-violet-500/10'
                        : 'border-white/10 hover:border-white/20'
                    }`}
                    data-testid={`role-${role.id}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${isSelected ? 'bg-violet-500/20' : 'bg-zinc-800'}`}>
                        <Icon className={`w-5 h-5 ${isSelected ? 'text-violet-400' : 'text-zinc-500'}`} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={`font-medium ${isSelected ? 'text-white' : 'text-zinc-400'}`}>
                            {role.label}
                          </span>
                          {isSelected && <CheckCircle className="w-4 h-4 text-violet-400" />}
                        </div>
                        <p className="text-xs text-zinc-500 mt-1">{role.description}</p>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>

            <Button
              onClick={handleContinue}
              className="w-full bg-violet-500 hover:bg-violet-600 mt-4"
              data-testid="continue-to-features-btn"
            >
              Continue to Features
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        )}

        {/* Step 2: AI Features Selection */}
        {step === 2 && (
          <div className="space-y-4 mt-4">
            {/* Course Type Badge */}
            <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50">
              <div className="flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-blue-400" />
                <span className="text-sm">
                  {courseType === 'standard' ? 'Standard Course' : 'Customized Subject'}
                </span>
              </div>
              <Badge className={courseType === 'standard' ? 'bg-blue-500/20 text-blue-400' : 'bg-violet-500/20 text-violet-400'}>
                {selectedRole}
              </Badge>
            </div>

            {/* Features Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {AI_FEATURES.map(feature => {
                const Icon = feature.icon;
                const isEnabled = selectedFeatures[feature.id];
                return (
                  <button
                    key={feature.id}
                    onClick={() => toggleFeature(feature.id)}
                    className={`p-4 rounded-xl border transition-all text-left ${
                      isEnabled
                        ? `border-${feature.color}-500/50 bg-${feature.color}-500/10`
                        : 'border-white/10 hover:border-white/20'
                    }`}
                    data-testid={`feature-${feature.id}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${isEnabled ? `bg-${feature.color}-500/20` : 'bg-zinc-800'}`}>
                        <Icon className={`w-5 h-5 ${isEnabled ? `text-${feature.color}-400` : 'text-zinc-500'}`} />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className={`font-medium text-sm ${isEnabled ? 'text-white' : 'text-zinc-400'}`}>
                            {feature.name}
                          </span>
                          <div className="flex items-center gap-2">
                            <Badge className={isEnabled ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-700 text-zinc-400'}>
                              +${feature.extraFee}
                            </Badge>
                            {isEnabled && (
                              <CheckCircle className={`w-4 h-4 text-${feature.color}-400`} />
                            )}
                          </div>
                        </div>
                        <p className="text-xs text-zinc-500 mt-1">{feature.description}</p>
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Summary */}
            <div className="p-4 rounded-xl bg-gradient-to-r from-violet-500/10 to-purple-500/10 border border-violet-500/20">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-400">Selected Features</p>
                  <p className="text-2xl font-bold text-white">{selectedCount} of {AI_FEATURES.length}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-zinc-400">Additional Fee</p>
                  <p className="text-2xl font-bold text-violet-400">
                    {totalFee > 0 ? `+$${totalFee.toFixed(2)}` : 'Free'}
                  </p>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              {showRoleSelection && (
                <Button
                  variant="outline"
                  onClick={() => setStep(1)}
                  className="border-white/10"
                >
                  Back
                </Button>
              )}
              <Button
                onClick={handleContinue}
                disabled={loading}
                className="flex-1 bg-violet-500 hover:bg-violet-600"
                data-testid="confirm-features-btn"
              >
                {loading ? 'Saving...' : 'Confirm Selection'}
                <CheckCircle className="w-4 h-4 ml-2" />
              </Button>
            </div>

            <p className="text-xs text-zinc-500 text-center">
              Selected features will apply to all courses and affect AI Mentor, Assignments, and Assessments.
            </p>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
