import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Label } from '../components/ui/label';
import { Checkbox } from '../components/ui/checkbox';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '../components/ui/dialog';
import { toast } from 'sonner';
import AIFeaturesGridModal from '../components/AIFeaturesGridModal';
import {
  Layers,
  Plus,
  BookOpen,
  Target,
  Clock,
  CheckCircle,
  Trash2,
  Edit,
  Play,
  Sparkles,
  GraduationCap,
  ArrowRight,
  RefreshCw,
  Search,
  Filter,
  MoreVertical,
  Eye
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

export default function MultiSubjectPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [multiSubjects, setMultiSubjects] = useState([]);
  const [availableCourses, setAvailableCourses] = useState([]);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showAIFeaturesModal, setShowAIFeaturesModal] = useState(false);
  const [selectedAIFeatures, setSelectedAIFeatures] = useState({});
  const [searchTerm, setSearchTerm] = useState('');
  const [creating, setCreating] = useState(false);
  
  const [newMultiSubject, setNewMultiSubject] = useState({
    name: '',
    description: '',
    goal: '',
    selected_courses: [],
    duration_weeks: 8
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = localStorage.getItem('cognify_token');
      
      // Load user's multi-subject paths
      const multiResponse = await fetch(`${API}/api/multi-subject/my-paths`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (multiResponse.ok) {
        const data = await multiResponse.json();
        setMultiSubjects(data || []);
      }

      // Load available courses
      const coursesResponse = await fetch(`${API}/api/courses`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (coursesResponse.ok) {
        const courses = await coursesResponse.json();
        setAvailableCourses(courses || []);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCourseToggle = (courseId) => {
    setNewMultiSubject(prev => ({
      ...prev,
      selected_courses: prev.selected_courses.includes(courseId)
        ? prev.selected_courses.filter(id => id !== courseId)
        : [...prev.selected_courses, courseId]
    }));
  };

  const handleCreate = async () => {
    if (!newMultiSubject.name.trim() || newMultiSubject.selected_courses.length < 2) {
      toast.error('Please provide a name and select at least 2 courses');
      return;
    }

    setCreating(true);
    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/multi-subject/create`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...newMultiSubject,
          ai_features: selectedAIFeatures
        })
      });

      if (response.ok) {
        const data = await response.json();
        toast.success('Multi-subject path created successfully!');
        setShowCreateDialog(false);
        setNewMultiSubject({
          name: '',
          description: '',
          goal: '',
          selected_courses: [],
          duration_weeks: 8
        });
        loadData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create path');
      }
    } catch (error) {
      toast.error('Failed to create multi-subject path');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (pathId) => {
    if (!confirm('Are you sure you want to delete this learning path?')) return;

    try {
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/multi-subject/${pathId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Learning path deleted');
        loadData();
      }
    } catch (error) {
      toast.error('Failed to delete path');
    }
  };

  const filteredCourses = availableCourses.filter(c =>
    c.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.category?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getSelectedCoursesInfo = () => {
    return availableCourses.filter(c => newMultiSubject.selected_courses.includes(c.id));
  };

  const calculateTotalDuration = () => {
    const selected = getSelectedCoursesInfo();
    return selected.reduce((total, c) => total + (c.duration_weeks || 4), 0);
  };

  return (
    <DashboardLayout>
      <Header 
        title="Multi-Subject Learning"
        subtitle="Create personalized learning paths combining multiple subjects"
      />

      <div className="p-8">
        {/* Header Actions */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div className="flex items-center gap-4">
            <Badge className="bg-violet-500/20 text-violet-400">
              <Layers className="w-3 h-3 mr-1" />
              {multiSubjects.length} Learning Paths
            </Badge>
          </div>
          <Button 
            onClick={() => setShowAIFeaturesModal(true)}
            className="bg-violet-500 hover:bg-violet-600"
            data-testid="create-multi-subject-btn"
          >
            <Plus className="w-4 h-4 mr-2" />
            Create Multi-Subject Path
          </Button>
        </div>

        {/* Existing Paths */}
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <RefreshCw className="w-8 h-8 animate-spin text-violet-500" />
          </div>
        ) : multiSubjects.length === 0 ? (
          <div className="glass-card p-12 text-center">
            <Layers className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">No Learning Paths Yet</h3>
            <p className="text-zinc-500 mb-6 max-w-md mx-auto">
              Create your first multi-subject learning path to study multiple topics together 
              with AI-powered personalized scheduling.
            </p>
            <Button 
              onClick={() => setShowAIFeaturesModal(true)}
              className="bg-violet-500 hover:bg-violet-600"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Path
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {multiSubjects.map((path) => (
              <div 
                key={path.id}
                className="glass-card p-6 hover:border-violet-500/30 transition-all"
                data-testid={`multi-subject-card-${path.id}`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="p-3 rounded-xl bg-violet-500/20">
                    <Layers className="w-6 h-6 text-violet-400" />
                  </div>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <Edit className="w-4 h-4" />
                    </Button>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-8 w-8 text-red-400 hover:text-red-300"
                      onClick={() => handleDelete(path.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                <h3 className="font-semibold text-lg mb-2">{path.name}</h3>
                <p className="text-sm text-zinc-500 mb-4 line-clamp-2">
                  {path.description || path.goal}
                </p>

                {/* Courses in path */}
                <div className="flex flex-wrap gap-1 mb-4">
                  {path.courses?.slice(0, 3).map((course, idx) => (
                    <Badge key={idx} variant="outline" className="text-xs border-white/10">
                      {course.title?.substring(0, 20) || `Course ${idx + 1}`}
                    </Badge>
                  ))}
                  {path.courses?.length > 3 && (
                    <Badge variant="outline" className="text-xs border-white/10">
                      +{path.courses.length - 3} more
                    </Badge>
                  )}
                </div>

                {/* Progress */}
                <div className="mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-zinc-500">Progress</span>
                    <span className="text-violet-400">{path.progress || 0}%</span>
                  </div>
                  <Progress value={path.progress || 0} className="h-2" />
                </div>

                {/* Stats */}
                <div className="flex items-center gap-4 text-sm text-zinc-500">
                  <span className="flex items-center gap-1">
                    <BookOpen className="w-4 h-4" />
                    {path.courses?.length || 0} courses
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {path.duration_weeks || 8} weeks
                  </span>
                </div>

                <Button 
                  className="w-full mt-4 bg-zinc-800 hover:bg-zinc-700"
                  onClick={() => window.location.href = `/multi-subject/${path.id}`}
                >
                  <Play className="w-4 h-4 mr-2" />
                  Continue Learning
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* AI Features Modal - Opens first */}
      <AIFeaturesGridModal
        isOpen={showAIFeaturesModal}
        onClose={() => setShowAIFeaturesModal(false)}
        onComplete={(result) => {
          setSelectedAIFeatures(result.features);
          setShowAIFeaturesModal(false);
          setShowCreateDialog(true);
        }}
        courseType="customized"
        initialFeatures={selectedAIFeatures}
      />

      {/* Create Multi-Subject Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="bg-zinc-900 border-white/10 max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-violet-400" />
              Create Multi-Subject Learning Path
            </DialogTitle>
            <DialogDescription className="text-zinc-500">
              Combine multiple courses into a single learning journey with AI-powered scheduling.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 py-4">
            {/* Basic Info */}
            <div className="space-y-4">
              <div>
                <Label htmlFor="path-name">Learning Path Name</Label>
                <Input
                  id="path-name"
                  placeholder="e.g., Full-Stack Development Journey"
                  value={newMultiSubject.name}
                  onChange={(e) => setNewMultiSubject(prev => ({...prev, name: e.target.value}))}
                  className="mt-1 bg-zinc-800 border-white/10"
                  data-testid="path-name-input"
                />
              </div>

              <div>
                <Label htmlFor="path-goal">Learning Goal</Label>
                <Textarea
                  id="path-goal"
                  placeholder="What do you want to achieve with this learning path?"
                  value={newMultiSubject.goal}
                  onChange={(e) => setNewMultiSubject(prev => ({...prev, goal: e.target.value}))}
                  className="mt-1 bg-zinc-800 border-white/10"
                />
              </div>

              <div>
                <Label htmlFor="path-description">Description (Optional)</Label>
                <Textarea
                  id="path-description"
                  placeholder="Additional details about your learning path"
                  value={newMultiSubject.description}
                  onChange={(e) => setNewMultiSubject(prev => ({...prev, description: e.target.value}))}
                  className="mt-1 bg-zinc-800 border-white/10"
                />
              </div>
            </div>

            {/* Course Selection */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Select Courses (min 2)</Label>
                <Badge className="bg-violet-500/20 text-violet-400">
                  {newMultiSubject.selected_courses.length} selected
                </Badge>
              </div>

              {/* Search */}
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
                <Input
                  placeholder="Search courses..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 bg-zinc-800 border-white/10"
                />
              </div>

              {/* Courses Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-[300px] overflow-y-auto p-1">
                {filteredCourses.map((course) => {
                  const isSelected = newMultiSubject.selected_courses.includes(course.id);
                  return (
                    <div
                      key={course.id}
                      className={`p-4 rounded-lg border cursor-pointer transition-all ${
                        isSelected 
                          ? 'border-violet-500 bg-violet-500/10' 
                          : 'border-white/10 hover:border-white/20'
                      }`}
                      onClick={() => handleCourseToggle(course.id)}
                    >
                      <div className="flex items-start gap-3">
                        <Checkbox 
                          checked={isSelected}
                          onCheckedChange={() => handleCourseToggle(course.id)}
                          className="mt-1"
                        />
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-sm truncate">{course.title}</h4>
                          <p className="text-xs text-zinc-500 mt-1 line-clamp-2">{course.description}</p>
                          <div className="flex items-center gap-2 mt-2">
                            <Badge className="bg-zinc-800 text-xs">{course.category || 'General'}</Badge>
                            <span className="text-xs text-zinc-500">{course.duration_weeks || 4} weeks</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Selected Courses Summary */}
            {newMultiSubject.selected_courses.length > 0 && (
              <div className="p-4 rounded-lg bg-violet-500/10 border border-violet-500/20">
                <h4 className="font-medium mb-2 flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-violet-400" />
                  Selected Courses ({newMultiSubject.selected_courses.length})
                </h4>
                <div className="flex flex-wrap gap-2">
                  {getSelectedCoursesInfo().map(course => (
                    <Badge key={course.id} className="bg-violet-500/20 text-violet-400">
                      {course.title?.substring(0, 25)}
                    </Badge>
                  ))}
                </div>
                <p className="text-sm text-zinc-500 mt-2">
                  Estimated duration: <span className="text-violet-400 font-medium">{calculateTotalDuration()} weeks</span>
                </p>
              </div>
            )}

            {/* AI Features Summary */}
            <div className="p-4 rounded-lg bg-zinc-800/50 border border-white/5">
              <h4 className="font-medium mb-2 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-amber-400" />
                AI Features Enabled
              </h4>
              <div className="flex flex-wrap gap-2">
                {Object.entries(selectedAIFeatures).filter(([, v]) => v).map(([key]) => (
                  <Badge key={key} className="bg-amber-500/20 text-amber-400 capitalize">
                    {key.replace(/_/g, ' ')}
                  </Badge>
                ))}
                {Object.values(selectedAIFeatures).filter(Boolean).length === 0 && (
                  <p className="text-xs text-zinc-500">No AI features selected</p>
                )}
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setShowCreateDialog(false)}
              className="border-white/10"
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={creating || newMultiSubject.selected_courses.length < 2 || !newMultiSubject.name.trim()}
              className="bg-violet-500 hover:bg-violet-600"
              data-testid="create-path-btn"
            >
              {creating ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Learning Path
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
