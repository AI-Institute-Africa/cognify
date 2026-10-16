import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { getUserKnowledgeProgress, getConcepts, getGrades, getAchievements } from '../services/api';
import { 
  TrendingUp,
  Award,
  Target,
  Calendar,
  Star,
  BookOpen,
  CheckCircle,
  Clock,
  Zap,
  Trophy,
  Flame,
  ArrowUp,
  ArrowDown
} from 'lucide-react';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';

const milestones = [
  { id: 1, name: 'First Steps', description: 'Complete your first concept', icon: Star, target: 1, type: 'concepts' },
  { id: 2, name: 'Quick Learner', description: 'Master 5 concepts', icon: Zap, target: 5, type: 'mastered' },
  { id: 3, name: 'Knowledge Builder', description: 'Master 10 concepts', icon: BookOpen, target: 10, type: 'mastered' },
  { id: 4, name: 'Subject Expert', description: 'Master 25 concepts', icon: Trophy, target: 25, type: 'mastered' },
  { id: 5, name: 'Scholar', description: 'Maintain GPA above 3.5', icon: Award, target: 3.5, type: 'gpa' },
  { id: 6, name: 'Streak Master', description: '7 days learning streak', icon: Flame, target: 7, type: 'streak' },
];

export default function LearningJourneyPage() {
  const { user } = useAuth();
  const [progress, setProgress] = useState([]);
  const [concepts, setConcepts] = useState([]);
  const [grades, setGrades] = useState([]);
  const [achievements, setAchievements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeline, setTimeline] = useState([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [progressData, conceptsData, gradesData, achievementsData] = await Promise.all([
        getUserKnowledgeProgress(),
        getConcepts(),
        getGrades(),
        getAchievements()
      ]);
      setProgress(progressData);
      setConcepts(conceptsData);
      setGrades(gradesData);
      setAchievements(achievementsData);
      
      // Generate timeline
      generateTimeline(progressData, gradesData, achievementsData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateTimeline = (progressData, gradesData, achievementsData) => {
    const events = [];
    
    // Add concept progress events
    progressData.forEach(p => {
      if (p.last_reviewed) {
        events.push({
          id: `concept-${p.id}`,
          type: 'concept',
          title: p.concept?.name || 'Concept learned',
          description: `Status: ${p.status}, Confidence: ${Math.round(p.confidence * 100)}%`,
          date: new Date(p.last_reviewed),
          icon: p.status === 'mastered' ? CheckCircle : Clock,
          color: p.status === 'mastered' ? 'emerald' : 'blue'
        });
      }
    });
    
    // Add grade events
    gradesData.forEach(g => {
      events.push({
        id: `grade-${g.id}`,
        type: 'grade',
        title: `${g.assessment_name}`,
        description: `Score: ${g.score}/${g.max_score} (${Math.round(g.score/g.max_score*100)}%)`,
        date: new Date(g.graded_at),
        icon: g.score/g.max_score >= 0.8 ? Star : BookOpen,
        color: g.score/g.max_score >= 0.8 ? 'amber' : 'zinc'
      });
    });
    
    // Add achievement events
    achievementsData.forEach(a => {
      events.push({
        id: `achievement-${a.id}`,
        type: 'achievement',
        title: a.title,
        description: a.description,
        date: new Date(a.date_awarded),
        icon: Trophy,
        color: 'violet'
      });
    });
    
    // Sort by date descending
    events.sort((a, b) => b.date - a.date);
    setTimeline(events.slice(0, 20)); // Show last 20 events
  };

  const calculateMilestoneProgress = (milestone) => {
    switch (milestone.type) {
      case 'concepts':
        return Math.min(progress.length / milestone.target * 100, 100);
      case 'mastered':
        const mastered = progress.filter(p => p.status === 'mastered').length;
        return Math.min(mastered / milestone.target * 100, 100);
      case 'gpa':
        // Calculate average from grades
        if (grades.length === 0) return 0;
        const avg = grades.reduce((sum, g) => sum + (g.score / g.max_score * 4), 0) / grades.length;
        return Math.min(avg / milestone.target * 100, 100);
      case 'streak':
        return 30; // Placeholder
      default:
        return 0;
    }
  };

  const stats = {
    totalConcepts: concepts.length,
    mastered: progress.filter(p => p.status === 'mastered').length,
    learning: progress.filter(p => p.status === 'learning').length,
    totalGrades: grades.length,
    avgScore: grades.length > 0 
      ? Math.round(grades.reduce((sum, g) => sum + (g.score / g.max_score * 100), 0) / grades.length)
      : 0,
    achievements: achievements.length
  };

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
        title="Learning Journey"
        subtitle="Track your progress and achievements over time"
      />
      
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          {/* Overview Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="glass-card p-5">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-500/20">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Mastered</p>
                  <p className="text-xl font-bold">{stats.mastered}</p>
                </div>
              </div>
            </div>
            <div className="glass-card p-5">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-500/20">
                  <Clock className="w-5 h-5 text-blue-400" />
                </div>
                <div>
                  <p className="text-xs text-zinc-500">In Progress</p>
                  <p className="text-xl font-bold">{stats.learning}</p>
                </div>
              </div>
            </div>
            <div className="glass-card p-5">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-amber-500/20">
                  <Star className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Avg Score</p>
                  <p className="text-xl font-bold">{stats.avgScore}%</p>
                </div>
              </div>
            </div>
            <div className="glass-card p-5">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-violet-500/20">
                  <Trophy className="w-5 h-5 text-violet-400" />
                </div>
                <div>
                  <p className="text-xs text-zinc-500">Achievements</p>
                  <p className="text-xl font-bold">{stats.achievements}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Milestones */}
            <div className="lg:col-span-1">
              <div className="glass-card p-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Target className="w-5 h-5 text-blue-400" />
                  Milestones
                </h2>
                <div className="space-y-4">
                  {milestones.map(milestone => {
                    const progressPercent = calculateMilestoneProgress(milestone);
                    const isComplete = progressPercent >= 100;
                    
                    return (
                      <div 
                        key={milestone.id}
                        className={`p-4 rounded-xl border transition-all ${
                          isComplete 
                            ? 'bg-emerald-500/10 border-emerald-500/30' 
                            : 'bg-zinc-800/50 border-white/5 hover:border-white/10'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className={`p-2 rounded-lg ${isComplete ? 'bg-emerald-500/20' : 'bg-zinc-700'}`}>
                            <milestone.icon className={`w-4 h-4 ${isComplete ? 'text-emerald-400' : 'text-zinc-400'}`} />
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <h3 className="font-medium text-sm">{milestone.name}</h3>
                              {isComplete && (
                                <Badge className="bg-emerald-500/20 text-emerald-400 text-xs">
                                  Complete!
                                </Badge>
                              )}
                            </div>
                            <p className="text-xs text-zinc-500 mt-1">{milestone.description}</p>
                            <div className="mt-2">
                              <Progress value={progressPercent} className="h-1.5 bg-zinc-700" />
                              <p className="text-xs text-zinc-600 mt-1">{Math.round(progressPercent)}%</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Timeline */}
            <div className="lg:col-span-2">
              <div className="glass-card p-6">
                <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-violet-400" />
                  Activity Timeline
                </h2>
                
                {timeline.length === 0 ? (
                  <div className="text-center py-12">
                    <TrendingUp className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                    <p className="text-zinc-500">No activity yet</p>
                    <p className="text-zinc-600 text-sm mt-1">Start learning to see your progress here</p>
                  </div>
                ) : (
                  <div className="relative">
                    {/* Timeline line */}
                    <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-zinc-800" />
                    
                    <div className="space-y-4">
                      {timeline.map((event, index) => {
                        const Icon = event.icon;
                        const colorClasses = {
                          emerald: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
                          blue: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                          amber: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
                          violet: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
                          zinc: 'bg-zinc-500/20 text-zinc-400 border-zinc-500/30'
                        };
                        
                        return (
                          <div key={event.id} className="relative flex gap-4 animate-fadeIn" style={{ animationDelay: `${index * 50}ms` }}>
                            {/* Icon */}
                            <div className={`relative z-10 w-12 h-12 rounded-xl flex items-center justify-center border ${colorClasses[event.color]}`}>
                              <Icon className="w-5 h-5" />
                            </div>
                            
                            {/* Content */}
                            <div className="flex-1 pb-4">
                              <div className="glass-card p-4 hover:border-white/20 transition-all">
                                <div className="flex items-start justify-between">
                                  <div>
                                    <h3 className="font-medium">{event.title}</h3>
                                    <p className="text-sm text-zinc-500 mt-1">{event.description}</p>
                                  </div>
                                  <Badge variant="outline" className="text-xs border-zinc-700 text-zinc-500">
                                    {event.type}
                                  </Badge>
                                </div>
                                <p className="text-xs text-zinc-600 mt-2">
                                  {event.date.toLocaleDateString('en-US', { 
                                    month: 'short', 
                                    day: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </p>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
