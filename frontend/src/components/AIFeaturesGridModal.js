import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Checkbox } from './ui/checkbox';
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
  CheckCircle,
  DollarSign,
  Monitor
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

// AI Features Configuration
// Standard Course Features: Multi Modal, Multi-Language, Avatar, AI Mentor
// Customized Course Features: ALL features
const AI_FEATURES = [
  { 
    id: 'multimodal', 
    name: 'Multi-Modal Learning', 
    description: 'Learn through text, video, audio, slides, and interactive content',
    icon: Monitor,
    color: 'blue',
    extraFee: 0,
    standardAllowed: true,
    customizedAllowed: true
  },
  { 
    id: 'multilingual', 
    name: 'Multilingual Support', 
    description: 'Auto-translate content to multiple languages',
    icon: Globe,
    color: 'pink',
    extraFee: 5.99,
    standardAllowed: true,
    customizedAllowed: true
  },
  { 
    id: 'avatar_tutor', 
    name: 'Avatar Tutor', 
    description: 'Virtual AI instructor for interactive lessons',
    icon: Users,
    color: 'amber',
    extraFee: 14.99,
    standardAllowed: true,
    customizedAllowed: true
  },
  { 
    id: 'ai_mentor', 
    name: 'AI Mentor', 
    description: 'Personal AI mentor for guidance and support',
    icon: Sparkles,
    color: 'orange',
    extraFee: 11.99,
    standardAllowed: true,
    customizedAllowed: true
  },
  { 
    id: 'ktce', 
    name: 'KTCE (Knowledge Time Compression)', 
    description: 'Compress learning time with AI-optimized content delivery',
    icon: Zap,
    color: 'violet',
    extraFee: 9.99,
    standardAllowed: false,
    customizedAllowed: true
  },
  { 
    id: 'outcome_based', 
    name: 'Outcome Based Learning', 
    description: 'Goal-oriented learning with measurable outcomes',
    icon: Target,
    color: 'emerald',
    extraFee: 7.99,
    standardAllowed: false,
    customizedAllowed: true
  },
  { 
    id: 'adaptive', 
    name: 'Adaptive Learning', 
    description: 'Personalized learning paths based on student performance',
    icon: Brain,
    color: 'cyan',
    extraFee: 12.99,
    standardAllowed: false,
    customizedAllowed: true
  },
  { 
    id: 'multidisciplinary', 
    name: 'Multi-disciplinary', 
    description: 'Cross-subject learning integration',
    icon: Layers,
    color: 'teal',
    extraFee: 8.99,
    standardAllowed: false,
    customizedAllowed: true
  }
];

export default function AIFeaturesGridModal({ 
  isOpen, 
  onClose, 
  onComplete,
  courseType = 'standard', // 'standard' or 'customized'
  initialFeatures = {}
}) {
  const { user } = useAuth();
  const [selectedFeatures, setSelectedFeatures] = useState(initialFeatures);
  const [loading, setLoading] = useState(false);

  // Filter features based on course type
  const availableFeatures = AI_FEATURES.filter(f => 
    courseType === 'customized' ? f.customizedAllowed : f.standardAllowed
  );

  useEffect(() => {
    if (isOpen) {
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
        }
      }
    } catch (error) {
      console.error('Failed to load preferences:', error);
    }
  };

  const toggleFeature = (featureId) => {
    const feature = AI_FEATURES.find(f => f.id === featureId);
    // Check if feature is allowed for this course type
    if (courseType === 'standard' && !feature?.standardAllowed) {
      toast.error('This feature is only available for Customized Courses');
      return;
    }
    
    setSelectedFeatures(prev => ({
      ...prev,
      [featureId]: !prev[featureId]
    }));
  };

  const calculateTotalFee = () => {
    return availableFeatures.reduce((total, feature) => {
      if (selectedFeatures[feature.id]) {
        return total + feature.extraFee;
      }
      return total;
    }, 0);
  };

  const handleConfirm = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('cognify_token');
      
      await fetch(`${API}/api/user/ai-preferences`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          features: selectedFeatures,
          role: user?.role,
          course_type: courseType,
          total_fee: calculateTotalFee()
        })
      });

      if (onComplete) {
        onComplete({
          features: selectedFeatures,
          role: user?.role,
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
            AI Features Selection Canvas
          </DialogTitle>
          <DialogDescription className="text-zinc-500">
            Select the AI capabilities you want for your {courseType === 'standard' ? 'Standard' : 'Customized'} Course. 
            Tick the checkbox to enable each feature.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* Course Type Badge */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50 border border-white/5">
            <div className="flex items-center gap-2">
              <GraduationCap className="w-5 h-5 text-blue-400" />
              <span className="text-sm font-medium">
                {courseType === 'standard' ? 'Standard Course' : 'Customized Course'}
              </span>
            </div>
            <Badge className={courseType === 'standard' ? 'bg-blue-500/20 text-blue-400' : 'bg-violet-500/20 text-violet-400'}>
              {availableFeatures.length} Features Available
            </Badge>
          </div>

          {/* Features Canvas - Checkbox Grid */}
          <div className="space-y-3">
            <p className="text-sm text-zinc-400 font-medium">Tick the features you want to enable:</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {availableFeatures.map(feature => {
                const Icon = feature.icon;
                const isEnabled = selectedFeatures[feature.id];
                
                return (
                  <div
                    key={feature.id}
                    className={`p-4 rounded-xl border transition-all ${
                      isEnabled
                        ? 'border-violet-500/50 bg-violet-500/5'
                        : 'border-white/10 hover:border-white/20'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      {/* Checkbox */}
                      <div className="pt-0.5">
                        <Checkbox
                          id={`feature-${feature.id}`}
                          checked={isEnabled}
                          onCheckedChange={() => toggleFeature(feature.id)}
                          className="border-white/30 data-[state=checked]:bg-violet-500 data-[state=checked]:border-violet-500"
                          data-testid={`checkbox-${feature.id}`}
                        />
                      </div>
                      
                      {/* Feature Icon */}
                      <div className={`p-2 rounded-lg ${isEnabled ? 'bg-violet-500/20' : 'bg-zinc-800'}`}>
                        <Icon className={`w-5 h-5 ${isEnabled ? 'text-violet-400' : 'text-zinc-500'}`} />
                      </div>
                      
                      {/* Feature Info */}
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <label 
                            htmlFor={`feature-${feature.id}`}
                            className={`font-medium text-sm cursor-pointer ${isEnabled ? 'text-white' : 'text-zinc-400'}`}
                          >
                            {feature.name}
                          </label>
                          <Badge className={isEnabled ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-700 text-zinc-400'}>
                            {feature.extraFee === 0 ? 'Free' : `+$${feature.extraFee}`}
                          </Badge>
                        </div>
                        <p className="text-xs text-zinc-500 mt-1">{feature.description}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Customized Course Note */}
          {courseType === 'standard' && (
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
              <p className="text-sm text-amber-400">
                <strong>Note:</strong> Additional AI features like KTCE, Adaptive Learning, and Outcome Based Learning 
                are available when creating a Customized Course.
              </p>
            </div>
          )}

          {/* Summary */}
          <div className="p-4 rounded-xl bg-gradient-to-r from-violet-500/10 to-purple-500/10 border border-violet-500/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-400">Selected Features</p>
                <p className="text-2xl font-bold text-white">{selectedCount} of {availableFeatures.length}</p>
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
          <Button
            onClick={handleConfirm}
            disabled={loading}
            className="w-full bg-violet-500 hover:bg-violet-600"
            data-testid="confirm-features-btn"
          >
            {loading ? 'Saving...' : 'Confirm Selection'}
            <CheckCircle className="w-4 h-4 ml-2" />
          </Button>

          <p className="text-xs text-zinc-500 text-center">
            Selected features will enhance your learning experience with AI-powered tools.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
