import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { 
  Brain, 
  CheckCircle, 
  XCircle, 
  ArrowRight, 
  Trophy,
  Clock,
  Sparkles,
  X
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

export default function PopupQuiz({ 
  isOpen, 
  onClose, 
  lessonId, 
  courseId, 
  lessonTitle,
  onComplete 
}) {
  const [loading, setLoading] = useState(true);
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [score, setScore] = useState(0);
  const [completed, setCompleted] = useState(false);
  const [timeLeft, setTimeLeft] = useState(30);

  useEffect(() => {
    if (isOpen && lessonId) {
      loadQuizQuestions();
    }
  }, [isOpen, lessonId]);

  useEffect(() => {
    let timer;
    if (isOpen && !showResult && !completed && timeLeft > 0) {
      timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            handleTimeout();
            return 30;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isOpen, showResult, completed, timeLeft]);

  const loadQuizQuestions = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(
        `${API}/api/lessons/${lessonId}/quiz-questions?count=3`,
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        if (data.questions && data.questions.length > 0) {
          setQuestions(data.questions);
        } else {
          // Generate default questions if none exist
          setQuestions([
            {
              id: '1',
              question: `Quick check: What is the main concept covered in "${lessonTitle}"?`,
              options: [
                'Understanding the basics',
                'Advanced implementation',
                'Testing and debugging',
                'Documentation practices'
              ],
              correct_answer: 0
            }
          ]);
        }
      } else {
        // Fallback questions
        setQuestions([
          {
            id: '1',
            question: 'Are you following the lesson content?',
            options: ['Yes, completely', 'Mostly', 'Need to review', 'Just started'],
            correct_answer: 0
          }
        ]);
      }
    } catch (error) {
      console.error('Failed to load quiz:', error);
      setQuestions([
        {
          id: '1',
          question: 'Quick engagement check - how is your learning going?',
          options: ['Great!', 'Good', 'Need help', 'Taking a break'],
          correct_answer: 0
        }
      ]);
    } finally {
      setLoading(false);
      setTimeLeft(30);
    }
  };

  const handleTimeout = () => {
    if (!showResult) {
      setShowResult(true);
      setIsCorrect(false);
      toast.info("Time's up! Moving to next question.");
    }
  };

  const handleAnswerSelect = (index) => {
    if (showResult) return;
    setSelectedAnswer(index);
  };

  const handleSubmitAnswer = () => {
    if (selectedAnswer === null) {
      toast.error('Please select an answer');
      return;
    }

    const currentQuestion = questions[currentIndex];
    const correct = selectedAnswer === currentQuestion.correct_answer;
    setIsCorrect(correct);
    setShowResult(true);
    
    if (correct) {
      setScore(prev => prev + 1);
    }
  };

  const handleNextQuestion = () => {
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(prev => prev + 1);
      setSelectedAnswer(null);
      setShowResult(false);
      setTimeLeft(30);
    } else {
      setCompleted(true);
      // Save quiz result
      saveQuizResult();
    }
  };

  const saveQuizResult = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      await fetch(`${API}/api/lessons/${lessonId}/quiz-result`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          course_id: courseId,
          score: score,
          total: questions.length,
          passed: score >= questions.length * 0.6
        })
      });
    } catch (error) {
      console.error('Failed to save quiz result:', error);
    }
  };

  const handleClose = () => {
    if (completed && onComplete) {
      onComplete(score, questions.length);
    }
    // Reset state
    setCurrentIndex(0);
    setSelectedAnswer(null);
    setShowResult(false);
    setScore(0);
    setCompleted(false);
    setTimeLeft(30);
    onClose();
  };

  if (!isOpen) return null;

  const currentQuestion = questions[currentIndex];
  const progress = ((currentIndex + 1) / questions.length) * 100;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-lg mx-4 glass-card p-6 animate-scaleIn">
        {/* Close button */}
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 text-zinc-500 hover:text-white transition-colors"
          data-testid="close-quiz-btn"
        >
          <X className="w-5 h-5" />
        </button>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-12">
            <Brain className="w-12 h-12 text-violet-400 animate-pulse mb-4" />
            <p className="text-zinc-400">Loading quiz...</p>
          </div>
        ) : completed ? (
          /* Completion Screen */
          <div className="text-center py-8">
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center">
              <Trophy className="w-10 h-10 text-white" />
            </div>
            <h3 className="text-2xl font-bold mb-2">Quiz Complete!</h3>
            <p className="text-zinc-400 mb-6">
              You scored {score} out of {questions.length}
            </p>
            
            <div className="flex justify-center gap-2 mb-6">
              {Array.from({ length: questions.length }).map((_, i) => (
                <div
                  key={i}
                  className={`w-3 h-3 rounded-full ${
                    i < score ? 'bg-emerald-500' : 'bg-zinc-600'
                  }`}
                />
              ))}
            </div>

            {score >= questions.length * 0.6 ? (
              <Badge className="bg-emerald-500/20 text-emerald-400 mb-6">
                <CheckCircle className="w-4 h-4 mr-1" />
                Great job! Keep learning!
              </Badge>
            ) : (
              <Badge className="bg-amber-500/20 text-amber-400 mb-6">
                <Sparkles className="w-4 h-4 mr-1" />
                Review the lesson for better understanding
              </Badge>
            )}

            <Button
              onClick={handleClose}
              className="w-full bg-violet-500 hover:bg-violet-600"
              data-testid="continue-learning-btn"
            >
              Continue Learning
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        ) : (
          /* Question Screen */
          <>
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2">
                <Brain className="w-5 h-5 text-violet-400" />
                <span className="font-semibold">Quick Quiz</span>
              </div>
              <div className="flex items-center gap-4">
                <Badge variant="outline" className="border-white/10">
                  {currentIndex + 1} / {questions.length}
                </Badge>
                <div className={`flex items-center gap-1 ${timeLeft <= 10 ? 'text-red-400' : 'text-zinc-400'}`}>
                  <Clock className="w-4 h-4" />
                  <span className="text-sm font-mono">{timeLeft}s</span>
                </div>
              </div>
            </div>

            {/* Progress */}
            <Progress value={progress} className="h-1 mb-6" />

            {/* Question */}
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-4" data-testid="quiz-question">
                {currentQuestion?.question}
              </h3>

              <div className="space-y-3">
                {currentQuestion?.options?.map((option, index) => (
                  <button
                    key={index}
                    onClick={() => handleAnswerSelect(index)}
                    disabled={showResult}
                    data-testid={`quiz-option-${index}`}
                    className={`w-full p-4 rounded-xl text-left transition-all border ${
                      showResult
                        ? index === currentQuestion.correct_answer
                          ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400'
                          : index === selectedAnswer
                            ? 'bg-red-500/20 border-red-500/50 text-red-400'
                            : 'bg-zinc-800/50 border-white/5 text-zinc-500'
                        : selectedAnswer === index
                          ? 'bg-violet-500/20 border-violet-500/50'
                          : 'bg-zinc-800/50 border-white/10 hover:border-white/20'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                        showResult
                          ? index === currentQuestion.correct_answer
                            ? 'bg-emerald-500/30 text-emerald-400'
                            : index === selectedAnswer
                              ? 'bg-red-500/30 text-red-400'
                              : 'bg-zinc-700 text-zinc-500'
                          : selectedAnswer === index
                            ? 'bg-violet-500/30 text-violet-400'
                            : 'bg-zinc-700 text-zinc-400'
                      }`}>
                        {String.fromCharCode(65 + index)}
                      </div>
                      <span>{option}</span>
                      {showResult && index === currentQuestion.correct_answer && (
                        <CheckCircle className="w-5 h-5 ml-auto text-emerald-400" />
                      )}
                      {showResult && index === selectedAnswer && index !== currentQuestion.correct_answer && (
                        <XCircle className="w-5 h-5 ml-auto text-red-400" />
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Result Message */}
            {showResult && (
              <div className={`p-4 rounded-xl mb-4 ${
                isCorrect 
                  ? 'bg-emerald-500/10 border border-emerald-500/30' 
                  : 'bg-red-500/10 border border-red-500/30'
              }`}>
                <div className="flex items-center gap-2">
                  {isCorrect ? (
                    <>
                      <CheckCircle className="w-5 h-5 text-emerald-400" />
                      <span className="text-emerald-400 font-medium">Correct!</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="w-5 h-5 text-red-400" />
                      <span className="text-red-400 font-medium">Not quite right</span>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              {!showResult ? (
                <Button
                  onClick={handleSubmitAnswer}
                  disabled={selectedAnswer === null}
                  className="flex-1 bg-violet-500 hover:bg-violet-600"
                  data-testid="submit-answer-btn"
                >
                  Submit Answer
                </Button>
              ) : (
                <Button
                  onClick={handleNextQuestion}
                  className="flex-1 bg-violet-500 hover:bg-violet-600"
                  data-testid="next-question-btn"
                >
                  {currentIndex < questions.length - 1 ? 'Next Question' : 'See Results'}
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
