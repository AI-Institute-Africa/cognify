import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import {
  Layers,
  Plus,
  BookOpen,
  Brain,
  Sparkles,
  Play,
  Trash2,
  Edit2,
  Clock,
  Users,
  Target,
  Mic,
  MicOff,
  CheckCircle,
  ArrowRight,
  Loader2,
  Network
} from 'lucide-react';
import { toast } from 'sonner';
import AIFeaturesGridModal from '../components/AIFeaturesGridModal';

const API = process.env.REACT_APP_BACKEND_URL;

export default function MultiSubjectPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [subjects, setSubjects] = useState([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showAIFeaturesModal, setShowAIFeaturesModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [aiFeatures, setAIFeatures] = useState({});
  
  // Voice input
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef(null);
  
  const [newSubject, setNewSubject] = useState({
    name: '',
    description: '',
    subjects: [],
    learning_goals: '',
    estimated_weeks: 4
  });
  const [subjectInput, setSubjectInput] = useState('');

  useEffect(() => {
    loadSubjects();
    loadAIFeatures();
  }, []);

  const loadSubjects = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/multi-subject/my-subjects`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSubjects(data.subjects || []);
      }
    } catch (error) {
      console.error('Failed to load subjects:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAIFeatures = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/user/ai-preferences`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setAIFeatures(data.preferences?.features || {});
      }
    } catch (error) {
      console.error('Failed to load AI features:', error);
    }
  };

  const handleCreateSubject = async () => {
    if (!newSubject.name || newSubject.subjects.length === 0) {
      toast.error('Please provide a name and at least one subject');
      return;
    }

    // Check if AI features are selected
    if (Object.keys(aiFeatures).length === 0) {
      setShowAIFeaturesModal(true);
      return;
    }

    setCreating(true);
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/multi-subject/create`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...newSubject,
          ai_features: aiFeatures
        })
      });

      if (response.ok) {
        toast.success('Multi-Subject learning path created!');
        setShowCreateDialog(false);
        setNewSubject({
          name: '',
          description: '',
          subjects: [],
          learning_goals: '',
          estimated_weeks: 4
        });
        loadSubjects();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create');
      }
    } catch (error) {
      toast.error('Failed to create multi-subject path');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteSubject = async (subjectId) => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/multi-subject/${subjectId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Deleted successfully');
        loadSubjects();
      }
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const addSubjectToList = () => {
    if (subjectInput.trim() && !newSubject.subjects.includes(subjectInput.trim())) {
      setNewSubject(prev => ({
        ...prev,
        subjects: [...prev.subjects, subjectInput.trim()]
      }));
      setSubjectInput('');
    }
  };

  const removeSubjectFromList = (index) => {
    setNewSubject(prev => ({
      ...prev,
      subjects: prev.subjects.filter((_, i) => i !== index)
    }));
  };

  // Voice input for subjects
  const startVoiceInput = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      toast.error('Speech recognition not supported');
      return;
    }

    recognitionRef.current = new SpeechRecognition();
    recognitionRef.current.continuous = false;
    recognitionRef.current.interimResults = true;

    recognitionRef.current.onstart = () => {
      setIsRecording(true);
      toast.info('Listening... Say the subject name');
    };

    recognitionRef.current.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(result => result[0].transcript)
        .join('');
      setSubjectInput(transcript);
    };

    recognitionRef.current.onerror = (event) => {
      console.error('Speech error:', event.error);
      setIsRecording(false);
    };

    recognitionRef.current.onend = () => {
      setIsRecording(false);
    };

    recognitionRef.current.start();
  };

  const stopVoiceInput = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsRecording(false);
  };

  const handleAIFeaturesComplete = (result) => {
    setAIFeatures(result.features || {});
    // Continue with creation
    handleCreateSubject();
  };

  // Check if user can create multi-subject
  const canCreate = ['student', 'org_admin', 'org_staff', 'admin', 'teacher'].includes(user?.role);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <Loader2 className="w-12 h-12 animate-spin text-violet-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header 
        title="Multi-Subject Learning"
        subtitle="Combine multiple subjects for integrated, cross-disciplinary learning"
      />
      
      <div className="p-4 sm:p-6 lg:p-8">
        {/* Info Banner */}
        <div className="glass-card p-6 mb-8 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border-cyan-500/20">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/20 flex items-center justify-center">
              <Network className="w-6 h-6 text-cyan-400" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-lg mb-1">Cross-Disciplinary Learning</h3>
              <p className="text-zinc-400 text-sm">
                Create learning paths that combine multiple subjects. Perfect for understanding 
                how different fields connect and complement each other.
              </p>
              {!aiFeatures?.multidisciplinary && (
                <Button
                  onClick={() => setShowAIFeaturesModal(true)}
                  variant="outline"
                  size="sm"
                  className="mt-3 border-cyan-500/30 text-cyan-400"
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  Enable AI Features
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <p className="text-zinc-400">
              {subjects.length} multi-subject {subjects.length === 1 ? 'path' : 'paths'} created
            </p>
          </div>
          {canCreate && (
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button className="bg-cyan-500 hover:bg-cyan-600" data-testid="create-multi-subject-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Multi-Subject Path
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-zinc-900 border-white/10 max-w-lg">
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <Layers className="w-5 h-5 text-cyan-400" />
                    Create Multi-Subject Learning Path
                  </DialogTitle>
                  <DialogDescription className="text-zinc-500">
                    Combine subjects for integrated learning experience
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 mt-4">
                  <div className="space-y-2">
                    <Label>Path Name</Label>
                    <Input
                      placeholder="e.g., Data Science Fundamentals"
                      value={newSubject.name}
                      onChange={(e) => setNewSubject(prev => ({ ...prev, name: e.target.value }))}
                      className="bg-zinc-800/50 border-white/10"
                      data-testid="multi-subject-name-input"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Textarea
                      placeholder="Describe what students will learn..."
                      value={newSubject.description}
                      onChange={(e) => setNewSubject(prev => ({ ...prev, description: e.target.value }))}
                      className="bg-zinc-800/50 border-white/10"
                      rows={3}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Subjects to Combine</Label>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Add a subject (e.g., Mathematics)"
                        value={subjectInput}
                        onChange={(e) => setSubjectInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && addSubjectToList()}
                        className="bg-zinc-800/50 border-white/10 flex-1"
                        data-testid="subject-input"
                      />
                      <Button
                        type="button"
                        onClick={isRecording ? stopVoiceInput : startVoiceInput}
                        variant="outline"
                        className={`border-white/10 ${isRecording ? 'bg-red-500/20 text-red-400' : ''}`}
                        data-testid="voice-subject-btn"
                      >
                        {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                      </Button>
                      <Button
                        type="button"
                        onClick={addSubjectToList}
                        variant="outline"
                        className="border-white/10"
                      >
                        <Plus className="w-4 h-4" />
                      </Button>
                    </div>
                    
                    {newSubject.subjects.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {newSubject.subjects.map((subject, index) => (
                          <Badge
                            key={index}
                            className="bg-cyan-500/20 text-cyan-400 pr-1 flex items-center gap-1"
                          >
                            {subject}
                            <button
                              onClick={() => removeSubjectFromList(index)}
                              className="ml-1 hover:text-red-400"
                            >
                              ×
                            </button>
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label>Learning Goals</Label>
                    <Textarea
                      placeholder="What should students achieve after completing this path?"
                      value={newSubject.learning_goals}
                      onChange={(e) => setNewSubject(prev => ({ ...prev, learning_goals: e.target.value }))}
                      className="bg-zinc-800/50 border-white/10"
                      rows={2}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Estimated Duration (weeks)</Label>
                    <Input
                      type="number"
                      min="1"
                      max="52"
                      value={newSubject.estimated_weeks}
                      onChange={(e) => setNewSubject(prev => ({ ...prev, estimated_weeks: parseInt(e.target.value) || 4 }))}
                      className="bg-zinc-800/50 border-white/10 w-32"
                    />
                  </div>

                  <Button
                    onClick={handleCreateSubject}
                    disabled={creating || !newSubject.name || newSubject.subjects.length === 0}
                    className="w-full bg-cyan-500 hover:bg-cyan-600"
                    data-testid="submit-multi-subject-btn"
                  >
                    {creating ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Create Learning Path
                      </>
                    )}
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          )}
        </div>

        {/* Subjects Grid */}
        {subjects.length === 0 ? (
          <div className="text-center py-20">
            <Layers className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">No Multi-Subject Paths Yet</h3>
            <p className="text-zinc-500 mb-4">
              Create your first multi-subject learning path to combine different disciplines.
            </p>
            {canCreate && (
              <Button
                onClick={() => setShowCreateDialog(true)}
                className="bg-cyan-500 hover:bg-cyan-600"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Path
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {subjects.map((subject, index) => (
              <div
                key={subject.id}
                className={`glass-card p-6 hover:border-white/20 transition-all duration-300 group animate-fadeIn stagger-${(index % 5) + 1}`}
                data-testid={`multi-subject-card-${subject.id}`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500/20 to-blue-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Layers className="w-6 h-6 text-cyan-400" />
                  </div>
                  <Badge className="bg-cyan-500/20 text-cyan-400">
                    {subject.subjects?.length || 0} Subjects
                  </Badge>
                </div>

                <h3 className="text-lg font-semibold mb-2">{subject.name}</h3>
                <p className="text-sm text-zinc-500 mb-3 line-clamp-2">{subject.description}</p>

                <div className="flex flex-wrap gap-1 mb-4">
                  {(subject.subjects || []).slice(0, 3).map((s, i) => (
                    <Badge key={i} variant="outline" className="text-xs border-white/10">
                      {s}
                    </Badge>
                  ))}
                  {(subject.subjects?.length || 0) > 3 && (
                    <Badge variant="outline" className="text-xs border-white/10">
                      +{subject.subjects.length - 3} more
                    </Badge>
                  )}
                </div>

                <div className="flex items-center gap-4 text-sm text-zinc-500 mb-4">
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {subject.estimated_weeks || 4} weeks
                  </span>
                  <span className="flex items-center gap-1">
                    <Target className="w-4 h-4" />
                    {subject.progress || 0}%
                  </span>
                </div>

                <div className="flex gap-2">
                  <Button
                    onClick={() => navigate(`/multi-subject/${subject.id}`)}
                    className="flex-1 bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500 hover:text-white border border-cyan-500/30"
                  >
                    <Play className="w-4 h-4 mr-2" />
                    Start Learning
                  </Button>
                  <Button
                    onClick={() => handleDeleteSubject(subject.id)}
                    variant="outline"
                    className="border-white/10 text-zinc-400 hover:text-red-400 hover:border-red-500/30"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* AI Features Modal */}
      <AIFeaturesGridModal
        isOpen={showAIFeaturesModal}
        onClose={() => setShowAIFeaturesModal(false)}
        onComplete={handleAIFeaturesComplete}
        courseType="customized"
      />
    </DashboardLayout>
  );
}
