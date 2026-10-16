import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import axios from 'axios';
import {
  Zap, Upload, FileText, Brain, BookOpen, ClipboardList,
  ChevronDown, ChevronRight, CheckCircle, AlertCircle,
  Layers, RefreshCw, Download, Mic, MicOff, Lightbulb,
  Target, Award, HelpCircle, Star, GraduationCap, Send
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';
import { useVoiceInput } from '../hooks/useVoiceInput';

const API = process.env.REACT_APP_BACKEND_URL;
const getAuth = () => ({ Authorization: `Bearer ${localStorage.getItem('cognify_token')}` });

const DIFFICULTY_COLORS = {
  basic: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  intermediate: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  advanced: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  scenario: 'bg-violet-500/20 text-violet-400 border-violet-500/30',
  mcq: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
};

function QACard({ item, index, type }) {
  const [open, setOpen] = useState(false);
  const [selectedOption, setSelectedOption] = useState(null);

  if (type === 'mcq') {
    return (
      <div className="glass-card p-4 space-y-3" data-testid={`mcq-${index}`}>
        <div className="flex items-start gap-3">
          <span className="text-xs font-bold px-2 py-1 rounded bg-cyan-500/20 text-cyan-400 shrink-0">MCQ {index + 1}</span>
          <p className="text-sm font-medium">{item.q}</p>
        </div>
        <div className="space-y-2 pl-10">
          {(item.options || []).map((opt, oi) => {
            const letter = opt.charAt(0);
            const isCorrect = letter === item.correct;
            const isSelected = selectedOption === letter;
            return (
              <button
                key={oi}
                onClick={() => setSelectedOption(letter)}
                className={`w-full text-left px-3 py-2 text-sm rounded-lg border transition-all ${
                  isSelected
                    ? isCorrect
                      ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300'
                      : 'bg-red-500/20 border-red-500/50 text-red-300'
                    : 'border-white/10 hover:border-white/20 hover:bg-white/5'
                }`}
                data-testid={`mcq-${index}-option-${oi}`}
              >
                {opt}
                {isSelected && isCorrect && <CheckCircle className="w-4 h-4 inline ml-2 text-emerald-400" />}
                {isSelected && !isCorrect && <AlertCircle className="w-4 h-4 inline ml-2 text-red-400" />}
              </button>
            );
          })}
        </div>
        {selectedOption && (
          <div className={`ml-10 p-3 rounded-lg text-sm ${
            selectedOption === item.correct ? 'bg-emerald-500/10 border border-emerald-500/30' : 'bg-red-500/10 border border-red-500/30'
          }`}>
            <p className="font-medium mb-1">
              {selectedOption === item.correct ? 'Correct!' : `Incorrect. The answer is ${item.correct}.`}
            </p>
            <p className="text-zinc-400">{item.explanation}</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="glass-card p-4" data-testid={`qa-${type}-${index}`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-start gap-3 text-left"
      >
        <Badge className={`shrink-0 text-xs ${DIFFICULTY_COLORS[type] || 'bg-zinc-700 text-zinc-300'}`}>
          {type === 'basic' ? 'Basic' : type === 'intermediate' ? 'Intermediate' : type === 'advanced' ? 'Advanced' : 'Scenario'}
        </Badge>
        <p className="text-sm font-medium flex-1">{item.q}</p>
        {open ? <ChevronDown className="w-4 h-4 text-zinc-500 shrink-0 mt-0.5" /> : <ChevronRight className="w-4 h-4 text-zinc-500 shrink-0 mt-0.5" />}
      </button>
      {open && (
        <div className="mt-3 ml-16 p-3 rounded-lg bg-white/5 border border-white/10 text-sm text-zinc-300 leading-relaxed">
          {item.a}
        </div>
      )}
    </div>
  );
}

function FlashcardView({ cards }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);

  if (!cards || cards.length === 0) return null;
  const card = cards[currentIndex];

  return (
    <div className="space-y-4" data-testid="flashcard-view">
      <div className="flex items-center justify-between">
        <span className="text-sm text-zinc-400">Card {currentIndex + 1} of {cards.length}</span>
        <Badge variant="outline" className="text-xs">{card.category || 'General'}</Badge>
      </div>
      <div
        onClick={() => setFlipped(!flipped)}
        className="glass-card p-8 min-h-[200px] flex items-center justify-center cursor-pointer hover:border-violet-500/30 transition-all"
        data-testid="flashcard-active"
      >
        <div className="text-center">
          <p className="text-xs text-zinc-500 mb-2">{flipped ? 'ANSWER' : 'QUESTION'}</p>
          <p className={`text-lg font-medium ${flipped ? 'text-emerald-300' : 'text-white'}`}>
            {flipped ? card.back : card.front}
          </p>
          <p className="text-xs text-zinc-600 mt-4">Click to {flipped ? 'see question' : 'reveal answer'}</p>
        </div>
      </div>
      <div className="flex gap-2 justify-center">
        <Button
          variant="outline" size="sm"
          onClick={() => { setCurrentIndex(Math.max(0, currentIndex - 1)); setFlipped(false); }}
          disabled={currentIndex === 0}
          className="border-white/10"
        >Previous</Button>
        <Button
          variant="outline" size="sm"
          onClick={() => { setCurrentIndex(Math.min(cards.length - 1, currentIndex + 1)); setFlipped(false); }}
          disabled={currentIndex === cards.length - 1}
          className="border-white/10"
        >Next</Button>
      </div>
    </div>
  );
}

export default function AITrainingEnginePage() {
  const { user } = useAuth();
  const [content, setContent] = useState('');
  const [topic, setTopic] = useState('');
  const [numQuestions, setNumQuestions] = useState(20);
  const [difficulty, setDifficulty] = useState('mixed');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('questions');
  const [generatingType, setGeneratingType] = useState('');
  const [questions, setQuestions] = useState(null);
  const [flashcards, setFlashcards] = useState(null);
  const [exam, setExam] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [loadingCourses, setLoadingCourses] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState({
    basic: true, intermediate: true, advanced: true, scenario: true, mcq: true
  });
  const fileInputRef = useRef(null);

  const voiceCallback = useCallback((text) => setContent(text), []);
  const { isRecording, toggleRecording } = useVoiceInput(voiceCallback);

  useEffect(() => {
    const loadCourses = async () => {
      setLoadingCourses(true);
      try {
        const { data } = await axios.get(`${API}/api/courses`, { headers: getAuth() });
        setCourses(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error('Failed to load courses:', err);
      } finally {
        setLoadingCourses(false);
      }
    };
    loadCourses();
  }, []);

  const handleCourseSelect = async (courseId) => {
    if (!courseId || courseId === 'none') {
      setSelectedCourse(null);
      return;
    }
    const course = courses.find(c => c.id === courseId);
    if (!course) return;

    setSelectedCourse(course);
    setTopic(course.title || '');

    // Load lesson content for this course
    try {
      const { data } = await axios.get(`${API}/api/courses/${courseId}`, { headers: getAuth() });
      const lessons = data.lessons || [];
      let courseText = `Course: ${data.title || ''}\n${data.description || ''}\n\n`;
      for (const lesson of lessons) {
        courseText += `## ${lesson.title || ''}\n${lesson.text || lesson.content || lesson.description || ''}\n\n`;
      }
      if (courseText.trim().length > 50) {
        setContent(courseText.trim());
        toast.success(`Loaded ${lessons.length} lesson(s) from "${course.title}"`);
      } else {
        setContent('');
        toast.info('Course loaded but has minimal text content. You can supplement with your own text.');
      }
    } catch (err) {
      toast.error('Failed to load course content');
      setContent('');
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File too large. Max 10MB.');
      return;
    }
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await axios.post(`${API}/api/content/upload-source`, formData, {
        headers: { ...getAuth(), 'Content-Type': 'multipart/form-data' }
      });
      setUploadedFile({ id: data.file_id, name: file.name, text: data.extracted_text });
      setContent(data.extracted_text || '');
      toast.success(`Uploaded: ${file.name} (${data.text_length} chars extracted)`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to upload file');
    } finally {
      setLoading(false);
    }
  };

  const generateQuestions = async () => {
    if (!content.trim() && !uploadedFile) {
      toast.error('Provide content text or upload a document first.');
      return;
    }
    setGeneratingType('questions');
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/training-engine/generate-questions`, {
        content: content.trim(),
        file_id: uploadedFile?.id || null,
        course_id: selectedCourse?.id || null,
        topic: topic || 'General',
        num_questions: numQuestions,
        difficulty
      }, { headers: getAuth(), timeout: 65000 });
      setQuestions(data);
      setActiveTab('questions');
      toast.success(`Generated ${data.total_questions || 'multiple'} questions!`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to generate questions. Try with shorter content.');
    } finally {
      setLoading(false);
      setGeneratingType('');
    }
  };

  const generateFlashcards = async () => {
    if (!content.trim() && !uploadedFile) {
      toast.error('Provide content first.');
      return;
    }
    setGeneratingType('flashcards');
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/training-engine/generate-flashcards`, {
        content: content.trim(),
        file_id: uploadedFile?.id || null,
        course_id: selectedCourse?.id || null,
        topic: topic || 'General',
        num_cards: 15
      }, { headers: getAuth(), timeout: 65000 });
      setFlashcards(data.flashcards || []);
      setActiveTab('flashcards');
      toast.success(`Generated ${(data.flashcards || []).length} flashcards!`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to generate flashcards.');
    } finally {
      setLoading(false);
      setGeneratingType('');
    }
  };

  const generateExam = async () => {
    if (!content.trim() && !uploadedFile) {
      toast.error('Provide content first.');
      return;
    }
    setGeneratingType('exam');
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/training-engine/generate-exam`, {
        content: content.trim(),
        file_id: uploadedFile?.id || null,
        course_id: selectedCourse?.id || null,
        topic: topic || 'General',
        exam_duration_minutes: 30,
        num_questions: 15
      }, { headers: getAuth(), timeout: 65000 });
      setExam(data);
      setActiveTab('exam');
      toast.success('Exam simulation generated!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to generate exam.');
    } finally {
      setLoading(false);
      setGeneratingType('');
    }
  };

  const toggleCategory = (cat) => {
    setExpandedCategories(prev => ({ ...prev, [cat]: !prev[cat] }));
  };

  const totalQuestionCount = questions?.categories
    ? Object.values(questions.categories).reduce((sum, arr) => sum + (Array.isArray(arr) ? arr.length : 0), 0)
    : 0;

  const exportQuestions = () => {
    if (!questions) return;
    let text = `# ${questions.topic || 'Questions'}\n\n`;
    const cats = questions.categories || {};
    for (const [cat, items] of Object.entries(cats)) {
      if (!Array.isArray(items) || items.length === 0) continue;
      text += `## ${cat.charAt(0).toUpperCase() + cat.slice(1)} Questions\n\n`;
      items.forEach((item, i) => {
        text += `Q${i+1}: ${item.q}\n`;
        if (cat === 'mcq') {
          (item.options || []).forEach(o => { text += `  ${o}\n`; });
          text += `Correct: ${item.correct}\nExplanation: ${item.explanation}\n\n`;
        } else {
          text += `A${i+1}: ${item.a}\n\n`;
        }
      });
    }
    if (questions.key_takeaways?.length) {
      text += `## Key Takeaways\n`;
      questions.key_takeaways.forEach(t => { text += `- ${t}\n`; });
    }
    const blob = new Blob([text], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${questions.topic || 'questions'}_qa.md`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Questions exported!');
  };

  const publishAsAssignment = async () => {
    if (!questions || !selectedCourse) {
      toast.error('Generate questions and select a course first.');
      return;
    }
    const allQuestions = [];
    for (const [cat, items] of Object.entries(questions.categories || {})) {
      if (Array.isArray(items)) {
        items.forEach(item => allQuestions.push({ ...item, category: cat }));
      }
    }
    try {
      await axios.post(`${API}/api/training-engine/publish-assignment`, {
        title: `${questions.topic || topic || 'AI Generated'} - Assignment`,
        course_id: selectedCourse.id,
        questions: allQuestions,
        description: `Auto-generated from AI Q&A Generator. ${allQuestions.length} questions.`,
        max_score: allQuestions.length * 5
      }, { headers: getAuth() });
      toast.success('Published as Assignment!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to publish assignment');
    }
  };

  const publishAsExam = async () => {
    if (!exam || !selectedCourse) {
      toast.error('Generate an exam and select a course first.');
      return;
    }
    try {
      await axios.post(`${API}/api/training-engine/publish-exam`, {
        title: exam.exam_title || `${topic || 'AI Generated'} - Exam`,
        course_id: selectedCourse.id,
        sections: exam.sections || [],
        duration_minutes: exam.duration_minutes || 60,
        total_marks: exam.total_marks || 100,
        description: `Auto-generated exam simulation from AI Q&A Generator.`
      }, { headers: getAuth() });
      toast.success('Published as Exam!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to publish exam');
    }
  };

  return (
    <DashboardLayout>
      <Header
        title="AI Training Intelligence Engine"
        subtitle="Select a course, upload content, or paste text to generate structured Q&A, flashcards, and exams"
      />

      <div className="max-w-6xl mx-auto space-y-6 p-4 sm:p-6">
        {/* Input Section */}
        <div className="glass-card p-6 space-y-4" data-testid="content-input-section">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-violet-500 to-cyan-500 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Content Input</h2>
              <p className="text-sm text-zinc-500">Select a course, paste text, upload a document, or use voice input</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 space-y-3">
              {/* Generate from Course */}
              <div className="flex items-center gap-3 p-3 rounded-lg bg-gradient-to-r from-violet-500/5 to-cyan-500/5 border border-white/5">
                <GraduationCap className="w-5 h-5 text-violet-400 shrink-0" />
                <div className="flex-1 min-w-0">
                  <Select onValueChange={handleCourseSelect} value={selectedCourse?.id || 'none'}>
                    <SelectTrigger className="bg-zinc-800 border-white/10 h-9" data-testid="course-select">
                      <SelectValue placeholder={loadingCourses ? "Loading courses..." : "Generate from an enrolled course..."} />
                    </SelectTrigger>
                    <SelectContent className="max-h-[250px]">
                      <SelectItem value="none">-- No course (use text/upload) --</SelectItem>
                      {courses.map(c => (
                        <SelectItem key={c.id} value={c.id}>
                          {c.title}{c.course_branch === 'customized' ? ' (Custom)' : ''}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {selectedCourse && (
                  <Badge className="bg-violet-500/20 text-violet-300 border-violet-500/30 text-xs shrink-0">
                    Course loaded
                  </Badge>
                )}
              </div>

              <div className="flex items-center justify-between">
                <Label>Content / Training Material</Label>
                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" onClick={toggleRecording}
                    className={isRecording ? 'text-red-400 animate-pulse' : 'text-zinc-400 hover:text-violet-400'}
                    data-testid="voice-content-btn"
                  >
                    {isRecording ? <MicOff className="w-4 h-4 mr-1" /> : <Mic className="w-4 h-4 mr-1" />}
                    {isRecording ? 'Stop' : 'Voice'}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => fileInputRef.current?.click()}
                    className="text-zinc-400 hover:text-cyan-400"
                    data-testid="upload-content-btn"
                  >
                    <Upload className="w-4 h-4 mr-1" /> Upload
                  </Button>
                  <input ref={fileInputRef} type="file" accept=".pdf,.docx,.doc,.txt,.pptx"
                    onChange={handleFileUpload} className="hidden" />
                </div>
              </div>
              <Textarea
                placeholder="Paste your training material, course content, textbook excerpts, or any educational content here..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="min-h-[200px] bg-zinc-800 border-white/10 text-sm"
                data-testid="content-textarea"
              />
              {uploadedFile && (
                <div className="flex items-center gap-2 text-sm text-emerald-400">
                  <FileText className="w-4 h-4" />
                  <span>{uploadedFile.name}</span>
                  <Badge variant="outline" className="text-xs ml-auto">Uploaded</Badge>
                </div>
              )}
            </div>

            <div className="space-y-4">
              <div>
                <Label>Topic / Section Name</Label>
                <Input value={topic} onChange={(e) => setTopic(e.target.value)}
                  placeholder="e.g., Project Management"
                  className="bg-zinc-800 border-white/10 mt-1"
                  data-testid="topic-input"
                />
              </div>
              <div>
                <Label>Number of Questions</Label>
                <Select value={String(numQuestions)} onValueChange={(v) => setNumQuestions(parseInt(v))}>
                  <SelectTrigger className="bg-zinc-800 border-white/10 mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10 Questions</SelectItem>
                    <SelectItem value="15">15 Questions</SelectItem>
                    <SelectItem value="20">20 Questions</SelectItem>
                    <SelectItem value="30">30 Questions</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Difficulty</Label>
                <Select value={difficulty} onValueChange={setDifficulty}>
                  <SelectTrigger className="bg-zinc-800 border-white/10 mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="mixed">Mixed (All Levels)</SelectItem>
                    <SelectItem value="basic">Basic Only</SelectItem>
                    <SelectItem value="intermediate">Intermediate</SelectItem>
                    <SelectItem value="advanced">Advanced</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3 pt-2">
            <Button onClick={generateQuestions} disabled={loading}
              className="bg-gradient-to-r from-violet-500 to-cyan-500 hover:opacity-90"
              data-testid="generate-questions-btn"
            >
              {generatingType === 'questions' ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Brain className="w-4 h-4 mr-2" />}
              Generate Q&A
            </Button>
            <Button onClick={generateFlashcards} disabled={loading} variant="outline"
              className="border-white/10 hover:bg-white/5"
              data-testid="generate-flashcards-btn"
            >
              {generatingType === 'flashcards' ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <Layers className="w-4 h-4 mr-2" />}
              Flashcards
            </Button>
            <Button onClick={generateExam} disabled={loading} variant="outline"
              className="border-white/10 hover:bg-white/5"
              data-testid="generate-exam-btn"
            >
              {generatingType === 'exam' ? <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> : <ClipboardList className="w-4 h-4 mr-2" />}
              Exam Simulation
            </Button>
            {questions && (
              <Button onClick={exportQuestions} variant="outline" className="border-white/10 ml-auto"
                data-testid="export-btn"
              >
                <Download className="w-4 h-4 mr-2" /> Export
              </Button>
            )}
          </div>
        </div>

        {/* Publish Section - Always visible for teachers/org_admin */}
        {(user?.role === 'teacher' || user?.role === 'org_admin' || user?.role === 'admin') && (
          <div className="glass-card p-5 border-emerald-500/20" data-testid="publish-section">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                <Send className="w-4 h-4 text-emerald-400" />
              </div>
              <div>
                <h3 className="font-semibold text-sm">Publish to Students</h3>
                <p className="text-xs text-zinc-500">
                  {!selectedCourse && !questions && !exam
                    ? '1. Select a course  2. Generate Q&A or Exam  3. Publish as Assignment or Exam'
                    : selectedCourse
                      ? `Ready to publish to "${selectedCourse.title || selectedCourse.name}"`
                      : 'Select a course from the dropdown above to enable publishing'}
                </p>
              </div>
            </div>
            {!questions && !exam ? (
              <p className="text-xs text-zinc-500 bg-zinc-800/50 p-3 rounded-lg">
                Generate Q&A or an Exam above first. The generated content will be publishable as a formal graded assignment or exam for enrolled students.
              </p>
            ) : !selectedCourse ? (
              <p className="text-xs text-amber-400 bg-amber-500/10 p-3 rounded-lg">
                Select a course from the dropdown above to enable publishing.
              </p>
            ) : (
              <div className="flex flex-wrap gap-3">
                {questions && (
                  <Button onClick={publishAsAssignment} className="bg-emerald-600 hover:bg-emerald-700"
                    data-testid="publish-assignment-btn"
                  >
                    <Send className="w-4 h-4 mr-2" /> Publish Q&A as Assignment
                  </Button>
                )}
                {exam && (
                  <Button onClick={publishAsExam} className="bg-orange-600 hover:bg-orange-700"
                    data-testid="publish-exam-btn"
                  >
                    <Send className="w-4 h-4 mr-2" /> Publish as Exam
                  </Button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Results Section */}
        {(questions || flashcards || exam) && (
          <div className="space-y-4">
            {/* Tab Switcher */}
            <div className="flex gap-2 border-b border-white/10 pb-2">
              {questions && (
                <button onClick={() => setActiveTab('questions')}
                  className={`px-4 py-2 text-sm rounded-t-lg transition-colors ${activeTab === 'questions' ? 'bg-violet-500/20 text-violet-300 border-b-2 border-violet-500' : 'text-zinc-500 hover:text-zinc-300'}`}
                  data-testid="tab-questions"
                >
                  <HelpCircle className="w-4 h-4 inline mr-1" /> Q&A ({totalQuestionCount})
                </button>
              )}
              {flashcards && (
                <button onClick={() => setActiveTab('flashcards')}
                  className={`px-4 py-2 text-sm rounded-t-lg transition-colors ${activeTab === 'flashcards' ? 'bg-cyan-500/20 text-cyan-300 border-b-2 border-cyan-500' : 'text-zinc-500 hover:text-zinc-300'}`}
                  data-testid="tab-flashcards"
                >
                  <Layers className="w-4 h-4 inline mr-1" /> Flashcards ({flashcards.length})
                </button>
              )}
              {exam && (
                <button onClick={() => setActiveTab('exam')}
                  className={`px-4 py-2 text-sm rounded-t-lg transition-colors ${activeTab === 'exam' ? 'bg-orange-500/20 text-orange-300 border-b-2 border-orange-500' : 'text-zinc-500 hover:text-zinc-300'}`}
                  data-testid="tab-exam"
                >
                  <ClipboardList className="w-4 h-4 inline mr-1" /> Exam
                </button>
              )}
            </div>

            {/* Questions Tab */}
            {activeTab === 'questions' && questions && (
              <div className="space-y-6" data-testid="questions-results">
                {/* Key Takeaways */}
                {questions.key_takeaways?.length > 0 && (
                  <div className="glass-card p-4 border-emerald-500/20">
                    <div className="flex items-center gap-2 mb-3">
                      <Lightbulb className="w-4 h-4 text-emerald-400" />
                      <span className="text-sm font-semibold text-emerald-400">Key Takeaways</span>
                    </div>
                    <ul className="space-y-1">
                      {questions.key_takeaways.map((t, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-zinc-300">
                          <CheckCircle className="w-3 h-3 text-emerald-500 mt-1 shrink-0" />
                          {t}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Knowledge Gaps */}
                {questions.knowledge_gaps?.length > 0 && (
                  <div className="glass-card p-4 border-amber-500/20">
                    <div className="flex items-center gap-2 mb-3">
                      <Target className="w-4 h-4 text-amber-400" />
                      <span className="text-sm font-semibold text-amber-400">Potential Knowledge Gaps</span>
                    </div>
                    <ul className="space-y-1">
                      {questions.knowledge_gaps.map((g, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-zinc-300">
                          <AlertCircle className="w-3 h-3 text-amber-500 mt-1 shrink-0" />
                          {g}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Question Categories */}
                {Object.entries(questions.categories || {}).map(([category, items]) => {
                  if (!Array.isArray(items) || items.length === 0) return null;
                  const labels = {
                    basic: { icon: BookOpen, label: 'Basic Understanding', color: 'text-emerald-400' },
                    intermediate: { icon: Brain, label: 'Intermediate Application', color: 'text-blue-400' },
                    advanced: { icon: Award, label: 'Advanced / Expert', color: 'text-orange-400' },
                    scenario: { icon: Target, label: 'Scenario-Based', color: 'text-violet-400' },
                    mcq: { icon: ClipboardList, label: 'Multiple Choice', color: 'text-cyan-400' },
                  };
                  const cfg = labels[category] || { icon: HelpCircle, label: category, color: 'text-zinc-400' };
                  const Icon = cfg.icon;
                  const isExpanded = expandedCategories[category];

                  return (
                    <div key={category} className="space-y-3">
                      <button
                        onClick={() => toggleCategory(category)}
                        className="flex items-center gap-2 w-full text-left"
                        data-testid={`category-${category}`}
                      >
                        <Icon className={`w-4 h-4 ${cfg.color}`} />
                        <span className={`text-sm font-semibold ${cfg.color}`}>{cfg.label}</span>
                        <Badge variant="outline" className="text-xs ml-1">{items.length}</Badge>
                        <ChevronDown className={`w-4 h-4 text-zinc-500 ml-auto transition-transform ${isExpanded ? '' : '-rotate-90'}`} />
                      </button>
                      {isExpanded && (
                        <div className="space-y-2 pl-2">
                          {items.map((item, i) => (
                            <QACard key={i} item={item} index={i} type={category} />
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Flashcards Tab */}
            {activeTab === 'flashcards' && flashcards && (
              <FlashcardView cards={flashcards} />
            )}

            {/* Exam Tab */}
            {activeTab === 'exam' && exam && (
              <div className="space-y-6" data-testid="exam-results">
                <div className="glass-card p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold">{exam.exam_title}</h3>
                    <div className="flex gap-3 text-sm text-zinc-400">
                      <span>{exam.duration_minutes} min</span>
                      <span>{exam.total_marks} marks</span>
                    </div>
                  </div>
                </div>
                {(exam.sections || []).map((section, si) => (
                  <div key={si} className="space-y-3">
                    <div className="flex items-center gap-2">
                      <ClipboardList className="w-4 h-4 text-orange-400" />
                      <h4 className="text-sm font-semibold text-orange-400">{section.name}</h4>
                    </div>
                    <div className="space-y-2 pl-2">
                      {(section.questions || []).map((q, qi) => (
                        <div key={qi} className="glass-card p-4 space-y-2">
                          <div className="flex items-start justify-between gap-2">
                            <p className="text-sm font-medium">{q.q}</p>
                            <Badge variant="outline" className="text-xs shrink-0">{q.marks} marks</Badge>
                          </div>
                          {q.type === 'mcq' && (
                            <div className="space-y-1 pl-4">
                              {(q.options || []).map((o, oi) => (
                                <p key={oi} className="text-sm text-zinc-400">{o}</p>
                              ))}
                            </div>
                          )}
                          <details className="text-sm">
                            <summary className="cursor-pointer text-zinc-500 hover:text-zinc-300">Show answer</summary>
                            <div className="mt-2 p-3 rounded-lg bg-white/5 text-zinc-300">
                              {q.model_answer || q.explanation || `Correct: ${q.correct}`}
                            </div>
                          </details>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!questions && !flashcards && !exam && !loading && (
          <div className="glass-card p-12 text-center" data-testid="empty-state">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500/20 to-cyan-500/20 flex items-center justify-center mx-auto mb-4">
              <Zap className="w-8 h-8 text-violet-400" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Ready to Generate</h3>
            <p className="text-sm text-zinc-500 max-w-md mx-auto">
              Paste your training material or upload a document (PDF, DOCX, TXT), then click Generate to create
              structured questions, flashcards, and exam simulations.
            </p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
