import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { 
  getConcepts, 
  getUserKnowledgeProgress, 
  teachAIStudent, 
  evaluateTeaching,
  generateTTS,
  getMicroHint
} from '../services/api';
import { 
  GraduationCap,
  Mic,
  MicOff,
  Send,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  MessageSquare,
  Brain,
  Target,
  Lightbulb,
  Star,
  Volume2,
  VolumeX,
  User,
  Bot,
  HelpCircle,
  Award,
  TrendingUp
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

const STUDENT_PERSONALITIES = [
  { id: 'curious', name: 'Curious Learner', description: 'Asks lots of questions', icon: '🤔' },
  { id: 'skeptical', name: 'Skeptical Student', description: 'Challenges your explanations', icon: '🧐' },
  { id: 'confused', name: 'Confused Beginner', description: 'Needs extra clarity', icon: '😕' },
  { id: 'advanced', name: 'Advanced Student', description: 'Asks deep follow-ups', icon: '🎓' },
];

export default function LearnByTeachingPage() {
  const { user } = useAuth();
  const { t, language } = useLanguage();
  const [concepts, setConcepts] = useState([]);
  const [progress, setProgress] = useState([]);
  const [selectedConcept, setSelectedConcept] = useState(null);
  const [selectedPersonality, setSelectedPersonality] = useState('curious');
  const [explanation, setExplanation] = useState('');
  const [loading, setLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(true);
  const [conversation, setConversation] = useState([]);
  const [teachingScore, setTeachingScore] = useState(null);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const [gettingHint, setGettingHint] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [conceptsData, progressData] = await Promise.all([
        getConcepts(),
        getUserKnowledgeProgress()
      ]);
      setConcepts(conceptsData || []);
      setProgress(progressData || []);
    } catch (error) {
      console.error('Failed to load data:', error);
      // Set some demo concepts if API fails
      setConcepts([
        { id: 'photosynthesis', name: 'Photosynthesis', subject: 'Biology', description: 'Process by which plants make food' },
        { id: 'newton-laws', name: "Newton's Laws of Motion", subject: 'Physics', description: 'Three fundamental laws of classical mechanics' },
        { id: 'quadratic-equations', name: 'Quadratic Equations', subject: 'Mathematics', description: 'Solving equations with degree 2' },
        { id: 'french-revolution', name: 'French Revolution', subject: 'History', description: 'Major political upheaval in France (1789-1799)' },
      ]);
    } finally {
      setDataLoading(false);
    }
  };

  const getConceptProgress = (conceptId) => {
    return progress.find(p => p.concept_id === conceptId) || { status: 'not_started', mastery_level: 0 };
  };

  const handleSelectConcept = (conceptId) => {
    const concept = concepts.find(c => c.id === conceptId);
    setSelectedConcept(concept);
    setExplanation('');
    setConversation([]);
    setTeachingScore(null);
  };

  const handleSubmitExplanation = async () => {
    if (!selectedConcept || !explanation.trim()) {
      toast.error('Please select a concept and provide an explanation');
      return;
    }

    setLoading(true);
    try {
      // Add user's explanation to conversation
      const userMessage = { role: 'teacher', content: explanation };
      setConversation(prev => [...prev, userMessage]);

      // Get AI student response
      const response = await teachAIStudent(
        explanation,
        selectedConcept.name || selectedConcept.id,
        selectedPersonality
      );

      // Add AI student response
      const aiMessage = {
        role: 'student',
        content: response.question || response.feedback || response.raw_response,
        understood: response.understood,
        followUpNeeded: response.follow_up_needed,
        encouragement: response.encouragement
      };
      setConversation(prev => [...prev, aiMessage]);

      // Clear input for next round
      setExplanation('');

      // If the AI student understood, offer to evaluate
      if (response.understood && !response.follow_up_needed) {
        toast.success('Great explanation! Ready to get your teaching score?');
      }
    } catch (error) {
      console.error('Teaching interaction failed:', error);
      toast.error('Failed to get AI student response');
    } finally {
      setLoading(false);
    }
  };

  const handleGetTeachingScore = async () => {
    if (conversation.length < 2) {
      toast.error('Please have at least one teaching exchange first');
      return;
    }

    setLoading(true);
    try {
      const allExplanations = conversation
        .filter(m => m.role === 'teacher')
        .map(m => m.content)
        .join('\n\n');

      const result = await evaluateTeaching(
        allExplanations,
        selectedConcept.name || selectedConcept.id
      );

      setTeachingScore(result);
      toast.success('Teaching evaluation complete!');
    } catch (error) {
      console.error('Evaluation failed:', error);
      toast.error('Failed to evaluate teaching');
    } finally {
      setLoading(false);
    }
  };

  const handleGetHint = async () => {
    if (!selectedConcept) {
      toast.error('Please select a concept first');
      return;
    }

    setGettingHint(true);
    try {
      const result = await getMicroHint(
        selectedConcept.name || selectedConcept.id,
        'teacher explaining to students'
      );

      if (result.hint) {
        toast.info(result.hint, { duration: 10000 });
      }
    } catch (error) {
      console.error('Failed to get hint:', error);
      toast.error('Failed to get hint');
    } finally {
      setGettingHint(false);
    }
  };

  const handlePlayAudio = async (text) => {
    try {
      setAudioPlaying(true);
      const result = await generateTTS(text, 'nova');
      if (result.audio_url) {
        const audio = new Audio(result.audio_url);
        audio.onended = () => setAudioPlaying(false);
        audio.onerror = () => {
          setAudioPlaying(false);
          toast.error('Failed to play audio');
        };
        await audio.play();
      }
    } catch (error) {
      console.error('TTS failed:', error);
      setAudioPlaying(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 8) return 'text-emerald-400';
    if (score >= 6) return 'text-amber-400';
    return 'text-red-400';
  };

  if (dataLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="w-12 h-12 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header 
        title={t('learnByTeaching')}
        subtitle="Teach an AI student to master concepts - the Feynman technique"
      />
      
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          {/* Info Banner */}
          <div className="glass-card p-6 mb-8 bg-gradient-to-r from-violet-500/10 to-purple-500/10 border-violet-500/20">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-violet-500/20 flex items-center justify-center">
                <Brain className="w-6 h-6 text-violet-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-1">The Feynman Technique</h3>
                <p className="text-zinc-400 text-sm">
                  Teaching others is the fastest way to learn. Explain concepts to an AI student 
                  who will ask questions, challenge your explanations, and help identify gaps in 
                  your understanding.
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left: Setup Panel */}
            <div className="glass-card p-6 space-y-6">
              <h3 className="font-semibold flex items-center gap-2">
                <Target className="w-5 h-5 text-violet-400" />
                Setup
              </h3>

              {/* Concept Selection */}
              <div className="space-y-2">
                <Label>Select Concept to Teach</Label>
                <Select value={selectedConcept?.id} onValueChange={handleSelectConcept}>
                  <SelectTrigger data-testid="concept-select" className="bg-zinc-800 border-white/10">
                    <SelectValue placeholder="Choose a concept..." />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-800 border-white/10">
                    {concepts.map((concept) => {
                      const prog = getConceptProgress(concept.id);
                      return (
                        <SelectItem key={concept.id} value={concept.id}>
                          <div className="flex items-center gap-2">
                            <span>{concept.name}</span>
                            {prog.mastery_level > 0.7 && <CheckCircle className="w-4 h-4 text-emerald-400" />}
                          </div>
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>

              {/* Student Personality */}
              <div className="space-y-2">
                <Label>AI Student Type</Label>
                <div className="grid grid-cols-2 gap-2">
                  {STUDENT_PERSONALITIES.map((personality) => (
                    <button
                      key={personality.id}
                      onClick={() => setSelectedPersonality(personality.id)}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        selectedPersonality === personality.id
                          ? 'bg-violet-500/20 border-violet-500'
                          : 'bg-zinc-800/50 border-white/5 hover:border-white/10'
                      }`}
                    >
                      <div className="text-2xl mb-1">{personality.icon}</div>
                      <div className="text-sm font-medium">{personality.name}</div>
                      <div className="text-xs text-zinc-500">{personality.description}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Get Hint Button */}
              <Button
                variant="outline"
                onClick={handleGetHint}
                disabled={!selectedConcept || gettingHint}
                className="w-full border-white/10"
              >
                <Lightbulb className="w-4 h-4 mr-2" />
                {gettingHint ? 'Getting Hint...' : 'Get Teaching Hint'}
              </Button>

              {/* Current Progress */}
              {selectedConcept && (
                <div className="p-4 rounded-lg bg-zinc-800/50">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-zinc-400">Your Mastery</span>
                    <span className="text-sm font-medium">
                      {Math.round((getConceptProgress(selectedConcept.id).mastery_level || 0) * 100)}%
                    </span>
                  </div>
                  <Progress 
                    value={(getConceptProgress(selectedConcept.id).mastery_level || 0) * 100} 
                    className="h-2"
                  />
                </div>
              )}
            </div>

            {/* Center: Teaching Area */}
            <div className="lg:col-span-2 space-y-6">
              {/* Conversation */}
              <div className="glass-card p-6">
                <h3 className="font-semibold flex items-center gap-2 mb-4">
                  <MessageSquare className="w-5 h-5 text-violet-400" />
                  Teaching Session
                  {selectedConcept && (
                    <Badge className="ml-2 bg-violet-500/20 text-violet-300">
                      {selectedConcept.name}
                    </Badge>
                  )}
                </h3>

                {/* Conversation Messages */}
                <div className="space-y-4 max-h-[400px] overflow-y-auto mb-4">
                  {conversation.length === 0 ? (
                    <div className="text-center py-12 text-zinc-500">
                      <GraduationCap className="w-16 h-16 mx-auto mb-4 opacity-50" />
                      <p>Start teaching by explaining the concept below</p>
                      <p className="text-sm mt-2">Your AI student is ready to learn!</p>
                    </div>
                  ) : (
                    conversation.map((message, index) => (
                      <div
                        key={index}
                        className={`flex gap-3 ${message.role === 'teacher' ? 'justify-end' : 'justify-start'}`}
                      >
                        {message.role === 'student' && (
                          <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center flex-shrink-0">
                            <Bot className="w-5 h-5 text-amber-400" />
                          </div>
                        )}
                        <div
                          className={`max-w-[80%] p-4 rounded-xl ${
                            message.role === 'teacher'
                              ? 'bg-violet-500/20 border border-violet-500/30'
                              : 'bg-zinc-800 border border-white/5'
                          }`}
                        >
                          <p className="text-sm">{message.content}</p>
                          {message.encouragement && (
                            <p className="text-xs text-emerald-400 mt-2">{message.encouragement}</p>
                          )}
                          {message.role === 'student' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handlePlayAudio(message.content)}
                              disabled={audioPlaying}
                              className="mt-2 h-7 px-2"
                            >
                              {audioPlaying ? (
                                <VolumeX className="w-3 h-3 mr-1" />
                              ) : (
                                <Volume2 className="w-3 h-3 mr-1" />
                              )}
                              Listen
                            </Button>
                          )}
                        </div>
                        {message.role === 'teacher' && (
                          <div className="w-10 h-10 rounded-full bg-violet-500/20 flex items-center justify-center flex-shrink-0">
                            <User className="w-5 h-5 text-violet-400" />
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>

                {/* Input Area */}
                <div className="space-y-3">
                  <Textarea
                    placeholder={selectedConcept 
                      ? `Explain ${selectedConcept.name} in your own words...`
                      : 'Select a concept to start teaching...'}
                    value={explanation}
                    onChange={(e) => setExplanation(e.target.value)}
                    disabled={!selectedConcept || loading}
                    data-testid="explanation-input"
                    className="min-h-[100px] bg-zinc-800 border-white/10"
                  />
                  <div className="flex gap-3">
                    <Button
                      onClick={handleSubmitExplanation}
                      disabled={!selectedConcept || !explanation.trim() || loading}
                      data-testid="submit-explanation-btn"
                      className="flex-1 bg-violet-500 hover:bg-violet-600"
                    >
                      {loading ? (
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Send className="w-4 h-4 mr-2" />
                      )}
                      {loading ? 'Thinking...' : 'Explain to Student'}
                    </Button>
                    {conversation.length >= 2 && (
                      <Button
                        onClick={handleGetTeachingScore}
                        disabled={loading}
                        variant="outline"
                        className="border-white/10"
                      >
                        <Award className="w-4 h-4 mr-2" />
                        Get Score
                      </Button>
                    )}
                  </div>
                </div>
              </div>

              {/* Teaching Score */}
              {teachingScore && (
                <div className="glass-card p-6">
                  <h3 className="font-semibold flex items-center gap-2 mb-4">
                    <Award className="w-5 h-5 text-amber-400" />
                    Teaching Quality Score
                  </h3>

                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                    {teachingScore.scores && Object.entries(teachingScore.scores).map(([key, value]) => (
                      <div key={key} className="text-center p-3 rounded-lg bg-zinc-800/50">
                        <div className={`text-2xl font-bold ${getScoreColor(value)}`}>{value}/10</div>
                        <div className="text-xs text-zinc-500 capitalize">{key}</div>
                      </div>
                    ))}
                  </div>

                  <div className="flex items-center justify-center gap-4 p-4 rounded-lg bg-gradient-to-r from-violet-500/10 to-amber-500/10">
                    <div className="text-center">
                      <div className="text-4xl font-bold text-violet-400">
                        {teachingScore.overall_score || '--'}/10
                      </div>
                      <div className="text-sm text-zinc-400">Overall Score</div>
                    </div>
                    {teachingScore.mastery_level && (
                      <div className="text-center">
                        <div className="text-4xl font-bold text-emerald-400">
                          {Math.round(teachingScore.mastery_level * 100)}%
                        </div>
                        <div className="text-sm text-zinc-400">Mastery Level</div>
                      </div>
                    )}
                  </div>

                  {teachingScore.strengths && teachingScore.strengths.length > 0 && (
                    <div className="mt-4">
                      <h4 className="text-sm font-medium text-emerald-400 mb-2">Strengths</h4>
                      <ul className="space-y-1">
                        {teachingScore.strengths.map((s, i) => (
                          <li key={i} className="text-sm text-zinc-300 flex items-start gap-2">
                            <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                            {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {teachingScore.gaps && teachingScore.gaps.length > 0 && (
                    <div className="mt-4">
                      <h4 className="text-sm font-medium text-amber-400 mb-2">Areas to Improve</h4>
                      <ul className="space-y-1">
                        {teachingScore.gaps.map((g, i) => (
                          <li key={i} className="text-sm text-zinc-300 flex items-start gap-2">
                            <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                            {g}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {teachingScore.recommendations && teachingScore.recommendations.length > 0 && (
                    <div className="mt-4">
                      <h4 className="text-sm font-medium text-violet-400 mb-2">Recommendations</h4>
                      <ul className="space-y-1">
                        {teachingScore.recommendations.map((r, i) => (
                          <li key={i} className="text-sm text-zinc-300 flex items-start gap-2">
                            <TrendingUp className="w-4 h-4 text-violet-400 flex-shrink-0 mt-0.5" />
                            {r}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
