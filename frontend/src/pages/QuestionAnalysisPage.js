import React, { useState, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { analyzeQuestion, evaluateAnswer, generateTTS } from '../services/api';
import { 
  HelpCircle,
  Brain,
  CheckCircle,
  AlertCircle,
  Lightbulb,
  Target,
  RefreshCw,
  Send,
  Volume2,
  BookOpen,
  TrendingUp,
  Layers,
  Mic,
  MicOff
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';

const BLOOMS_LEVELS = {
  'Remember': { color: 'bg-red-500', description: 'Recall facts and basic concepts' },
  'Understand': { color: 'bg-orange-500', description: 'Explain ideas or concepts' },
  'Apply': { color: 'bg-yellow-500', description: 'Use information in new situations' },
  'Analyze': { color: 'bg-green-500', description: 'Draw connections among ideas' },
  'Evaluate': { color: 'bg-blue-500', description: 'Justify a decision or position' },
  'Create': { color: 'bg-purple-500', description: 'Produce new or original work' },
};

export default function QuestionAnalysisPage() {
  const { user } = useAuth();
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [subject, setSubject] = useState('general');
  const [analyzing, setAnalyzing] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [isRecordingQuestion, setIsRecordingQuestion] = useState(false);
  const [isRecordingAnswer, setIsRecordingAnswer] = useState(false);
  const questionRecognitionRef = useRef(null);
  const answerRecognitionRef = useRef(null);

  const startVoiceInput = useCallback((target) => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      toast.error('Voice input not supported in this browser. Try Chrome or Edge.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    if (target === 'question') {
      questionRecognitionRef.current = recognition;
      setIsRecordingQuestion(true);
    } else {
      answerRecognitionRef.current = recognition;
      setIsRecordingAnswer(true);
    }

    let finalTranscript = '';

    recognition.onresult = (event) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript + ' ';
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      if (target === 'question') {
        setQuestion(prev => {
          const base = prev.endsWith(' ') ? prev : (prev ? prev + ' ' : '');
          return finalTranscript + interim;
        });
      } else {
        setAnswer(prev => {
          const base = prev.endsWith(' ') ? prev : (prev ? prev + ' ' : '');
          return finalTranscript + interim;
        });
      }
    };

    recognition.onerror = (event) => {
      if (event.error === 'no-speech') {
        toast.info('No speech detected. Try again.');
      } else if (event.error !== 'aborted') {
        toast.error('Voice recognition error: ' + event.error);
      }
      if (target === 'question') setIsRecordingQuestion(false);
      else setIsRecordingAnswer(false);
    };

    recognition.onend = () => {
      if (target === 'question') setIsRecordingQuestion(false);
      else setIsRecordingAnswer(false);
    };

    try {
      recognition.start();
      toast.success('Listening... Speak now');
    } catch (e) {
      toast.error('Could not start voice recognition. Please check microphone permissions.');
      if (target === 'question') setIsRecordingQuestion(false);
      else setIsRecordingAnswer(false);
    }
  }, []);

  const stopVoiceInput = useCallback((target) => {
    if (target === 'question' && questionRecognitionRef.current) {
      questionRecognitionRef.current.stop();
      questionRecognitionRef.current = null;
      setIsRecordingQuestion(false);
    } else if (target === 'answer' && answerRecognitionRef.current) {
      answerRecognitionRef.current.stop();
      answerRecognitionRef.current = null;
      setIsRecordingAnswer(false);
    }
  }, []);

  const handleAnalyzeQuestion = async () => {
    if (!question.trim()) {
      toast.error('Please enter a question to analyze');
      return;
    }

    setAnalyzing(true);
    setAnalysis(null);
    setEvaluation(null);
    try {
      const result = await analyzeQuestion(question, subject);
      setAnalysis(result);
      toast.success('Question analyzed!');
    } catch (error) {
      console.error('Analysis failed:', error);
      toast.error('Failed to analyze question');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleEvaluateAnswer = async () => {
    if (!question.trim() || !answer.trim()) {
      toast.error('Please provide both question and answer');
      return;
    }

    setEvaluating(true);
    try {
      const result = await evaluateAnswer(question, answer, subject);
      setEvaluation(result);
      toast.success('Answer evaluated!');
    } catch (error) {
      console.error('Evaluation failed:', error);
      toast.error('Failed to evaluate answer');
    } finally {
      setEvaluating(false);
    }
  };

  const handlePlayAudio = async (text) => {
    try {
      const result = await generateTTS(text, 'nova');
      if (result.audio_url) {
        const audio = new Audio(result.audio_url);
        await audio.play();
      }
    } catch (error) {
      toast.error('Failed to play audio');
    }
  };

  const getBloomsColor = (level) => {
    return BLOOMS_LEVELS[level]?.color || 'bg-zinc-500';
  };

  return (
    <DashboardLayout>
      <Header 
        title="Question Gap Analysis"
        subtitle="Create questions and analyze them using Bloom's Taxonomy"
      />
      
      <div className="p-8">
        <div className="max-w-5xl mx-auto">
          {/* Info Banner */}
          <div className="glass-card p-6 mb-8 bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border-cyan-500/20">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-cyan-500/20 flex items-center justify-center">
                <HelpCircle className="w-6 h-6 text-cyan-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-1">From Consumer to Creator</h3>
                <p className="text-zinc-400 text-sm">
                  Write your own questions about any topic. The AI analyzes coverage level using 
                  Bloom's Taxonomy, identifies gaps, detects misconceptions, and evaluates your understanding.
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Input Section */}
            <div className="space-y-6">
              <div className="glass-card p-6 space-y-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <Brain className="w-5 h-5 text-cyan-400" />
                  Create Your Question
                </h3>

                <div className="space-y-2">
                  <Label>Subject Area</Label>
                  <Input
                    placeholder="e.g., Biology, Mathematics, History"
                    value={subject}
                    onChange={(e) => setSubject(e.target.value)}
                    className="bg-zinc-800 border-white/10"
                  />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label>Your Question</Label>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => isRecordingQuestion ? stopVoiceInput('question') : startVoiceInput('question')}
                      className={isRecordingQuestion ? 'text-red-400 animate-pulse' : 'text-zinc-400 hover:text-cyan-400'}
                      data-testid="voice-question-btn"
                    >
                      {isRecordingQuestion ? <MicOff className="w-4 h-4 mr-1" /> : <Mic className="w-4 h-4 mr-1" />}
                      {isRecordingQuestion ? 'Stop' : 'Voice'}
                    </Button>
                  </div>
                  <Textarea
                    placeholder="Write or speak a question about any topic you're learning..."
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    className="min-h-[120px] bg-zinc-800 border-white/10"
                    data-testid="question-input"
                  />
                </div>

                <Button
                  onClick={handleAnalyzeQuestion}
                  disabled={!question.trim() || analyzing}
                  className="w-full bg-cyan-500 hover:bg-cyan-600"
                  data-testid="analyze-question-btn"
                >
                  {analyzing ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Brain className="w-4 h-4 mr-2" />
                      Analyze Question
                    </>
                  )}
                </Button>
              </div>

              {/* Answer Section */}
              {analysis && (
                <div className="glass-card p-6 space-y-4">
                  <h3 className="font-semibold flex items-center gap-2">
                    <Target className="w-5 h-5 text-emerald-400" />
                    Answer Your Question
                  </h3>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>Your Answer</Label>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => isRecordingAnswer ? stopVoiceInput('answer') : startVoiceInput('answer')}
                        className={isRecordingAnswer ? 'text-red-400 animate-pulse' : 'text-zinc-400 hover:text-emerald-400'}
                        data-testid="voice-answer-btn"
                      >
                        {isRecordingAnswer ? <MicOff className="w-4 h-4 mr-1" /> : <Mic className="w-4 h-4 mr-1" />}
                        {isRecordingAnswer ? 'Stop' : 'Voice'}
                      </Button>
                    </div>
                    <Textarea
                      placeholder="Write or speak your answer..."
                      value={answer}
                      onChange={(e) => setAnswer(e.target.value)}
                      className="min-h-[150px] bg-zinc-800 border-white/10"
                      data-testid="answer-input"
                    />
                  </div>

                  <Button
                    onClick={handleEvaluateAnswer}
                    disabled={!answer.trim() || evaluating}
                    className="w-full bg-emerald-500 hover:bg-emerald-600"
                    data-testid="evaluate-answer-btn"
                  >
                    {evaluating ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Evaluating...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-4 h-4 mr-2" />
                        Evaluate Answer
                      </>
                    )}
                  </Button>
                </div>
              )}
            </div>

            {/* Results Section */}
            <div className="space-y-6">
              {/* Question Analysis Results */}
              {analysis && (
                <div className="glass-card p-6 space-y-4">
                  <h3 className="font-semibold flex items-center gap-2">
                    <Layers className="w-5 h-5 text-violet-400" />
                    Question Analysis
                  </h3>

                  {/* Bloom's Level */}
                  <div className="p-4 rounded-lg bg-zinc-800/50">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-zinc-400">Bloom's Taxonomy Level</span>
                      <Badge className={`${getBloomsColor(analysis.blooms_level)} text-white`}>
                        {analysis.blooms_level || 'Unknown'}
                      </Badge>
                    </div>
                    <p className="text-xs text-zinc-500">
                      {BLOOMS_LEVELS[analysis.blooms_level]?.description || 'Level description'}
                    </p>
                    {analysis.blooms_score && (
                      <div className="mt-2">
                        <Progress value={(analysis.blooms_score / 6) * 100} className="h-2" />
                        <span className="text-xs text-zinc-500">Depth: {analysis.blooms_score}/6</span>
                      </div>
                    )}
                  </div>

                  {/* Coverage */}
                  {analysis.coverage && (
                    <div className="p-4 rounded-lg bg-zinc-800/50">
                      <div className="text-sm font-medium mb-2">Coverage Analysis</div>
                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="p-2 rounded bg-zinc-700/50">
                          <div className="text-xs text-zinc-500">Topic</div>
                          <div className="text-sm truncate">{analysis.coverage.topic}</div>
                        </div>
                        <div className="p-2 rounded bg-zinc-700/50">
                          <div className="text-xs text-zinc-500">Depth</div>
                          <div className="text-sm capitalize">{analysis.coverage.depth}</div>
                        </div>
                        <div className="p-2 rounded bg-zinc-700/50">
                          <div className="text-xs text-zinc-500">Breadth</div>
                          <div className="text-sm capitalize">{analysis.coverage.breadth}</div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Clarity Score */}
                  {analysis.clarity_score && (
                    <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50">
                      <span className="text-sm">Question Clarity</span>
                      <div className="flex items-center gap-2">
                        <Progress value={analysis.clarity_score * 10} className="w-20 h-2" />
                        <span className="text-sm font-medium">{analysis.clarity_score}/10</span>
                      </div>
                    </div>
                  )}

                  {/* Potential Misconceptions */}
                  {analysis.potential_misconceptions?.length > 0 && (
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-amber-400 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4" />
                        Potential Misconceptions
                      </div>
                      <ul className="space-y-1">
                        {analysis.potential_misconceptions.map((m, i) => (
                          <li key={i} className="text-sm text-zinc-300 flex items-start gap-2 p-2 rounded bg-amber-500/10">
                            <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                            {m}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Suggestions */}
                  {analysis.suggestions?.length > 0 && (
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-cyan-400 flex items-center gap-2">
                        <Lightbulb className="w-4 h-4" />
                        Suggestions to Improve
                      </div>
                      <ul className="space-y-1">
                        {analysis.suggestions.map((s, i) => (
                          <li key={i} className="text-sm text-zinc-300 flex items-start gap-2">
                            <TrendingUp className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
                            {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Related Topics */}
                  {analysis.related_topics?.length > 0 && (
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-zinc-400">Related Topics to Explore</div>
                      <div className="flex flex-wrap gap-2">
                        {analysis.related_topics.map((topic, i) => (
                          <Badge key={i} variant="outline" className="border-white/10">
                            {topic}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Answer Evaluation Results */}
              {evaluation && (
                <div className="glass-card p-6 space-y-4">
                  <h3 className="font-semibold flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                    Answer Evaluation
                  </h3>

                  {/* Scores */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-lg bg-zinc-800/50 text-center">
                      <div className="text-3xl font-bold text-emerald-400">
                        {evaluation.understanding_score || '--'}/10
                      </div>
                      <div className="text-xs text-zinc-500">Understanding</div>
                    </div>
                    <div className="p-4 rounded-lg bg-zinc-800/50 text-center">
                      <div className="text-3xl font-bold text-cyan-400">
                        {evaluation.completeness_score || '--'}/10
                      </div>
                      <div className="text-xs text-zinc-500">Completeness</div>
                    </div>
                  </div>

                  {/* Correct/Incorrect */}
                  <div className={`p-4 rounded-lg ${evaluation.correct ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-red-500/10 border border-red-500/20'}`}>
                    <div className="flex items-center gap-2">
                      {evaluation.correct ? (
                        <CheckCircle className="w-5 h-5 text-emerald-400" />
                      ) : (
                        <AlertCircle className="w-5 h-5 text-red-400" />
                      )}
                      <span className={evaluation.correct ? 'text-emerald-400' : 'text-red-400'}>
                        {evaluation.correct ? 'Correct Understanding!' : 'Needs Improvement'}
                      </span>
                    </div>
                  </div>

                  {/* Feedback */}
                  {evaluation.feedback && (
                    <div className="p-4 rounded-lg bg-zinc-800/50">
                      <div className="text-sm font-medium mb-2">Feedback</div>
                      <p className="text-sm text-zinc-300">{evaluation.feedback}</p>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handlePlayAudio(evaluation.feedback)}
                        className="mt-2"
                      >
                        <Volume2 className="w-4 h-4 mr-1" />
                        Listen
                      </Button>
                    </div>
                  )}

                  {/* Misunderstandings */}
                  {evaluation.misunderstandings?.length > 0 && (
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-amber-400">Misunderstandings Detected</div>
                      <ul className="space-y-1">
                        {evaluation.misunderstandings.map((m, i) => (
                          <li key={i} className="text-sm text-zinc-300 flex items-start gap-2 p-2 rounded bg-amber-500/10">
                            <AlertCircle className="w-4 h-4 text-amber-400 mt-0.5 flex-shrink-0" />
                            {m}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Improvement Suggestions */}
                  {evaluation.improvement_suggestions?.length > 0 && (
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-cyan-400">How to Improve</div>
                      <ul className="space-y-1">
                        {evaluation.improvement_suggestions.map((s, i) => (
                          <li key={i} className="text-sm text-zinc-300 flex items-start gap-2">
                            <TrendingUp className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
                            {s}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Empty State */}
              {!analysis && !evaluation && (
                <div className="glass-card p-12 text-center">
                  <HelpCircle className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">Create Your First Question</h3>
                  <p className="text-zinc-500 text-sm">
                    Write a question about any topic you're learning. The AI will analyze 
                    its depth, identify gaps, and help you understand better.
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
