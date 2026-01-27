import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { 
  getOrgAdminDashboard, 
  getOrgTeachers, 
  getOrgStudents, 
  createCourseFromPDF, 
  bulkEnrollStudents,
  getOrgAnalytics 
} from '../services/api';
import { 
  Building2, Users, GraduationCap, BookOpen, DollarSign,
  Upload, UserPlus, BarChart3, TrendingUp, FileText,
  Loader2, Search, Mail, Phone, CheckCircle, AlertCircle,
  PieChart, Calendar
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
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
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { toast } from 'sonner';

export default function OrgAdminDashboardPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [teachers, setTeachers] = useState([]);
  const [students, setStudents] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  // PDF Course Creation
  const [showCreateCourseDialog, setShowCreateCourseDialog] = useState(false);
  const [creatingCourse, setCreatingCourse] = useState(false);
  const [newCourse, setNewCourse] = useState({
    title: '',
    category: 'certificate',
    price: 0,
    file: null
  });
  
  // Bulk Enrollment
  const [showEnrollDialog, setShowEnrollDialog] = useState(false);
  const [enrolling, setEnrolling] = useState(false);
  const [enrollmentData, setEnrollmentData] = useState({
    courseId: '',
    emails: ''
  });
  
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [dashboardData, teachersData, studentsData, analyticsData] = await Promise.all([
        getOrgAdminDashboard(),
        getOrgTeachers(),
        getOrgStudents(),
        getOrgAnalytics()
      ]);
      
      setDashboard(dashboardData);
      setTeachers(teachersData || []);
      setStudents(studentsData || []);
      setAnalytics(analyticsData);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCourseFromPDF = async () => {
    if (!newCourse.file || !newCourse.title) {
      toast.error('Please provide a PDF file and course title');
      return;
    }
    
    setCreatingCourse(true);
    try {
      const result = await createCourseFromPDF(
        newCourse.file,
        newCourse.title,
        newCourse.category,
        newCourse.price
      );
      
      toast.success(`Course created with ${result.lessons_created} lessons!`);
      setShowCreateCourseDialog(false);
      setNewCourse({ title: '', category: 'certificate', price: 0, file: null });
      loadDashboardData();
    } catch (error) {
      console.error('Failed to create course:', error);
      toast.error('Failed to create course from PDF');
    } finally {
      setCreatingCourse(false);
    }
  };

  const handleBulkEnroll = async () => {
    if (!enrollmentData.courseId || !enrollmentData.emails.trim()) {
      toast.error('Please select a course and enter student emails');
      return;
    }
    
    const emailList = enrollmentData.emails
      .split(/[\n,;]/)
      .map(e => e.trim())
      .filter(e => e && e.includes('@'));
    
    if (emailList.length === 0) {
      toast.error('No valid emails found');
      return;
    }
    
    setEnrolling(true);
    try {
      const result = await bulkEnrollStudents(enrollmentData.courseId, emailList);
      
      toast.success(`Enrolled ${result.enrolled_count} students!`);
      if (result.failed_emails?.length > 0) {
        toast.warning(`${result.failed_emails.length} emails could not be enrolled`);
      }
      
      setShowEnrollDialog(false);
      setEnrollmentData({ courseId: '', emails: '' });
      loadDashboardData();
    } catch (error) {
      console.error('Bulk enrollment failed:', error);
      toast.error('Bulk enrollment failed');
    } finally {
      setEnrolling(false);
    }
  };

  const filteredTeachers = teachers.filter(t => 
    t.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredStudents = students.filter(s => 
    s.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.email?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <div className="text-center">
            <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
            <p className="text-zinc-400">Loading organization dashboard...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header 
        title="Organization Admin Dashboard"
        subtitle={dashboard?.organization?.name || 'Manage your educational organization'}
      />
      
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                  <Users className="w-6 h-6 text-blue-400" />
                </div>
                <Badge className="bg-blue-500/20 text-blue-400">Teachers</Badge>
              </div>
              <p className="text-3xl font-bold">{dashboard?.statistics?.teachers || 0}</p>
              <p className="text-sm text-zinc-500">Active instructors</p>
            </div>
            
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                  <GraduationCap className="w-6 h-6 text-emerald-400" />
                </div>
                <Badge className="bg-emerald-500/20 text-emerald-400">Students</Badge>
              </div>
              <p className="text-3xl font-bold">{dashboard?.statistics?.students || 0}</p>
              <p className="text-sm text-zinc-500">Enrolled learners</p>
            </div>
            
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-violet-500/20 flex items-center justify-center">
                  <BookOpen className="w-6 h-6 text-violet-400" />
                </div>
                <Badge className="bg-violet-500/20 text-violet-400">Courses</Badge>
              </div>
              <p className="text-3xl font-bold">{dashboard?.statistics?.courses || 0}</p>
              <p className="text-sm text-zinc-500">Available courses</p>
            </div>
            
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-amber-500/20 flex items-center justify-center">
                  <DollarSign className="w-6 h-6 text-amber-400" />
                </div>
                <Badge className="bg-amber-500/20 text-amber-400">Revenue</Badge>
              </div>
              <p className="text-3xl font-bold">${dashboard?.statistics?.total_revenue?.toFixed(2) || '0.00'}</p>
              <p className="text-sm text-zinc-500">Total earnings</p>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="glass-card p-6 mb-8">
            <h3 className="font-semibold mb-4">Quick Actions</h3>
            <div className="flex flex-wrap gap-3">
              <Dialog open={showCreateCourseDialog} onOpenChange={setShowCreateCourseDialog}>
                <DialogTrigger asChild>
                  <Button className="bg-violet-500 hover:bg-violet-600" data-testid="create-course-pdf-btn">
                    <Upload className="w-4 h-4 mr-2" />
                    Create Course from PDF
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-zinc-900 border-white/10">
                  <DialogHeader>
                    <DialogTitle>Create Course from PDF</DialogTitle>
                    <DialogDescription className="text-zinc-500">
                      Upload a PDF syllabus or content to automatically create a structured course
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 mt-4">
                    <div>
                      <Label>Course Title *</Label>
                      <Input
                        placeholder="e.g., Introduction to Data Science"
                        value={newCourse.title}
                        onChange={(e) => setNewCourse({...newCourse, title: e.target.value})}
                        className="bg-zinc-800 border-white/10 mt-1"
                        data-testid="pdf-course-title"
                      />
                    </div>
                    
                    <div>
                      <Label>Category</Label>
                      <Select 
                        value={newCourse.category} 
                        onValueChange={(v) => setNewCourse({...newCourse, category: v})}
                      >
                        <SelectTrigger className="bg-zinc-800 border-white/10 mt-1">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-800 border-white/10">
                          <SelectItem value="3-day">3-Day Course</SelectItem>
                          <SelectItem value="certificate">Certificate Program</SelectItem>
                          <SelectItem value="diploma">Diploma Program</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label>Price (USD)</Label>
                      <Input
                        type="number"
                        placeholder="0 for free"
                        value={newCourse.price}
                        onChange={(e) => setNewCourse({...newCourse, price: parseFloat(e.target.value) || 0})}
                        className="bg-zinc-800 border-white/10 mt-1"
                      />
                    </div>
                    
                    <div>
                      <Label>PDF File *</Label>
                      <Input
                        type="file"
                        accept=".pdf"
                        onChange={(e) => setNewCourse({...newCourse, file: e.target.files[0]})}
                        className="bg-zinc-800 border-white/10 mt-1"
                        data-testid="pdf-file-input"
                      />
                    </div>
                    
                    <div className="flex justify-end gap-3 pt-4">
                      <Button variant="ghost" onClick={() => setShowCreateCourseDialog(false)}>
                        Cancel
                      </Button>
                      <Button 
                        onClick={handleCreateCourseFromPDF}
                        disabled={creatingCourse}
                        className="bg-violet-500 hover:bg-violet-600"
                        data-testid="submit-pdf-course-btn"
                      >
                        {creatingCourse ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Creating...
                          </>
                        ) : (
                          <>
                            <Upload className="w-4 h-4 mr-2" />
                            Create Course
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
              
              <Dialog open={showEnrollDialog} onOpenChange={setShowEnrollDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="border-white/10" data-testid="bulk-enroll-btn">
                    <UserPlus className="w-4 h-4 mr-2" />
                    Bulk Enroll Students
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-zinc-900 border-white/10">
                  <DialogHeader>
                    <DialogTitle>Bulk Student Enrollment</DialogTitle>
                    <DialogDescription className="text-zinc-500">
                      Enroll multiple students in a course at once
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4 mt-4">
                    <div>
                      <Label>Select Course</Label>
                      <Select 
                        value={enrollmentData.courseId}
                        onValueChange={(v) => setEnrollmentData({...enrollmentData, courseId: v})}
                      >
                        <SelectTrigger className="bg-zinc-800 border-white/10 mt-1">
                          <SelectValue placeholder="Choose a course" />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-800 border-white/10">
                          {/* Would need to fetch courses list */}
                          <SelectItem value="course-1">Course 1</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label>Student Emails</Label>
                      <Textarea
                        placeholder="Enter student emails (one per line, or comma/semicolon separated)"
                        value={enrollmentData.emails}
                        onChange={(e) => setEnrollmentData({...enrollmentData, emails: e.target.value})}
                        className="bg-zinc-800 border-white/10 mt-1 min-h-[120px]"
                        data-testid="bulk-emails-input"
                      />
                      <p className="text-xs text-zinc-500 mt-1">
                        Example: student1@example.com, student2@example.com
                      </p>
                    </div>
                    
                    <div className="flex justify-end gap-3 pt-4">
                      <Button variant="ghost" onClick={() => setShowEnrollDialog(false)}>
                        Cancel
                      </Button>
                      <Button 
                        onClick={handleBulkEnroll}
                        disabled={enrolling}
                        data-testid="submit-bulk-enroll-btn"
                      >
                        {enrolling ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Enrolling...
                          </>
                        ) : (
                          <>
                            <UserPlus className="w-4 h-4 mr-2" />
                            Enroll Students
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
              
              <Button variant="outline" className="border-white/10">
                <BarChart3 className="w-4 h-4 mr-2" />
                Export Reports
              </Button>
            </div>
          </div>

          {/* Main Content Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="bg-zinc-900/50 border border-white/10 mb-6">
              <TabsTrigger value="overview" className="data-[state=active]:bg-blue-500/20">
                <PieChart className="w-4 h-4 mr-2" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="teachers" className="data-[state=active]:bg-blue-500/20">
                <Users className="w-4 h-4 mr-2" />
                Teachers
              </TabsTrigger>
              <TabsTrigger value="students" className="data-[state=active]:bg-blue-500/20">
                <GraduationCap className="w-4 h-4 mr-2" />
                Students
              </TabsTrigger>
              <TabsTrigger value="analytics" className="data-[state=active]:bg-blue-500/20">
                <TrendingUp className="w-4 h-4 mr-2" />
                Analytics
              </TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Recent Enrollments */}
                <div className="glass-card p-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <Calendar className="w-5 h-5 text-blue-400" />
                    Recent Enrollments
                  </h3>
                  {dashboard?.recent_enrollments?.length > 0 ? (
                    <div className="space-y-3">
                      {dashboard.recent_enrollments.slice(0, 5).map((enrollment, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50">
                          <div>
                            <p className="font-medium text-sm">{enrollment.student_name || 'Student'}</p>
                            <p className="text-xs text-zinc-500">{enrollment.course_name || 'Course'}</p>
                          </div>
                          <Badge className="bg-emerald-500/20 text-emerald-400">
                            <CheckCircle className="w-3 h-3 mr-1" />
                            Enrolled
                          </Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-zinc-500 text-center py-8">No recent enrollments</p>
                  )}
                </div>

                {/* Course Performance */}
                <div className="glass-card p-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-violet-400" />
                    Course Performance
                  </h3>
                  {analytics?.course_analytics?.length > 0 ? (
                    <div className="space-y-3">
                      {analytics.course_analytics.slice(0, 5).map((course, idx) => (
                        <div key={idx} className="p-3 rounded-lg bg-zinc-800/50">
                          <div className="flex items-center justify-between mb-2">
                            <p className="font-medium text-sm truncate max-w-[200px]">{course.course_name}</p>
                            <span className="text-xs text-zinc-500">{course.enrolled} enrolled</span>
                          </div>
                          <div className="w-full bg-zinc-700 rounded-full h-2">
                            <div 
                              className="bg-violet-500 h-2 rounded-full transition-all"
                              style={{ width: `${Math.min(course.completion_rate, 100)}%` }}
                            />
                          </div>
                          <p className="text-xs text-zinc-500 mt-1">{course.completion_rate?.toFixed(1)}% completion</p>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-zinc-500 text-center py-8">No course data available</p>
                  )}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="teachers">
              <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="font-semibold">Teachers ({teachers.length})</h3>
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
                    <Input
                      placeholder="Search teachers..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 bg-zinc-800 border-white/10 w-64"
                    />
                  </div>
                </div>
                
                <Table>
                  <TableHeader>
                    <TableRow className="border-white/10">
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Department</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTeachers.map((teacher, idx) => (
                      <TableRow key={teacher.id || idx} className="border-white/10">
                        <TableCell className="font-medium">{teacher.full_name}</TableCell>
                        <TableCell className="text-zinc-400">{teacher.email}</TableCell>
                        <TableCell>{teacher.department || 'General'}</TableCell>
                        <TableCell>
                          <Badge className="bg-emerald-500/20 text-emerald-400">Active</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                    {filteredTeachers.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center text-zinc-500 py-8">
                          No teachers found
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </TabsContent>

            <TabsContent value="students">
              <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="font-semibold">Students ({students.length})</h3>
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
                    <Input
                      placeholder="Search students..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 bg-zinc-800 border-white/10 w-64"
                    />
                  </div>
                </div>
                
                <Table>
                  <TableHeader>
                    <TableRow className="border-white/10">
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>GPA</TableHead>
                      <TableHead>Courses</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredStudents.map((student, idx) => (
                      <TableRow key={student.id || idx} className="border-white/10">
                        <TableCell className="font-medium">{student.full_name}</TableCell>
                        <TableCell className="text-zinc-400">{student.email}</TableCell>
                        <TableCell>
                          <Badge className={student.gpa >= 3.0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}>
                            {student.gpa?.toFixed(2) || 'N/A'}
                          </Badge>
                        </TableCell>
                        <TableCell>{student.enrolled_courses || 0}</TableCell>
                        <TableCell>
                          <Badge className="bg-blue-500/20 text-blue-400">Active</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                    {filteredStudents.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-zinc-500 py-8">
                          No students found
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </TabsContent>

            <TabsContent value="analytics">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Attendance Rate */}
                <div className="glass-card p-6">
                  <h3 className="font-semibold mb-4">Attendance Overview</h3>
                  <div className="text-center py-8">
                    <div className="relative w-32 h-32 mx-auto mb-4">
                      <svg className="w-32 h-32 transform -rotate-90">
                        <circle
                          className="text-zinc-700"
                          strokeWidth="8"
                          stroke="currentColor"
                          fill="transparent"
                          r="56"
                          cx="64"
                          cy="64"
                        />
                        <circle
                          className="text-emerald-500"
                          strokeWidth="8"
                          strokeDasharray={`${(analytics?.attendance_rate || 0) * 3.52} 352`}
                          strokeLinecap="round"
                          stroke="currentColor"
                          fill="transparent"
                          r="56"
                          cx="64"
                          cy="64"
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-2xl font-bold">{analytics?.attendance_rate?.toFixed(1) || 0}%</span>
                      </div>
                    </div>
                    <p className="text-zinc-400">Overall Attendance Rate</p>
                  </div>
                </div>

                {/* Monthly Revenue */}
                <div className="glass-card p-6">
                  <h3 className="font-semibold mb-4">Monthly Revenue</h3>
                  {analytics?.monthly_revenue && Object.keys(analytics.monthly_revenue).length > 0 ? (
                    <div className="space-y-3">
                      {Object.entries(analytics.monthly_revenue)
                        .sort((a, b) => b[0].localeCompare(a[0]))
                        .slice(0, 6)
                        .map(([month, amount]) => (
                          <div key={month} className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50">
                            <span className="text-zinc-400">{month}</span>
                            <span className="font-semibold text-emerald-400">${amount.toFixed(2)}</span>
                          </div>
                        ))}
                    </div>
                  ) : (
                    <p className="text-zinc-500 text-center py-8">No revenue data available</p>
                  )}
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </DashboardLayout>
  );
}
