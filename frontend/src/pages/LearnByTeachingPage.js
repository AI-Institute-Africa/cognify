import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { getConcepts, getUserKnowledgeProgress, teachBack } from '../services/api';
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
  Volume2
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

export default function LearnByTeachingPage() {
  const { user } = useAuth();
  const [concepts, setConcepts] = useState([]);
  const [progress, setProgress] = useState([]);
  const [selectedConcept, setSelectedConcept] = useState(null);
  const [explanation, setExplanation] = useState('');
  const [loading, setLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(true);
  const [evaluation, setEvaluation] = useState(null);
  const [isRecording, setIsRecording] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [conceptsData, progressData] = await Promise.all([
        getConcepts(),
        getUserKnowledgeProgress()
      ]);
      setConcepts(conceptsData);
      setProgress(progressData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setDataLoading(false);
    }
  };

  const getConceptProgress = (conceptId) => {
    return progress.find(p => p.concept_id === conceptId) || { status: 'not_started', confidence: 0 };
  };

  const handleSelectConcept = (conceptId) => {
    const concept = concepts.find(c => c.id === conceptId);
    setSelectedConcept(concept);
    setExplanation('');
    setEvaluation(null);
  };

  const handleSubmitExplanation = async () => {
    if (!selectedConcept || !explanation.trim()) {
      toast.error('Please select a concept and provide an explanation');
      return;
    }

    setLoading(true);
    try {
      const result = await teachBack(selectedConcept.id, explanation.trim());
      setEvaluation(result);
      toast.success('Explanation evaluated!');
    } catch (error) {
      toast.error('Failed to evaluate explanation');
    } finally {
      setLoading(false);
    }
  };

  const parseEvaluation = (evalText) => {
    try {
      const jsonMatch = evalText.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0]);
      }
    } catch {
      // Return raw text if not JSON
    }
    return { raw: evalText };
  };

  const parsedEval = evaluation ? parseEvaluation(evaluation.evaluation) : null;

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
        title="Learn by Teaching"
        subtitle="Master concepts by explaining them to an AI student"
      />
      
      <div className="p-8">
        <div className="max-w-5xl mx-auto">
          {/* Info Banner */}
          <div className="glass-card p-6 mb-8 border-violet-500/20">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-violet-500/20">
                <GraduationCap className="w-6 h-6 text-violet-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-2">The Feynman Technique</h3>
                <p className="text-zinc-400 text-sm">
                  Teaching is the best way to learn. Explain a concept to our AI student avatar, 
                  and it will ask clarifying questions, identify gaps in your understanding, 
                  and help you master the material.
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Concept Selection */}
            <div className="lg:col-span-1">
              <div className="glass-card p-6 sticky top-8">
                <h2 className="text-lg font-semibold mb-4">Select a Concept</h2>
                
                <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2">
                  {concepts.length === 0 ? (
                    <div className="text-center py-8">
                      <Brain className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                      <p className="text-zinc-500 text-sm">No concepts available</p>
                      <p className="text-zinc-600 text-xs mt-1">Upload a syllabus to get started</p>
                    </div>
                  ) : (
                    concepts.map((concept) => {
                      const state = getConceptProgress(concept.id);
                      const isSelected = selectedConcept?.id === concept.id;
                      
                      return (
                        <button
                          key={concept.id}
                          onClick={() => handleSelectConcept(concept.id)}
                          data-testid={`teach-concept-${concept.id}`}
                          className={`w-full p-4 rounded-xl text-left transition-all ${
                            isSelected
                              ? 'bg-violet-500/20 border border-violet-500/30'
                              : 'bg-zinc-800/50 border border-white/5 hover:border-white/10'
                          }`}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <h3 className="font-medium text-sm">{concept.name}</h3>
                            <Badge 
                              variant="outline" 
                              className={`text-xs ${
                                state.status === 'mastered' ? 'text-emerald-400 border-emerald-500/30' :
                                state.status === 'learning' ? 'text-blue-400 border-blue-500/30' :
                                'text-zinc-500 border-zinc-700'
                              }`}
                            >
                              {Math.round(state.confidence * 100)}%
                            </Badge>
                          </div>
                          <p className="text-xs text-zinc-500 mt-1 line-clamp-2">{concept.description}</p>
                        </button>
                      );
                    })
                  )}
                </div>
              </div>
            </div>

            {/* Teaching Area */}
            <div className="lg:col-span-2 space-y-6">
              {selectedConcept ? (
                <>
                  {/* Selected Concept Info */}
                  <div className="glass-card p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h2 className="text-xl font-semibold">{selectedConcept.name}</h2>
                        <p className="text-zinc-400 text-sm mt-1">{selectedConcept.description}</p>
                      </div>
                      <Badge className="bg-violet-500/20 text-violet-400">
                        Lvl {selectedConcept.difficulty}
                      </Badge>
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-zinc-500">
                      <span className="flex items-center gap-1">
                        <Target className="w-4 h-4" />
                        {selectedConcept.subject}
                      </span>
                      <span className="flex items-center gap-1">
                        <Brain className="w-4 h-4" />
                        {selectedConcept.estimated_time_minutes || 30} min
                      </span>
                    </div>
                  </div>

                  {/* AI Student Avatar */}
                  <div className="glass-card p-6">
                    <div className="flex items-center gap-4 mb-6">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
                        <MessageSquare className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <h3 className="font-semibold">AI Student</h3>
                        <p className="text-sm text-zinc-500">
                          I'm ready to learn! Explain this concept to me like I'm a beginner.
                        </p>
                      </div>
                    </div>

                    {/* Explanation Input */}
                    <div className="space-y-4">
                      <Label>Your Explanation</Label>
                      <Textarea
                        value={explanation}
                        onChange={(e) => setExplanation(e.target.value)}
                        placeholder={`Explain "${selectedConcept.name}" in your own words. Use examples and analogies...`}
                        className="min-h-[200px] bg-zinc-900/50 border-white/10 resize-none"
                        data-testid="teach-explanation-input"
                      />
                      
                      <div className="flex items-center justify-between">
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setIsRecording(!isRecording)}
                            className={`border-white/10 ${isRecording ? 'bg-red-500/20 text-red-400' : ''}`}
                          >
                            {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                          </Button>
                          <span className="text-xs text-zinc-500 self-center">
                            {explanation.length} characters
                          </span>
                        </div>
                        
                        <Button
                          onClick={handleSubmitExplanation}
                          disabled={!explanation.trim() || loading}
                          data-testid="submit-explanation-btn"
                          className="bg-violet-500 hover:bg-violet-600"
                        >
                          {loading ? (
                            <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                          ) : (
                            <Send className="w-4 h-4 mr-2" />
                          )}
                          Submit Explanation
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Evaluation Results */}
                  {evaluation && (
                    <div className="glass-card p-6 animate-fadeIn">
                      <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 rounded-lg bg-amber-500/20">
                          <Star className="w-5 h-5 text-amber-400" />
                        </div>
                        <h2 className="text-lg font-semibold">AI Student Feedback</h2>
                      </div>

                      {/* Rating */}
                      {parsedEval?.rating && (
                        <div className="mb-6 p-4 rounded-xl bg-zinc-800/50">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-zinc-400">Understanding Score</span>
                            <span className="text-2xl font-bold text-amber-400">{parsedEval.rating}/10</span>
                          </div>
                          <Progress value={parsedEval.rating * 10} className="h-2 bg-zinc-700" />
                        </div>
                      )}

                      {/* Questions */}
                      {parsedEval?.questions && parsedEval.questions.length > 0 && (
                        <div className="mb-4">
                          <h3 className="text-sm font-medium text-zinc-400 mb-3 flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-blue-400" />
                            Clarifying Questions
                          </h3>
                          <ul className="space-y-2">
                            {parsedEval.questions.map((q, i) => (
                              <li key={i} className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-sm">
                                {q}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Misconceptions */}
                      {parsedEval?.misconceptions && parsedEval.misconceptions.length > 0 && (
                        <div className="mb-4">
                          <h3 className="text-sm font-medium text-zinc-400 mb-3 flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-red-400" />
                            Areas to Review
                          </h3>
                          <ul className="space-y-2">
                            {parsedEval.misconceptions.map((m, i) => (
                              <li key={i} className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-sm">
                                {m}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Suggestions */}
                      {parsedEval?.suggestions && (
                        <div className="mb-4">
                          <h3 className="text-sm font-medium text-zinc-400 mb-3 flex items-center gap-2">
                            <Lightbulb className="w-4 h-4 text-emerald-400" />
                            Suggestions for Improvement
                          </h3>
                          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-sm">
                            {Array.isArray(parsedEval.suggestions) 
                              ? parsedEval.suggestions.join(', ')
                              : parsedEval.suggestions
                            }
                          </div>
                        </div>
                      )}

                      {/* Raw response fallback */}
                      {parsedEval?.raw && (
                        <div className="p-4 rounded-xl bg-zinc-800/50 text-sm whitespace-pre-wrap">
                          {parsedEval.raw}
                        </div>
                      )}

                      {/* Try Again */}
                      <div className="flex gap-3 mt-6">
                        <Button
                          variant="outline"
                          onClick={() => { setExplanation(''); setEvaluation(null); }}
                          className="flex-1 border-white/10"
                        >
                          Try Again
                        </Button>
                        <Button
                          onClick={() => setSelectedConcept(null)}
                          className="flex-1 bg-violet-500 hover:bg-violet-600"
                        >
                          Choose Another Concept
                        </Button>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="glass-card p-12 text-center">
                  <GraduationCap className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">Select a Concept to Teach</h3>
                  <p className="text-zinc-500">
                    Choose a concept from the list to start explaining it to the AI student
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
