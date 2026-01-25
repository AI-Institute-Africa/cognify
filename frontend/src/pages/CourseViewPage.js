import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { getCourse, getCourseContent, translateText, generateTTS, uploadCourseContent } from '../services/api';
import { 
  BookOpen, Video, FileText, Headphones, Image, 
  ArrowLeft, Play, Pause, Volume2, Globe, 
  ChevronRight, Download, Share2, CheckCircle,
  Clock, Users, GraduationCap, Loader2, Plus, Upload
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';

const LEARNING_MODES = [
  { id: 'text', icon: FileText, label: 'Text', description: 'Read at your own pace' },
  { id: 'video', icon: Video, label: 'Video', description: 'Watch video lessons' },
  { id: 'audio', icon: Headphones, label: 'Audio', description: 'Listen while multitasking' },
  { id: 'slides', icon: Image, label: 'Slides', description: 'Visual picture slides' },
];

const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇬🇧' },
  { code: 'sw', name: 'Swahili', flag: '🇰🇪' },
  { code: 'sn', name: 'Shona', flag: '🇿🇼' },
  { code: 'nd', name: 'Ndebele', flag: '🇿🇼' },
  { code: 'zu', name: 'Zulu', flag: '🇿🇦' },
  { code: 'xh', name: 'Xhosa', flag: '🇿🇦' },
  { code: 'fr', name: 'French', flag: '🇫🇷' },
  { code: 'pt', name: 'Portuguese', flag: '🇵🇹' },
  { code: 'ar', name: 'Arabic', flag: '🇸🇦' },
  { code: 'es', name: 'Spanish', flag: '🇪🇸' },
];

export default function CourseViewPage() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { language: appLanguage } = useLanguage();
  
  const [course, setCourse] = useState(null);
  const [content, setContent] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMode, setSelectedMode] = useState('text');
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const [translatedContent, setTranslatedContent] = useState({});
  const [translating, setTranslating] = useState(false);
  const [audioPlaying, setAudioPlaying] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [generatingAudio, setGeneratingAudio] = useState(false);
  const [currentLessonIndex, setCurrentLessonIndex] = useState(0);
  
  // Micro-hints state
  const [showHint, setShowHint] = useState(false);
  const [currentHint, setCurrentHint] = useState('');
  const [loadingHint, setLoadingHint] = useState(false);
  const [lastActivity, setLastActivity] = useState(Date.now());
  const [researchPapers, setResearchPapers] = useState([]);
  
  // Teacher content upload state
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [newContent, setNewContent] = useState({
    title: '',
    description: '',
    type: 'text',
    content_text: '',
    content_url: ''
  });
  
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin' || user?.role === 'org_admin';

  // Auto micro-hints after 15 seconds of inactivity
  useEffect(() => {
    const checkInactivity = setInterval(() => {
      if (Date.now() - lastActivity > 15000 && !showHint && !isTeacher) {
        generateMicroHint();
      }
    }, 5000);
    
    return () => clearInterval(checkInactivity);
  }, [lastActivity, showHint, currentLessonIndex]);

  // Track user activity
  useEffect(() => {
    const handleActivity = () => setLastActivity(Date.now());
    window.addEventListener('mousemove', handleActivity);
    window.addEventListener('keypress', handleActivity);
    window.addEventListener('click', handleActivity);
    
    return () => {
      window.removeEventListener('mousemove', handleActivity);
      window.removeEventListener('keypress', handleActivity);
      window.removeEventListener('click', handleActivity);
    };
  }, []);

  // Auto-load research papers when lesson changes
  useEffect(() => {
    if (course && content[currentLessonIndex]) {
      loadResearchPapers();
    }
  }, [currentLessonIndex, course]);

  const generateMicroHint = async () => {
    const lesson = content[currentLessonIndex];
    if (!lesson) return;
    
    setLoadingHint(true);
    try {
      const token = localStorage.getItem('eduos_token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/ai/micro-hint`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          topic: lesson.title,
          context: lesson.text || lesson.description,
          language: selectedLanguage
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        setCurrentHint(data.hint || getDefaultHint(lesson));
      } else {
        setCurrentHint(getDefaultHint(lesson));
      }
    } catch (error) {
      setCurrentHint(getDefaultHint(lesson));
    }
    setLoadingHint(false);
    setShowHint(true);
  };

  const getDefaultHint = (lesson) => {
    const hints = [
      `💡 Tip: Try to summarize "${lesson.title}" in your own words to better understand the concept.`,
      `🧠 Remember: The key concepts in this lesson connect to real-world applications. Can you think of an example?`,
      `📚 Study tip: Take notes on the main points. Writing helps reinforce memory!`,
      `🎯 Focus on understanding WHY, not just WHAT. This deepens your learning.`,
      `🔗 Try connecting this lesson to something you already know. It makes learning easier!`
    ];
    return hints[Math.floor(Math.random() * hints.length)];
  };

  const loadResearchPapers = async () => {
    const lesson = content[currentLessonIndex];
    if (!lesson) return;
    
    // Generate mock research papers related to the topic
    const papers = [
      { title: `Recent Advances in ${lesson.title}`, journal: 'Nature Education', year: 2025, url: '#' },
      { title: `${course?.name}: A Comprehensive Review`, journal: 'Science Direct', year: 2024, url: '#' },
      { title: `Teaching Methods for ${lesson.title}`, journal: 'Journal of Education', year: 2025, url: '#' },
    ];
    setResearchPapers(papers);
  };

  useEffect(() => {
    loadCourseData();
  }, [courseId]);

  const loadCourseData = async () => {
    try {
      setLoading(true);
      const [courseData, contentData] = await Promise.all([
        getCourse(courseId),
        getCourseContent(courseId)
      ]);
      setCourse(courseData);
      setContent(contentData);
      
      // Create default lessons if no content exists
      if (contentData.length === 0) {
        setContent(generateDefaultLessons(courseData));
      }
    } catch (error) {
      console.error('Failed to load course:', error);
      toast.error('Failed to load course content');
    } finally {
      setLoading(false);
    }
  };

  // Generate default lessons based on course info
  const generateDefaultLessons = (courseData) => {
    return [
      {
        id: '1',
        type: 'text',
        title: `Introduction to ${courseData.name}`,
        description: `Welcome to ${courseData.name}. This course will cover ${courseData.description}`,
        text: `# Introduction to ${courseData.name}\n\n${courseData.description}\n\n## What You'll Learn\n\n- Core concepts and fundamentals\n- Practical applications\n- Problem-solving techniques\n- Real-world case studies\n\n## Prerequisites\n\nThis course is designed for ${courseData.grade_level} students. Basic knowledge of the subject area is helpful but not required.\n\n## Course Structure\n\nThis course consists of multiple modules, each building upon the previous one. You can choose your preferred learning mode: text, video, audio, or picture slides.`
      },
      {
        id: '2',
        type: 'text',
        title: 'Core Concepts',
        description: 'Understanding the fundamental concepts',
        text: `# Core Concepts\n\nIn this module, we'll explore the fundamental concepts of ${courseData.name}.\n\n## Key Topics\n\n1. **Foundation Principles** - Understanding the basics\n2. **Building Blocks** - Essential components and structures\n3. **Relationships** - How concepts connect together\n4. **Applications** - Real-world usage and examples\n\n## Learning Objectives\n\nBy the end of this module, you will be able to:\n- Identify key concepts\n- Explain fundamental principles\n- Apply knowledge to solve problems`
      },
      {
        id: '3',
        type: 'text',
        title: 'Practice & Assessment',
        description: 'Testing your understanding',
        text: `# Practice & Assessment\n\nNow it's time to test what you've learned!\n\n## Practice Questions\n\n1. What are the main concepts covered in this course?\n2. How do these concepts apply to real-world situations?\n3. Explain the relationship between different topics.\n\n## Assessment Guidelines\n\n- Complete all practice exercises\n- Review materials as needed\n- Ask questions when uncertain\n\n## Next Steps\n\nAfter completing this module, you'll be ready to move on to more advanced topics.`
      }
    ];
  };

  const handleTranslate = async (text, index) => {
    if (selectedLanguage === 'en') {
      setTranslatedContent({});
      return;
    }
    
    setTranslating(true);
    try {
      const result = await translateText(text, selectedLanguage);
      setTranslatedContent(prev => ({
        ...prev,
        [index]: result.translated_text || text
      }));
    } catch (error) {
      console.error('Translation failed:', error);
      toast.error('Translation failed. Please try again.');
    } finally {
      setTranslating(false);
    }
  };

  const handleGenerateAudio = async (text) => {
    setGeneratingAudio(true);
    try {
      const result = await generateTTS(text.substring(0, 500), 'nova');
      if (result.audio_url) {
        setAudioUrl(result.audio_url);
        toast.success('Audio generated successfully!');
      }
    } catch (error) {
      console.error('TTS failed:', error);
      toast.error('Failed to generate audio. Please try again.');
    } finally {
      setGeneratingAudio(false);
    }
  };

  const playAudio = () => {
    if (audioUrl) {
      const audio = new Audio(audioUrl);
      audio.play();
      setAudioPlaying(true);
      audio.onended = () => setAudioPlaying(false);
    }
  };

  const handleUploadContent = async (e) => {
    e.preventDefault();
    if (!newContent.title) {
      toast.error('Please enter a title');
      return;
    }
    
    setUploading(true);
    try {
      await uploadCourseContent(
        courseId,
        newContent.type,
        newContent.title,
        newContent.description,
        newContent.content_url,
        newContent.content_text
      );
      toast.success('Content uploaded successfully!');
      setShowUploadDialog(false);
      setNewContent({
        title: '',
        description: '',
        type: 'text',
        content_text: '',
        content_url: ''
      });
      loadCourseData(); // Refresh content
    } catch (error) {
      console.error('Upload failed:', error);
      toast.error('Failed to upload content');
    } finally {
      setUploading(false);
    }
  };

  const currentLesson = content[currentLessonIndex];
  const displayText = translatedContent[currentLessonIndex] || currentLesson?.text || currentLesson?.description || '';

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-zinc-500 mt-4">Loading course content...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!course) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <BookOpen className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">Course not found</h3>
            <Button onClick={() => navigate('/courses')}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Courses
            </Button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="min-h-screen">
        {/* Course Header */}
        <div className="bg-gradient-to-r from-blue-500/10 via-violet-500/10 to-purple-500/10 border-b border-white/5">
          <div className="p-6">
            <Button 
              variant="ghost" 
              onClick={() => navigate('/courses')}
              className="mb-4 text-zinc-400 hover:text-white"
              data-testid="back-to-courses-btn"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Courses
            </Button>
            
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                    {course.code}
                  </Badge>
                  <Badge className="bg-zinc-800 text-zinc-300">
                    {course.grade_level}
                  </Badge>
                </div>
                <h1 className="text-2xl md:text-3xl font-bold mb-2" data-testid="course-title">
                  {course.name}
                </h1>
                <p className="text-zinc-400 max-w-2xl">{course.description}</p>
                
                <div className="flex items-center gap-6 mt-4 text-sm text-zinc-500">
                  <span className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    {course.credits} Credits
                  </span>
                  <span className="flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    {course.enrolled_students?.length || 0} Students
                  </span>
                  <span className="flex items-center gap-2">
                    <GraduationCap className="w-4 h-4" />
                    {content.length} Lessons
                  </span>
                </div>
              </div>
              
              {/* Language Selector and Teacher Upload */}
              <div className="flex items-center gap-3">
                {isTeacher && (
                  <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
                    <DialogTrigger asChild>
                      <Button className="bg-blue-500 hover:bg-blue-600" data-testid="upload-content-btn">
                        <Upload className="w-4 h-4 mr-2" />
                        Add Content
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="bg-zinc-900 border-white/10 max-w-lg">
                      <DialogHeader>
                        <DialogTitle>Upload Course Content</DialogTitle>
                        <DialogDescription className="text-zinc-500">
                          Add new content to this course for students to learn from
                        </DialogDescription>
                      </DialogHeader>
                      <form onSubmit={handleUploadContent} className="space-y-4 mt-4">
                        <div className="space-y-2">
                          <Label>Content Type</Label>
                          <Select
                            value={newContent.type}
                            onValueChange={(value) => setNewContent({...newContent, type: value})}
                          >
                            <SelectTrigger className="bg-zinc-800 border-white/10">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent className="bg-zinc-800 border-white/10">
                              <SelectItem value="text">
                                <span className="flex items-center gap-2">
                                  <FileText className="w-4 h-4" /> Text Content
                                </span>
                              </SelectItem>
                              <SelectItem value="video">
                                <span className="flex items-center gap-2">
                                  <Video className="w-4 h-4" /> Video
                                </span>
                              </SelectItem>
                              <SelectItem value="audio">
                                <span className="flex items-center gap-2">
                                  <Headphones className="w-4 h-4" /> Audio
                                </span>
                              </SelectItem>
                              <SelectItem value="image">
                                <span className="flex items-center gap-2">
                                  <Image className="w-4 h-4" /> Image/Slides
                                </span>
                              </SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        
                        <div className="space-y-2">
                          <Label>Title</Label>
                          <Input
                            placeholder="Lesson title..."
                            value={newContent.title}
                            onChange={(e) => setNewContent({...newContent, title: e.target.value})}
                            className="bg-zinc-800 border-white/10"
                            data-testid="content-title-input"
                          />
                        </div>
                        
                        <div className="space-y-2">
                          <Label>Description</Label>
                          <Textarea
                            placeholder="Brief description..."
                            value={newContent.description}
                            onChange={(e) => setNewContent({...newContent, description: e.target.value})}
                            className="bg-zinc-800 border-white/10 min-h-[80px]"
                          />
                        </div>
                        
                        {newContent.type === 'text' ? (
                          <div className="space-y-2">
                            <Label>Content Text</Label>
                            <Textarea
                              placeholder="Enter your lesson content here... Use # for headings, - for bullet points"
                              value={newContent.content_text}
                              onChange={(e) => setNewContent({...newContent, content_text: e.target.value})}
                              className="bg-zinc-800 border-white/10 min-h-[150px] font-mono text-sm"
                              data-testid="content-text-input"
                            />
                          </div>
                        ) : (
                          <div className="space-y-2">
                            <Label>Content URL</Label>
                            <Input
                              placeholder={`Enter ${newContent.type} URL...`}
                              value={newContent.content_url}
                              onChange={(e) => setNewContent({...newContent, content_url: e.target.value})}
                              className="bg-zinc-800 border-white/10"
                              data-testid="content-url-input"
                            />
                            <p className="text-xs text-zinc-500">
                              Paste a link to your {newContent.type} content (YouTube, Vimeo, cloud storage, etc.)
                            </p>
                          </div>
                        )}
                        
                        <div className="flex justify-end gap-3 pt-4">
                          <Button type="button" variant="ghost" onClick={() => setShowUploadDialog(false)}>
                            Cancel
                          </Button>
                          <Button type="submit" disabled={uploading} data-testid="submit-content-btn">
                            {uploading ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Uploading...
                              </>
                            ) : (
                              <>
                                <Plus className="w-4 h-4 mr-2" />
                                Add Content
                              </>
                            )}
                          </Button>
                        </div>
                      </form>
                    </DialogContent>
                  </Dialog>
                )}
                
                <Globe className="w-5 h-5 text-zinc-500" />
                <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                  <SelectTrigger className="w-[180px] bg-zinc-900/50 border-white/10" data-testid="language-selector">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-zinc-900 border-white/10">
                    {SUPPORTED_LANGUAGES.map(lang => (
                      <SelectItem key={lang.code} value={lang.code}>
                        <span className="flex items-center gap-2">
                          <span>{lang.flag}</span>
                          <span>{lang.name}</span>
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Sidebar - Lesson Navigation */}
            <div className="lg:col-span-1">
              <div className="glass-card p-4">
                <h3 className="font-semibold mb-4 text-sm uppercase tracking-wider text-zinc-500">
                  Course Lessons
                </h3>
                <div className="space-y-2">
                  {content.map((lesson, index) => (
                    <button
                      key={lesson.id}
                      onClick={() => setCurrentLessonIndex(index)}
                      className={`w-full text-left p-3 rounded-lg transition-all flex items-center gap-3 ${
                        currentLessonIndex === index
                          ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                          : 'hover:bg-white/5 text-zinc-400'
                      }`}
                      data-testid={`lesson-btn-${index}`}
                    >
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                        currentLessonIndex === index ? 'bg-blue-500 text-white' : 'bg-zinc-800'
                      }`}>
                        {index + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="truncate font-medium text-sm">{lesson.title}</p>
                      </div>
                      {currentLessonIndex === index && (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Main Content Area */}
            <div className="lg:col-span-3">
              {/* Learning Mode Selector */}
              <div className="glass-card p-4 mb-6">
                <h3 className="font-semibold mb-4 text-sm uppercase tracking-wider text-zinc-500">
                  Choose Learning Mode
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {LEARNING_MODES.map((mode) => (
                    <button
                      key={mode.id}
                      onClick={() => setSelectedMode(mode.id)}
                      className={`p-4 rounded-xl transition-all flex flex-col items-center gap-2 ${
                        selectedMode === mode.id
                          ? 'bg-blue-500/10 text-blue-400 border-2 border-blue-500/30'
                          : 'bg-zinc-900/50 hover:bg-zinc-800/50 text-zinc-400 border-2 border-transparent'
                      }`}
                      data-testid={`mode-${mode.id}-btn`}
                    >
                      <mode.icon className="w-6 h-6" />
                      <span className="font-medium">{mode.label}</span>
                      <span className="text-xs text-zinc-500 text-center">{mode.description}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Content Display */}
              <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold" data-testid="current-lesson-title">
                    {currentLesson?.title}
                  </h2>
                  <div className="flex items-center gap-2">
                    {selectedLanguage !== 'en' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTranslate(currentLesson?.text || currentLesson?.description, currentLessonIndex)}
                        disabled={translating}
                        className="border-white/10"
                        data-testid="translate-btn"
                      >
                        {translating ? (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <Globe className="w-4 h-4 mr-2" />
                        )}
                        {translating ? 'Translating...' : 'Translate'}
                      </Button>
                    )}
                    {selectedMode === 'audio' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => audioPlaying ? setAudioPlaying(false) : (audioUrl ? playAudio() : handleGenerateAudio(displayText))}
                        disabled={generatingAudio}
                        className="border-white/10"
                        data-testid="audio-btn"
                      >
                        {generatingAudio ? (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : audioPlaying ? (
                          <Pause className="w-4 h-4 mr-2" />
                        ) : (
                          <Play className="w-4 h-4 mr-2" />
                        )}
                        {generatingAudio ? 'Generating...' : audioPlaying ? 'Pause' : audioUrl ? 'Play Audio' : 'Generate Audio'}
                      </Button>
                    )}
                  </div>
                </div>

                {/* Mode-specific content rendering */}
                <Tabs value={selectedMode} className="w-full">
                  <TabsContent value="text" className="mt-0">
                    <div className="prose prose-invert max-w-none">
                      <div 
                        className="text-zinc-300 leading-relaxed whitespace-pre-wrap"
                        data-testid="lesson-content-text"
                      >
                        {displayText.split('\n').map((line, i) => {
                          if (line.startsWith('# ')) {
                            return <h1 key={i} className="text-2xl font-bold mt-6 mb-4 text-white">{line.slice(2)}</h1>;
                          }
                          if (line.startsWith('## ')) {
                            return <h2 key={i} className="text-xl font-semibold mt-5 mb-3 text-white">{line.slice(3)}</h2>;
                          }
                          if (line.startsWith('- ')) {
                            return <li key={i} className="ml-4 text-zinc-300">{line.slice(2)}</li>;
                          }
                          if (line.match(/^\d+\.\s/)) {
                            return <li key={i} className="ml-4 text-zinc-300 list-decimal">{line.replace(/^\d+\.\s/, '')}</li>;
                          }
                          if (line.includes('**')) {
                            const parts = line.split(/\*\*(.*?)\*\*/g);
                            return (
                              <p key={i} className="my-2">
                                {parts.map((part, j) => 
                                  j % 2 === 1 ? <strong key={j} className="text-white">{part}</strong> : part
                                )}
                              </p>
                            );
                          }
                          return line ? <p key={i} className="my-2">{line}</p> : <br key={i} />;
                        })}
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="video" className="mt-0">
                    <div className="aspect-video bg-zinc-900 rounded-xl flex items-center justify-center border border-white/10">
                      <div className="text-center">
                        <Video className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
                        <p className="text-zinc-500 mb-4">Video content for this lesson</p>
                        <Button className="bg-blue-500 hover:bg-blue-600">
                          <Play className="w-4 h-4 mr-2" />
                          Play Video
                        </Button>
                        <p className="text-sm text-zinc-600 mt-4">
                          Video lessons can be uploaded by your teacher
                        </p>
                      </div>
                    </div>
                    <div className="mt-4 p-4 bg-zinc-900/50 rounded-lg border border-white/5">
                      <h4 className="font-medium mb-2">Lesson Notes</h4>
                      <div className="text-sm text-zinc-400">
                        {displayText.substring(0, 300)}...
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="audio" className="mt-0">
                    <div className="p-8 bg-gradient-to-br from-violet-500/10 to-blue-500/10 rounded-xl border border-white/10">
                      <div className="text-center mb-8">
                        <div className="w-24 h-24 bg-violet-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                          <Headphones className="w-12 h-12 text-violet-400" />
                        </div>
                        <h3 className="text-xl font-bold mb-2">Audio Learning Mode</h3>
                        <p className="text-zinc-400">Listen to this lesson while you're on the go</p>
                      </div>
                      
                      {audioUrl ? (
                        <div className="bg-zinc-900/50 p-4 rounded-lg">
                          <div className="flex items-center justify-center gap-4">
                            <Button
                              size="lg"
                              onClick={playAudio}
                              className="bg-violet-500 hover:bg-violet-600"
                            >
                              {audioPlaying ? <Pause className="w-5 h-5 mr-2" /> : <Play className="w-5 h-5 mr-2" />}
                              {audioPlaying ? 'Pause' : 'Play'}
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <Button
                          size="lg"
                          onClick={() => handleGenerateAudio(displayText)}
                          disabled={generatingAudio}
                          className="w-full bg-violet-500 hover:bg-violet-600"
                        >
                          {generatingAudio ? (
                            <>
                              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                              Generating Audio...
                            </>
                          ) : (
                            <>
                              <Volume2 className="w-5 h-5 mr-2" />
                              Generate Audio Version
                            </>
                          )}
                        </Button>
                      )}
                    </div>
                    
                    <div className="mt-4 p-4 bg-zinc-900/50 rounded-lg border border-white/5">
                      <h4 className="font-medium mb-2">Text Transcript</h4>
                      <div className="text-sm text-zinc-400 max-h-48 overflow-y-auto">
                        {displayText}
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="slides" className="mt-0">
                    <div className="space-y-4">
                      {/* Slide viewer */}
                      <div className="aspect-video bg-gradient-to-br from-blue-500/5 to-violet-500/5 rounded-xl flex items-center justify-center border border-white/10 p-8">
                        <div className="text-center max-w-2xl">
                          <div className="w-20 h-20 bg-blue-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                            <Image className="w-10 h-10 text-blue-400" />
                          </div>
                          <h3 className="text-2xl font-bold mb-4">{currentLesson?.title}</h3>
                          <p className="text-zinc-400 text-lg">
                            {currentLesson?.description || displayText.substring(0, 200)}
                          </p>
                        </div>
                      </div>
                      
                      {/* Slide thumbnails */}
                      <div className="flex gap-2 overflow-x-auto pb-2">
                        {content.map((lesson, index) => (
                          <button
                            key={index}
                            onClick={() => setCurrentLessonIndex(index)}
                            className={`flex-shrink-0 w-32 h-20 rounded-lg border-2 transition-all ${
                              currentLessonIndex === index
                                ? 'border-blue-500 bg-blue-500/10'
                                : 'border-white/10 bg-zinc-900/50 hover:border-white/20'
                            }`}
                          >
                            <div className="w-full h-full flex items-center justify-center">
                              <span className="text-sm font-medium">{index + 1}</span>
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </TabsContent>
                </Tabs>

                {/* Navigation buttons */}
                <div className="flex justify-between mt-8 pt-6 border-t border-white/10">
                  <Button
                    variant="outline"
                    onClick={() => setCurrentLessonIndex(Math.max(0, currentLessonIndex - 1))}
                    disabled={currentLessonIndex === 0}
                    className="border-white/10"
                    data-testid="prev-lesson-btn"
                  >
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    Previous Lesson
                  </Button>
                  <Button
                    onClick={() => setCurrentLessonIndex(Math.min(content.length - 1, currentLessonIndex + 1))}
                    disabled={currentLessonIndex === content.length - 1}
                    className="bg-blue-500 hover:bg-blue-600"
                    data-testid="next-lesson-btn"
                  >
                    Next Lesson
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
