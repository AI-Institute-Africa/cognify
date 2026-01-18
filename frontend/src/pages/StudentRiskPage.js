import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { 
  AlertTriangle, 
  TrendingDown,
  TrendingUp,
  Brain,
  BookOpen,
  Clock,
  Target,
  Users,
  Bell,
  ChevronRight,
  RefreshCw,
  CheckCircle,
  XCircle,
  Mail
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
  DialogTrigger,
} from '../components/ui/dialog';
import { toast } from 'sonner';

export default function StudentRiskPage() {
  const { user } = useAuth();
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [selectedStudent, setSelectedStudent] = useState(null);

  useEffect(() => {
    // Mock at-risk students data
    setStudents([
      {
        id: '1',
        name: 'Tapiwa Zimba',
        grade: 'Grade 11',
        risk_score: 78,
        risk_level: 'high',
        factors: [
          { name: 'Attendance Drop', impact: 35, description: 'Missed 8 classes in last 2 weeks' },
          { name: 'Grade Decline', impact: 28, description: 'GPA dropped from 3.2 to 2.5' },
          { name: 'Assignment Submissions', impact: 15, description: '3 late submissions' }
        ],
        predictions: {
          dropout_probability: 23,
          grade_decline_probability: 67,
          intervention_success: 82
        },
        recommendations: [
          'Schedule one-on-one meeting with counselor',
          'Assign peer tutor for Mathematics',
          'Contact parents for family engagement',
          'Reduce course load if needed'
        ],
        trend: 'declining',
        last_updated: '2026-01-18'
      },
      {
        id: '2',
        name: 'Chipo Moyo',
        grade: 'Grade 10',
        risk_score: 62,
        risk_level: 'medium',
        factors: [
          { name: 'Low Engagement', impact: 25, description: 'Minimal participation in AI Mentor sessions' },
          { name: 'Test Anxiety', impact: 22, description: 'Pattern of underperformance in exams vs. homework' },
          { name: 'Social Isolation', impact: 15, description: 'Not part of any study groups' }
        ],
        predictions: {
          dropout_probability: 8,
          grade_decline_probability: 45,
          intervention_success: 88
        },
        recommendations: [
          'Introduce to AI Study Groups feature',
          'Provide test-taking strategies workshop',
          'Assign study buddy with complementary skills'
        ],
        trend: 'stable',
        last_updated: '2026-01-18'
      },
      {
        id: '3',
        name: 'Tendai Ndlovu',
        grade: 'Grade 12',
        risk_score: 45,
        risk_level: 'low',
        factors: [
          { name: 'Slight Grade Dip', impact: 20, description: 'Small decrease in Chemistry scores' },
          { name: 'Increased Absences', impact: 15, description: '2 unexcused absences this month' },
          { name: 'Workload Stress', impact: 10, description: 'Self-reported high stress levels' }
        ],
        predictions: {
          dropout_probability: 2,
          grade_decline_probability: 25,
          intervention_success: 95
        },
        recommendations: [
          'Monitor for next 2 weeks',
          'Share stress management resources',
          'Encourage use of AI Mentor for Chemistry help'
        ],
        trend: 'improving',
        last_updated: '2026-01-18'
      }
    ]);
    setLoading(false);
  }, []);

  const runAnalysis = async () => {
    setAnalyzing(true);
    await new Promise(r => setTimeout(r, 2000));
    toast.success('AI analysis complete! Risk scores updated.');
    setAnalyzing(false);
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'high': return 'text-red-400 bg-red-500/20 border-red-500/30';
      case 'medium': return 'text-amber-400 bg-amber-500/20 border-amber-500/30';
      case 'low': return 'text-emerald-400 bg-emerald-500/20 border-emerald-500/30';
      default: return 'text-zinc-400 bg-zinc-500/20 border-zinc-500/30';
    }
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'declining': return <TrendingDown className="w-4 h-4 text-red-400" />;
      case 'improving': return <TrendingUp className="w-4 h-4 text-emerald-400" />;
      default: return <Target className="w-4 h-4 text-zinc-400" />;
    }
  };

  const stats = {
    high: students.filter(s => s.risk_level === 'high').length,
    medium: students.filter(s => s.risk_level === 'medium').length,
    low: students.filter(s => s.risk_level === 'low').length,
    total: students.length
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
        title="Student Risk Prediction"
        subtitle="AI-powered early warning system for at-risk students"
      />
      
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          {/* Info Banner */}
          <div className="glass-card p-6 mb-8 border-amber-500/20">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl bg-amber-500/20">
                <Brain className="w-6 h-6 text-amber-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-lg mb-2">AI Early Warning System</h3>
                <p className="text-zinc-400 text-sm">
                  Our AI analyzes attendance patterns, grade trends, engagement metrics, and behavioral 
                  indicators to identify students who may need additional support before they fall behind.
                </p>
              </div>
              <Button 
                onClick={runAnalysis} 
                disabled={analyzing}
                className="bg-amber-500 hover:bg-amber-600"
              >
                {analyzing ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Brain className="w-4 h-4 mr-2" />
                    Run Analysis
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-4 gap-4 mb-8">
            <div className="glass-card p-4 text-center border-red-500/20">
              <div className="text-3xl font-bold text-red-400">{stats.high}</div>
              <p className="text-sm text-zinc-500">High Risk</p>
            </div>
            <div className="glass-card p-4 text-center border-amber-500/20">
              <div className="text-3xl font-bold text-amber-400">{stats.medium}</div>
              <p className="text-sm text-zinc-500">Medium Risk</p>
            </div>
            <div className="glass-card p-4 text-center border-emerald-500/20">
              <div className="text-3xl font-bold text-emerald-400">{stats.low}</div>
              <p className="text-sm text-zinc-500">Low Risk</p>
            </div>
            <div className="glass-card p-4 text-center">
              <div className="text-3xl font-bold text-blue-400">{stats.total}</div>
              <p className="text-sm text-zinc-500">Total Flagged</p>
            </div>
          </div>

          {/* At-Risk Students */}
          <div className="glass-card p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              At-Risk Students
            </h2>
            
            <div className="space-y-4">
              {students.map((student) => (
                <div 
                  key={student.id}
                  className={`p-5 rounded-xl border transition-all cursor-pointer hover:scale-[1.01] ${
                    student.risk_level === 'high' ? 'bg-red-500/5 border-red-500/20' :
                    student.risk_level === 'medium' ? 'bg-amber-500/5 border-amber-500/20' :
                    'bg-zinc-800/50 border-white/5'
                  }`}
                  onClick={() => setSelectedStudent(student)}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center text-white font-semibold">
                        {student.name.charAt(0)}
                      </div>
                      <div>
                        <h3 className="font-semibold">{student.name}</h3>
                        <p className="text-sm text-zinc-500">{student.grade}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-1">
                        {getTrendIcon(student.trend)}
                        <span className="text-xs text-zinc-500 capitalize">{student.trend}</span>
                      </div>
                      <Badge className={getRiskColor(student.risk_level)}>
                        {student.risk_score}% Risk
                      </Badge>
                    </div>
                  </div>
                  
                  {/* Risk Factors Preview */}
                  <div className="grid grid-cols-3 gap-3 mb-4">
                    {student.factors.slice(0, 3).map((factor, i) => (
                      <div key={i} className="p-3 rounded-lg bg-zinc-800/50">
                        <p className="text-xs text-zinc-500">{factor.name}</p>
                        <p className="font-medium text-sm">{factor.impact}% impact</p>
                      </div>
                    ))}
                  </div>
                  
                  {/* Quick Actions */}
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" className="border-white/10 flex-1">
                      <Mail className="w-4 h-4 mr-2" />
                      Contact Parent
                    </Button>
                    <Button size="sm" variant="outline" className="border-white/10 flex-1">
                      <Bell className="w-4 h-4 mr-2" />
                      Set Alert
                    </Button>
                    <Button size="sm" className="flex-1 bg-violet-500 hover:bg-violet-600">
                      View Details
                      <ChevronRight className="w-4 h-4 ml-2" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Student Detail Modal */}
          <Dialog open={!!selectedStudent} onOpenChange={() => setSelectedStudent(null)}>
            <DialogContent className="bg-zinc-900 border-white/10 max-w-2xl">
              <DialogHeader>
                <DialogTitle>Risk Assessment: {selectedStudent?.name}</DialogTitle>
                <DialogDescription className="text-zinc-500">
                  Detailed AI analysis and intervention recommendations
                </DialogDescription>
              </DialogHeader>
              
              {selectedStudent && (
                <div className="space-y-6 mt-4">
                  {/* Risk Score */}
                  <div className="text-center p-6 rounded-xl bg-zinc-800/50">
                    <div className={`text-5xl font-bold mb-2 ${
                      selectedStudent.risk_level === 'high' ? 'text-red-400' :
                      selectedStudent.risk_level === 'medium' ? 'text-amber-400' :
                      'text-emerald-400'
                    }`}>
                      {selectedStudent.risk_score}%
                    </div>
                    <p className="text-zinc-500">Overall Risk Score</p>
                    <Progress value={selectedStudent.risk_score} className="h-2 bg-zinc-700 mt-4" />
                  </div>
                  
                  {/* Predictions */}
                  <div>
                    <h4 className="font-medium mb-3">AI Predictions</h4>
                    <div className="grid grid-cols-3 gap-3">
                      <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-center">
                        <p className="text-2xl font-bold text-red-400">{selectedStudent.predictions.dropout_probability}%</p>
                        <p className="text-xs text-zinc-500">Dropout Risk</p>
                      </div>
                      <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-center">
                        <p className="text-2xl font-bold text-amber-400">{selectedStudent.predictions.grade_decline_probability}%</p>
                        <p className="text-xs text-zinc-500">Grade Decline</p>
                      </div>
                      <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-center">
                        <p className="text-2xl font-bold text-emerald-400">{selectedStudent.predictions.intervention_success}%</p>
                        <p className="text-xs text-zinc-500">Intervention Success</p>
                      </div>
                    </div>
                  </div>
                  
                  {/* Risk Factors */}
                  <div>
                    <h4 className="font-medium mb-3">Contributing Factors</h4>
                    <div className="space-y-2">
                      {selectedStudent.factors.map((factor, i) => (
                        <div key={i} className="p-3 rounded-lg bg-zinc-800/50 flex items-center justify-between">
                          <div>
                            <p className="font-medium text-sm">{factor.name}</p>
                            <p className="text-xs text-zinc-500">{factor.description}</p>
                          </div>
                          <Badge variant="outline" className="border-zinc-700">
                            {factor.impact}%
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  {/* Recommendations */}
                  <div>
                    <h4 className="font-medium mb-3">AI Recommendations</h4>
                    <div className="space-y-2">
                      {selectedStudent.recommendations.map((rec, i) => (
                        <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-violet-500/10 border border-violet-500/20">
                          <CheckCircle className="w-5 h-5 text-violet-400 flex-shrink-0" />
                          <p className="text-sm">{rec}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  
                  <Button className="w-full" onClick={() => setSelectedStudent(null)}>
                    Create Intervention Plan
                  </Button>
                </div>
              )}
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </DashboardLayout>
  );
}
