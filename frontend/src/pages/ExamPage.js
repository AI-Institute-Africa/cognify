import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { 
  FileText, Clock, AlertTriangle, CheckCircle, XCircle, 
  Play, Pause, Camera, Eye, EyeOff, Shield, Award,
  Plus, Loader2, Timer, Send, ChevronRight, BookOpen
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

// Mock exams for demo
const MOCK_EXAMS = [
  { id: '1', title: 'Physics Fundamentals Midterm', course: 'Physics Fundamentals', duration: 60, questions: 20, status: 'available', dueDate: '2026-02-01' },
  { id: '2', title: 'Math Final Exam', course: 'Advanced Mathematics', duration: 90, questions: 30, status: 'available', dueDate: '2026-02-15' },
  { id: '3', title: 'Chemistry Quiz 1', course: 'Chemistry Basics', duration: 30, questions: 15, status: 'completed', score: 85, dueDate: '2026-01-15' },
];

export default function ExamPage() {
  const { user } = useAuth();
  const [exams, setExams] = useState(MOCK_EXAMS);
  const [selectedExam, setSelectedExam] = useState(null);
  const [examStarted, setExamStarted] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState({});
  const [timeLeft, setTimeLeft] = useState(0);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [generating, setGenerating] = useState(false);
  
  // Proctoring state
  const [webcamEnabled, setWebcamEnabled] = useState(false);
  const [tabSwitches, setTabSwitches] = useState(0);
  const [warnings, setWarnings] = useState([]);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const isTeacher = user?.role === 'teacher' || user?.role === 'admin';

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
        setWarnings(prev => [...prev, { time: new Date(), type: 'tab_switch', message: 'Tab switch detected' }]);
        toast.warning('Warning: Tab switch detected! This will be reported.');
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [examStarted]);

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
      toast.error('Could not access webcam. Please allow camera access.');
    }
  };

  const stopWebcam = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      setWebcamEnabled(false);
    }
  };

  const handleStartExam = async (exam) => {
    setSelectedExam(exam);
    setGenerating(true);
    
    try {
      // Generate questions via AI
      const token = localStorage.getItem('eduos_token');
      const response = await fetch(`${API_URL}/api/exam/generate?topic=${encodeURIComponent(exam.course)}&count=${exam.questions}&difficulty=medium`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setQuestions(data.questions || generateMockQuestions(exam));
      } else {
        setQuestions(generateMockQuestions(exam));
      }
    } catch (error) {
      setQuestions(generateMockQuestions(exam));
    }
    
    setGenerating(false);
    setTimeLeft(exam.duration * 60);
    setExamStarted(true);
    startWebcam();
  };

  const generateMockQuestions = (exam) => {
    const subjects = {
      'Physics Fundamentals': [
        { id: 1, question: "What is Newton's First Law of Motion?", type: 'multiple', options: ['Law of Inertia', 'Law of Acceleration', 'Law of Action-Reaction', 'Law of Gravity'], correct: 0 },
        { id: 2, question: "What is the SI unit of force?", type: 'multiple', options: ['Joule', 'Newton', 'Watt', 'Pascal'], correct: 1 },
        { id: 3, question: "Explain the concept of momentum in your own words.", type: 'essay' },
        { id: 4, question: "What is the formula for kinetic energy?", type: 'multiple', options: ['E = mc²', 'KE = ½mv²', 'F = ma', 'P = mv'], correct: 1 },
        { id: 5, question: "What happens to the velocity of an object in free fall? (ignoring air resistance)", type: 'multiple', options: ['Decreases', 'Stays constant', 'Increases', 'Becomes zero'], correct: 2 },
      ],
      'Advanced Mathematics': [
        { id: 1, question: "What is the derivative of x²?", type: 'multiple', options: ['x', '2x', '2', 'x²'], correct: 1 },
        { id: 2, question: "What is the integral of 2x?", type: 'multiple', options: ['x²', 'x² + C', '2x²', '2x + C'], correct: 1 },
        { id: 3, question: "Explain the Fundamental Theorem of Calculus.", type: 'essay' },
        { id: 4, question: "What is sin(90°)?", type: 'multiple', options: ['0', '1', '-1', '0.5'], correct: 1 },
        { id: 5, question: "What is the limit of 1/x as x approaches infinity?", type: 'multiple', options: ['Infinity', '1', '0', 'Undefined'], correct: 2 },
      ],
    };
    
    const courseQuestions = subjects[exam.course] || subjects['Physics Fundamentals'];
    return courseQuestions.slice(0, Math.min(exam.questions, courseQuestions.length));
  };

  const handleAnswer = (questionId, answer) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }));
  };

  const handleSubmitExam = async () => {
    setSubmitting(true);
    stopWebcam();
    
    try {
      // Calculate score locally for demo
      let correctCount = 0;
      questions.forEach(q => {
        if (q.type === 'multiple' && answers[q.id] === q.correct) {
          correctCount++;
        } else if (q.type === 'essay' && answers[q.id]?.length > 20) {
          correctCount += 0.8; // Partial credit for essays
        }
      });
      
      const score = Math.round((correctCount / questions.length) * 100);
      
      // Try to get AI evaluation
      const token = localStorage.getItem('eduos_token');
      try {
        const response = await fetch(`${API_URL}/api/exam/evaluate`, {
          method: 'POST',
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            exam_id: selectedExam.id,
            answers,
            questions,
            time_taken: selectedExam.duration * 60 - timeLeft,
            tab_switches: tabSwitches,
            warnings
          })
        });

        if (response.ok) {
          const data = await response.json();
          setResult(data);
        } else {
          setResult({
            score,
            grade: score >= 90 ? 'A' : score >= 80 ? 'B' : score >= 70 ? 'C' : score >= 60 ? 'D' : 'F',
            feedback: 'Your exam has been evaluated. Review your answers for areas of improvement.',
            violations: tabSwitches > 0 ? [`${tabSwitches} tab switches detected`] : []
          });
        }
      } catch {
        setResult({
          score,
          grade: score >= 90 ? 'A' : score >= 80 ? 'B' : score >= 70 ? 'C' : score >= 60 ? 'D' : 'F',
          feedback: 'Your exam has been evaluated. Review your answers for areas of improvement.',
          violations: tabSwitches > 0 ? [`${tabSwitches} tab switches detected`] : []
        });
      }
    } finally {
      setSubmitting(false);
      setExamStarted(false);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Exam Taking View
  if (examStarted && selectedExam) {
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
              {/* Timer */}
              <div className={`flex items-center gap-2 px-4 py-2 rounded-lg ${timeLeft < 300 ? 'bg-red-500/20 text-red-400' : 'bg-zinc-800'}`}>
                <Timer className="w-5 h-5" />
                <span className="font-mono text-lg">{formatTime(timeLeft)}</span>
              </div>
              
              {/* Webcam indicator */}
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${webcamEnabled ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                <Camera className="w-4 h-4" />
                <span className="text-sm">{webcamEnabled ? 'Monitored' : 'Off'}</span>
              </div>
              
              {/* Tab switches warning */}
              {tabSwitches > 0 && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-yellow-500/20 text-yellow-400">
                  <AlertTriangle className="w-4 h-4" />
                  <span className="text-sm">{tabSwitches} violations</span>
                </div>
              )}
              
              <Button 
                onClick={handleSubmitExam}
                className="bg-blue-500 hover:bg-blue-600"
                data-testid="submit-exam-btn"
              >
                Submit Exam
              </Button>
            </div>
          </div>
        </div>

        {/* Webcam Preview */}
        {webcamEnabled && (
          <div className="fixed bottom-4 right-4 z-50">
            <video 
              ref={videoRef} 
              autoPlay 
              muted 
              className="w-48 h-36 rounded-lg border-2 border-green-500/50 object-cover"
            />
          </div>
        )}

        {/* Question Content */}
        <div className="pt-24 pb-32 px-6">
          <div className="max-w-4xl mx-auto">
            {question && (
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
                    {question.options.map((option, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleAnswer(question.id, idx)}
                        className={`w-full text-left p-4 rounded-xl border-2 transition-all ${
                          answers[question.id] === idx
                            ? 'border-blue-500 bg-blue-500/10'
                            : 'border-white/10 hover:border-white/20'
                        }`}
                        data-testid={`option-${idx}`}
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
                      data-testid="essay-answer"
                    />
                  </div>
                )}
              </div>
            )}

            {/* Navigation */}
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
              
              <p className="text-zinc-300">{result.feedback}</p>
              
              {result.violations?.length > 0 && (
                <div className="mt-4 p-4 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
                  <p className="text-yellow-400 font-medium flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    Proctoring Alerts
                  </p>
                  <ul className="text-sm text-zinc-400 mt-2">
                    {result.violations.map((v, i) => <li key={i}>• {v}</li>)}
                  </ul>
                </div>
              )}
            </div>
            
            <Button onClick={() => { setResult(null); setSelectedExam(null); setAnswers({}); }} className="bg-blue-500 hover:bg-blue-600">
              Back to Exams
            </Button>
          </div>
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
          {/* Proctoring Info */}
          <div className="glass-card p-6 mb-8 border-yellow-500/30">
            <div className="flex items-start gap-4">
              <Shield className="w-8 h-8 text-yellow-400 flex-shrink-0" />
              <div>
                <h3 className="font-semibold text-yellow-400">Exam Proctoring Enabled</h3>
                <p className="text-sm text-zinc-400 mt-1">
                  All exams are monitored with webcam proctoring and tab-switch detection. 
                  Ensure you have a working camera and stay on the exam page throughout.
                </p>
              </div>
            </div>
          </div>

          {/* Teacher: Create Exam Button */}
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

          {/* Exam List */}
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
                      <p className="text-sm text-zinc-500">{exam.course}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-6">
                    <div className="text-right">
                      <div className="flex items-center gap-4 text-sm text-zinc-400">
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {exam.duration} min
                        </span>
                        <span>{exam.questions} questions</span>
                      </div>
                      <p className="text-xs text-zinc-500 mt-1">Due: {exam.dueDate}</p>
                    </div>
                    
                    {exam.status === 'completed' ? (
                      <Badge className="bg-green-500/20 text-green-400">
                        Score: {exam.score}%
                      </Badge>
                    ) : (
                      <Button 
                        onClick={() => handleStartExam(exam)}
                        disabled={generating}
                        className="bg-blue-500 hover:bg-blue-600"
                        data-testid={`start-exam-${exam.id}`}
                      >
                        {generating ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Preparing...
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4 mr-2" />
                            Start Exam
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Create Exam Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="bg-zinc-900 border-white/10 max-w-lg">
          <DialogHeader>
            <DialogTitle>Create New Exam</DialogTitle>
            <DialogDescription className="text-zinc-500">
              Create a new exam for your students
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Label>Exam Title</Label>
              <Input placeholder="Midterm Exam" className="bg-zinc-800 border-white/10 mt-1" />
            </div>
            <div>
              <Label>Course</Label>
              <Select>
                <SelectTrigger className="bg-zinc-800 border-white/10 mt-1">
                  <SelectValue placeholder="Select course" />
                </SelectTrigger>
                <SelectContent className="bg-zinc-800 border-white/10">
                  <SelectItem value="physics">Physics Fundamentals</SelectItem>
                  <SelectItem value="math">Advanced Mathematics</SelectItem>
                  <SelectItem value="chemistry">Chemistry Basics</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Duration (minutes)</Label>
                <Input type="number" defaultValue={60} className="bg-zinc-800 border-white/10 mt-1" />
              </div>
              <div>
                <Label>Number of Questions</Label>
                <Input type="number" defaultValue={20} className="bg-zinc-800 border-white/10 mt-1" />
              </div>
            </div>
            <div>
              <Label>Question Generation</Label>
              <Select defaultValue="ai">
                <SelectTrigger className="bg-zinc-800 border-white/10 mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-800 border-white/10">
                  <SelectItem value="ai">Auto-generate with AI</SelectItem>
                  <SelectItem value="manual">Create manually</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="ghost" onClick={() => setShowCreateDialog(false)}>Cancel</Button>
              <Button className="bg-blue-500 hover:bg-blue-600">Create Exam</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
