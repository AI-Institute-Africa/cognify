import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { getCourse, getCourseContent, translateText, generateTTS, uploadCourseContent, uploadCourseFile, avatarTeachLesson, generateVideoContent, generateSlidesContent, getAvatarSettings } from '../services/api';
import { 
  BookOpen, Video, FileText, Headphones, Image, 
  ArrowLeft, Play, Pause, Volume2, Globe, 
  ChevronRight, Download, Share2, CheckCircle,
  Clock, Users, GraduationCap, Loader2, Plus, Upload,
  Lightbulb, X, ExternalLink, FileSearch, User, Sparkles, Wand2, Zap,
  Lock, CreditCard
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
import axios from 'axios';
import PopupQuiz from '../components/PopupQuiz';

const API = process.env.REACT_APP_BACKEND_URL;

const LEARNING_MODES = [
  { id: 'text', icon: FileText, label: 'Text', description: 'Read at your own pace' },
  { id: 'video', icon: Video, label: 'Video', description: 'Watch video lessons' },
  { id: 'audio', icon: Headphones, label: 'Audio', description: 'Listen while multitasking' },
  { id: 'slides', icon: Image, label: 'Slides', description: 'Visual picture slides' },
  { id: 'avatar', icon: User, label: 'Avatar Tutor', description: 'AI tutor teaches you' },
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
  
  // Enrollment gate state
  const [accessRestricted, setAccessRestricted] = useState(false);
  const [restrictionMessage, setRestrictionMessage] = useState('');
  const [coursePrice, setCoursePrice] = useState(0);
  
  // Teacher content upload state
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMode, setUploadMode] = useState('url'); // 'url' or 'file'
  const [selectedFile, setSelectedFile] = useState(null);
  const [newContent, setNewContent] = useState({
    title: '',
    description: '',
    type: 'text',
    content_text: '',
    content_url: ''
  });
  
  // Avatar teaching state
  const [avatarSettings, setAvatarSettings] = useState(null);
  const [avatarTeaching, setAvatarTeaching] = useState(false);
  const [avatarScript, setAvatarScript] = useState('');
  const [avatarAudioUrl, setAvatarAudioUrl] = useState(null);
  const [avatarPlaying, setAvatarPlaying] = useState(false);
  
  // Content generation state
  const [generatingContent, setGeneratingContent] = useState(false);
  const [showGenerateDialog, setShowGenerateDialog] = useState(false);
  const [generateType, setGenerateType] = useState('video');
  const [generatingVideo, setGeneratingVideo] = useState(false);
  const [generatingSlides, setGeneratingSlides] = useState(false);
  const [avatarVideoId, setAvatarVideoId] = useState(null);
  const [activeAvatarAudio, setActiveAvatarAudio] = useState(null);
  const [avatarVideoUrl, setAvatarVideoUrl] = useState(null);
  
  // Popup quiz state
  const [showQuiz, setShowQuiz] = useState(false);
  const [quizLessonId, setQuizLessonId] = useState(null);
  const [lessonProgress, setLessonProgress] = useState({});
  
  const isTeacher = user?.role === 'teacher' || user?.role === 'admin' || user?.role === 'org_admin';

  // Load avatar settings on mount
  useEffect(() => {
    loadAvatarSettings();
  }, []);

  const loadAvatarSettings = async () => {
    try {
      const settings = await getAvatarSettings();
      setAvatarSettings(settings);
    } catch (error) {
      console.error('Failed to load avatar settings:', error);
    }
  };

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
      const token = localStorage.getItem('cognify_token');
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
      
      let finalContent = [];
      // Handle enrollment gate response
      if (contentData && contentData.access_restricted) {
        // Student hasn't paid - show restricted content
        finalContent = contentData.contents || [];
        setContent(finalContent);
        setAccessRestricted(true);
        setRestrictionMessage(contentData.message);
        setCoursePrice(contentData.course_price);
        toast.info(contentData.message);
      } else {
        finalContent = Array.isArray(contentData) ? contentData : [];
        setContent(finalContent);
        setAccessRestricted(false);
      }
      
      // Create default lessons if no content exists
      if ((!contentData || (Array.isArray(contentData) && contentData.length === 0)) && !contentData?.access_restricted) {
        finalContent = generateDefaultLessons(courseData);
        setContent(finalContent);
      }
      return finalContent;
    } catch (error) {
      console.error('Failed to load course:', error);
      toast.error('Failed to load course content');
      return [];
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
        [index]: result.translated || result.translated_text || text
      }));
      toast.success('Content translated!');
    } catch (error) {
      console.error('Translation failed:', error);
      toast.error('Translation failed. Please try again.');
    } finally {
      setTranslating(false);
    }
  };

  // Web Speech API fallback (works offline, no API key, reads any length)
  const speakWithBrowserTTS = (text) => {
    if (!('speechSynthesis' in window)) {
      toast.error('Audio not supported on this browser.');
      return false;
    }
    try {
      window.speechSynthesis.cancel();
      const utter = new window.SpeechSynthesisUtterance((text || '').toString());
      utter.rate = 1.0;
      utter.pitch = 1.0;
      utter.volume = 1.0;
      utter.lang = 'en-US';
      // Pick a higher quality voice if available
      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find(v => /en[-_]US/i.test(v.lang) && /google|natural|samantha|microsoft/i.test(v.name))
        || voices.find(v => v.default && /en/i.test(v.lang))
        || voices.find(v => /en/i.test(v.lang));
      if (preferred) utter.voice = preferred;
      utter.onstart = () => setAudioPlaying(true);
      utter.onend = () => setAudioPlaying(false);
      utter.onerror = () => setAudioPlaying(false);
      activeBrowserUtterRef.current = utter;
      window.speechSynthesis.speak(utter);
      return true;
    } catch (err) {
      console.error('Browser TTS failed:', err);
      return false;
    }
  };

  const handleGenerateAudio = async (text) => {
    const fullText = (text || '').toString().trim();
    if (!fullText) {
      toast.error('No text to read.');
      return;
    }
    setGeneratingAudio(true);
    try {
      const voiceId = avatarSettings?.voice_id || 'nova';
      const result = await generateTTS(fullText, voiceId);
      if (result.audio_url) {
        setAudioUrl(result.audio_url);
        const chunks = result.chunks || 1;
        toast.success(`Audio generated${chunks > 1 ? ` (${chunks} segments combined)` : ''}!`);
        return;
      }
      throw new Error('No audio URL in response');
    } catch (error) {
      console.error('Cloud TTS failed:', error);
      const detail = error.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail.error || detail.message) : detail;
      // Fall back to browser-native TTS so audio mode always works
      const ok = speakWithBrowserTTS(fullText);
      if (ok) {
        toast.info(
          msg && /budget|quota/i.test(msg)
            ? 'Cloud audio quota reached — using browser voice instead.'
            : 'Using your browser voice to read the lesson.',
          { duration: 4000 }
        );
        setAudioUrl(null);
      } else {
        toast.error('Failed to generate audio. Please try again.');
      }
    } finally {
      setGeneratingAudio(false);
    }
  };

  const activeBrowserUtterRef = React.useRef(null);

  const playAudio = () => {
    // If we have a cloud audio URL, play that. Otherwise, replay via browser TTS.
    if (audioUrl) {
      if (activeAudioRef.current && !activeAudioRef.current.paused) {
        activeAudioRef.current.pause();
        setAudioPlaying(false);
        return;
      }
      // Prefix relative /api/... URLs with the backend base
      const fullUrl = audioUrl.startsWith('/api/') ? `${API}${audioUrl}` : audioUrl;
      const audio = new Audio(fullUrl);
      activeAudioRef.current = audio;
      audio.play();
      setAudioPlaying(true);
      audio.onended = () => { setAudioPlaying(false); activeAudioRef.current = null; };
      return;
    }
    // Browser-TTS path: pause/resume
    if ('speechSynthesis' in window) {
      if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
        window.speechSynthesis.pause();
        setAudioPlaying(false);
      } else if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
        setAudioPlaying(true);
      }
    }
  };
  
  const activeAudioRef = React.useRef(null);

  const handleUploadContent = async (e) => {
    e.preventDefault();
    if (!newContent.title) {
      toast.error('Please enter a title');
      return;
    }
    
    setUploading(true);
    try {
      if (uploadMode === 'file' && selectedFile) {
        // File upload mode
        await uploadCourseFile(
          courseId,
          selectedFile,
          newContent.title,
          newContent.description,
          newContent.type
        );
        toast.success('File uploaded successfully!');
      } else {
        // URL or text mode
        await uploadCourseContent(
          courseId,
          newContent.type,
          newContent.title,
          newContent.description,
          newContent.content_url,
          newContent.content_text
        );
        toast.success('Content uploaded successfully!');
      }
      setShowUploadDialog(false);
      setNewContent({
        title: '',
        description: '',
        type: 'text',
        content_text: '',
        content_url: ''
      });
      setSelectedFile(null);
      setUploadMode('url');
      loadCourseData(); // Refresh content
    } catch (error) {
      console.error('Upload failed:', error);
      toast.error('Failed to upload content');
    } finally {
      setUploading(false);
    }
  };

  // Avatar Teaching Function
  const handleAvatarTeach = async () => {
    const lesson = content[currentLessonIndex];
    if (!lesson) {
      toast.error('No lesson selected');
      return;
    }
    
    setAvatarTeaching(true);
    setAvatarScript('');
    setAvatarAudioUrl(null);
    setAvatarVideoId(null);
    setAvatarVideoUrl(null);
    
    try {
      const lessonText = lesson.text || lesson.content || displayText || '';
      const lessonTitle = lesson.title || course?.name || 'Lesson';
      
      if (!lessonText) {
        toast.error('No lesson content available');
        setAvatarTeaching(false);
        return;
      }
      
      // Use avatar settings from the user's preferences
      const avatarId = avatarSettings?.heygen_avatar_id || 'Abigail_expressive_2024112501';
      const voiceId = avatarSettings?.heygen_voice_id || avatarSettings?.voice_id || 'f38a635bee7a4d1f9b0a654a31d050d2';
      
      // Call the full avatar orchestrator pipeline: Script + HeyGen Video
      const { data } = await axios.post(`${API}/api/avatar-orchestrator/generate-video`, {
        course_id: courseId,
        lesson_id: lesson.id,
        lesson_content: lessonText,
        lesson_title: lessonTitle,
        avatar_id: avatarId,
        voice_id: voiceId,
        user_level: 'intermediate',
        language: selectedLanguage || 'en'
      }, { headers: { Authorization: `Bearer ${localStorage.getItem('cognify_token')}` }, timeout: 90000 });
      
      if (data.script_preview) {
        setAvatarScript(data.script_preview);
      }
      if (data.video_id) {
        setAvatarVideoId(data.video_id);
        toast.success('Avatar video generation started! Auto-checking status...');
        // Start auto-polling
        pollVideoStatus(data.video_id);
      } else {
        toast.error(data.detail || 'Failed to generate video');
      }
      
      // Also generate TTS audio as immediate playback while video renders
      try {
        const voiceForTts = avatarSettings?.voice_id || 'nova';
        const result = await avatarTeachLesson(lesson.id, voiceForTts);
        if (result.teaching_script) setAvatarScript(result.teaching_script);
        if (result.audio_url) setAvatarAudioUrl(result.audio_url);
      } catch (ttsErr) {
        // TTS is optional fallback
      }
    } catch (error) {
      console.error('Avatar teaching failed:', error);
      const errMsg = error.response?.data?.detail || 'Failed to generate avatar teaching.';
      if (errMsg.includes('Insufficient credit')) {
        toast.error('HeyGen credits exhausted. Please add credits to your HeyGen account.');
      } else {
        toast.error(errMsg);
      }
    } finally {
      setAvatarTeaching(false);
    }
  };

  const pollVideoStatus = (videoId) => {
    let attempts = 0;
    const maxAttempts = 30; // Poll for up to 5 minutes (every 10s)
    
    const interval = setInterval(async () => {
      attempts++;
      try {
        const { data } = await axios.get(`${API}/api/avatar-orchestrator/video-status/${videoId}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('cognify_token')}` }
        });
        
        if (data.status === 'completed' && data.video_url) {
          setAvatarVideoUrl(data.video_url);
          toast.success('Avatar video is ready!');
          clearInterval(interval);
        } else if (data.status === 'failed') {
          const errDetail = data.error?.detail || data.error?.message || 'Video generation failed';
          if (errDetail.includes('Insufficient credit') || errDetail.includes('INSUFFICIENT_CREDIT')) {
            toast.error('HeyGen credits exhausted. Add credits at app.heygen.com');
          } else {
            toast.error(`Video failed: ${errDetail}`);
          }
          clearInterval(interval);
        } else if (attempts >= maxAttempts) {
          toast.info('Video is taking longer than expected. Try checking status later.');
          clearInterval(interval);
        }
      } catch (e) {
        // Silently retry
        if (attempts >= maxAttempts) clearInterval(interval);
      }
    }, 10000);
  };

  const playAvatarAudio = () => {
    if (avatarAudioUrl) {
      if (activeAvatarAudio && !activeAvatarAudio.paused) {
        activeAvatarAudio.pause();
        setAvatarPlaying(false);
        return;
      }
      const fullAvatarUrl = avatarAudioUrl.startsWith('/api/') ? `${API}${avatarAudioUrl}` : avatarAudioUrl;
      const audio = new Audio(fullAvatarUrl);
      setActiveAvatarAudio(audio);
      audio.play();
      setAvatarPlaying(true);
      audio.onended = () => { setAvatarPlaying(false); setActiveAvatarAudio(null); };
    }
  };

  // Generate Video/Slides Content
  const handleGenerateContent = async () => {
    const lesson = content[currentLessonIndex];
    const topic = lesson?.title || course?.name || 'Educational content';
    
    setGeneratingContent(true);
    try {
      if (generateType === 'video') {
        toast.info('Generating video... This may take a few minutes.');
        const result = await generateVideoContent(topic, courseId, 12);
        toast.success('Video generated successfully!');
        // Refresh content to show new video
        loadCourseData();
      } else {
        // Async slides — kick off and poll
        toast.info('Generating slides (background task, ~30-60s)...');
        const start = await generateSlidesContent(topic, courseId, 5);
        const slideshowId = start.slideshow_id;
        if (!slideshowId) throw new Error('No slideshow_id returned');

        let attempts = 0;
        let finalSlides = [];
        while (attempts < 90) { // ~90 * 2s = 3 min max
          await new Promise((r) => setTimeout(r, 2000));
          attempts += 1;
          let statusResp;
          try {
            const { data } = await axios.get(`${API}/api/content/slides-status/${slideshowId}`, {
              headers: { Authorization: `Bearer ${localStorage.getItem('cognify_token')}` }
            });
            statusResp = data;
          } catch (pollErr) {
            console.warn('Slides poll failed', pollErr);
            continue;
          }
          if (statusResp.status === 'completed') {
            finalSlides = statusResp.slides || [];
            break;
          }
          if (statusResp.status === 'failed') {
            throw new Error(statusResp.error || 'Slides generation failed');
          }
        }
        if (finalSlides.length === 0) {
          throw new Error('Slides generation timed out. Please try again.');
        }
        toast.success(`Generated ${finalSlides.length} slides!`);
        loadCourseData();
      }
      setShowGenerateDialog(false);
    } catch (error) {
      console.error('Content generation failed:', error);
      const detail = error.response?.data?.detail;
      const msg = (typeof detail === 'string' ? detail : (detail?.error || detail?.message)) || error.message || `Failed to generate ${generateType}. Please try again.`;
      toast.error(msg);
    } finally {
      setGeneratingContent(false);
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
                {/* KTCE Button for Students */}
                {!isTeacher && (
                  <Button 
                    onClick={() => navigate(`/ktce/${courseId}`)}
                    className="bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600"
                    data-testid="ktce-optimize-btn"
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    KTCE Optimize
                  </Button>
                )}
                
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
                              <SelectItem value="document">
                                <span className="flex items-center gap-2">
                                  <FileSearch className="w-4 h-4" /> Document (PDF/DOCX)
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
                          <div className="space-y-4">
                            {/* Upload Mode Toggle */}
                            <div className="flex gap-2 p-1 bg-zinc-800/50 rounded-lg">
                              <button
                                type="button"
                                onClick={() => setUploadMode('url')}
                                className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
                                  uploadMode === 'url' 
                                    ? 'bg-blue-500 text-white' 
                                    : 'text-zinc-400 hover:text-white'
                                }`}
                              >
                                URL Link
                              </button>
                              <button
                                type="button"
                                onClick={() => setUploadMode('file')}
                                className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
                                  uploadMode === 'file' 
                                    ? 'bg-blue-500 text-white' 
                                    : 'text-zinc-400 hover:text-white'
                                }`}
                              >
                                Upload File
                              </button>
                            </div>
                            
                            {uploadMode === 'url' ? (
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
                            ) : (
                              <div className="space-y-2">
                                <Label>Upload File</Label>
                                <div 
                                  className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                                    selectedFile 
                                      ? 'border-blue-500/50 bg-blue-500/10' 
                                      : 'border-white/20 hover:border-blue-500/50'
                                  }`}
                                >
                                  {selectedFile ? (
                                    <div className="space-y-2">
                                      <CheckCircle className="w-8 h-8 text-blue-400 mx-auto" />
                                      <p className="text-sm text-white font-medium">{selectedFile.name}</p>
                                      <p className="text-xs text-zinc-500">
                                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                      </p>
                                      <Button 
                                        type="button" 
                                        variant="ghost" 
                                        size="sm"
                                        onClick={() => setSelectedFile(null)}
                                        className="text-red-400 hover:text-red-300"
                                      >
                                        <X className="w-4 h-4 mr-1" />
                                        Remove
                                      </Button>
                                    </div>
                                  ) : (
                                    <label className="cursor-pointer">
                                      <Upload className="w-8 h-8 text-zinc-500 mx-auto mb-2" />
                                      <p className="text-sm text-zinc-400 mb-1">Click to upload or drag & drop</p>
                                      <p className="text-xs text-zinc-600">
                                        PDF, DOCX, MP4, MP3, JPG, PNG (max 100MB)
                                      </p>
                                      <input
                                        type="file"
                                        className="hidden"
                                        accept=".pdf,.doc,.docx,.ppt,.pptx,.mp4,.mov,.webm,.mp3,.wav,.jpg,.jpeg,.png,.gif,.webp"
                                        onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                                        data-testid="file-upload-input"
                                      />
                                    </label>
                                  )}
                                </div>
                              </div>
                            )}
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
                      onClick={() => {
                        // Trigger quiz popup when moving to a new lesson (after every 3 lessons for students)
                        if (!isTeacher && currentLessonIndex !== index && (index + 1) % 3 === 0 && !lessonProgress[lesson.id]?.completed) {
                          setQuizLessonId(lesson.id);
                          setShowQuiz(true);
                        }
                        setCurrentLessonIndex(index);
                      }}
                      className={`w-full text-left p-3 rounded-lg transition-all flex items-center gap-3 ${
                        currentLessonIndex === index
                          ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                          : 'hover:bg-white/5 text-zinc-400'
                      }`}
                      data-testid={`lesson-btn-${index}`}
                    >
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                        lessonProgress[lesson.id]?.completed 
                          ? 'bg-emerald-500 text-white' 
                          : currentLessonIndex === index 
                            ? 'bg-blue-500 text-white' 
                            : 'bg-zinc-800'
                      }`}>
                        {lessonProgress[lesson.id]?.completed ? <CheckCircle className="w-4 h-4" /> : index + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="truncate font-medium text-sm">{lesson.title}</p>
                        {lessonProgress[lesson.id]?.completed && (
                          <p className="text-xs text-emerald-400">
                            Quiz: {lessonProgress[lesson.id].score}/{lessonProgress[lesson.id].total}
                          </p>
                        )}
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
              {/* Enrollment Gate Banner */}
              {accessRestricted && (
                <div className="glass-card p-6 mb-6 border-2 border-amber-500/30 bg-amber-500/5" data-testid="enrollment-gate-banner">
                  <div className="flex items-start gap-4">
                    <div className="p-3 rounded-full bg-amber-500/20">
                      <Lock className="w-6 h-6 text-amber-400" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-amber-400 mb-2">
                        Full Content Locked
                      </h3>
                      <p className="text-zinc-400 mb-4">
                        {restrictionMessage || 'Complete payment to access all course content, assignments, and features.'}
                      </p>
                      <div className="flex items-center gap-4">
                        <Button 
                          onClick={() => navigate(`/payment/${courseId}`)}
                          className="bg-amber-500 hover:bg-amber-600 text-black"
                          data-testid="unlock-course-btn"
                        >
                          <CreditCard className="w-4 h-4 mr-2" />
                          Unlock Full Course - ${coursePrice}
                        </Button>
                        <span className="text-sm text-zinc-500">
                          Viewing preview content only
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
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
                        onClick={() => {
                          if (audioPlaying) {
                            playAudio(); // toggle pause for both cloud and browser TTS
                          } else if (audioUrl) {
                            playAudio();
                          } else if ('speechSynthesis' in window && window.speechSynthesis.paused) {
                            playAudio(); // resume browser TTS
                          } else {
                            handleGenerateAudio(displayText);
                          }
                        }}
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
                      {/* Key Points from generated lessons */}
                      {currentLesson?.key_points && currentLesson.key_points.length > 0 && (
                        <div className="mt-6 p-4 rounded-xl bg-violet-500/10 border border-violet-500/20">
                          <h3 className="text-sm font-semibold text-violet-400 mb-2">Key Points</h3>
                          <ul className="space-y-1.5">
                            {currentLesson.key_points.map((kp, i) => (
                              <li key={i} className="text-sm text-zinc-300 flex items-start gap-2">
                                <CheckCircle className="w-4 h-4 text-violet-400 mt-0.5 shrink-0" />
                                {kp}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </TabsContent>

                  <TabsContent value="video" className="mt-0">
                    {(currentLesson?.video_url || currentLesson?.url) && currentLesson?.type === 'video' ? (
                      <div className="aspect-video bg-zinc-900 rounded-xl overflow-hidden border border-white/10">
                        {(currentLesson.video_url || currentLesson.url).includes('youtube.com') || (currentLesson.video_url || currentLesson.url).includes('youtu.be') ? (
                          <iframe
                            src={(currentLesson.video_url || currentLesson.url).replace('watch?v=', 'embed/')}
                            className="w-full h-full"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowFullScreen
                          />
                        ) : (
                          <video
                            src={currentLesson.video_url || currentLesson.url}
                            controls
                            className="w-full h-full"
                            data-testid="video-player"
                          >
                            Your browser does not support the video tag.
                          </video>
                        )}
                      </div>
                    ) : (
                      <div className="aspect-video bg-zinc-900 rounded-xl flex items-center justify-center border border-white/10">
                        {avatarVideoUrl ? (
                          <video src={`${API}${avatarVideoUrl}`} controls autoPlay className="w-full h-full rounded-xl" data-testid="sora-video-player" />
                        ) : avatarVideoId ? (
                          <div className="text-center">
                            <Loader2 className="w-12 h-12 text-violet-400 mx-auto mb-3 animate-spin" />
                            <p className="text-violet-300 font-medium">Video generating...</p>
                            <p className="text-zinc-500 text-sm mt-1">Auto-checking. Takes 2-5 minutes.</p>
                          </div>
                        ) : (
                          <div className="text-center">
                            <Video className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
                            <p className="text-zinc-500 mb-4">No video uploaded for this lesson</p>
                          <div className="flex gap-3 justify-center flex-wrap">
                            {isTeacher && (
                              <Button 
                                onClick={() => setShowUploadDialog(true)}
                                className="bg-blue-500 hover:bg-blue-600"
                              >
                                <Upload className="w-4 h-4 mr-2" />
                                Upload Video
                              </Button>
                            )}
                            <Button 
                              onClick={async () => {
                                setGeneratingVideo(true);
                                try {
                                  const lessonText = currentLesson?.text || currentLesson?.content || displayText || '';
                                  const lessonTitle = currentLesson?.title || course?.name || 'Lesson';
                                  if (!lessonText) {
                                    toast.error('No lesson content to generate video from. Select a text lesson first.');
                                    setGeneratingVideo(false);
                                    return;
                                  }
                                  // Use Sora 2 via Emergent LLM for video generation (async)
                                  const { data } = await axios.post(`${API}/api/content/generate-video`, null, {
                                    params: {
                                      topic: lessonTitle,
                                      course_id: courseId,
                                      duration: 12
                                    },
                                    headers: { Authorization: `Bearer ${localStorage.getItem('cognify_token')}` },
                                    timeout: 30000
                                  });
                                  if (data.video_id) {
                                    toast.success('Video generation started! It takes 2-5 minutes. Auto-checking...');
                                    setAvatarVideoId(data.video_id);
                                    // Poll for video completion
                                    const poll = setInterval(async () => {
                                      try {
                                        const { data: status } = await axios.get(`${API}/api/content/video-status/${data.video_id}`, {
                                          headers: { Authorization: `Bearer ${localStorage.getItem('cognify_token')}` }
                                        });
                                        if (status.status === 'completed' && status.video_url) {
                                          setAvatarVideoUrl(status.video_url);
                                          toast.success('Video ready!');
                                          clearInterval(poll);
                                        } else if (status.status === 'failed') {
                                          toast.error('Video generation failed: ' + (status.error || 'Unknown'));
                                          clearInterval(poll);
                                        }
                                      } catch (pe) { /* silent retry */ }
                                    }, 15000);
                                    // Stop after 8 min
                                    setTimeout(() => clearInterval(poll), 480000);
                                  } else {
                                    toast.error(data.detail || 'Failed to start video generation');
                                  }
                                } catch (e) {
                                  console.error('Video generation error:', e);
                                  const msg = e.response?.data?.detail || 'Failed to generate video';
                                  toast.error(msg.includes('timeout') ? 'Video generation is taking long. It may still complete.' : msg);
                                } finally {
                                  setGeneratingVideo(false);
                                }
                              }}
                              disabled={generatingVideo}
                              className="bg-violet-500 hover:bg-violet-600"
                              data-testid="generate-avatar-video-btn"
                            >
                              {generatingVideo ? (
                                <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating Video...</>
                              ) : (
                                <><Wand2 className="w-4 h-4 mr-2" /> AI Generate Video</>
                              )}
                            </Button>
                          </div>
                        </div>
                        )}
                      </div>
                    )}
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
                        <p className="text-zinc-400">Listen to this lesson while you&apos;re on the go</p>
                      </div>
                      
                      {(audioUrl || audioPlaying) ? (
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
                      {(() => {
                        const prefixUrl = (u) => (u && u.startsWith('/api/')) ? `${API}${u}` : u;
                        if (currentLesson?.image_url || currentLesson?.slides_url || (currentLesson?.url && currentLesson?.type === 'image')) {
                          return (
                            <div className="aspect-video bg-zinc-900 rounded-xl overflow-hidden border border-white/10">
                              <img
                                src={prefixUrl(currentLesson.image_url || currentLesson.slides_url || currentLesson.url)}
                                alt={currentLesson.title}
                                className="w-full h-full object-contain"
                              />
                            </div>
                          );
                        }
                        if (currentLesson?.slides && currentLesson.slides.length > 0) {
                          return (
                            <div className="space-y-4">
                              {currentLesson.slides.map((slide, idx) => (
                                <div key={slide.id || idx} className="bg-gradient-to-br from-blue-500/5 to-violet-500/5 rounded-xl border border-white/10 p-6">
                                  <h3 className="text-2xl font-bold mb-4 text-center">{slide.title || `Slide ${idx + 1}`}</h3>
                                  {slide.image_url && (
                                    <div className="bg-zinc-900 rounded-lg overflow-hidden mb-4">
                                      <img
                                        src={prefixUrl(slide.image_url)}
                                        alt={slide.title || `Slide ${idx + 1}`}
                                        className="w-full max-h-[520px] object-contain mx-auto"
                                        data-testid={`slide-image-${idx}`}
                                        onError={(e) => { e.target.style.display = 'none'; console.warn('Slide image failed to load:', slide.image_url); }}
                                      />
                                    </div>
                                  )}
                                  {(slide.content || slide.description) && (
                                    <p className="text-zinc-300 text-base whitespace-pre-wrap text-center max-w-3xl mx-auto">
                                      {slide.content || slide.description}
                                    </p>
                                  )}
                                </div>
                              ))}
                            </div>
                          );
                        }
                        return null;
                      })()}
                      {!(currentLesson?.image_url || currentLesson?.slides_url || (currentLesson?.url && currentLesson?.type === 'image') || (currentLesson?.slides && currentLesson.slides.length > 0)) && (
                        <div className="aspect-video bg-gradient-to-br from-blue-500/5 to-violet-500/5 rounded-xl flex items-center justify-center border border-white/10 p-8">
                          <div className="text-center max-w-2xl">
                            <div className="w-20 h-20 bg-blue-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                              <Image className="w-10 h-10 text-blue-400" />
                            </div>
                            <h3 className="text-2xl font-bold mb-4">{currentLesson?.title}</h3>
                            <p className="text-zinc-400 text-lg mb-6">
                              {currentLesson?.description || displayText.substring(0, 200)}
                            </p>
                            <div className="flex gap-3 justify-center flex-wrap">
                              {isTeacher && (
                                <Button 
                                  onClick={() => {
                                    setNewContent({ ...newContent, type: 'image' });
                                    setShowUploadDialog(true);
                                  }}
                                  className="bg-blue-500 hover:bg-blue-600"
                                >
                                  <Upload className="w-4 h-4 mr-2" />
                                  Upload Slides
                                </Button>
                              )}
                              <Button 
                                onClick={async () => {
                                  setGeneratingSlides(true);
                                  try {
                                    const lessonTitle = currentLesson?.title || content[currentLessonIndex]?.title || course?.name || 'Lesson';
                                    const authHeader = { Authorization: `Bearer ${localStorage.getItem('cognify_token')}` };

                                    // Kick off async background job
                                    const { data: start } = await axios.post(`${API}/api/content/generate-slides`, null, {
                                      params: { topic: lessonTitle, course_id: courseId, slide_count: 5 },
                                      headers: authHeader,
                                      timeout: 30000,
                                    });
                                    const slideshowId = start.slideshow_id;
                                    if (!slideshowId) throw new Error('No slideshow_id returned');
                                    toast.info('Slides generation started — this takes ~30-60 seconds...');

                                    // Poll for status (every 2s, up to 3 min)
                                    let attempts = 0;
                                    let finalSlides = [];
                                    while (attempts < 90) {
                                      await new Promise((r) => setTimeout(r, 2000));
                                      attempts += 1;
                                      let st;
                                      try {
                                        const { data } = await axios.get(`${API}/api/content/slides-status/${slideshowId}`, { headers: authHeader });
                                        st = data;
                                      } catch (pe) {
                                        continue;
                                      }
                                      if (st.status === 'completed') {
                                        finalSlides = st.slides || [];
                                        break;
                                      }
                                      if (st.status === 'failed') {
                                        throw new Error(st.error || 'Slides generation failed');
                                      }
                                    }
                                    if (finalSlides.length === 0) {
                                      toast.warning('Slides are still being generated. Refresh the page in a moment.');
                                    } else {
                                      toast.success(`Generated ${finalSlides.length} pictorial slides!`);
                                      // Reload course content, then jump to the newly created slides lesson
                                      const refreshed = await loadCourseData();
                                      const newContentId = `content-${slideshowId}`;
                                      const list = Array.isArray(refreshed) ? refreshed : null;
                                      if (list) {
                                        const newIdx = list.findIndex((c) => c.id === newContentId || c.slideshow_id === slideshowId);
                                        if (newIdx >= 0) setCurrentLessonIndex(newIdx);
                                      }
                                      // Ensure user is on the Slides view mode
                                      setSelectedMode('slides');
                                    }
                                  } catch (e) {
                                    console.error('Slides error:', e);
                                    const detail = e.response?.data?.detail;
                                    const msg = (typeof detail === 'string' ? detail : (detail?.error || detail?.message)) || e.message || 'Failed to generate slides';
                                    toast.error(msg);
                                  } finally {
                                    setGeneratingSlides(false);
                                  }
                                }}
                                disabled={generatingSlides}
                                className="bg-cyan-600 hover:bg-cyan-700"
                                data-testid="auto-generate-slides-btn"
                              >
                                {generatingSlides ? (
                                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating Slides...</>
                                ) : (
                                  <><Wand2 className="w-4 h-4 mr-2" /> AI Generate Slides</>
                                )}
                              </Button>
                            </div>
                          </div>
                        </div>
                      )}
                      
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
                              {lesson.image_url ? (
                                <img src={lesson.image_url.startsWith('/api/') ? `${API}${lesson.image_url}` : lesson.image_url} alt="" className="w-full h-full object-cover rounded-md" />
                              ) : (
                                <span className="text-sm font-medium">{index + 1}</span>
                              )}
                            </div>
                          </button>
                        ))}
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="avatar" className="mt-0">
                    <div className="space-y-6">
                      {/* Avatar Teaching Section */}
                      <div className="p-8 bg-gradient-to-br from-violet-500/10 via-blue-500/10 to-cyan-500/10 rounded-xl border border-white/10">
                        <div className="flex items-start gap-6 mb-6">
                          {/* Avatar Display */}
                          <div className="flex-shrink-0">
                            <div className="w-24 h-24 rounded-full overflow-hidden border-4 border-violet-500/30 bg-zinc-800">
                              {avatarSettings?.avatar_image ? (
                                <img 
                                  src={avatarSettings.avatar_image} 
                                  alt="AI Tutor"
                                  className="w-full h-full object-cover"
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-violet-500/20 to-blue-500/20">
                                  <User className="w-12 h-12 text-violet-400" />
                                </div>
                              )}
                            </div>
                            <p className="text-center mt-2 font-medium text-sm">
                              {avatarSettings?.avatar_name || 'AI Tutor'}
                            </p>
                          </div>
                          
                          {/* Avatar Info */}
                          <div className="flex-1">
                            <h3 className="text-xl font-bold mb-2">Avatar-Guided Learning</h3>
                            <p className="text-zinc-400 mb-4">
                              Let your personal AI tutor explain this lesson to you in an engaging, conversational way.
                            </p>
                            <div className="flex items-center gap-2 text-sm text-zinc-500">
                              <Badge className="bg-violet-500/20 text-violet-400">
                                {avatarSettings?.teaching_style || 'Friendly'} Style
                              </Badge>
                              <Badge className="bg-blue-500/20 text-blue-400">
                                Voice: {avatarSettings?.voice_id || 'Nova'}
                              </Badge>
                            </div>
                          </div>
                        </div>
                        
                        {/* Generate / Play Buttons */}
                        <div className="flex gap-3">
                          <Button
                            onClick={handleAvatarTeach}
                            disabled={avatarTeaching}
                            className="flex-1 bg-violet-500 hover:bg-violet-600"
                            data-testid="avatar-teach-btn"
                          >
                            {avatarTeaching ? (
                              <>
                                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                Generating Lesson...
                              </>
                            ) : (
                              <>
                                <Sparkles className="w-5 h-5 mr-2" />
                                {avatarScript ? 'Regenerate Lesson' : 'Start Avatar Teaching'}
                              </>
                            )}
                          </Button>
                          
                          {avatarAudioUrl && (
                            <Button
                              onClick={playAvatarAudio}
                              variant="outline"
                              className="border-violet-500/30 text-violet-400"
                              data-testid="avatar-audio-btn"
                            >
                              {avatarPlaying ? <Pause className="w-5 h-5 mr-2" /> : <Play className="w-5 h-5 mr-2" />}
                              {avatarPlaying ? 'Pause' : 'Play Audio'}
                            </Button>
                          )}
                          
                          <Button
                            variant="outline"
                            onClick={() => navigate('/avatar-settings')}
                            className="border-white/10"
                          >
                            <User className="w-4 h-4 mr-2" />
                            Customize
                          </Button>
                        </div>
                      </div>
                      
                      {/* Avatar Teaching Script */}
                      {avatarScript && (
                        <div className="glass-card p-6">
                          <h4 className="font-semibold mb-4 flex items-center gap-2">
                            <BookOpen className="w-5 h-5 text-violet-400" />
                            Avatar Teaching
                          </h4>
                          
                          {/* HeyGen Video Player */}
                          {avatarVideoUrl && (
                            <div className="mb-4 rounded-xl overflow-hidden border border-violet-500/20">
                              <video 
                                src={avatarVideoUrl} 
                                controls 
                                autoPlay
                                className="w-full max-h-[450px]" 
                                data-testid="avatar-video-player"
                              />
                            </div>
                          )}
                          
                          {/* Video Status (while rendering) */}
                          {avatarVideoId && !avatarVideoUrl && (
                            <div className="mb-4 p-4 bg-violet-500/10 rounded-xl border border-violet-500/20">
                              <div className="flex items-center gap-3">
                                <Loader2 className="w-5 h-5 text-violet-400 animate-spin" />
                                <div>
                                  <p className="text-sm font-medium text-violet-300">HeyGen Avatar Video Rendering...</p>
                                  <p className="text-xs text-zinc-500">Auto-checking every 10 seconds. Video will appear here when ready.</p>
                                </div>
                              </div>
                            </div>
                          )}
                          
                          {/* Teaching Script Text */}
                          <div className="prose prose-invert max-w-none">
                            <p className="text-xs text-zinc-500 mb-2 uppercase tracking-wider">Teaching Script</p>
                            <div className="text-zinc-300 leading-relaxed whitespace-pre-wrap bg-zinc-900/50 p-4 rounded-lg max-h-64 overflow-y-auto text-sm">
                              {avatarScript.split('\n').map((line, i) => (
                                <p key={i} className="my-1.5">{line}</p>
                              ))}
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {/* No Avatar Script Yet */}
                      {!avatarScript && !avatarTeaching && (
                        <div className="text-center py-8">
                          <User className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
                          <p className="text-zinc-500">
                            Click &quot;Start Avatar Teaching&quot; to have your AI tutor explain this lesson
                          </p>
                        </div>
                      )}
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
              
              {/* Research Papers Section */}
              {researchPapers.length > 0 && (
                <div className="glass-card p-6 mt-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <FileSearch className="w-5 h-5 text-violet-400" />
                    Related Research Publications
                  </h3>
                  <div className="space-y-3">
                    {researchPapers.map((paper, idx) => (
                      <a 
                        key={idx} 
                        href={paper.url}
                        className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50 hover:bg-zinc-800 transition-colors group"
                      >
                        <div>
                          <p className="font-medium text-sm group-hover:text-blue-400 transition-colors">{paper.title}</p>
                          <p className="text-xs text-zinc-500">{paper.journal} • {paper.year}</p>
                        </div>
                        <ExternalLink className="w-4 h-4 text-zinc-500 group-hover:text-blue-400" />
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Micro-Hint Popup */}
        {showHint && (
          <div className="fixed bottom-6 right-6 z-50 max-w-md animate-in slide-in-from-bottom-5">
            <div className="glass-card p-4 border-yellow-500/30 bg-gradient-to-r from-yellow-500/10 to-amber-500/10">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-yellow-500/20 flex items-center justify-center flex-shrink-0">
                  <Lightbulb className="w-5 h-5 text-yellow-400" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-yellow-400">Learning Hint</h4>
                    <button 
                      onClick={() => setShowHint(false)}
                      className="text-zinc-500 hover:text-white"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                  <p className="text-sm text-zinc-300">{currentHint}</p>
                  <div className="flex gap-2 mt-3">
                    <Button 
                      size="sm" 
                      variant="outline" 
                      onClick={() => setShowHint(false)}
                      className="border-white/10 text-xs"
                    >
                      Got it!
                    </Button>
                    <Button 
                      size="sm" 
                      onClick={() => { setShowHint(false); generateMicroHint(); }}
                      className="bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 text-xs"
                    >
                      Another hint
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* AI Content Generation Dialog */}
        <Dialog open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
          <DialogContent className="bg-zinc-900 border-white/10">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Wand2 className="w-5 h-5 text-violet-400" />
                AI Content Generation
              </DialogTitle>
              <DialogDescription className="text-zinc-500">
                Generate educational content using AI for this lesson
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <Label>Content Type</Label>
                <div className="grid grid-cols-2 gap-3 mt-2">
                  <button
                    onClick={() => setGenerateType('video')}
                    className={`p-4 rounded-xl border-2 text-center transition-all ${
                      generateType === 'video'
                        ? 'border-violet-500 bg-violet-500/10'
                        : 'border-white/10 hover:border-white/20'
                    }`}
                  >
                    <Video className="w-8 h-8 mx-auto mb-2 text-violet-400" />
                    <p className="font-medium">Video</p>
                    <p className="text-xs text-zinc-500">4-12 second explainer</p>
                  </button>
                  <button
                    onClick={() => setGenerateType('slides')}
                    className={`p-4 rounded-xl border-2 text-center transition-all ${
                      generateType === 'slides'
                        ? 'border-blue-500 bg-blue-500/10'
                        : 'border-white/10 hover:border-white/20'
                    }`}
                  >
                    <Image className="w-8 h-8 mx-auto mb-2 text-blue-400" />
                    <p className="font-medium">Slides</p>
                    <p className="text-xs text-zinc-500">5 visual slides</p>
                  </button>
                </div>
              </div>
              
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                <p className="text-sm text-amber-300 flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  {generateType === 'video' 
                    ? 'Video generation uses Sora 2 and may take 2-5 minutes'
                    : 'Slides use Gemini Nano Banana for educational visuals'}
                </p>
              </div>
              
              <div className="flex justify-end gap-3 pt-4">
                <Button variant="ghost" onClick={() => setShowGenerateDialog(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={handleGenerateContent}
                  disabled={generatingContent}
                  className="bg-violet-500 hover:bg-violet-600"
                >
                  {generatingContent ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Wand2 className="w-4 h-4 mr-2" />
                      Generate {generateType === 'video' ? 'Video' : 'Slides'}
                    </>
                  )}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Popup Quiz Component */}
        <PopupQuiz
          isOpen={showQuiz}
          onClose={() => setShowQuiz(false)}
          lessonId={quizLessonId}
          courseId={courseId}
          lessonTitle={currentLesson?.title}
          onComplete={(score, total) => {
            setLessonProgress(prev => ({
              ...prev,
              [quizLessonId]: { score, total, completed: true }
            }));
            toast.success(`Quiz completed! Score: ${score}/${total}`);
          }}
        />
      </div>
    </DashboardLayout>
  );
}
