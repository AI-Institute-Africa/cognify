import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { generateAssignment, evaluateAssignmentSubmission } from '../services/api';
import { 
  FileCheck,
  Brain,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Target,
  Clock,
  Plus,
  Send,
  Award,
  BookOpen,
  TrendingUp
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Progress } from '../components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';

const ASSIGNMENT_TYPES = [
  { id: 'reflection', name: 'Reflection Essay', description: 'Thoughtful analysis and personal insights' },
  { id: 'problem_solving', name: 'Problem Solving', description: 'Apply concepts to solve challenges' },
  { id: 'research', name: 'Research Project', description: 'Investigate and present findings' },
  { id: 'creative', name: 'Creative Project', description: 'Express understanding creatively' },
  { id: 'case_study', name: 'Case Study', description: 'Analyze real-world scenarios' },
];

export default function AssignmentGeneratorPage() {
  const { user } = useAuth();
  const [topic, setTopic] = useState('');
  const [objectives, setObjectives] = useState(['']);
  const [assignmentType, setAssignmentType] = useState('reflection');
  const [difficulty, setDifficulty] = useState('medium');
  const [loading, setLoading] = useState(false);
  const [assignment, setAssignment] = useState(null);
  const [submission, setSubmission] = useState('');
  const [evaluating, setEvaluating] = useState(false);
  const [evaluation, setEvaluation] = useState(null);

  const addObjective = () => {
    if (objectives.length < 5) {
      setObjectives([...objectives, '']);
    }
  };

  const updateObjective = (index, value) => {
    const newObjectives = [...objectives];
    newObjectives[index] = value;
    setObjectives(newObjectives);
  };

  const removeObjective = (index) => {
    if (objectives.length > 1) {
      setObjectives(objectives.filter((_, i) => i !== index));
    }
  };

  const handleGenerate = async () => {
    if (!topic.trim()) {
      toast.error('Please enter a lesson topic');
      return;
    }
    const validObjectives = objectives.filter(o => o.trim());
    if (validObjectives.length === 0) {
      toast.error('Please add at least one learning objective');
      return;
    }

    setLoading(true);
    setEvaluation(null);
    try {
      const result = await generateAssignment(topic, validObjectives, assignmentType, difficulty);
      setAssignment(result);
      toast.success('Assignment generated!');
    } catch (error) {
      console.error('Generation failed:', error);
      toast.error('Failed to generate assignment');
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluate = async () => {
    if (!submission.trim()) {
      toast.error('Please enter your submission');
      return;
    }
    if (!assignment?.assignment_id) {
      toast.error('No assignment to evaluate');
      return;
    }

    setEvaluating(true);
    try {
      const result = await evaluateAssignmentSubmission(assignment.assignment_id, submission);
      setEvaluation(result);
      toast.success('Submission evaluated!');
    } catch (error) {
      console.error('Evaluation failed:', error);
      toast.error('Failed to evaluate submission');
    } finally {
      setEvaluating(false);
    }
  };

  const getGradeColor = (grade) => {
    if (grade === 'A') return 'text-emerald-400';
    if (grade === 'B') return 'text-blue-400';
    if (grade === 'C') return 'text-amber-400';
    return 'text-red-400';
  };

  return (
    <DashboardLayout>
      <Header 
        title="AI Assignment Generator"
        subtitle="Auto-generate assignments and get AI evaluation"
      />
      
      <div className="p-8">
        <div className="max-w-5xl mx-auto">
          {/* Info Banner */}
          <div className="glass-card p-6 mb-8 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border-emerald-500/20">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                <FileCheck className="w-6 h-6 text-emerald-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-1">Smart Assignment Creation</h3>
                <p className="text-zinc-400 text-sm">
                  After any lesson, the AI can auto-generate relevant assignments. It then analyzes 
                  submissions, checks understanding, and updates your knowledge graph.
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Generator Section */}
            <div className="space-y-6">
              <div className="glass-card p-6 space-y-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <Brain className="w-5 h-5 text-emerald-400" />
                  Generate Assignment
                </h3>

                <div className="space-y-2">
                  <Label>Lesson Topic</Label>
                  <Input
                    placeholder="e.g., Photosynthesis, World War II, Quadratic Equations"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    className="bg-zinc-800 border-white/10"
                    data-testid="topic-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Learning Objectives</Label>
                  {objectives.map((obj, index) => (
                    <div key={index} className="flex gap-2">
                      <Input
                        placeholder={`Objective ${index + 1}`}
                        value={obj}
                        onChange={(e) => updateObjective(index, e.target.value)}
                        className="bg-zinc-800 border-white/10"
                      />
                      {objectives.length > 1 && (
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => removeObjective(index)}
                          className="flex-shrink-0"
                        >
                          ×
                        </Button>
                      )}
                    </div>
                  ))}
                  {objectives.length < 5 && (
                    <Button variant="ghost" size="sm" onClick={addObjective}>
                      <Plus className="w-4 h-4 mr-1" /> Add Objective
                    </Button>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Assignment Type</Label>
                    <Select value={assignmentType} onValueChange={setAssignmentType}>
                      <SelectTrigger className="bg-zinc-800 border-white/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-zinc-800 border-white/10">
                        {ASSIGNMENT_TYPES.map((type) => (
                          <SelectItem key={type.id} value={type.id}>
                            {type.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Difficulty</Label>
                    <Select value={difficulty} onValueChange={setDifficulty}>
                      <SelectTrigger className="bg-zinc-800 border-white/10">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-zinc-800 border-white/10">
                        <SelectItem value="easy">Easy</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="hard">Hard</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <Button
                  onClick={handleGenerate}
                  disabled={loading}
                  className="w-full bg-emerald-500 hover:bg-emerald-600"
                  data-testid="generate-btn"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <FileCheck className="w-4 h-4 mr-2" />
                      Generate Assignment
                    </>
                  )}
                </Button>
              </div>

              {/* Generated Assignment */}
              {assignment && (
                <div className="glass-card p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">{assignment.title || 'Assignment'}</h3>
                    <div className="flex gap-2">
                      <Badge className="bg-emerald-500/20 text-emerald-400 capitalize">
                        {assignmentType.replace('_', ' ')}
                      </Badge>
                      <Badge className="bg-zinc-700">
                        <Clock className="w-3 h-3 mr-1" />
                        {assignment.estimated_time_minutes || 30}min
                      </Badge>
                    </div>
                  </div>

                  {assignment.instructions && (
                    <div className="p-4 rounded-lg bg-zinc-800/50">
                      <div className="text-sm font-medium mb-2">Instructions</div>
                      <p className="text-sm text-zinc-300">{assignment.instructions}</p>
                    </div>
                  )}

                  {assignment.questions?.length > 0 && (
                    <div className="space-y-3">
                      <div className="text-sm font-medium">Questions</div>
                      {assignment.questions.map((q, index) => (
                        <div key={index} className="p-3 rounded-lg bg-zinc-800/50 border-l-2 border-emerald-500">
                          <div className="flex items-start justify-between">
                            <p className="text-sm text-zinc-300">{q.question}</p>
                            <Badge variant="outline" className="ml-2 text-xs border-white/10">
                              {q.points || 10} pts
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Submission & Evaluation Section */}
            <div className="space-y-6">
              {assignment ? (
                <>
                  <div className="glass-card p-6 space-y-4">
                    <h3 className="font-semibold flex items-center gap-2">
                      <Send className="w-5 h-5 text-blue-400" />
                      Submit Your Work
                    </h3>

                    <Textarea
                      placeholder="Write your response here..."
                      value={submission}
                      onChange={(e) => setSubmission(e.target.value)}
                      className="min-h-[250px] bg-zinc-800 border-white/10"
                      data-testid="submission-input"
                    />

                    <Button
                      onClick={handleEvaluate}
                      disabled={!submission.trim() || evaluating}
                      className="w-full bg-blue-500 hover:bg-blue-600"
                      data-testid="submit-btn"
                    >
                      {evaluating ? (
                        <>
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                          Evaluating...
                        </>
                      ) : (
                        <>
                          <Send className="w-4 h-4 mr-2" />
                          Submit for AI Evaluation
                        </>
                      )}
                    </Button>
                  </div>

                  {/* Evaluation Results */}
                  {evaluation && (
                    <div className="glass-card p-6 space-y-4">
                      <h3 className="font-semibold flex items-center gap-2">
                        <Award className="w-5 h-5 text-amber-400" />
                        Evaluation Results
                      </h3>

                      {/* Score */}
                      <div className="flex items-center justify-center gap-8 p-6 rounded-lg bg-zinc-800/50">
                        <div className="text-center">
                          <div className="text-4xl font-bold">
                            {evaluation.score || '--'}/{evaluation.max_score || 100}
                          </div>
                          <div className="text-sm text-zinc-500">Score</div>
                        </div>
                        {evaluation.grade && (
                          <div className="text-center">
                            <div className={`text-5xl font-bold ${getGradeColor(evaluation.grade)}`}>
                              {evaluation.grade}
                            </div>
                            <div className="text-sm text-zinc-500">Grade</div>
                          </div>
                        )}
                      </div>

                      {/* Feedback */}
                      {evaluation.feedback && (
                        <div className="p-4 rounded-lg bg-zinc-800/50">
                          <div className="text-sm font-medium mb-2">Feedback</div>
                          <p className="text-sm text-zinc-300">{evaluation.feedback}</p>
                        </div>
                      )}

                      {/* Strengths */}
                      {evaluation.strengths?.length > 0 && (
                        <div className="space-y-2">
                          <div className="text-sm font-medium text-emerald-400 flex items-center gap-2">
                            <CheckCircle className="w-4 h-4" />
                            Strengths
                          </div>
                          <ul className="space-y-1">
                            {evaluation.strengths.map((s, i) => (
                              <li key={i} className="text-sm text-zinc-300 flex items-start gap-2">
                                <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                                {s}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Areas for Improvement */}
                      {evaluation.areas_for_improvement?.length > 0 && (
                        <div className="space-y-2">
                          <div className="text-sm font-medium text-amber-400 flex items-center gap-2">
                            <TrendingUp className="w-4 h-4" />
                            Areas to Improve
                          </div>
                          <ul className="space-y-1">
                            {evaluation.areas_for_improvement.map((a, i) => (
                              <li key={i} className="text-sm text-zinc-300 flex items-start gap-2">
                                <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                                {a}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Knowledge Graph Updates */}
                      {evaluation.knowledge_graph_updates?.length > 0 && (
                        <div className="p-4 rounded-lg bg-violet-500/10 border border-violet-500/20">
                          <div className="text-sm font-medium text-violet-400 mb-2 flex items-center gap-2">
                            <Brain className="w-4 h-4" />
                            Knowledge Graph Updated
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {evaluation.knowledge_graph_updates.map((update, i) => (
                              <Badge 
                                key={i} 
                                className={`${
                                  update.status === 'mastered' ? 'bg-emerald-500/20 text-emerald-400' :
                                  update.status === 'learning' ? 'bg-blue-500/20 text-blue-400' :
                                  'bg-amber-500/20 text-amber-400'
                                }`}
                              >
                                {update.concept}: {update.status}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </>
              ) : (
                <div className="glass-card p-12 text-center">
                  <FileCheck className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">Generate an Assignment First</h3>
                  <p className="text-zinc-500 text-sm">
                    Configure and generate an assignment on the left, then submit 
                    your work here for AI evaluation.
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
