import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Progress } from '../components/ui/progress';
import {
  Zap,
  Clock,
  Target,
  CheckCircle,
  ChevronRight,
  ChevronDown,
  Brain,
  Sparkles,
  BookOpen,
  Play,
  Loader2,
  ArrowLeft,
  Lightbulb,
  Route
} from 'lucide-react';
import { toast } from 'sonner';
import { ktceOptimizePath, ktceGetCompressedLesson, getCourse } from '../services/api';

export default function KTCELearningPage() {
  const { courseId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { t } = useLanguage();
  
  const [course, setCourse] = useState(null);
  const [learnerGoal, setLearnerGoal] = useState('');
  const [ktceResult, setKtceResult] = useState(null);
  const [currentConceptIndex, setCurrentConceptIndex] = useState(0);
  const [expandedConcept, setExpandedConcept] = useState(null);
  const [compressedLesson, setCompressedLesson] = useState(null);
  const [loading, setLoading] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [lessonLoading, setLessonLoading] = useState(false);
  const [conceptLearning, setConceptLearning] = useState(null);

  // Load concept from Knowledge Graph navigation
  useEffect(() => {
    const conceptId = searchParams.get('concept');
    if (conceptId) {
      // Load from session storage if navigating from knowledge graph
      const storedLearning = sessionStorage.getItem('currentLearning');
      if (storedLearning) {
        try {
          const learningData = JSON.parse(storedLearning);
          setConceptLearning(learningData);
          toast.success(`Learning: ${learningData.concept_name}`);
        } catch (e) {
          console.error('Failed to parse learning data:', e);
        }
      }
    }
  }, [searchParams]);

  useEffect(() => {
    if (courseId) {
      loadCourse();
    }
  }, [courseId]);

  const loadCourse = async () => {
    try {
      const data = await getCourse(courseId);
      setCourse(data);
      setLearnerGoal(`Master ${data.title || data.name} and apply the concepts in practice`);
    } catch (error) {
      console.error('Failed to load course:', error);
    }
  };

  const handleOptimize = async () => {
    if (!learnerGoal.trim()) {
      toast.error('Please enter your learning goal');
      return;
    }

    setOptimizing(true);
    try {
      const result = await ktceOptimizePath(courseId, learnerGoal);
      setKtceResult(result);
      setCurrentConceptIndex(0);
      toast.success(`Optimized path created! ${result.minimum_viable_concepts?.length || 0} essential concepts identified.`);
    } catch (error) {
      console.error('KTCE optimization failed:', error);
      toast.error('Failed to optimize learning path');
    } finally {
      setOptimizing(false);
    }
  };

  const loadCompressedLesson = async (concept) => {
    setLessonLoading(true);
    setExpandedConcept(concept.concept_id);
    
    try {
      const result = await ktceGetCompressedLesson(
        concept.concept_id,
        concept.concept_name,
        concept.essence || ''
      );
      setCompressedLesson(result.compressed_lesson);
    } catch (error) {
      console.error('Failed to load compressed lesson:', error);
      // Use the pre-generated essence from KTCE
      setCompressedLesson({
        essence: concept.essence,
        decision_rule: concept.decision_rule,
        example: 'See course materials for detailed examples.',
        verification_question: `Can you explain ${concept.concept_name} in your own words?`
      });
    } finally {
      setLessonLoading(false);
    }
  };

  const markConceptComplete = () => {
    if (currentConceptIndex < (ktceResult?.minimum_viable_concepts?.length || 0) - 1) {
      setCurrentConceptIndex(currentConceptIndex + 1);
      setExpandedConcept(null);
      setCompressedLesson(null);
    } else {
      toast.success('Congratulations! You\'ve completed the optimized learning path!');
    }
  };

  const progressPercent = ktceResult?.minimum_viable_concepts?.length 
    ? Math.round((currentConceptIndex / ktceResult.minimum_viable_concepts.length) * 100)
    : 0;

  return (
    <DashboardLayout>
      <Header title="KTCE Learning" subtitle="Knowledge Time Compression Engine" />
      
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="max-w-4xl mx-auto">
          {/* Back Button */}
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors mb-6"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Course
          </button>

          {/* Header */}
          <div className="glass-card p-6 sm:p-8 mb-8">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br from-emerald-500/20 to-cyan-500/20 flex items-center justify-center">
                <Zap className="w-6 h-6 sm:w-8 sm:h-8 text-emerald-400" />
              </div>
              <div className="flex-1">
                <h1 className="text-xl sm:text-2xl font-bold flex items-center gap-2">
                  <span>KTCE</span>
                  <span className="text-emerald-400">Knowledge Time Compression</span>
                </h1>
                <p className="text-zinc-400 mt-1">
                  Minimize time-to-competence while preserving correctness. Learn only what you need.
                </p>
                {course && (
                  <p className="text-sm text-zinc-500 mt-2">
                    Course: <span className="text-white">{course.title || course.name}</span>
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Goal Input Section */}
          {!ktceResult && (
            <div className="glass-card p-8">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-400" />
                Define Your Learning Goal
              </h2>
              <p className="text-zinc-400 mb-6">
                What do you want to be able to do after completing this course? Be specific about outcomes.
              </p>
              
              <div className="space-y-4">
                <div>
                  <Label>Your Goal</Label>
                  <Input
                    value={learnerGoal}
                    onChange={(e) => setLearnerGoal(e.target.value)}
                    placeholder="e.g., Solve differential equations, Build REST APIs, Analyze financial statements..."
                    className="mt-2 h-12 bg-zinc-900/50 border-white/10"
                  />
                </div>
                
                <div className="flex gap-2 flex-wrap">
                  <span className="text-sm text-zinc-500">Quick goals:</span>
                  {[
                    'Apply concepts in real problems',
                    'Pass the final exam',
                    'Build a project from scratch',
                    'Understand fundamentals deeply'
                  ].map((goal) => (
                    <button
                      key={goal}
                      onClick={() => setLearnerGoal(goal)}
                      className="px-3 py-1 rounded-full bg-zinc-800 text-xs text-zinc-400 hover:bg-zinc-700 hover:text-white transition-colors"
                    >
                      {goal}
                    </button>
                  ))}
                </div>
                
                <Button
                  onClick={handleOptimize}
                  disabled={optimizing || !learnerGoal.trim()}
                  className="w-full h-12 bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600"
                >
                  {optimizing ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Analyzing Knowledge Graph...
                    </>
                  ) : (
                    <>
                      <Zap className="w-5 h-5 mr-2" />
                      Optimize My Learning Path
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* KTCE Results */}
          {ktceResult && (
            <div className="space-y-6">
              {/* Stats Bar */}
              <div className="grid grid-cols-4 gap-4">
                <div className="glass-card p-4 text-center">
                  <p className="text-2xl font-bold text-emerald-400">
                    {ktceResult.minimum_viable_concepts?.length || 0}
                  </p>
                  <p className="text-xs text-zinc-500">Essential Concepts</p>
                </div>
                <div className="glass-card p-4 text-center">
                  <p className="text-2xl font-bold text-cyan-400">
                    {ktceResult.excluded_concepts?.length || 0}
                  </p>
                  <p className="text-xs text-zinc-500">Skipped Concepts</p>
                </div>
                <div className="glass-card p-4 text-center">
                  <p className="text-2xl font-bold text-violet-400">
                    {ktceResult.collapsed_concept_groups?.length || 0}
                  </p>
                  <p className="text-xs text-zinc-500">Collapsed Groups</p>
                </div>
                <div className="glass-card p-4 text-center">
                  <p className="text-2xl font-bold text-amber-400">
                    {ktceResult.estimated_time_to_competence_minutes || 30}
                  </p>
                  <p className="text-xs text-zinc-500">Minutes Est.</p>
                </div>
              </div>

              {/* Progress */}
              <div className="glass-card p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-zinc-400">Progress</span>
                  <span className="text-sm font-medium">{progressPercent}%</span>
                </div>
                <Progress value={progressPercent} className="h-2" />
              </div>

              {/* Learning Path */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Route className="w-5 h-5 text-emerald-400" />
                  Minimum Viable Learning Path
                </h3>
                
                <div className="space-y-3">
                  {ktceResult.minimum_viable_concepts?.map((concept, index) => (
                    <div
                      key={concept.concept_id}
                      className={`rounded-xl border transition-all ${
                        index === currentConceptIndex
                          ? 'border-emerald-500/50 bg-emerald-500/5'
                          : index < currentConceptIndex
                          ? 'border-green-500/30 bg-green-500/5'
                          : 'border-white/10 bg-zinc-900/30'
                      }`}
                    >
                      <button
                        onClick={() => {
                          if (index === currentConceptIndex) {
                            loadCompressedLesson(concept);
                          }
                        }}
                        className="w-full p-4 text-left"
                        disabled={index !== currentConceptIndex}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            index < currentConceptIndex
                              ? 'bg-green-500 text-white'
                              : index === currentConceptIndex
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50'
                              : 'bg-zinc-800 text-zinc-500'
                          }`}>
                            {index < currentConceptIndex ? (
                              <CheckCircle className="w-5 h-5" />
                            ) : (
                              <span className="text-sm font-medium">{index + 1}</span>
                            )}
                          </div>
                          
                          <div className="flex-1">
                            <h4 className={`font-medium ${
                              index === currentConceptIndex ? 'text-white' : 'text-zinc-400'
                            }`}>
                              {concept.concept_name}
                            </h4>
                            <p className="text-sm text-zinc-500 mt-1 line-clamp-1">
                              {concept.essence}
                            </p>
                          </div>
                          
                          {index === currentConceptIndex && (
                            <ChevronRight className="w-5 h-5 text-emerald-400" />
                          )}
                        </div>
                      </button>
                      
                      {/* Expanded Lesson */}
                      {expandedConcept === concept.concept_id && (
                        <div className="px-4 pb-4 border-t border-white/10 mt-2 pt-4">
                          {lessonLoading ? (
                            <div className="flex items-center justify-center py-8">
                              <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
                            </div>
                          ) : compressedLesson && (
                            <div className="space-y-4">
                              {/* Essence */}
                              <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                                <div className="flex items-center gap-2 mb-2">
                                  <Lightbulb className="w-4 h-4 text-emerald-400" />
                                  <span className="text-sm font-semibold text-emerald-400">Essence</span>
                                </div>
                                <p className="text-sm text-zinc-300">{compressedLesson.essence}</p>
                              </div>
                              
                              {/* Decision Rule */}
                              <div className="p-4 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
                                <div className="flex items-center gap-2 mb-2">
                                  <Target className="w-4 h-4 text-cyan-400" />
                                  <span className="text-sm font-semibold text-cyan-400">Decision Rule</span>
                                </div>
                                <p className="text-sm text-zinc-300 font-mono">{compressedLesson.decision_rule}</p>
                              </div>
                              
                              {/* Example */}
                              {compressedLesson.example && (
                                <div className="p-4 rounded-lg bg-violet-500/10 border border-violet-500/20">
                                  <div className="flex items-center gap-2 mb-2">
                                    <BookOpen className="w-4 h-4 text-violet-400" />
                                    <span className="text-sm font-semibold text-violet-400">Example</span>
                                  </div>
                                  <p className="text-sm text-zinc-300">{compressedLesson.example}</p>
                                </div>
                              )}
                              
                              {/* Verification Question */}
                              {compressedLesson.verification_question && (
                                <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/20">
                                  <div className="flex items-center gap-2 mb-2">
                                    <Brain className="w-4 h-4 text-amber-400" />
                                    <span className="text-sm font-semibold text-amber-400">Quick Check</span>
                                  </div>
                                  <p className="text-sm text-zinc-300">{compressedLesson.verification_question}</p>
                                </div>
                              )}
                              
                              <Button
                                onClick={markConceptComplete}
                                className="w-full bg-emerald-500 hover:bg-emerald-600"
                              >
                                <CheckCircle className="w-4 h-4 mr-2" />
                                I Understand - Next Concept
                              </Button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Excluded Concepts */}
              {ktceResult.excluded_concepts?.length > 0 && (
                <div className="glass-card p-6">
                  <h3 className="text-lg font-semibold mb-4 text-zinc-400">
                    Skipped Concepts ({ktceResult.excluded_concepts.length})
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {ktceResult.excluded_concepts.map((concept) => (
                      <span
                        key={concept.concept_id}
                        className="px-3 py-1 rounded-full bg-zinc-800/50 text-xs text-zinc-500"
                        title={concept.reason}
                      >
                        {concept.concept_id}
                      </span>
                    ))}
                  </div>
                  <p className="text-xs text-zinc-600 mt-3">
                    These concepts were skipped because they are already mastered, can be inferred, or have low operational value for your goal.
                  </p>
                </div>
              )}

              {/* Reset Button */}
              <div className="text-center">
                <Button
                  variant="outline"
                  onClick={() => {
                    setKtceResult(null);
                    setCurrentConceptIndex(0);
                    setExpandedConcept(null);
                    setCompressedLesson(null);
                  }}
                  className="border-zinc-700"
                >
                  Reset & Choose Different Goal
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
