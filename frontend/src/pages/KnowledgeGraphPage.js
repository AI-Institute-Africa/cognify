import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { getConcepts, getUserKnowledgeProgress, getConceptHint, updateConceptState } from '../services/api';
import { 
  Network, 
  Brain, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  Lightbulb,
  ArrowRight,
  BookOpen,
  Target,
  Zap,
  RefreshCw
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import { toast } from 'sonner';

const statusColors = {
  mastered: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  learning: { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500/30' },
  needs_review: { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/30' },
  not_started: { bg: 'bg-zinc-500/20', text: 'text-zinc-400', border: 'border-zinc-500/30' }
};

const statusIcons = {
  mastered: CheckCircle,
  learning: Clock,
  needs_review: AlertCircle,
  not_started: BookOpen
};

export default function KnowledgeGraphPage() {
  const { user } = useAuth();
  const [concepts, setConcepts] = useState([]);
  const [progress, setProgress] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedConcept, setSelectedConcept] = useState(null);
  const [hintLoading, setHintLoading] = useState(false);
  const [hint, setHint] = useState(null);
  const [filter, setFilter] = useState('all');

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
      console.error('Failed to load knowledge graph:', error);
    } finally {
      setLoading(false);
    }
  };

  const getConceptProgress = (conceptId) => {
    return progress.find(p => p.concept_id === conceptId) || { status: 'not_started', confidence: 0 };
  };

  const handleGetHint = async (conceptId) => {
    setHintLoading(true);
    try {
      const result = await getConceptHint(conceptId);
      setHint(result.hint);
    } catch (error) {
      toast.error('Failed to get hint');
    } finally {
      setHintLoading(false);
    }
  };

  const handleStartLearning = async (conceptId) => {
    try {
      await updateConceptState(conceptId, 0.1, 0, false);
      await loadData();
      toast.success('Started learning!');
    } catch (error) {
      toast.error('Failed to update progress');
    }
  };

  const calculateStats = () => {
    const total = concepts.length;
    const mastered = progress.filter(p => p.status === 'mastered').length;
    const learning = progress.filter(p => p.status === 'learning').length;
    const needsReview = progress.filter(p => p.status === 'needs_review').length;
    return { total, mastered, learning, needsReview };
  };

  const filteredConcepts = concepts.filter(concept => {
    if (filter === 'all') return true;
    const state = getConceptProgress(concept.id);
    return state.status === filter;
  });

  const stats = calculateStats();

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header 
        title="Knowledge Graph"
        subtitle="Your live-sync learning architecture"
      />
      
      <div className="p-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="glass-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-500">Total Concepts</p>
                <h3 className="text-3xl font-bold mt-2">{stats.total}</h3>
              </div>
              <div className="p-3 rounded-xl bg-blue-500/20">
                <Network className="w-6 h-6 text-blue-400" />
              </div>
            </div>
          </div>
          
          <div className="glass-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-500">Mastered</p>
                <h3 className="text-3xl font-bold mt-2 text-emerald-400">{stats.mastered}</h3>
              </div>
              <div className="p-3 rounded-xl bg-emerald-500/20">
                <CheckCircle className="w-6 h-6 text-emerald-400" />
              </div>
            </div>
          </div>
          
          <div className="glass-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-500">In Progress</p>
                <h3 className="text-3xl font-bold mt-2 text-blue-400">{stats.learning}</h3>
              </div>
              <div className="p-3 rounded-xl bg-blue-500/20">
                <Clock className="w-6 h-6 text-blue-400" />
              </div>
            </div>
          </div>
          
          <div className="glass-card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-zinc-500">Needs Review</p>
                <h3 className="text-3xl font-bold mt-2 text-amber-400">{stats.needsReview}</h3>
              </div>
              <div className="p-3 rounded-xl bg-amber-500/20">
                <RefreshCw className="w-6 h-6 text-amber-400" />
              </div>
            </div>
          </div>
        </div>

        {/* Mastery Progress */}
        <div className="glass-card p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">Overall Mastery</h3>
            <span className="text-sm text-blue-400">
              {stats.total > 0 ? ((stats.mastered / stats.total) * 100).toFixed(0) : 0}%
            </span>
          </div>
          <Progress 
            value={stats.total > 0 ? (stats.mastered / stats.total) * 100 : 0} 
            className="h-3 bg-zinc-800" 
          />
          <div className="flex justify-between mt-4 text-xs text-zinc-500">
            <span>Beginner</span>
            <span>Intermediate</span>
            <span>Expert</span>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mb-6">
          {['all', 'mastered', 'learning', 'needs_review', 'not_started'].map(status => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                filter === status
                  ? 'bg-blue-500 text-white'
                  : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
              }`}
            >
              {status === 'all' ? 'All' : status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </button>
          ))}
        </div>

        {/* Concepts Grid */}
        {filteredConcepts.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <Network className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">No concepts found</h3>
            <p className="text-zinc-500">
              {filter === 'all' 
                ? 'Start by enrolling in courses to see concepts'
                : `No concepts with status: ${filter.replace('_', ' ')}`
              }
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredConcepts.map((concept, index) => {
              const state = getConceptProgress(concept.id);
              const StatusIcon = statusIcons[state.status] || BookOpen;
              const colors = statusColors[state.status] || statusColors.not_started;
              
              return (
                <div
                  key={concept.id}
                  className={`glass-card p-6 hover:border-white/20 transition-all duration-300 cursor-pointer animate-fadeIn stagger-${(index % 5) + 1}`}
                  onClick={() => setSelectedConcept(concept)}
                  data-testid={`concept-card-${concept.id}`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className={`p-3 rounded-xl ${colors.bg}`}>
                      <StatusIcon className={`w-6 h-6 ${colors.text}`} />
                    </div>
                    <Badge variant="outline" className={`${colors.bg} ${colors.text} ${colors.border}`}>
                      {state.status.replace('_', ' ')}
                    </Badge>
                  </div>
                  
                  <h3 className="text-lg font-semibold mb-2">{concept.name}</h3>
                  <p className="text-sm text-zinc-500 mb-4 line-clamp-2">{concept.description}</p>
                  
                  <div className="flex items-center gap-4 text-sm text-zinc-500 mb-4">
                    <span className="flex items-center gap-1">
                      <BookOpen className="w-4 h-4" />
                      {concept.subject}
                    </span>
                    <span className="flex items-center gap-1">
                      <Target className="w-4 h-4" />
                      Lvl {concept.difficulty}
                    </span>
                  </div>
                  
                  {/* Confidence Bar */}
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-zinc-500">Confidence</span>
                      <span className={colors.text}>{Math.round(state.confidence * 100)}%</span>
                    </div>
                    <Progress value={state.confidence * 100} className="h-2 bg-zinc-800" />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Concept Detail Dialog */}
        <Dialog open={!!selectedConcept} onOpenChange={() => { setSelectedConcept(null); setHint(null); }}>
          <DialogContent className="bg-zinc-900 border-white/10 max-w-lg">
            <DialogHeader>
              <DialogTitle>{selectedConcept?.name}</DialogTitle>
              <DialogDescription className="text-zinc-500">
                {selectedConcept?.description}
              </DialogDescription>
            </DialogHeader>
            
            {selectedConcept && (
              <div className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 rounded-lg bg-zinc-800/50">
                    <p className="text-xs text-zinc-500">Subject</p>
                    <p className="font-medium">{selectedConcept.subject}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-800/50">
                    <p className="text-xs text-zinc-500">Difficulty</p>
                    <p className="font-medium">Level {selectedConcept.difficulty}/10</p>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-800/50">
                    <p className="text-xs text-zinc-500">Est. Time</p>
                    <p className="font-medium">{selectedConcept.estimated_time_minutes} min</p>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-800/50">
                    <p className="text-xs text-zinc-500">Prerequisites</p>
                    <p className="font-medium">{selectedConcept.prerequisites?.length || 0}</p>
                  </div>
                </div>
                
                {/* Real-world Applications */}
                {selectedConcept.real_world_apps?.length > 0 && (
                  <div>
                    <p className="text-sm text-zinc-500 mb-2">Real-world Applications</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedConcept.real_world_apps.map((app, i) => (
                        <Badge key={i} variant="outline" className="border-zinc-700">
                          {app}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Hint Section */}
                {hint && (
                  <div className="p-4 rounded-xl bg-violet-500/10 border border-violet-500/20">
                    <div className="flex items-center gap-2 mb-2">
                      <Lightbulb className="w-4 h-4 text-violet-400" />
                      <span className="text-sm font-medium text-violet-400">30-Second Hint</span>
                    </div>
                    <p className="text-sm text-zinc-300">{hint}</p>
                  </div>
                )}
                
                <div className="flex gap-3 pt-4">
                  <Button
                    variant="outline"
                    onClick={() => handleGetHint(selectedConcept.id)}
                    disabled={hintLoading}
                    className="flex-1 border-white/10"
                  >
                    <Lightbulb className="w-4 h-4 mr-2" />
                    {hintLoading ? 'Loading...' : 'Get Hint'}
                  </Button>
                  <Button
                    onClick={() => {
                      handleStartLearning(selectedConcept.id);
                      setSelectedConcept(null);
                    }}
                    className="flex-1 bg-blue-500 hover:bg-blue-600"
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    Start Learning
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
