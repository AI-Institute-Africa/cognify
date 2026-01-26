import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { getCourses, enrollCourse, createCourse } from '../services/api';
import { BookOpen, Users, Clock, Plus, Search, Filter, ArrowRight, Eye, CheckCircle, DollarSign, Award, GraduationCap, Calendar } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
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

const COURSE_CATEGORIES = [
  { id: '3day', name: '3-Day Course', icon: Calendar, color: 'emerald', description: 'Quick intensive training' },
  { id: 'certification', name: 'Certification', icon: Award, color: 'blue', description: 'Professional certification' },
  { id: 'certificate', name: 'Certificate', icon: CheckCircle, color: 'violet', description: 'Completion certificate' },
  { id: 'diploma', name: 'Diploma', icon: GraduationCap, color: 'amber', description: 'Full diploma program' },
];

export default function CoursesPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [creating, setCreating] = useState(false);
  const [enrolledCourseIds, setEnrolledCourseIds] = useState([]);
  const [newCourse, setNewCourse] = useState({
    code: '',
    name: '',
    description: '',
    grade_level: 'Grade 10',
    credits: 3,
    max_students: 30,
    category: 'certificate',
    price: 0,
    is_paid: false,
    duration_weeks: 4
  });

  useEffect(() => {
    loadCourses();
  }, []);

  const loadCourses = async () => {
    try {
      const data = await getCourses();
      setCourses(data);
      // Track enrolled courses for current student
      if (user?.role === 'student') {
        const enrolled = data.filter(c => 
          c.enrolled_students?.includes(user.id)
        ).map(c => c.id);
        setEnrolledCourseIds(enrolled);
      }
    } catch (error) {
      console.error('Failed to load courses:', error);
      toast.error('Failed to load courses');
    } finally {
      setLoading(false);
    }
  };

  const handleEnroll = async (course) => {
    // If course is paid, redirect to payment page
    if (course.is_paid && course.price > 0) {
      navigate(`/payment/${course.id}`);
      return;
    }
    
    // Free enrollment
    try {
      await enrollCourse(course.id);
      toast.success('Enrolled successfully!');
      loadCourses();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to enroll');
    }
  };

  const handleCreateCourse = async (e) => {
    e.preventDefault();
    if (!newCourse.code || !newCourse.name || !newCourse.description) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    setCreating(true);
    try {
      await createCourse(newCourse);
      toast.success('Course created successfully!');
      setShowCreateDialog(false);
      setNewCourse({
        code: '',
        name: '',
        description: '',
        grade_level: 'Grade 10',
        credits: 3,
        max_students: 30,
        category: 'certificate',
        price: 0,
        is_paid: false,
        duration_weeks: 4
      });
      loadCourses();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create course');
    } finally {
      setCreating(false);
    }
  };

  const filteredCourses = courses.filter(course => {
    const matchesSearch = course.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      course.code.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || course.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const getCategoryInfo = (categoryId) => {
    return COURSE_CATEGORIES.find(c => c.id === categoryId) || COURSE_CATEGORIES[2];
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header 
        title={user?.role === 'student' ? 'My Courses' : 'Courses'}
        subtitle={`${courses.length} courses available`}
      />
      
      <div className="p-8">
        {/* Actions Bar */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-zinc-500" />
            <Input
              placeholder="Search courses..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              data-testid="course-search-input"
              className="pl-11 bg-zinc-900/50 border-white/10 h-12"
            />
          </div>
          
          <Button variant="outline" className="h-12 border-white/10">
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </Button>
          
          {(user?.role === 'admin' || user?.role === 'teacher') && (
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button data-testid="create-course-btn" className="h-12 bg-blue-500 hover:bg-blue-600">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Course
                </Button>
              </DialogTrigger>
              <DialogContent className="bg-zinc-900 border-white/10 max-w-lg">
                <DialogHeader>
                  <DialogTitle>Create New Course</DialogTitle>
                  <DialogDescription className="text-zinc-500">
                    Add a new course to the curriculum
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateCourse} className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Course Code</Label>
                      <Input
                        placeholder="CS101"
                        value={newCourse.code}
                        onChange={(e) => setNewCourse({...newCourse, code: e.target.value})}
                        data-testid="course-code-input"
                        className="bg-zinc-800 border-white/10"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Credits</Label>
                      <Input
                        type="number"
                        value={newCourse.credits}
                        onChange={(e) => setNewCourse({...newCourse, credits: parseInt(e.target.value)})}
                        data-testid="course-credits-input"
                        className="bg-zinc-800 border-white/10"
                      />
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Course Name</Label>
                    <Input
                      placeholder="Introduction to Computer Science"
                      value={newCourse.name}
                      onChange={(e) => setNewCourse({...newCourse, name: e.target.value})}
                      data-testid="course-name-input"
                      className="bg-zinc-800 border-white/10"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Description</Label>
                    <Textarea
                      placeholder="Course description..."
                      value={newCourse.description}
                      onChange={(e) => setNewCourse({...newCourse, description: e.target.value})}
                      data-testid="course-description-input"
                      className="bg-zinc-800 border-white/10 min-h-[100px]"
                    />
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Grade Level</Label>
                      <Select
                        value={newCourse.grade_level}
                        onValueChange={(value) => setNewCourse({...newCourse, grade_level: value})}
                      >
                        <SelectTrigger className="bg-zinc-800 border-white/10">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-800 border-white/10">
                          {['Grade 9', 'Grade 10', 'Grade 11', 'Grade 12', 'Undergraduate', 'Graduate'].map(grade => (
                            <SelectItem key={grade} value={grade}>{grade}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Max Students</Label>
                      <Input
                        type="number"
                        value={newCourse.max_students}
                        onChange={(e) => setNewCourse({...newCourse, max_students: parseInt(e.target.value)})}
                        data-testid="course-max-students-input"
                        className="bg-zinc-800 border-white/10"
                      />
                    </div>
                  </div>
                  
                  <div className="flex justify-end gap-3 pt-4">
                    <Button type="button" variant="ghost" onClick={() => setShowCreateDialog(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" data-testid="submit-create-course-btn" disabled={creating}>
                      {creating ? 'Creating...' : 'Create Course'}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>
        
        {/* Courses Grid */}
        {filteredCourses.length === 0 ? (
          <div className="text-center py-20">
            <BookOpen className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold mb-2">No courses found</h3>
            <p className="text-zinc-500">
              {searchQuery ? 'Try a different search term' : 'No courses available at the moment'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCourses.map((course, index) => (
              <div
                key={course.id}
                className={`glass-card p-6 hover:border-white/20 transition-all duration-300 group animate-fadeIn stagger-${(index % 5) + 1}`}
                data-testid={`course-card-${course.id}`}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500/20 to-violet-500/20 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                    <BookOpen className="w-7 h-7 text-blue-400" />
                  </div>
                  <Badge variant="outline" className="text-zinc-400 border-zinc-700">
                    {course.credits} Credits
                  </Badge>
                </div>
                
                <h3 className="text-lg font-semibold mb-2">{course.name}</h3>
                <p className="text-sm text-zinc-500 mb-4 line-clamp-2">{course.description}</p>
                
                <div className="flex items-center gap-4 text-sm text-zinc-500 mb-4">
                  <span className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {course.code}
                  </span>
                  <span className="flex items-center gap-1">
                    <Users className="w-4 h-4" />
                    {course.enrolled_students?.length || 0}/{course.max_students}
                  </span>
                </div>
                
                <Badge className="bg-zinc-800 text-zinc-300 mb-4">
                  {course.grade_level}
                </Badge>
                
                {user?.role === 'student' && (
                  enrolledCourseIds.includes(course.id) ? (
                    <Button
                      onClick={() => navigate(`/course/${course.id}`)}
                      data-testid={`view-course-btn-${course.id}`}
                      className="w-full mt-4 bg-green-500/10 text-green-400 hover:bg-green-500 hover:text-white border border-green-500/30 transition-all"
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      View Course
                      <CheckCircle className="w-4 h-4 ml-2" />
                    </Button>
                  ) : (
                    <Button
                      onClick={() => handleEnroll(course.id)}
                      data-testid={`enroll-btn-${course.id}`}
                      className="w-full mt-4 bg-blue-500/10 text-blue-400 hover:bg-blue-500 hover:text-white border border-blue-500/30 transition-all"
                    >
                      Enroll Now
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  )
                )}
                
                {(user?.role === 'teacher' || user?.role === 'admin') && (
                  <Button
                    onClick={() => navigate(`/course/${course.id}`)}
                    data-testid={`manage-course-btn-${course.id}`}
                    className="w-full mt-4 bg-violet-500/10 text-violet-400 hover:bg-violet-500 hover:text-white border border-violet-500/30 transition-all"
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    Manage Course
                  </Button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
