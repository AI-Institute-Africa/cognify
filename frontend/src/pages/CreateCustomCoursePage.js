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
  Globe,
  Upload,
  FileUp,
  Copy,
  PenTool,
  ArrowLeft
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
import AIFeaturesGridModal from '../components/AIFeaturesGridModal';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

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

// Course creation methods
const CREATION_METHODS = [
  { 
    id: 'from_scratch', 
    name: 'Create from Scratch', 
    description: 'Design a completely new course with AI assistance',
    icon: PenTool,
    color: 'violet'
  },
  { 
    id: 'from_upload', 
    name: 'Upload Content', 
    description: 'Create from your uploaded documents, PDFs, or files',
    icon: Upload,
    color: 'blue'
  },
  { 
    id: 'import_standard', 
    name: 'Import from Standard', 
    description: 'Start from an existing standard course and customize it',
    icon: Copy,
    color: 'emerald'
  }
];

export default function CreateCustomCoursePage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(0); // 0: AI Features, 1: Method, 2: Define, 3: Configure, 4: Generate, 5: Preview
  const [loading, setLoading] = useState(false);
  const [generatedCourse, setGeneratedCourse] = useState(null);
  const [showAIFeaturesModal, setShowAIFeaturesModal] = useState(true); // Show on load
  const [aiFeatures, setAIFeatures] = useState({});
  const [creationMethod, setCreationMethod] = useState(null);
  const [standardCourses, setStandardCourses] = useState([]);
  const [selectedStandardCourse, setSelectedStandardCourse] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  
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
    topics: []
  });

  useEffect(() => {
    loadStandardCourses();
  }, []);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('cognify_token');
    return { Authorization: `Bearer ${token}` };
  };

  const loadStandardCourses = async () => {
    try {
      const { data } = await axios.get(`${API}/api/courses`, { headers: getAuthHeaders() });
      const standard = (data || []).filter(c => c.course_branch !== 'customized' && !c.is_user_created);
      setStandardCourses(standard);
    } catch (error) {
      console.error('Failed to load courses:', error);
    }
  };

  const handleAIFeaturesComplete = (result) => {
    setAIFeatures(result.features || {});
    setShowAIFeaturesModal(false);
    setStep(1); // Move to method selection
  };

  const handleChange = (field, value) => {
    setCourseData(prev => ({ ...prev, [field]: value }));
  };

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    if (files.length === 0) return;

    setLoading(true);
    const uploaded = [];

    for (const file of files) {
      if (file.size > 10 * 1024 * 1024) {
        toast.error(`${file.name} is too large (max 10MB)`);
        continue;
      }

      try {
        const formData = new FormData();
        formData.append('file', file);
        
        const { data } = await axios.post(`${API}/api/content/upload-source`, formData, {
          headers: { ...getAuthHeaders(), 'Content-Type': 'multipart/form-data' }
        });
        uploaded.push({
          name: file.name,
          id: data.file_id,
          type: file.type,
          extracted_text: data.extracted_text
        });
      } catch (error) {
        toast.error(`Failed to upload ${file.name}`);
      }
    }

    setUploadedFiles(prev => [...prev, ...uploaded]);
    setLoading(false);
    
    if (uploaded.length > 0) {
      toast.success(`${uploaded.length} file(s) uploaded successfully`);
    }
  };

  const handleImportCourse = async (courseId) => {
    setLoading(true);
    try {
      const { data: course } = await axios.get(`${API}/api/courses/${courseId}`, { headers: getAuthHeaders() });
      setSelectedStandardCourse(course);
      setCourseData(prev => ({
        ...prev,
        title: `${course.title} - Customized`,
        description: course.description,
        learningGoal: course.description,
        targetAudience: course.target_audience || 'beginner',
        numLessons: course.lessons?.length || 10
      }));
      toast.success('Course imported! You can now customize it.');
      setStep(2);
    } catch (error) {
      toast.error('Failed to import course');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateCourse = async () => {
    if (!courseData.title.trim() || !courseData.learningGoal.trim()) {
      toast.error('Please fill in the course title and learning goal');
      return;
    }

    setLoading(true);
    try {
      const requestBody = {
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
        language: courseData.language,
        ai_features: aiFeatures,
        creation_method: creationMethod,
        source_course_id: selectedStandardCourse?.id || null,
        uploaded_file_ids: uploadedFiles.map(f => f.id)
      };

      const { data: result } = await axios.post(`${API}/api/courses/generate-custom`, requestBody, {
        headers: getAuthHeaders(),
        timeout: 90000
      });

      // Async generation — poll status until 'ready' or 'failed'
      if (result.generation_status === 'generating' && result.course_id) {
        toast.success('Course generation started. This may take a minute…');
        const started = Date.now();
        // Poll every 3s for up to 5 minutes
        const maxMs = 5 * 60 * 1000;
        // eslint-disable-next-line no-constant-condition
        while (true) {
          await new Promise((r) => setTimeout(r, 3000));
          try {
            const { data: status } = await axios.get(
              `${API}/api/courses/${result.course_id}/generation-status`,
              { headers: getAuthHeaders(), timeout: 20000 }
            );
            if (status.status === 'ready') {
              setGeneratedCourse({
                course_id: status.course_id,
                title: status.title,
                description: status.description,
                duration_weeks: status.duration_weeks,
                lessons: status.lessons,
                learning_objectives: status.learning_objectives,
                price: status.price,
              });
              setStep(5);
              toast.success('Course generated successfully!');
              break;
            }
            if (status.status === 'failed') {
              toast.error(status.generation_error || 'Course generation failed. Please try again.');
              break;
            }
            if (Date.now() - started > maxMs) {
              toast.error('Generation is still running. Please check the Courses page in a moment.');
              break;
            }
          } catch (pollErr) {
            console.warn('poll error', pollErr);
          }
        }
      } else {
        setGeneratedCourse(result);
        setStep(5);
        toast.success('Course generated successfully!');
      }
    } catch (error) {
      console.error('Course generation error:', error);
      let message = error.response?.data?.detail || error.message || 'Failed to generate course.';
      if (error.code === 'ECONNABORTED' || message.includes('timeout') || message.includes('502')) {
        message = 'Generation is taking longer than expected. Try reducing the number of lessons (5-6 is recommended) or simplify the topic.';
      }
      toast.error(message);
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
      await axios.post(`${API}/api/courses/${generatedCourse.course_id}/publish`, {}, {
        headers: getAuthHeaders()
      });

      toast.success('Course published successfully!');
      navigate(`/courses/${generatedCourse.course_id}`);
    } catch (error) {
      console.error('Publish error:', error);
      const message = error.response?.data?.detail || error.message || 'Failed to publish course';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const selectExample = (example) => {
    handleChange('learningGoal', example);
    const words = example.split(' ').slice(0, 5).join(' ');
    handleChange('title', words);
  };

  const getPrice = () => {
    const type = COURSE_TYPES.find(t => t.id === courseData.courseType);
    return type ? type.price : 0;
  };

  const getStepTitle = () => {
    switch(step) {
      case 0: return 'Select AI Features';
      case 1: return 'Choose Creation Method';
      case 2: return 'Define Course';
      case 3: return 'Configure';
      case 4: return 'Generate';
      case 5: return 'Preview & Publish';
      default: return '';
    }
  };

  return (
    <DashboardLayout>
      <Header 
        title="Create Customized Course"
        subtitle="Design your own AI-powered learning experience"
      />
      
      <div className="p-8">
        <div className="max-w-5xl mx-auto">
          {/* Progress Steps */}
          <div className="flex items-center justify-between mb-8 overflow-x-auto pb-2">
            {[
              { num: 0, label: 'AI Features' },
              { num: 1, label: 'Method' },
              { num: 2, label: 'Define' },
              { num: 3, label: 'Configure' },
              { num: 4, label: 'Generate' },
              { num: 5, label: 'Preview' }
            ].map((s, idx) => (
              <div key={s.num} className="flex items-center">
                <div 
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${
                    step >= s.num ? 'bg-violet-500 text-white' : 'bg-zinc-800 text-zinc-500'
                  }`}
                >
                  {step > s.num ? <CheckCircle className="w-4 h-4" /> : s.num + 1}
                </div>
                <span className={`ml-1 text-xs hidden sm:inline ${step >= s.num ? 'text-white' : 'text-zinc-500'}`}>
                  {s.label}
                </span>
                {idx < 5 && (
                  <div className={`w-8 h-0.5 mx-1 ${step > s.num ? 'bg-violet-500' : 'bg-zinc-800'}`} />
                )}
              </div>
            ))}
          </div>

          {/* Step 1: Creation Method Selection */}
          {step === 1 && (
            <div className="space-y-6">
              <div className="glass-card p-6 bg-gradient-to-r from-violet-500/10 to-purple-500/10 border-violet-500/20">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 rounded-xl bg-violet-500/20 flex items-center justify-center">
                    <Rocket className="w-6 h-6 text-violet-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg mb-1">How do you want to create your course?</h3>
                    <p className="text-zinc-400 text-sm">
                      Choose how you'd like to start creating your customized course.
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {CREATION_METHODS.map(method => {
                  const Icon = method.icon;
                  const isSelected = creationMethod === method.id;
                  return (
                    <button
                      key={method.id}
                      onClick={() => setCreationMethod(method.id)}
                      className={`p-6 rounded-xl border transition-all text-left hover:scale-[1.02] ${
                        isSelected
                          ? `border-${method.color}-500/50 bg-${method.color}-500/10`
                          : 'border-white/10 hover:border-white/20'
                      }`}
                      data-testid={`method-${method.id}`}
                    >
                      <div className={`w-12 h-12 rounded-xl ${isSelected ? `bg-${method.color}-500/20` : 'bg-zinc-800'} flex items-center justify-center mb-4`}>
                        <Icon className={`w-6 h-6 ${isSelected ? `text-${method.color}-400` : 'text-zinc-500'}`} />
                      </div>
                      <h3 className={`font-semibold mb-2 ${isSelected ? 'text-white' : 'text-zinc-300'}`}>
                        {method.name}
                      </h3>
                      <p className="text-sm text-zinc-500">{method.description}</p>
                      {isSelected && (
                        <Badge className={`mt-3 bg-${method.color}-500/20 text-${method.color}-400`}>
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Selected
                        </Badge>
                      )}
                    </button>
                  );
                })}
              </div>

              {/* Upload Section - Show if upload method selected */}
              {creationMethod === 'from_upload' && (
                <div className="glass-card p-6 space-y-4">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Upload className="w-5 h-5 text-blue-400" />
                    Upload Your Content
                  </h4>
                  <p className="text-sm text-zinc-400">
                    Upload documents, PDFs, or text files that will be used to generate your course content.
                  </p>
                  
                  <div className="border-2 border-dashed border-white/10 rounded-xl p-8 text-center hover:border-blue-500/30 transition-colors">
                    <input
                      type="file"
                      multiple
                      accept=".pdf,.doc,.docx,.txt,.md"
                      onChange={handleFileUpload}
                      className="hidden"
                      id="file-upload"
                    />
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <FileUp className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
                      <p className="text-zinc-400">Click to upload or drag and drop</p>
                      <p className="text-xs text-zinc-600 mt-1">PDF, DOC, DOCX, TXT, MD (max 10MB each)</p>
                    </label>
                  </div>

                  {uploadedFiles.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-sm text-zinc-400">Uploaded files:</p>
                      {uploadedFiles.map((file, idx) => (
                        <div key={idx} className="flex items-center gap-2 p-2 rounded-lg bg-zinc-800/50">
                          <FileText className="w-4 h-4 text-blue-400" />
                          <span className="text-sm flex-1 truncate">{file.name}</span>
                          <Badge className="bg-emerald-500/20 text-emerald-400">Uploaded</Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Import Section - Show if import method selected */}
              {creationMethod === 'import_standard' && (
                <div className="glass-card p-6 space-y-4">
                  <h4 className="font-semibold flex items-center gap-2">
                    <Copy className="w-5 h-5 text-emerald-400" />
                    Select a Standard Course to Import
                  </h4>
                  <p className="text-sm text-zinc-400">
                    Choose an existing standard course to use as a starting point for your customized course.
                  </p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[300px] overflow-y-auto">
                    {standardCourses.length === 0 ? (
                      <p className="text-zinc-500 col-span-2 text-center py-8">
                        No standard courses available to import
                      </p>
                    ) : (
                      standardCourses.map(course => (
                        <button
                          key={course.id}
                          onClick={() => handleImportCourse(course.id)}
                          className="p-4 rounded-lg bg-zinc-800/50 border border-white/5 hover:border-emerald-500/30 text-left transition-all"
                        >
                          <h5 className="font-medium text-sm mb-1">{course.title}</h5>
                          <p className="text-xs text-zinc-500 line-clamp-2">{course.description}</p>
                          <Badge className="mt-2 bg-zinc-700 text-xs">
                            {course.lessons?.length || 0} Lessons
                          </Badge>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              )}

              <div className="flex gap-4">
                <Button 
                  variant="outline" 
                  onClick={() => setShowAIFeaturesModal(true)} 
                  className="border-white/10"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back to AI Features
                </Button>
                <Button
                  onClick={() => setStep(2)}
                  disabled={!creationMethod || (creationMethod === 'from_upload' && uploadedFiles.length === 0)}
                  className="flex-1 bg-violet-500 hover:bg-violet-600"
                >
                  Continue
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {/* Step 2: Define Course */}
          {step === 2 && (
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

                <div className="flex gap-4">
                  <Button variant="outline" onClick={() => setStep(1)} className="border-white/10">
                    Back
                  </Button>
                  <Button
                    onClick={() => setStep(3)}
                    disabled={!courseData.title.trim() || !courseData.learningGoal.trim()}
                    className="flex-1 bg-violet-500 hover:bg-violet-600"
                  >
                    Continue to Configuration
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
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

                {/* AI Features Summary */}
                <div className="pt-4 border-t border-white/10">
                  <h4 className="text-sm font-medium text-zinc-400 mb-2">Selected AI Features</h4>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(aiFeatures).filter(([, v]) => v).map(([key]) => (
                      <Badge key={key} className="bg-violet-500/20 text-violet-400 capitalize">
                        {key.replace(/_/g, ' ')}
                      </Badge>
                    ))}
                    {Object.values(aiFeatures).filter(Boolean).length === 0 && (
                      <p className="text-xs text-zinc-500">No AI features selected</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Configure */}
          {step === 3 && (
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

              <div className="flex gap-4">
                <Button variant="outline" onClick={() => setStep(2)} className="border-white/10">
                  Back
                </Button>
                <Button
                  onClick={() => setStep(4)}
                  className="flex-1 bg-violet-500 hover:bg-violet-600"
                >
                  Review & Generate
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {/* Step 4: Generate */}
          {step === 4 && (
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
                  <h4 className="text-sm text-zinc-500 mb-1">Creation Method</h4>
                  <p className="font-semibold capitalize">{creationMethod?.replace(/_/g, ' ')}</p>
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

              {/* AI Features Summary */}
              <div className="p-4 rounded-lg bg-zinc-800/50">
                <h4 className="text-sm text-zinc-500 mb-2">AI Features Enabled</h4>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(aiFeatures).filter(([, v]) => v).map(([key]) => (
                    <Badge key={key} className="bg-violet-500/20 text-violet-400 capitalize">
                      {key.replace(/_/g, ' ')}
                    </Badge>
                  ))}
                </div>
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
                <Button variant="outline" onClick={() => setStep(3)} className="border-white/10">
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

          {/* Step 5: Preview */}
          {step === 5 && generatedCourse && (
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
                <Button variant="outline" onClick={() => setStep(4)} className="border-white/10">
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

      {/* AI Features Modal - Opens first */}
      <AIFeaturesGridModal
        isOpen={showAIFeaturesModal}
        onClose={() => {
          if (step === 0) {
            // If closing at step 0, go back to courses
            navigate('/courses');
          } else {
            setShowAIFeaturesModal(false);
          }
        }}
        onComplete={handleAIFeaturesComplete}
        courseType="customized"
        initialFeatures={aiFeatures}
      />
    </DashboardLayout>
  );
}
