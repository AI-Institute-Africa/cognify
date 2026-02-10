import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { 
  Sparkles,
  Rocket,
  CheckCircle,
  Clock,
  Target,
  RefreshCw,
  ArrowRight,
  Lightbulb,
  BookOpen,
  FileText,
  Video,
  Layers,
  DollarSign,
  Users,
  Brain,
  Zap,
  GraduationCap,
  Globe
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { toast } from 'sonner';

const COURSE_EXAMPLES = [
  "Complete Web Development Bootcamp from scratch to job-ready",
  "Master Data Analysis with Python and Excel",
  "Introduction to African History and Culture",
  "Business English for Professionals",
  "Machine Learning Fundamentals for Beginners"
];

const COURSE_TYPES = [
  { id: 'free_custom', name: 'Free Custom Course', price: 0, description: 'Create and share free courses' },
  { id: 'custom_basic', name: 'Basic Custom Course', price: 49.99, description: 'AI-generated content with basic features' },
  { id: 'custom_advanced', name: 'Advanced Custom Course', price: 149.99, description: 'Full AI content generation with assessments' },
];

// AI Features for advanced course creation
const AI_FEATURES = [
  { 
    id: 'ktce', 
    name: 'KTCE (Knowledge Time Compression)', 
    description: 'Compress learning time with AI-optimized content delivery',
    icon: Zap,
    color: 'violet'
  },
  { 
    id: 'adaptive', 
    name: 'Adaptive Learning', 
    description: 'Personalized learning paths based on student performance',
    icon: Brain,
    color: 'blue'
  },
  { 
    id: 'avatar', 
    name: 'AI Avatar Teaching', 
    description: 'Virtual AI instructor for interactive lessons',
    icon: Users,
    color: 'emerald'
  },
  { 
    id: 'realtime_feedback', 
    name: 'Real-time Feedback', 
    description: 'Instant AI feedback on assignments and quizzes',
    icon: Lightbulb,
    color: 'amber'
  },
  { 
    id: 'multilingual', 
    name: 'Multilingual Support', 
    description: 'Auto-translate content to multiple languages',
    icon: Globe,
    color: 'cyan'
  },
  { 
    id: 'micro_hints', 
    name: 'Micro-Hints', 
    description: 'Context-aware learning hints during lessons',
    icon: Sparkles,
    color: 'pink'
  }
];

export default function CreateCustomCoursePage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1: Define, 2: Configure, 3: Generate, 4: Preview
  const [loading, setLoading] = useState(false);
  const [generatedCourse, setGeneratedCourse] = useState(null);
  
  const [courseData, setCourseData] = useState({
    title: '',
    description: '',
    learningGoal: '',
    targetAudience: 'beginner',
    estimatedDuration: '4',
    numLessons: 10,
    courseType: 'free_custom',
    includeQuizzes: true,
    includeVideo: false,
    includeSlides: true,
    language: 'en',
    topics: [],
    // AI Features selection
    aiFeatures: {
      ktce: false,
      adaptive: false,
      avatar: false,
      realtime_feedback: true,
      multilingual: false,
      micro_hints: true
    }
  });

  const API = process.env.REACT_APP_BACKEND_URL;

  const handleChange = (field, value) => {
    setCourseData(prev => ({ ...prev, [field]: value }));
  };

  const handleGenerateCourse = async () => {
    if (!courseData.title.trim() || !courseData.learningGoal.trim()) {
      toast.error('Please fill in the course title and learning goal');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/courses/generate-custom`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          title: courseData.title,
          description: courseData.description || courseData.learningGoal,
          learning_goal: courseData.learningGoal,
          target_audience: courseData.targetAudience,
          duration_weeks: parseInt(courseData.estimatedDuration),
          num_lessons: courseData.numLessons,
          course_type: courseData.courseType,
          include_quizzes: courseData.includeQuizzes,
          include_video: courseData.includeVideo,
          include_slides: courseData.includeSlides,
          language: courseData.language
        })
      });

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.detail || 'Failed to generate course');
      }

      setGeneratedCourse(result);
      setStep(4);
      toast.success('Course generated successfully!');
    } catch (error) {
      console.error('Course generation error:', error);
      toast.error(error.message || 'Failed to generate course');
    } finally {
      setLoading(false);
    }
  };

  const handlePublishCourse = async () => {
    if (!generatedCourse?.course_id) {
      toast.error('No course to publish');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/courses/${generatedCourse.course_id}/publish`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to publish course');

      toast.success('Course published successfully!');
      navigate(`/courses/${generatedCourse.course_id}`);
    } catch (error) {
      console.error('Publish error:', error);
      toast.error('Failed to publish course');
    } finally {
      setLoading(false);
    }
  };

  const selectExample = (example) => {
    handleChange('learningGoal', example);
    // Auto-generate title from example
    const words = example.split(' ').slice(0, 5).join(' ');
    handleChange('title', words);
  };

  const getPrice = () => {
    const type = COURSE_TYPES.find(t => t.id === courseData.courseType);
    return type ? type.price : 0;
  };

  return (
    <DashboardLayout>
      <Header 
        title="Create Custom Course"
        subtitle="Design your own AI-powered learning experience"
      />
      
      <div className="p-8">
        <div className="max-w-5xl mx-auto">
          {/* Progress Steps */}
          <div className="flex items-center justify-between mb-8">
            {[
              { num: 1, label: 'Define Course' },
              { num: 2, label: 'Configure' },
              { num: 3, label: 'Generate' },
              { num: 4, label: 'Preview & Publish' }
            ].map((s, idx) => (
              <div key={s.num} className="flex items-center">
                <div 
                  className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    step >= s.num ? 'bg-violet-500 text-white' : 'bg-zinc-800 text-zinc-500'
                  }`}
                >
                  {step > s.num ? <CheckCircle className="w-5 h-5" /> : s.num}
                </div>
                <span className={`ml-2 text-sm ${step >= s.num ? 'text-white' : 'text-zinc-500'}`}>
                  {s.label}
                </span>
                {idx < 3 && (
                  <div className={`w-16 h-0.5 mx-4 ${step > s.num ? 'bg-violet-500' : 'bg-zinc-800'}`} />
                )}
              </div>
            ))}
          </div>

          {/* Info Banner */}
          <div className="glass-card p-6 mb-8 bg-gradient-to-r from-violet-500/10 to-purple-500/10 border-violet-500/20">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-violet-500/20 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-violet-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-1">Create Your Own Course</h3>
                <p className="text-zinc-400 text-sm">
                  Define your learning goal and let AI generate a complete course with lessons, 
                  quizzes, and content tailored to your needs. Free or premium options available.
                </p>
              </div>
            </div>
          </div>

          {/* Step 1: Define Course */}
          {step === 1 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="glass-card p-6 space-y-6">
                <h3 className="font-semibold flex items-center gap-2">
                  <Rocket className="w-5 h-5 text-violet-400" />
                  Define Your Course
                </h3>

                <div className="space-y-4">
                  <div>
                    <Label htmlFor="title">Course Title</Label>
                    <Input
                      id="title"
                      placeholder="e.g., Complete Python Programming"
                      value={courseData.title}
                      onChange={(e) => handleChange('title', e.target.value)}
                      className="mt-1 bg-zinc-800 border-white/10"
                      data-testid="course-title-input"
                    />
                  </div>

                  <div>
                    <Label htmlFor="learningGoal">What will students learn?</Label>
                    <Textarea
                      id="learningGoal"
                      placeholder="Describe the main learning outcome... Be specific about skills they'll gain."
                      value={courseData.learningGoal}
                      onChange={(e) => handleChange('learningGoal', e.target.value)}
                      className="mt-1 min-h-[120px] bg-zinc-800 border-white/10"
                      data-testid="learning-goal-input"
                    />
                  </div>

                  <div>
                    <Label htmlFor="description">Course Description (optional)</Label>
                    <Textarea
                      id="description"
                      placeholder="Additional details about your course..."
                      value={courseData.description}
                      onChange={(e) => handleChange('description', e.target.value)}
                      className="mt-1 bg-zinc-800 border-white/10"
                    />
                  </div>
                </div>

                <Button
                  onClick={() => setStep(2)}
                  disabled={!courseData.title.trim() || !courseData.learningGoal.trim()}
                  className="w-full bg-violet-500 hover:bg-violet-600"
                >
                  Continue to Configuration
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>

              {/* Examples Section */}
              <div className="glass-card p-6 space-y-4">
                <h3 className="font-semibold flex items-center gap-2">
                  <Lightbulb className="w-5 h-5 text-violet-400" />
                  Course Ideas
                </h3>

                <div className="space-y-2">
                  {COURSE_EXAMPLES.map((example, index) => (
                    <button
                      key={index}
                      onClick={() => selectExample(example)}
                      className="w-full p-3 rounded-lg bg-zinc-800/50 border border-white/5 hover:border-violet-500/30 text-left transition-all"
                    >
                      <span className="text-sm">{example}</span>
                    </button>
                  ))}
                </div>

                <div className="pt-4 border-t border-white/10">
                  <h4 className="text-sm font-medium text-zinc-400 mb-2">Popular Categories</h4>
                  <div className="flex flex-wrap gap-2">
                    {['Technology', 'Business', 'Languages', 'Creative', 'Science', 'Health'].map(cat => (
                      <Badge key={cat} variant="outline" className="border-white/10 cursor-pointer hover:border-violet-500/30">
                        {cat}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Configure */}
          {step === 2 && (
            <div className="glass-card p-6 space-y-6">
              <h3 className="font-semibold flex items-center gap-2">
                <Layers className="w-5 h-5 text-violet-400" />
                Configure Your Course
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label>Target Audience</Label>
                  <Select value={courseData.targetAudience} onValueChange={(v) => handleChange('targetAudience', v)}>
                    <SelectTrigger className="mt-1 bg-zinc-800 border-white/10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-white/10">
                      <SelectItem value="beginner">Beginner - No prior knowledge</SelectItem>
                      <SelectItem value="intermediate">Intermediate - Some experience</SelectItem>
                      <SelectItem value="advanced">Advanced - Experienced learners</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Course Duration (weeks)</Label>
                  <Select value={courseData.estimatedDuration} onValueChange={(v) => handleChange('estimatedDuration', v)}>
                    <SelectTrigger className="mt-1 bg-zinc-800 border-white/10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-white/10">
                      <SelectItem value="1">1 week (Quick course)</SelectItem>
                      <SelectItem value="2">2 weeks</SelectItem>
                      <SelectItem value="4">4 weeks (Standard)</SelectItem>
                      <SelectItem value="8">8 weeks (Comprehensive)</SelectItem>
                      <SelectItem value="12">12 weeks (Deep dive)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Number of Lessons</Label>
                  <Select value={courseData.numLessons.toString()} onValueChange={(v) => handleChange('numLessons', parseInt(v))}>
                    <SelectTrigger className="mt-1 bg-zinc-800 border-white/10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-white/10">
                      <SelectItem value="5">5 lessons</SelectItem>
                      <SelectItem value="10">10 lessons</SelectItem>
                      <SelectItem value="15">15 lessons</SelectItem>
                      <SelectItem value="20">20 lessons</SelectItem>
                      <SelectItem value="30">30 lessons</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Course Language</Label>
                  <Select value={courseData.language} onValueChange={(v) => handleChange('language', v)}>
                    <SelectTrigger className="mt-1 bg-zinc-800 border-white/10">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-white/10">
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="sw">Kiswahili</SelectItem>
                      <SelectItem value="sn">Shona</SelectItem>
                      <SelectItem value="zu">isiZulu</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Course Type / Pricing */}
              <div className="pt-4 border-t border-white/10">
                <Label className="mb-4 block">Course Type & Pricing</Label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {COURSE_TYPES.map(type => (
                    <button
                      key={type.id}
                      onClick={() => handleChange('courseType', type.id)}
                      className={`p-4 rounded-xl border transition-all text-left ${
                        courseData.courseType === type.id
                          ? 'border-violet-500 bg-violet-500/10'
                          : 'border-white/10 hover:border-white/20'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold">{type.name}</span>
                        {type.price === 0 ? (
                          <Badge className="bg-emerald-500/20 text-emerald-400">Free</Badge>
                        ) : (
                          <Badge className="bg-violet-500/20 text-violet-400">${type.price}</Badge>
                        )}
                      </div>
                      <p className="text-xs text-zinc-500">{type.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Content Options */}
              <div className="pt-4 border-t border-white/10 space-y-4">
                <Label className="block">Content Options</Label>
                
                <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50">
                  <div className="flex items-center gap-3">
                    <FileText className="w-5 h-5 text-blue-400" />
                    <div>
                      <span className="font-medium">Include Quizzes</span>
                      <p className="text-xs text-zinc-500">Auto-generate quizzes for each lesson</p>
                    </div>
                  </div>
                  <Switch 
                    checked={courseData.includeQuizzes}
                    onCheckedChange={(v) => handleChange('includeQuizzes', v)}
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50">
                  <div className="flex items-center gap-3">
                    <Layers className="w-5 h-5 text-amber-400" />
                    <div>
                      <span className="font-medium">Generate Slides</span>
                      <p className="text-xs text-zinc-500">AI-generated visual slides for each topic</p>
                    </div>
                  </div>
                  <Switch 
                    checked={courseData.includeSlides}
                    onCheckedChange={(v) => handleChange('includeSlides', v)}
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50">
                  <div className="flex items-center gap-3">
                    <Video className="w-5 h-5 text-red-400" />
                    <div>
                      <span className="font-medium">Generate Videos</span>
                      <p className="text-xs text-zinc-500">AI video generation (takes longer)</p>
                    </div>
                  </div>
                  <Switch 
                    checked={courseData.includeVideo}
                    onCheckedChange={(v) => handleChange('includeVideo', v)}
                  />
                </div>
              </div>

              {/* AI Features Selection (for advanced course types) */}
              {courseData.courseType !== 'free_custom' && (
                <div className="pt-4 border-t border-white/10 space-y-4">
                  <Label className="block">AI Features (Select which features to enable)</Label>
                  <p className="text-sm text-zinc-500">Choose AI capabilities for your course</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {AI_FEATURES.map(feature => {
                      const Icon = feature.icon;
                      const isEnabled = courseData.aiFeatures[feature.id];
                      return (
                        <button
                          key={feature.id}
                          onClick={() => setCourseData(prev => ({
                            ...prev,
                            aiFeatures: {
                              ...prev.aiFeatures,
                              [feature.id]: !prev.aiFeatures[feature.id]
                            }
                          }))}
                          className={`p-4 rounded-xl border transition-all text-left ${
                            isEnabled
                              ? `border-${feature.color}-500/50 bg-${feature.color}-500/10`
                              : 'border-white/10 hover:border-white/20'
                          }`}
                          data-testid={`ai-feature-${feature.id}`}
                        >
                          <div className="flex items-start gap-3">
                            <div className={`p-2 rounded-lg ${isEnabled ? `bg-${feature.color}-500/20` : 'bg-zinc-800'}`}>
                              <Icon className={`w-5 h-5 ${isEnabled ? `text-${feature.color}-400` : 'text-zinc-500'}`} />
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center justify-between">
                                <span className={`font-medium ${isEnabled ? 'text-white' : 'text-zinc-400'}`}>
                                  {feature.name}
                                </span>
                                {isEnabled && (
                                  <CheckCircle className={`w-4 h-4 text-${feature.color}-400`} />
                                )}
                              </div>
                              <p className="text-xs text-zinc-500 mt-1">{feature.description}</p>
                            </div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="flex gap-4">
                <Button variant="outline" onClick={() => setStep(1)} className="border-white/10">
                  Back
                </Button>
                <Button
                  onClick={() => setStep(3)}
                  className="flex-1 bg-violet-500 hover:bg-violet-600"
                >
                  Review & Generate
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {/* Step 3: Generate */}
          {step === 3 && (
            <div className="glass-card p-6 space-y-6">
              <h3 className="font-semibold flex items-center gap-2">
                <Brain className="w-5 h-5 text-violet-400" />
                Review & Generate
              </h3>

              {/* Summary */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-lg bg-zinc-800/50">
                  <h4 className="text-sm text-zinc-500 mb-1">Course Title</h4>
                  <p className="font-semibold">{courseData.title}</p>
                </div>
                <div className="p-4 rounded-lg bg-zinc-800/50">
                  <h4 className="text-sm text-zinc-500 mb-1">Course Type</h4>
                  <p className="font-semibold">{COURSE_TYPES.find(t => t.id === courseData.courseType)?.name}</p>
                </div>
                <div className="p-4 rounded-lg bg-zinc-800/50">
                  <h4 className="text-sm text-zinc-500 mb-1">Duration</h4>
                  <p className="font-semibold">{courseData.estimatedDuration} weeks • {courseData.numLessons} lessons</p>
                </div>
                <div className="p-4 rounded-lg bg-zinc-800/50">
                  <h4 className="text-sm text-zinc-500 mb-1">Target Audience</h4>
                  <p className="font-semibold capitalize">{courseData.targetAudience}</p>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-zinc-800/50">
                <h4 className="text-sm text-zinc-500 mb-1">Learning Goal</h4>
                <p>{courseData.learningGoal}</p>
              </div>

              <div className="flex flex-wrap gap-2">
                {courseData.includeQuizzes && <Badge className="bg-blue-500/20 text-blue-400">Quizzes</Badge>}
                {courseData.includeSlides && <Badge className="bg-amber-500/20 text-amber-400">Slides</Badge>}
                {courseData.includeVideo && <Badge className="bg-red-500/20 text-red-400">Videos</Badge>}
              </div>

              {/* Pricing Summary */}
              <div className="p-4 rounded-lg bg-violet-500/10 border border-violet-500/20">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold">Total Cost</h4>
                    <p className="text-sm text-zinc-400">
                      {getPrice() === 0 ? 'Free course creation' : 'One-time payment for AI generation'}
                    </p>
                  </div>
                  <div className="text-2xl font-bold text-violet-400">
                    {getPrice() === 0 ? 'Free' : `$${getPrice()}`}
                  </div>
                </div>
              </div>

              <div className="flex gap-4">
                <Button variant="outline" onClick={() => setStep(2)} className="border-white/10">
                  Back
                </Button>
                <Button
                  onClick={handleGenerateCourse}
                  disabled={loading}
                  className="flex-1 bg-violet-500 hover:bg-violet-600"
                  data-testid="generate-course-btn"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Generating Course... (may take 1-2 min)
                    </>
                  ) : (
                    <>
                      <Zap className="w-4 h-4 mr-2" />
                      Generate Course
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* Step 4: Preview */}
          {step === 4 && generatedCourse && (
            <div className="space-y-6">
              <div className="glass-card p-6 bg-gradient-to-r from-emerald-500/10 to-green-500/10 border-emerald-500/20">
                <div className="flex items-center gap-4">
                  <CheckCircle className="w-12 h-12 text-emerald-400" />
                  <div>
                    <h3 className="text-xl font-bold text-emerald-400">Course Generated Successfully!</h3>
                    <p className="text-zinc-400">Review your course content below and publish when ready.</p>
                  </div>
                </div>
              </div>

              {/* Course Overview */}
              <div className="glass-card p-6">
                <h3 className="font-semibold text-xl mb-4">{generatedCourse.title}</h3>
                <p className="text-zinc-400 mb-4">{generatedCourse.description}</p>
                
                <div className="flex flex-wrap gap-4 mb-6">
                  <Badge className="bg-violet-500/20 text-violet-400">
                    <Clock className="w-3 h-3 mr-1" />
                    {generatedCourse.duration_weeks} weeks
                  </Badge>
                  <Badge className="bg-blue-500/20 text-blue-400">
                    <BookOpen className="w-3 h-3 mr-1" />
                    {generatedCourse.lessons?.length || 0} lessons
                  </Badge>
                  <Badge className="bg-amber-500/20 text-amber-400">
                    <Users className="w-3 h-3 mr-1" />
                    {courseData.targetAudience}
                  </Badge>
                </div>

                {/* Lessons Preview */}
                <h4 className="font-semibold mb-4 flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-violet-400" />
                  Course Content
                </h4>
                
                <div className="space-y-3">
                  {generatedCourse.lessons?.map((lesson, idx) => (
                    <div key={lesson.id || idx} className="p-4 rounded-lg bg-zinc-800/50 border border-white/5">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-violet-500/20 flex items-center justify-center text-sm font-medium text-violet-400">
                            {idx + 1}
                          </div>
                          <div>
                            <h5 className="font-medium">{lesson.title}</h5>
                            <p className="text-sm text-zinc-500">{lesson.description?.substring(0, 100)}...</p>
                          </div>
                        </div>
                        <Badge className="bg-zinc-700">{lesson.duration || '15 min'}</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-4">
                <Button variant="outline" onClick={() => setStep(3)} className="border-white/10">
                  Back to Edit
                </Button>
                <Button
                  onClick={handlePublishCourse}
                  disabled={loading}
                  className="flex-1 bg-emerald-500 hover:bg-emerald-600"
                  data-testid="publish-course-btn"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Publishing...
                    </>
                  ) : (
                    <>
                      <Rocket className="w-4 h-4 mr-2" />
                      Publish Course
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
