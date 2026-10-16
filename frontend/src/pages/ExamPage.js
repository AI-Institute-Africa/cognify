import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { 
  FileText, Clock, AlertTriangle, CheckCircle, XCircle, 
  Play, Pause, Camera, Shield, Award, Upload,
  Plus, Loader2, Timer, ChevronRight, BookOpen, Sparkles,
  Lock, CreditCard
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function ExamPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [exams, setExams] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedExam, setSelectedExam] = useState(null);
  const [examStarted, setExamStarted] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeLeft, setTimeLeft] = useState(0);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [creating, setCreating] = useState(false);
  const [paymentLockInfo, setPaymentLockInfo] = useState(null);
  
  // Create exam form state
  const [newExam, setNewExam] = useState({
    title: '',
    course_id: '',
    duration: 60,
    question_count: 20,
    generation_method: 'ai',
    source_content: '',
    due_date: ''
  });
  
  // Proctoring state
  const [webcamEnabled, setWebcamEnabled] = useState(false);
  const [tabSwitches, setTabSwitches] = useState(0);
  const [warnings, setWarnings] = useState([]);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const isTeacher = user?.role === 'teacher' || user?.role === 'admin' || user?.role === 'org_admin';

  useEffect(() => {
    loadData();
  }, []);

  // Timer effect
  useEffect(() => {
    let timer;
    if (examStarted && timeLeft > 0) {
      timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            handleSubmitExam();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [examStarted, timeLeft]);

  // Tab switch detection
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (examStarted && document.hidden) {
        setTabSwitches(prev => prev + 1);
        setWarnings(prev => [...prev, { time: new Date().toISOString(), type: 'tab_switch', message: 'Tab switch detected' }]);
        toast.warning('Warning: Tab switch detected! This will be reported.');
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [examStarted]);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      const headers = { 'Authorization': `Bearer ${token}` };
      
      const [examsRes, coursesRes] = await Promise.all([
        fetch(`${API_URL}/api/exams`, { headers }),
        fetch(`${API_URL}/api/courses`, { headers })
      ]);
      
      if (examsRes.ok) {
        const examsData = await examsRes.json();
        setExams(examsData);
      }
      
      if (coursesRes.ok) {
        const coursesData = await coursesRes.json();
        setCourses(coursesData);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const startWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setWebcamEnabled(true);
      toast.success('Webcam enabled for proctoring');
    } catch (error) {
      console.error('Webcam error:', error);
      toast.error('Could not access webcam. Exam will continue without proctoring.');
    }
  };

  const stopWebcam = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      setWebcamEnabled(false);
    }
  };

  const handleStartExam = async (exam) => {
    if (isTeacher) {
      toast.error('Teachers cannot take exams');
      return;
    }
    
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API_URL}/api/exams/${exam.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.status === 403) {
        const errorData = await response.json();
        const detail = errorData.detail || {};
        const lockMessage = typeof detail === 'object' ? (detail.message || 'Payment required') : (typeof detail === 'string' ? detail : 'Payment required');
        const courseId = (typeof detail === 'object' && detail.course_id) ? detail.course_id : exam.course_id;
        const amountRemaining = typeof detail === 'object' ? detail.amount_remaining : null;
        setPaymentLockInfo({
          message: lockMessage,
          courseId: courseId,
          amountRemaining: amountRemaining
        });
        toast.error('Assessment Locked: Payment Required');
        return;
      }

      if (response.ok) {
        const examData = await response.json();
        setSelectedExam(exam);
        setQuestions(examData.questions || []);
        setTimeLeft(exam.duration * 60);
        setExamStarted(true);
        startWebcam();
      } else {
        const errorData = await response.json().catch(() => ({}));
        const errDetail = errorData.detail;
        const msg = typeof errDetail === 'string' ? errDetail : (errDetail?.message || 'Failed to load exam questions');
        toast.error(msg);
      }
    } catch (error) {
      console.error('Failed to load exam questions:', error);
      toast.error('Network error loading exam');
    }
  };

  const handleAnswer = (questionId, answer) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

  const handleSubmitExam = async () => {
    setSubmitting(true);
    stopWebcam();
    
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API_URL}/api/exams/${selectedExam.id}/submit`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          exam_id: selectedExam.id,
          answers,
          time_taken: selectedExam.duration * 60 - timeLeft,
          tab_switches: tabSwitches,
          warnings
        })
      });
      
      if (response.status === 403) {
        const errorData = await response.json();
        const detail = errorData.detail || {};
        const lockMessage = typeof detail === 'object' ? (detail.message || 'Payment required') : (typeof detail === 'string' ? detail : 'Payment required');
        setPaymentLockInfo({
          message: lockMessage,
          courseId: selectedExam?.course_id,
          amountRemaining: typeof detail === 'object' ? detail.amount_remaining : null
        });
        toast.error('Submission blocked: Payment required');
        setSubmitting(false);
        return;
      }

      if (response.ok) {
        const resultData = await response.json();
        setResult(resultData);
        toast.success('Exam submitted successfully!');
      } else {
        // Fallback local grading
        let score = 0;
        questions.forEach(q => {
          if (q.type === 'multiple' && answers[q.id] === q.correct) {
            score += 100 / questions.length;
          }
        });
        setResult({
          score: Math.round(score),
          grade: score >= 90 ? 'A' : score >= 80 ? 'B' : score >= 70 ? 'C' : score >= 60 ? 'D' : 'F',
          feedback: 'Your exam has been submitted.'
        });
      }
    } catch (error) {
      console.error('Submit error:', error);
      toast.error('Failed to submit exam');
    } finally {
      setSubmitting(false);
      setExamStarted(false);
    }
  };

  const handleCreateExam = async () => {
    if (!newExam.title || !newExam.course_id) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    setCreating(true);
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API_URL}/api/exams`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newExam)
      });
      
      if (response.ok) {
        const createdExam = await response.json();
        setExams(prev => [...prev, createdExam]);
        setShowCreateDialog(false);
        setNewExam({
          title: '',
          course_id: '',
          duration: 60,
          question_count: 20,
          generation_method: 'ai',
          source_content: '',
          due_date: ''
        });
        toast.success('Exam created successfully!');
      } else {
        toast.error('Failed to create exam');
      }
    } catch (error) {
      console.error('Create exam error:', error);
      toast.error('Failed to create exam');
    } finally {
      setCreating(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Exam Taking View
  if (examStarted && selectedExam && questions.length > 0) {
    const question = questions[currentQuestion];
    
    return (
      <div className="min-h-screen bg-zinc-950 text-white">
        {/* Exam Header */}
        <div className="fixed top-0 left-0 right-0 z-50 bg-zinc-900 border-b border-white/10 p-4">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <div>
              <h1 className="font-bold">{selectedExam.title}</h1>
              <p className="text-sm text-zinc-400">Question {currentQuestion + 1} of {questions.length}</p>
            </div>
            
            <div className="flex items-center gap-6">
              <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${timeLeft < 300 ? 'bg-red-500/20 text-red-400' : 'bg-zinc-800'}`}>
                <Timer className="w-5 h-5" />
                <span className="font-mono text-lg">{formatTime(timeLeft)}</span>
              </div>
              
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${webcamEnabled ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                <Camera className="w-4 h-4" />
                <span className="text-sm">{webcamEnabled ? 'Monitored' : 'Off'}</span>
              </div>
              
              {tabSwitches > 0 && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-yellow-500/20 text-yellow-400">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-sm">{tabSwitches} violations</span>
                </div>
              )}
              
              <Button 
                onClick={handleSubmitExam}
                disabled={submitting}
                className="bg-blue-500 hover:bg-blue-600"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Submit Exam
              </Button>
            </div>
          </div>
        </div>

        {webcamEnabled && (
          <div className="fixed bottom-4 right-4 z-50">
            <video ref={videoRef} autoPlay muted className="w-48 h-36 rounded-lg border-2 border-green-500/50 object-cover" />
          </div>
        )}

        <div className="pt-24 pb-32 px-6">
          <div className="max-w-4xl mx-auto">
            <div className="glass-card p-8">
              <div className="flex items-start gap-4 mb-6">
                <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                  <span className="font-bold text-blue-400">{currentQuestion + 1}</span>
                </div>
                <div>
                  <Badge className="mb-2">{question.type === 'essay' ? 'Essay' : 'Multiple Choice'}</Badge>
                  <h2 className="text-xl font-semibold">{question.question}</h2>
                </div>
              </div>

              {question.type === 'multiple' ? (
                <div className="space-y-3 ml-14">
                  {question.options?.map((option, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleAnswer(question.id, idx)}
                      className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
                        answers[question.id] === idx
                          ? 'border-blue-500 bg-blue-500/10'
                          : 'border-white/10 hover:border-white/20'
                      }`}
                    >
                      <span className="font-medium mr-3">{String.fromCharCode(65 + idx)}.</span>
                      {option}
                    </button>
                  ))}
                </div>
              ) : (
                <div className="ml-14">
                  <Textarea
                    value={answers[question.id] || ''}
                    onChange={(e) => handleAnswer(question.id, e.target.value)}
                    placeholder="Type your answer here..."
                    className="min-h-[200px] bg-zinc-800 border-white/10"
                  />
                </div>
              )}
            </div>

            <div className="flex justify-between mt-6">
              <Button
                variant="outline"
                onClick={() => setCurrentQuestion(Math.max(0, currentQuestion - 1))}
                disabled={currentQuestion === 0}
                className="border-white/10"
              >
                Previous
              </Button>
              
              <div className="flex gap-2">
                {questions.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setCurrentQuestion(idx)}
                    className={`w-8 h-8 rounded-lg text-sm font-medium ${
                      idx === currentQuestion
                        ? 'bg-blue-500 text-white'
                        : answers[questions[idx]?.id] !== undefined
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-zinc-800 text-zinc-400'
                    }`}
                  >
                    {idx + 1}
                  </button>
                ))}
              </div>
              
              <Button
                onClick={() => setCurrentQuestion(Math.min(questions.length - 1, currentQuestion + 1))}
                disabled={currentQuestion === questions.length - 1}
                className="bg-blue-500 hover:bg-blue-600"
              >
                Next
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Results View
  if (result) {
    return (
      <DashboardLayout>
        <div className="p-8">
          <div className="max-w-2xl mx-auto text-center">
            <div className={`w-24 h-24 rounded-full mx-auto mb-6 flex items-center justify-center ${
              result.score >= 70 ? 'bg-green-500/20' : 'bg-red-500/20'
            }`}>
              {result.score >= 70 ? (
                <CheckCircle className="w-12 h-12 text-green-400" />
              ) : (
                <XCircle className="w-12 h-12 text-red-400" />
              )}
            </div>
            
            <h1 className="text-3xl font-bold mb-2">Exam Completed!</h1>
            <p className="text-zinc-400 mb-8">{selectedExam?.title}</p>
            
            <div className="glass-card p-8 mb-6">
              <div className="grid grid-cols-3 gap-6 mb-6">
                <div>
                  <p className="text-4xl font-bold text-blue-400">{result.score}%</p>
                  <p className="text-sm text-zinc-500">Score</p>
                </div>
                <div>
                  <p className="text-4xl font-bold text-violet-400">{result.grade}</p>
                  <p className="text-sm text-zinc-500">Grade</p>
                </div>
                <div>
                  <p className="text-4xl font-bold text-emerald-400">{questions.length}</p>
                  <p className="text-sm text-zinc-500">Questions</p>
                </div>
              </div>
              
              <p className="text-zinc-300">{result.feedback || 'Your exam has been graded by AI.'}</p>
              
              {tabSwitches > 0 && (
                <div className="mt-4 p-4 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
                  <p className="text-yellow-400 font-medium flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    Proctoring Alerts: {tabSwitches} tab switches detected
                  </p>
                </div>
              )}
            </div>
            
            <Button onClick={() => { setResult(null); setSelectedExam(null); setAnswers({}); setQuestions([]); }} className="bg-blue-500 hover:bg-blue-600">
              Back to Exams
            </Button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  // Loading
  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  // Exam List View
  return (
    <DashboardLayout>
      <Header 
        title="Exams"
        subtitle={isTeacher ? "Create and manage exams" : "Take proctored exams"}
      />
      
      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          <div className="glass-card p-6 mb-8 border-yellow-500/30">
            <div className="flex items-start gap-4">
              <Shield className="w-8 h-8 text-yellow-400 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-yellow-400">Exam Proctoring Enabled</h3>
                <p className="text-sm text-zinc-400 mt-1">
                  All exams are monitored with webcam proctoring and tab-switch detection.
                </p>
              </div>
            </div>
          </div>

          {isTeacher && (
            <div className="mb-6">
              <Button 
                onClick={() => setShowCreateDialog(true)}
                className="bg-blue-500 hover:bg-blue-600"
                data-testid="create-exam-btn"
              >
                <Plus className="w-4 h-4 mr-2" />
                Create New Exam
              </Button>
            </div>
          )}

          {exams.length === 0 ? (
            <div className="glass-card p-12 text-center">
              <FileText className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">No Exams Available</h3>
              <p className="text-zinc-500">
                {isTeacher ? 'Create your first exam to get started.' : 'No exams are currently available for your courses.'}
              </p>
            </div>
          ) : (
            <div className="grid gap-4">
              {exams.map((exam) => (
                <div key={exam.id} className="glass-card p-6 hover:border-white/20 transition-all">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                        exam.status === 'completed' ? 'bg-green-500/20' : 'bg-blue-500/20'
                      }`}>
                        {exam.status === 'completed' ? (
                          <Award className="w-6 h-6 text-green-400" />
                        ) : (
                          <FileText className="w-6 h-6 text-blue-400" />
                        )}
                      </div>
                      <div>
                        <h3 className="font-semibold">{exam.title}</h3>
                        <p className="text-sm text-zinc-500">
                          {courses.find(c => c.id === exam.course_id)?.name || 'Course'}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <div className="flex items-center gap-4 text-sm text-zinc-400">
                          <span className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {exam.duration} min
                          </span>
                          <span>{exam.question_count || exam.questions?.length || 0} questions</span>
                        </div>
                        {exam.due_date && (
                          <p className="text-xs text-zinc-500 mt-1">Due: {exam.due_date}</p>
                        )}
                      </div>
                      
                      {exam.status === 'completed' ? (
                        <Badge className="bg-green-500/20 text-green-400">
                          Score: {exam.score}%
                        </Badge>
                      ) : isTeacher ? (
                        <Badge className="bg-violet-500/20 text-violet-400">
                          {exam.questions?.length || 0} Questions
                        </Badge>
                      ) : (
                        <Button 
                          onClick={() => handleStartExam(exam)}
                          className="bg-blue-500 hover:bg-blue-600"
                        >
                          <Play className="w-4 h-4 mr-2" />
                          Start Exam
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Exam Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="bg-zinc-900 border-white/10 max-w-lg">
          <DialogHeader>
            <DialogTitle>Create New Exam</DialogTitle>
            <DialogDescription className="text-zinc-500">
              Create a new exam - questions will be generated by AI
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Label>Exam Title *</Label>
              <Input 
                placeholder="Midterm Exam" 
                value={newExam.title}
                onChange={(e) => setNewExam({...newExam, title: e.target.value})}
                className="bg-zinc-800 border-white/10 mt-1" 
              />
            </div>
            <div>
              <Label>Course *</Label>
              <Select 
                value={newExam.course_id}
                onValueChange={(value) => setNewExam({...newExam, course_id: value})}
              >
                <SelectTrigger className="bg-zinc-800 border-white/10 mt-1">
                  <SelectValue placeholder="Select course" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-800 border-white/10">
                  {courses.map(course => (
                    <SelectItem key={course.id} value={course.id}>{course.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Duration (minutes)</Label>
                <Input 
                  type="number" 
                  value={newExam.duration}
                  onChange={(e) => setNewExam({...newExam, duration: parseInt(e.target.value)})}
                  className="bg-zinc-800 border-white/10 mt-1" 
                />
              </div>
              <div>
                <Label>Number of Questions</Label>
                <Input 
                  type="number" 
                  value={newExam.question_count}
                  onChange={(e) => setNewExam({...newExam, question_count: parseInt(e.target.value)})}
                  className="bg-zinc-800 border-white/10 mt-1" 
                />
              </div>
            </div>
            <div>
              <Label>Question Generation</Label>
              <Select 
                value={newExam.generation_method}
                onValueChange={(value) => setNewExam({...newExam, generation_method: value})}
              >
                <SelectTrigger className="bg-zinc-800 border-white/10 mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-800 border-white/10">
                  <SelectItem value="ai">
                    <span className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4" /> Auto-generate with AI
                    </span>
                  </SelectItem>
                  <SelectItem value="upload">
                    <span className="flex items-center gap-2">
                      <Upload className="w-4 h-4" /> Generate from uploaded content
                    </span>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            {newExam.generation_method === 'upload' && (
              <div>
                <Label>Source Content (paste text or upload)</Label>
                <Textarea
                  placeholder="Paste content from a book or document..."
                  value={newExam.source_content}
                  onChange={(e) => setNewExam({...newExam, source_content: e.target.value})}
                  className="bg-zinc-800 border-white/10 mt-1 min-h-[100px]"
                />
              </div>
            )}
            <div>
              <Label>Due Date</Label>
              <Input 
                type="date" 
                value={newExam.due_date}
                onChange={(e) => setNewExam({...newExam, due_date: e.target.value})}
                className="bg-zinc-800 border-white/10 mt-1" 
              />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="ghost" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
              <Button 
                onClick={handleCreateExam}
                disabled={creating}
                className="bg-blue-500 hover:bg-blue-600"
              >
                {creating ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Create Exam
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Assessment Access Restriction Modal */}
      {paymentLockInfo && (
        <Dialog open={!!paymentLockInfo} onOpenChange={() => setPaymentLockInfo(null)}>
          <DialogContent className="bg-zinc-900 border-amber-500/40 text-white max-w-md">
            <DialogHeader>
              <div className="w-14 h-14 rounded-full bg-amber-500/20 border border-amber-500/40 flex items-center justify-center mx-auto mb-3">
                <Lock className="w-7 h-7 text-amber-400" />
              </div>
              <DialogTitle className="text-xl text-center text-amber-400 font-bold">
                Assessment Access Restricted
              </DialogTitle>
              <DialogDescription className="text-zinc-300 text-center mt-2 leading-relaxed">
                {paymentLockInfo.message}
              </DialogDescription>
            </DialogHeader>

            {paymentLockInfo.amountRemaining != null && (
              <div className="my-4 p-4 bg-zinc-800/80 rounded-xl text-center border border-white/10">
                <span className="text-xs uppercase tracking-wider text-zinc-400 block mb-1">Outstanding Balance</span>
                <span className="text-3xl font-extrabold text-amber-400">
                  ${Number(paymentLockInfo.amountRemaining).toFixed(2)}
                </span>
                <p className="text-xs text-zinc-400 mt-2">
                  Once settled, full examination and assignment privileges unlock automatically.
                </p>
              </div>
            )}

            <div className="flex gap-3 mt-4">
              <Button
                variant="outline"
                className="flex-1 border-white/20 text-zinc-300 hover:bg-white/5"
                onClick={() => setPaymentLockInfo(null)}
              >
                Close
              </Button>
              <Button
                className="flex-1 bg-amber-500 hover:bg-amber-600 text-black font-semibold shadow-lg shadow-amber-500/20"
                onClick={() => {
                  const courseId = paymentLockInfo.courseId;
                  setPaymentLockInfo(null);
                  navigate(`/payment?course_id=${courseId || ''}`);
                }}
              >
                <CreditCard className="w-4 h-4 mr-2" />
                Pay Balance
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </DashboardLayout>
  );
}
