import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';
import {
  Layers,
  BookOpen,
  Play,
  CheckCircle,
  Clock,
  ArrowLeft,
  ArrowRight,
  Target,
  RefreshCw,
  Video,
  FileText,
  ChevronRight,
  Lock
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function MultiSubjectLearningPage() {
  const { pathId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [learningPath, setLearningPath] = useState(null);
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [selectedLesson, setSelectedLesson] = useState(null);
  const [lessonContent, setLessonContent] = useState(null);

  useEffect(() => {
    if (pathId) {
      loadLearningPath();
    }
  }, [pathId]);

  const loadLearningPath = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      
      // Get the learning path details
      const pathResponse = await fetch(`${API}/api/multi-subject/${pathId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!pathResponse.ok) {
        toast.error('Learning path not found');
        navigate('/multi-subject');
        return;
      }
      
      const path = await pathResponse.json();
      setLearningPath(path);
      
      // Load course details for each course in the path
      const courseDetails = [];
      const courseIds = path.selected_courses || path.subjects || [];
      
      for (const courseId of courseIds) {
        const courseResponse = await fetch(`${API}/api/courses/${courseId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (courseResponse.ok) {
          const course = await courseResponse.json();
          courseDetails.push(course);
        }
      }
      
      setCourses(courseDetails);
      
      // Auto-select first course
      if (courseDetails.length > 0) {
        setSelectedCourse(courseDetails[0]);
        loadLessons(courseDetails[0].id);
      }
    } catch (error) {
      console.error('Failed to load learning path:', error);
      toast.error('Failed to load learning path');
    } finally {
      setLoading(false);
    }
  };

  const loadLessons = async (courseId) => {
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/courses/${courseId}/lessons`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setLessons(data || []);
        
        // Auto-select first lesson
        if (data && data.length > 0) {
          setSelectedLesson(data[0]);
          setLessonContent(data[0]);
        }
      }
    } catch (error) {
      console.error('Failed to load lessons:', error);
    }
  };

  const handleSelectCourse = (course) => {
    setSelectedCourse(course);
    setSelectedLesson(null);
    setLessonContent(null);
    loadLessons(course.id);
  };

  const handleSelectLesson = (lesson) => {
    setSelectedLesson(lesson);
    setLessonContent(lesson);
  };

  const markLessonComplete = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      await fetch(`${API}/api/lessons/${selectedLesson.id}/complete`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      toast.success('Lesson completed!');
      
      // Move to next lesson
      const currentIndex = lessons.findIndex(l => l.id === selectedLesson.id);
      if (currentIndex < lessons.length - 1) {
        handleSelectLesson(lessons[currentIndex + 1]);
      }
    } catch (error) {
      console.error('Failed to mark complete:', error);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <RefreshCw className="w-8 h-8 animate-spin text-violet-500" />
        </div>
      </DashboardLayout>
    );
  }

  if (!learningPath) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
          <Layers className="w-16 h-16 text-zinc-600 mb-4" />
          <h2 className="text-xl font-semibold mb-2">Learning Path Not Found</h2>
          <p className="text-zinc-500 mb-4">This learning path doesn't exist or you don't have access.</p>
          <Button onClick={() => navigate('/multi-subject')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Multi-Subject
          </Button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header 
        title={learningPath.name}
        subtitle="Multi-Subject Learning Path"
      />

      <div className="p-8">
        {/* Path Overview */}
        <div className="glass-card p-6 mb-6">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-xl bg-violet-500/20">
                <Layers className="w-8 h-8 text-violet-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold">{learningPath.name}</h2>
                <p className="text-zinc-500">{learningPath.description || learningPath.goal}</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="text-sm text-zinc-500">Overall Progress</p>
                <p className="text-2xl font-bold text-violet-400">{learningPath.progress || 0}%</p>
              </div>
              <Progress value={learningPath.progress || 0} className="w-32 h-3" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Course List Sidebar */}
          <div className="glass-card p-4 space-y-3">
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-violet-400" />
              Courses ({courses.length})
            </h3>
            
            {courses.map((course, idx) => (
              <button
                key={course.id}
                onClick={() => handleSelectCourse(course)}
                className={`w-full p-3 rounded-lg text-left transition-all ${
                  selectedCourse?.id === course.id
                    ? 'bg-violet-500/20 border border-violet-500/30'
                    : 'bg-zinc-800/50 hover:bg-zinc-800 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                    selectedCourse?.id === course.id ? 'bg-violet-500 text-white' : 'bg-zinc-700'
                  }`}>
                    {idx + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{course.title}</p>
                    <p className="text-xs text-zinc-500">{course.lessons?.length || 0} lessons</p>
                  </div>
                </div>
              </button>
            ))}

            <Button 
              variant="outline" 
              className="w-full mt-4 border-white/10"
              onClick={() => navigate('/multi-subject')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Paths
            </Button>
          </div>

          {/* Lesson List */}
          <div className="glass-card p-4 space-y-3">
            <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-400" />
              Lessons
            </h3>
            
            {lessons.length === 0 ? (
              <p className="text-zinc-500 text-center py-8">
                No lessons available for this course
              </p>
            ) : (
              lessons.map((lesson, idx) => (
                <button
                  key={lesson.id}
                  onClick={() => handleSelectLesson(lesson)}
                  className={`w-full p-3 rounded-lg text-left transition-all ${
                    selectedLesson?.id === lesson.id
                      ? 'bg-blue-500/20 border border-blue-500/30'
                      : 'bg-zinc-800/50 hover:bg-zinc-800 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                      lesson.completed ? 'bg-emerald-500' : 'bg-zinc-700'
                    }`}>
                      {lesson.completed ? <CheckCircle className="w-4 h-4" /> : idx + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{lesson.title}</p>
                      <p className="text-xs text-zinc-500">{lesson.duration || '15 min'}</p>
                    </div>
                    <ChevronRight className="w-4 h-4 text-zinc-500" />
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Lesson Content */}
          <div className="lg:col-span-2 glass-card p-6">
            {lessonContent ? (
              <div className="space-y-6">
                <div className="flex items-start justify-between">
                  <div>
                    <Badge className="mb-2 bg-violet-500/20 text-violet-400">
                      {selectedCourse?.title}
                    </Badge>
                    <h2 className="text-2xl font-bold">{lessonContent.title}</h2>
                    <div className="flex items-center gap-4 mt-2 text-sm text-zinc-500">
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {lessonContent.duration || '15 min'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="prose prose-invert max-w-none">
                  <p className="text-zinc-400">{lessonContent.description}</p>
                  
                  {lessonContent.text && (
                    <div className="mt-4 p-4 rounded-lg bg-zinc-800/50 border border-white/5">
                      <div className="whitespace-pre-wrap">{lessonContent.text}</div>
                    </div>
                  )}

                  {lessonContent.key_points && lessonContent.key_points.length > 0 && (
                    <div className="mt-4">
                      <h4 className="font-semibold mb-2 flex items-center gap-2">
                        <Target className="w-4 h-4 text-emerald-400" />
                        Key Points
                      </h4>
                      <ul className="space-y-2">
                        {lessonContent.key_points.map((point, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-sm">
                            <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />
                            <span>{point}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Video if available */}
                {lessonContent.video_url && (
                  <div className="rounded-xl overflow-hidden bg-black">
                    <video 
                      src={lessonContent.video_url} 
                      controls 
                      className="w-full"
                    />
                  </div>
                )}

                <div className="flex gap-4 pt-4 border-t border-white/10">
                  <Button 
                    onClick={markLessonComplete}
                    className="flex-1 bg-emerald-500 hover:bg-emerald-600"
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Mark as Complete
                  </Button>
                  {lessons.findIndex(l => l.id === selectedLesson?.id) < lessons.length - 1 && (
                    <Button 
                      variant="outline"
                      onClick={() => {
                        const idx = lessons.findIndex(l => l.id === selectedLesson?.id);
                        handleSelectLesson(lessons[idx + 1]);
                      }}
                      className="border-white/10"
                    >
                      Next Lesson
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16">
                <Play className="w-16 h-16 text-zinc-600 mb-4" />
                <h3 className="text-lg font-medium mb-2">Select a Lesson</h3>
                <p className="text-zinc-500 text-center">
                  Choose a lesson from the list to start learning
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
