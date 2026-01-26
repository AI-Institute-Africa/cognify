import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { decomposeOutcome, startOutcomeLearning, getOutcomePathways } from '../services/api';
import { 
  Target,
  Rocket,
  CheckCircle,
  Clock,
  TrendingUp,
  Award,
  Briefcase,
  GraduationCap,
  RefreshCw,
  ArrowRight,
  Star,
  Lightbulb,
  Repeat
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';

const OUTCOME_EXAMPLES = [
  "I want to become a data analyst earning $3000/month",
  "I want to pass the CFA Level 1 exam",
  "I want to build and deploy my first web application",
  "I want to become fluent in French within 6 months",
  "I want to get a job as a junior software developer"
];

export default function OutcomeLearningPage() {
  const { user } = useAuth();
  const [outcome, setOutcome] = useState('');
  const [loading, setLoading] = useState(false);
  const [startingLearning, setStartingLearning] = useState(false);
  const [pathway, setPathway] = useState(null);
  const [learningPlan, setLearningPlan] = useState(null);
  const [existingPathways, setExistingPathways] = useState([]);

  useEffect(() => {
    loadExistingPathways();
  }, []);

  const loadExistingPathways = async () => {
    try {
      const pathways = await getOutcomePathways();
      setExistingPathways(pathways);
    } catch (error) {
      console.error('Failed to load pathways:', error);
    }
  };

  const handleDecompose = async () => {
    if (!outcome.trim()) {
      toast.error('Please enter your desired outcome');
      return;
    }

    setLoading(true);
    try {
      const result = await decomposeOutcome(outcome);
      setPathway(result);
      toast.success('Outcome pathway created!');
      loadExistingPathways();
    } catch (error) {
      console.error('Decomposition failed:', error);
      toast.error('Failed to create pathway');
    } finally {
      setLoading(false);
    }
  };

  const handleStartLearning = async () => {
    if (!pathway?.pathway_id) {
      toast.error('No pathway selected');
      return;
    }

    setStartingLearning(true);
    try {
      const result = await startOutcomeLearning(pathway.pathway_id);
      setLearningPlan(result.learning_plan);
      toast.success('Learning journey started! Your personalized plan is ready.');
    } catch (error) {
      console.error('Failed to start learning:', error);
      toast.error('Failed to start learning journey');
    } finally {
      setStartingLearning(false);
    }
  };

  const selectExample = (example) => {
    setOutcome(example);
  };

  return (
    <DashboardLayout>
      <Header 
        title="Outcome-First Learning"
        subtitle="Define your goal and we'll create the path to achieve it"
      />
      
      <div className="p-8">
        <div className="max-w-5xl mx-auto">
          {/* Info Banner */}
          <div className="glass-card p-6 mb-8 bg-gradient-to-r from-amber-500/10 to-orange-500/10 border-amber-500/20">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center">
                <Target className="w-6 h-6 text-amber-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-1">Learn by Outcomes, Not Courses</h3>
                <p className="text-zinc-400 text-sm">
                  Tell us what you want to achieve, and we'll break it down into the exact skills, 
                  habits, and proofs you need. Education becomes results-driven, not content-driven.
                </p>
              </div>
            </div>
          </div>

          {!pathway ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Input Section */}
              <div className="glass-card p-6 space-y-6">
                <h3 className="font-semibold flex items-center gap-2">
                  <Rocket className="w-5 h-5 text-amber-400" />
                  Define Your Outcome
                </h3>

                <div className="space-y-2">
                  <Textarea
                    placeholder="What do you want to achieve? Be specific about your goal..."
                    value={outcome}
                    onChange={(e) => setOutcome(e.target.value)}
                    className="min-h-[120px] bg-zinc-800 border-white/10"
                    data-testid="outcome-input"
                  />
                  <p className="text-xs text-zinc-500">
                    Be specific: Include target role, income, certification, or measurable goal
                  </p>
                </div>

                <Button
                  onClick={handleDecompose}
                  disabled={!outcome.trim() || loading}
                  className="w-full bg-amber-500 hover:bg-amber-600"
                  data-testid="create-pathway-btn"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Creating Pathway...
                    </>
                  ) : (
                    <>
                      <Target className="w-4 h-4 mr-2" />
                      Create Learning Pathway
                    </>
                  )}
                </Button>
              </div>

              {/* Examples Section */}
              <div className="glass-card p-6 space-y-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <Lightbulb className="w-5 h-5 text-amber-400" />
                  Example Outcomes
                </h3>

                <div className="space-y-2">
                  {OUTCOME_EXAMPLES.map((example, index) => (
                    <button
                      key={index}
                      onClick={() => selectExample(example)}
                      className="w-full p-3 rounded-lg bg-zinc-800/50 border border-white/5 hover:border-amber-500/30 text-left transition-all"
                    >
                      <span className="text-sm">{example}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-8">
              {/* Outcome Header */}
              <div className="glass-card p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <Badge className="mb-2 bg-amber-500/20 text-amber-400">Outcome Pathway</Badge>
                    <h2 className="text-2xl font-bold">{pathway.outcome}</h2>
                    <p className="text-zinc-500 mt-1">
                      Estimated: {pathway.estimated_weeks} weeks • Success-based pricing
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => setPathway(null)}
                    className="border-white/10"
                  >
                    <Repeat className="w-4 h-4 mr-2" />
                    New Outcome
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Skills */}
                <div className="glass-card p-6">
                  <h3 className="font-semibold flex items-center gap-2 mb-4">
                    <GraduationCap className="w-5 h-5 text-blue-400" />
                    Skills to Master
                  </h3>
                  <div className="space-y-2">
                    {pathway.skills?.map((skill, index) => (
                      <div key={index} className="flex items-center gap-3 p-3 rounded-lg bg-zinc-800/50">
                        <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-sm font-medium text-blue-400">
                          {index + 1}
                        </div>
                        <span className="text-sm">{skill}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Habits */}
                <div className="glass-card p-6">
                  <h3 className="font-semibold flex items-center gap-2 mb-4">
                    <Repeat className="w-5 h-5 text-emerald-400" />
                    Habits to Build
                  </h3>
                  <div className="space-y-2">
                    {pathway.habits?.map((habit, index) => (
                      <div key={index} className="flex items-center gap-3 p-3 rounded-lg bg-zinc-800/50">
                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                        <span className="text-sm">{habit}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Proofs */}
                <div className="glass-card p-6">
                  <h3 className="font-semibold flex items-center gap-2 mb-4">
                    <Award className="w-5 h-5 text-violet-400" />
                    Proofs Required
                  </h3>
                  <div className="space-y-2">
                    {pathway.proofs?.map((proof, index) => (
                      <div key={index} className="flex items-center gap-3 p-3 rounded-lg bg-zinc-800/50">
                        <Star className="w-5 h-5 text-violet-400" />
                        <span className="text-sm">{proof}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Milestones Timeline */}
              <div className="glass-card p-6">
                <h3 className="font-semibold flex items-center gap-2 mb-6">
                  <TrendingUp className="w-5 h-5 text-amber-400" />
                  Your Milestone Roadmap
                </h3>

                <div className="relative">
                  {/* Timeline Line */}
                  <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-amber-500 via-emerald-500 to-violet-500"></div>

                  {/* Milestones */}
                  <div className="space-y-6">
                    {pathway.milestones?.map((milestone, index) => {
                      const colors = ['amber', 'blue', 'emerald', 'violet'];
                      const color = colors[index % colors.length];
                      
                      return (
                        <div key={index} className="flex gap-6 relative">
                          <div className={`w-16 h-16 rounded-xl bg-${color}-500/20 flex items-center justify-center flex-shrink-0 z-10`}>
                            <span className="text-2xl font-bold text-${color}-400">{index + 1}</span>
                          </div>
                          <div className="flex-1 p-4 rounded-xl bg-zinc-800/50 border border-white/5">
                            <div className="flex items-center justify-between mb-2">
                              <h4 className="font-semibold">{milestone.name}</h4>
                              <Badge className="bg-zinc-700">
                                <Clock className="w-3 h-3 mr-1" />
                                {milestone.weeks} weeks
                              </Badge>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {milestone.skills?.map((skill, i) => (
                                <Badge key={i} variant="outline" className="text-xs border-white/10">
                                  {skill}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </div>
                      );
                    })}

                    {/* Completion */}
                    <div className="flex gap-6 relative">
                      <div className="w-16 h-16 rounded-xl bg-emerald-500/20 flex items-center justify-center flex-shrink-0 z-10">
                        <Award className="w-8 h-8 text-emerald-400" />
                      </div>
                      <div className="flex-1 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                        <h4 className="font-semibold text-emerald-400">Outcome Achieved!</h4>
                        <p className="text-sm text-zinc-400 mt-1">
                          Complete all milestones and proofs to achieve your goal
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Pricing Model */}
              <div className="glass-card p-6 bg-gradient-to-r from-amber-500/10 to-violet-500/10 border-amber-500/20">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-lg">Success-Based Pricing</h3>
                    <p className="text-zinc-400 text-sm mt-1">
                      Pay only when you achieve your outcome. {pathway.success_fee_percentage}% success fee on completion.
                    </p>
                  </div>
                  <Button 
                    className="bg-amber-500 hover:bg-amber-600"
                    onClick={handleStartLearning}
                    disabled={startingLearning}
                    data-testid="start-learning-btn"
                  >
                    {startingLearning ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Starting...
                      </>
                    ) : (
                      <>
                        <Rocket className="w-4 h-4 mr-2" />
                        Start Learning
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {/* Learning Plan (shows after clicking Start Learning) */}
              {learningPlan && (
                <div className="glass-card p-6 border-emerald-500/20">
                  <h3 className="font-semibold flex items-center gap-2 mb-4 text-emerald-400">
                    <CheckCircle className="w-5 h-5" />
                    Your Personalized Learning Plan
                  </h3>
                  <p className="text-zinc-400 mb-4">{learningPlan.description}</p>
                  <p className="text-sm text-zinc-500 mb-4">Estimated Duration: {learningPlan.estimated_duration}</p>
                  
                  <div className="space-y-4">
                    {learningPlan.modules?.map((module, idx) => (
                      <div key={module.id || idx} className="p-4 rounded-lg bg-zinc-800/50 border border-white/5">
                        <h4 className="font-semibold mb-2">Module {idx + 1}: {module.title}</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                          {module.lessons?.map((lesson, lessonIdx) => (
                            <div key={lesson.id || lessonIdx} className="flex items-center gap-2 text-sm text-zinc-400">
                              <BookOpen className="w-4 h-4" />
                              <span>{lesson.title}</span>
                              <Badge className="text-xs bg-zinc-700">{lesson.duration}</Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  {learningPlan.milestones && (
                    <div className="mt-4 pt-4 border-t border-white/10">
                      <h4 className="font-semibold mb-2 flex items-center gap-2">
                        <Target className="w-4 h-4 text-amber-400" />
                        Milestones
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {learningPlan.milestones.map((milestone, idx) => (
                          <Badge key={idx} className="bg-amber-500/20 text-amber-400">{milestone}</Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
