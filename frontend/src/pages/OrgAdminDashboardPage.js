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
  getOrgAnalytics,
  inviteOrgStaff,
  assignStaffRights,
  uploadOrgDocument,
  getOrgDocuments
} from '../services/api';
import axios from 'axios';
import { 
  Building2, Users, GraduationCap, BookOpen, DollarSign,
  Upload, UserPlus, BarChart3, TrendingUp, FileText,
  Loader2, Search, Mail, Phone, CheckCircle, AlertCircle,
  PieChart, Calendar, Settings, Shield, Trash2, Download,
  UserCheck, XCircle, Clock
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
  
  // Staff Invitation
  const [showInviteStaffDialog, setShowInviteStaffDialog] = useState(false);
  const [invitingStaff, setInvitingStaff] = useState(false);
  const [newStaff, setNewStaff] = useState({
    email: '',
    fullName: '',
    role: 'teacher'
  });
  
  // Staff Rights Management
  const [showRightsDialog, setShowRightsDialog] = useState(false);
  const [selectedStaff, setSelectedStaff] = useState(null);
  const [staffRights, setStaffRights] = useState({
    can_create_courses: false,
    can_manage_participants: false,
    can_upload_content: false,
    can_invite_participants: false
  });
  
  // Document Upload
  const [showDocUploadDialog, setShowDocUploadDialog] = useState(false);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [orgDocuments, setOrgDocuments] = useState([]);
  const [newDocument, setNewDocument] = useState({
    file: null,
    title: '',
    description: '',
    docType: 'reference'
  });
  
  const [searchTerm, setSearchTerm] = useState('');
  const [pendingUsers, setPendingUsers] = useState([]);
  const [approvingUser, setApprovingUser] = useState(null);

  const API = process.env.REACT_APP_BACKEND_URL;
  const getAuth = () => ({ Authorization: `Bearer ${localStorage.getItem('cognify_token')}` });

  useEffect(() => {
    loadDashboardData();
    loadPendingUsers();
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

  const loadPendingUsers = async () => {
    try {
      const { data } = await axios.get(`${API}/api/organizations/pending-users`, { headers: getAuth() });
      setPendingUsers(data.pending_users || []);
    } catch (err) {
      console.error('Failed to load pending users:', err);
    }
  };

  const handleUserApproval = async (userId, action) => {
    setApprovingUser(userId);
    try {
      const { data } = await axios.post(`${API}/api/organizations/approve-user`, 
        { user_id: userId, action },
        { headers: getAuth() }
      );
      toast.success(data.message);
      setPendingUsers(prev => prev.filter(u => u.id !== userId));
      if (action === 'approve') loadDashboardData();
    } catch (err) {
      toast.error(err.response?.data?.detail || `Failed to ${action} user`);
    } finally {
      setApprovingUser(null);
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

  const handleInviteStaff = async () => {
    if (!newStaff.email || !newStaff.fullName) {
      toast.error('Please fill in all fields');
      return;
    }
    
    setInvitingStaff(true);
    try {
      const result = await inviteOrgStaff(newStaff.email, newStaff.fullName, newStaff.role);
      toast.success(`Staff member invited! ${result.temp_password ? `Temp password: ${result.temp_password}` : ''}`);
      setShowInviteStaffDialog(false);
      setNewStaff({ email: '', fullName: '', role: 'teacher' });
      loadDashboardData();
    } catch (error) {
      console.error('Failed to invite staff:', error);
      toast.error(error.response?.data?.detail || 'Failed to invite staff');
    } finally {
      setInvitingStaff(false);
    }
  };

  const handleAssignRights = async () => {
    if (!selectedStaff) return;
    
    try {
      await assignStaffRights(selectedStaff.id, staffRights);
      toast.success('Staff rights updated!');
      setShowRightsDialog(false);
      setSelectedStaff(null);
    } catch (error) {
      console.error('Failed to assign rights:', error);
      toast.error('Failed to update rights');
    }
  };

  const openRightsDialog = (staff) => {
    setSelectedStaff(staff);
    setStaffRights({
      can_create_courses: staff.rights?.can_create_courses || false,
      can_manage_participants: staff.rights?.can_manage_participants || false,
      can_upload_content: staff.rights?.can_upload_content || false,
      can_invite_participants: staff.rights?.can_invite_participants || false
    });
    setShowRightsDialog(true);
  };

  const handleUploadDocument = async () => {
    if (!newDocument.file || !newDocument.title) {
      toast.error('Please select a file and provide a title');
      return;
    }
    
    setUploadingDoc(true);
    try {
      await uploadOrgDocument(
        newDocument.file, 
        newDocument.title, 
        newDocument.description, 
        newDocument.docType
      );
      toast.success('Document uploaded successfully!');
      setShowDocUploadDialog(false);
      setNewDocument({ file: null, title: '', description: '', docType: 'reference' });
      // Reload documents
      const docs = await getOrgDocuments();
      setOrgDocuments(docs || []);
    } catch (error) {
      console.error('Failed to upload document:', error);
      toast.error('Failed to upload document');
    } finally {
      setUploadingDoc(false);
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

  // Export Reports Function
  const handleExportReports = (reportType) => {
    let data = [];
    let filename = '';
    let headers = [];

    switch (reportType) {
      case 'staff':
        headers = ['Name', 'Email', 'Role', 'Status', 'Joined Date'];
        data = teachers.map(t => [
          t.full_name || 'N/A',
          t.email || 'N/A',
          t.role || 'teacher',
          t.status || 'active',
          t.created_at ? new Date(t.created_at).toLocaleDateString() : 'N/A'
        ]);
        filename = 'staff_report.csv';
        break;
      case 'participants':
        headers = ['Name', 'Email', 'GPA', 'Courses Enrolled', 'Status'];
        data = students.map(s => [
          s.full_name || 'N/A',
          s.email || 'N/A',
          s.gpa || 'N/A',
          s.courses_count || 0,
          s.status || 'active'
        ]);
        filename = 'participants_report.csv';
        break;
      case 'enrollments':
        headers = ['Student', 'Course', 'Enrolled Date', 'Status'];
        data = (dashboard?.recent_enrollments || []).map(e => [
          e.student_name || 'N/A',
          e.course_name || 'N/A',
          e.enrolled_at ? new Date(e.enrolled_at).toLocaleDateString() : 'N/A',
          'Enrolled'
        ]);
        filename = 'enrollments_report.csv';
        break;
      case 'analytics':
        headers = ['Metric', 'Value'];
        data = [
          ['Total Staff', dashboard?.statistics?.teachers || 0],
          ['Total Participants', dashboard?.statistics?.students || 0],
          ['Total Courses', dashboard?.statistics?.courses || 0],
          ['Total Revenue', `$${dashboard?.statistics?.revenue || 0}`],
          ['Average Course Completion', `${analytics?.avg_completion || 0}%`],
          ['Active Enrollments', analytics?.active_enrollments || 0]
        ];
        filename = 'analytics_report.csv';
        break;
      default:
        toast.error('Invalid report type');
        return;
    }

    // Create CSV content
    const csvContent = [
      headers.join(','),
      ...data.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    // Download file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
    
    toast.success(`${reportType.charAt(0).toUpperCase() + reportType.slice(1)} report downloaded!`);
  };

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
              
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="outline" className="border-white/10" data-testid="export-reports-btn">
                    <Download className="w-4 h-4 mr-2" />
                    Export Reports
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-zinc-900 border-white/10">
                  <DialogHeader>
                    <DialogTitle>Export Reports</DialogTitle>
                    <DialogDescription className="text-zinc-500">
                      Download organizational data as CSV files
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-3 mt-4">
                    <Button
                      onClick={() => handleExportReports('staff')}
                      variant="outline"
                      className="w-full justify-start border-white/10"
                      data-testid="export-staff-btn"
                    >
                      <Users className="w-4 h-4 mr-3 text-blue-400" />
                      Staff Report
                      <span className="ml-auto text-xs text-zinc-500">{teachers.length} records</span>
                    </Button>
                    <Button
                      onClick={() => handleExportReports('participants')}
                      variant="outline"
                      className="w-full justify-start border-white/10"
                      data-testid="export-participants-btn"
                    >
                      <GraduationCap className="w-4 h-4 mr-3 text-emerald-400" />
                      Participants Report
                      <span className="ml-auto text-xs text-zinc-500">{students.length} records</span>
                    </Button>
                    <Button
                      onClick={() => handleExportReports('enrollments')}
                      variant="outline"
                      className="w-full justify-start border-white/10"
                      data-testid="export-enrollments-btn"
                    >
                      <Calendar className="w-4 h-4 mr-3 text-amber-400" />
                      Enrollments Report
                      <span className="ml-auto text-xs text-zinc-500">{dashboard?.recent_enrollments?.length || 0} records</span>
                    </Button>
                    <Button
                      onClick={() => handleExportReports('analytics')}
                      variant="outline"
                      className="w-full justify-start border-white/10"
                      data-testid="export-analytics-btn"
                    >
                      <BarChart3 className="w-4 h-4 mr-3 text-violet-400" />
                      Analytics Summary
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>

          {/* Main Content Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="bg-zinc-900/50 border border-white/10 mb-6 flex-wrap">
              <TabsTrigger value="overview" className="data-[state=active]:bg-blue-500/20">
                <PieChart className="w-4 h-4 mr-2" />
                Overview
              </TabsTrigger>
              <TabsTrigger value="profile" className="data-[state=active]:bg-blue-500/20">
                <Building2 className="w-4 h-4 mr-2" />
                Organization Profile
              </TabsTrigger>
              <TabsTrigger value="teachers" className="data-[state=active]:bg-blue-500/20">
                <Users className="w-4 h-4 mr-2" />
                Staff
              </TabsTrigger>
              <TabsTrigger value="students" className="data-[state=active]:bg-blue-500/20">
                <GraduationCap className="w-4 h-4 mr-2" />
                Participants
              </TabsTrigger>
              <TabsTrigger value="analytics" className="data-[state=active]:bg-blue-500/20">
                <TrendingUp className="w-4 h-4 mr-2" />
                Analytics
              </TabsTrigger>
              <TabsTrigger value="approvals" className="data-[state=active]:bg-amber-500/20">
                <UserCheck className="w-4 h-4 mr-2" />
                Approvals
                {pendingUsers.length > 0 && (
                  <span className="ml-1.5 px-1.5 py-0.5 text-xs bg-amber-500/20 text-amber-400 rounded-full">{pendingUsers.length}</span>
                )}
              </TabsTrigger>
              <TabsTrigger value="courses" className="data-[state=active]:bg-violet-500/20">
                <BookOpen className="w-4 h-4 mr-2" />
                Courses
              </TabsTrigger>
            </TabsList>

            {/* Organization Profile Tab */}
            <TabsContent value="profile">
              <OrgProfileSection dashboard={dashboard} onUpdate={loadDashboardData} />
            </TabsContent>

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
                  <h3 className="font-semibold">Staff Members ({teachers.length})</h3>
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
                      <Input
                        placeholder="Search staff..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10 bg-zinc-800 border-white/10 w-64"
                      />
                    </div>
                    <Button onClick={() => setShowInviteStaffDialog(true)} data-testid="invite-staff-btn">
                      <UserPlus className="w-4 h-4 mr-2" />
                      Invite Staff
                    </Button>
                  </div>
                </div>
                
                <Table>
                  <TableHeader>
                    <TableRow className="border-white/10">
                      <TableHead>Name</TableHead>
                      <TableHead>Email</TableHead>
                      <TableHead>Role</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredTeachers.map((teacher, idx) => (
                      <TableRow key={teacher.id || idx} className="border-white/10">
                        <TableCell className="font-medium">{teacher.full_name}</TableCell>
                        <TableCell className="text-zinc-400">{teacher.email}</TableCell>
                        <TableCell>
                          <Badge className={teacher.role === 'org_admin' ? 'bg-violet-500/20 text-violet-400' : 'bg-blue-500/20 text-blue-400'}>
                            {teacher.role === 'org_admin' ? 'Admin' : 'Teacher'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge className="bg-emerald-500/20 text-emerald-400">Active</Badge>
                        </TableCell>
                        <TableCell>
                          <Button 
                            size="sm" 
                            variant="outline" 
                            onClick={() => openRightsDialog(teacher)}
                            data-testid={`manage-rights-${teacher.id}`}
                          >
                            <Shield className="w-4 h-4 mr-1" />
                            Rights
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                    {filteredTeachers.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-zinc-500 py-8">
                          No staff members found. Click &quot;Invite Staff&quot; to add team members.
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
                  <h3 className="font-semibold">Participants ({students.length})</h3>
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
                      <Input
                        placeholder="Search participants..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10 bg-zinc-800 border-white/10 w-64"
                      />
                    </div>
                    <Button onClick={() => setShowEnrollDialog(true)} data-testid="bulk-enroll-btn">
                      <UserPlus className="w-4 h-4 mr-2" />
                      Bulk Enroll
                    </Button>
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

            {/* Approvals Tab */}
            <TabsContent value="approvals">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">Pending Registrations</h3>
                    <p className="text-sm text-zinc-500">Approve or reject new user registrations for your organization</p>
                  </div>
                  <Button variant="outline" size="sm" onClick={loadPendingUsers} className="border-white/10">
                    <Loader2 className="w-4 h-4 mr-2" /> Refresh
                  </Button>
                </div>

                {pendingUsers.length === 0 ? (
                  <div className="glass-card p-12 text-center">
                    <UserCheck className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
                    <h4 className="font-semibold mb-1">No Pending Registrations</h4>
                    <p className="text-sm text-zinc-500">All registration requests have been processed.</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {pendingUsers.map((pu) => (
                      <div key={pu.id} className="glass-card p-4 flex items-center gap-4" data-testid={`pending-user-${pu.id}`}>
                        <div className="w-10 h-10 rounded-full bg-amber-500/20 flex items-center justify-center shrink-0">
                          <Clock className="w-5 h-5 text-amber-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium truncate">{pu.full_name}</p>
                          <p className="text-sm text-zinc-500">{pu.email}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400">
                              {pu.role === 'student' ? 'Student' : 'Staff'}
                            </span>
                            <span className="text-xs text-zinc-600">
                              {pu.created_at ? new Date(pu.created_at).toLocaleDateString() : ''}
                            </span>
                          </div>
                        </div>
                        <div className="flex gap-2 shrink-0">
                          <Button
                            size="sm"
                            onClick={() => handleUserApproval(pu.id, 'approve')}
                            disabled={approvingUser === pu.id}
                            className="bg-emerald-500 hover:bg-emerald-600 text-white"
                            data-testid={`approve-user-${pu.id}`}
                          >
                            {approvingUser === pu.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-1" />}
                            Approve
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleUserApproval(pu.id, 'reject')}
                            disabled={approvingUser === pu.id}
                            className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                            data-testid={`reject-user-${pu.id}`}
                          >
                            <XCircle className="w-4 h-4 mr-1" /> Reject
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Courses Tab */}
            <TabsContent value="courses">
              <OrgCoursesSection />
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Invite Staff Dialog */}
      <Dialog open={showInviteStaffDialog} onOpenChange={setShowInviteStaffDialog}>
        <DialogContent className="bg-zinc-900 border-white/10">
          <DialogHeader>
            <DialogTitle>Invite Staff Member</DialogTitle>
            <DialogDescription>
              Add a new teacher or administrator to your organization.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Full Name</Label>
              <Input
                value={newStaff.fullName}
                onChange={(e) => setNewStaff({...newStaff, fullName: e.target.value})}
                className="mt-1 bg-zinc-800 border-white/10"
                placeholder="John Doe"
              />
            </div>
            <div>
              <Label>Email Address</Label>
              <Input
                type="email"
                value={newStaff.email}
                onChange={(e) => setNewStaff({...newStaff, email: e.target.value})}
                className="mt-1 bg-zinc-800 border-white/10"
                placeholder="john@example.com"
              />
            </div>
            <div>
              <Label>Role</Label>
              <Select value={newStaff.role} onValueChange={(v) => setNewStaff({...newStaff, role: v})}>
                <SelectTrigger className="mt-1 bg-zinc-800 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-800 border-white/10">
                  <SelectItem value="teacher">Teacher</SelectItem>
                  <SelectItem value="org_admin">Administrator</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex gap-3 justify-end">
            <Button variant="outline" onClick={() => setShowInviteStaffDialog(false)}>Cancel</Button>
            <Button onClick={handleInviteStaff} disabled={invitingStaff}>
              {invitingStaff ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <UserPlus className="w-4 h-4 mr-2" />}
              Invite
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Staff Rights Dialog */}
      <Dialog open={showRightsDialog} onOpenChange={setShowRightsDialog}>
        <DialogContent className="bg-zinc-900 border-white/10">
          <DialogHeader>
            <DialogTitle>Manage Staff Rights</DialogTitle>
            <DialogDescription>
              {selectedStaff?.full_name} - Configure what this staff member can do.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50">
              <div>
                <p className="font-medium">Create Courses</p>
                <p className="text-sm text-zinc-500">Can create and manage courses</p>
              </div>
              <input
                type="checkbox"
                checked={staffRights.can_create_courses}
                onChange={(e) => setStaffRights({...staffRights, can_create_courses: e.target.checked})}
                className="w-5 h-5"
              />
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50">
              <div>
                <p className="font-medium">Upload Content</p>
                <p className="text-sm text-zinc-500">Can upload course materials</p>
              </div>
              <input
                type="checkbox"
                checked={staffRights.can_upload_content}
                onChange={(e) => setStaffRights({...staffRights, can_upload_content: e.target.checked})}
                className="w-5 h-5"
              />
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50">
              <div>
                <p className="font-medium">Manage Participants</p>
                <p className="text-sm text-zinc-500">Can add/remove participants</p>
              </div>
              <input
                type="checkbox"
                checked={staffRights.can_manage_participants}
                onChange={(e) => setStaffRights({...staffRights, can_manage_participants: e.target.checked})}
                className="w-5 h-5"
              />
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50">
              <div>
                <p className="font-medium">Invite Participants</p>
                <p className="text-sm text-zinc-500">Can send email invitations</p>
              </div>
              <input
                type="checkbox"
                checked={staffRights.can_invite_participants}
                onChange={(e) => setStaffRights({...staffRights, can_invite_participants: e.target.checked})}
                className="w-5 h-5"
              />
            </div>
          </div>
          <div className="flex gap-3 justify-end">
            <Button variant="outline" onClick={() => setShowRightsDialog(false)}>Cancel</Button>
            <Button onClick={handleAssignRights}>
              <Shield className="w-4 h-4 mr-2" />
              Save Rights
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Document Upload Dialog */}
      <Dialog open={showDocUploadDialog} onOpenChange={setShowDocUploadDialog}>
        <DialogContent className="bg-zinc-900 border-white/10">
          <DialogHeader>
            <DialogTitle>Upload Organization Document</DialogTitle>
            <DialogDescription>
              Upload PDFs, DOCX files for course reference material.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Document Title</Label>
              <Input
                value={newDocument.title}
                onChange={(e) => setNewDocument({...newDocument, title: e.target.value})}
                className="mt-1 bg-zinc-800 border-white/10"
                placeholder="Company Training Manual"
              />
            </div>
            <div>
              <Label>Description</Label>
              <Textarea
                value={newDocument.description}
                onChange={(e) => setNewDocument({...newDocument, description: e.target.value})}
                className="mt-1 bg-zinc-800 border-white/10"
                placeholder="Brief description of the document..."
              />
            </div>
            <div>
              <Label>Document Type</Label>
              <Select value={newDocument.docType} onValueChange={(v) => setNewDocument({...newDocument, docType: v})}>
                <SelectTrigger className="mt-1 bg-zinc-800 border-white/10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-800 border-white/10">
                  <SelectItem value="reference">Reference Material</SelectItem>
                  <SelectItem value="syllabus">Syllabus</SelectItem>
                  <SelectItem value="policy">Policy Document</SelectItem>
                  <SelectItem value="training">Training Material</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>File (PDF, DOCX, TXT)</Label>
              <Input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={(e) => setNewDocument({...newDocument, file: e.target.files[0]})}
                className="mt-1 bg-zinc-800 border-white/10"
              />
            </div>
          </div>
          <div className="flex gap-3 justify-end">
            <Button variant="outline" onClick={() => setShowDocUploadDialog(false)}>Cancel</Button>
            <Button onClick={handleUploadDocument} disabled={uploadingDoc}>
              {uploadingDoc ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Upload className="w-4 h-4 mr-2" />}
              Upload
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}


// Organization Profile Section Component
function OrgProfileSection({ dashboard, onUpdate }) {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState({
    name: dashboard?.org_name || '',
    description: dashboard?.description || '',
    website: dashboard?.website || '',
    phone: dashboard?.phone || '',
    address: dashboard?.address || '',
    facebook: dashboard?.social_media?.facebook || '',
    twitter: dashboard?.social_media?.twitter || '',
    linkedin: dashboard?.social_media?.linkedin || '',
    instagram: dashboard?.social_media?.instagram || ''
  });

  useEffect(() => {
    if (dashboard) {
      setProfile({
        name: dashboard.org_name || '',
        description: dashboard.description || '',
        website: dashboard.website || '',
        phone: dashboard.phone || '',
        address: dashboard.address || '',
        facebook: dashboard.social_media?.facebook || '',
        twitter: dashboard.social_media?.twitter || '',
        linkedin: dashboard.social_media?.linkedin || '',
        instagram: dashboard.social_media?.instagram || ''
      });
    }
  }, [dashboard]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('cognify_token');
      const API = process.env.REACT_APP_BACKEND_URL;
      
      const response = await fetch(`${API}/api/org/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: profile.name,
          description: profile.description,
          website: profile.website,
          phone: profile.phone,
          address: profile.address,
          social_media: {
            facebook: profile.facebook,
            twitter: profile.twitter,
            linkedin: profile.linkedin,
            instagram: profile.instagram
          }
        })
      });
      
      if (response.ok) {
        toast.success('Organization profile updated!');
        setEditing(false);
        onUpdate();
      } else {
        toast.error('Failed to update profile');
      }
    } catch (error) {
      console.error('Profile update error:', error);
      toast.error('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Organization Profile</h2>
        {!editing ? (
          <Button onClick={() => setEditing(true)}>
            Edit Profile
          </Button>
        ) : (
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setEditing(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Save Changes
            </Button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Basic Info */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="font-semibold flex items-center gap-2">
            <Building2 className="w-5 h-5 text-blue-400" />
            Basic Information
          </h3>
          
          <div className="space-y-4">
            <div>
              <Label>Organization Name</Label>
              <Input
                value={profile.name}
                onChange={(e) => setProfile({...profile, name: e.target.value})}
                disabled={!editing}
                className="mt-1 bg-zinc-800 border-white/10"
              />
            </div>
            
            <div>
              <Label>Description</Label>
              <Textarea
                value={profile.description}
                onChange={(e) => setProfile({...profile, description: e.target.value})}
                disabled={!editing}
                className="mt-1 bg-zinc-800 border-white/10 min-h-[100px]"
                placeholder="Describe your organization..."
              />
            </div>
            
            <div>
              <Label>Website</Label>
              <Input
                value={profile.website}
                onChange={(e) => setProfile({...profile, website: e.target.value})}
                disabled={!editing}
                className="mt-1 bg-zinc-800 border-white/10"
                placeholder="https://www.example.com"
              />
            </div>
            
            <div>
              <Label>Phone</Label>
              <Input
                value={profile.phone}
                onChange={(e) => setProfile({...profile, phone: e.target.value})}
                disabled={!editing}
                className="mt-1 bg-zinc-800 border-white/10"
                placeholder="+263 XXX XXXX"
              />
            </div>
            
            <div>
              <Label>Address</Label>
              <Input
                value={profile.address}
                onChange={(e) => setProfile({...profile, address: e.target.value})}
                disabled={!editing}
                className="mt-1 bg-zinc-800 border-white/10"
                placeholder="123 Main Street, City, Country"
              />
            </div>
          </div>
        </div>

        {/* Social Media */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="font-semibold flex items-center gap-2">
            <Users className="w-5 h-5 text-violet-400" />
            Social Media Links
          </h3>
          
          <div className="space-y-4">
            <div>
              <Label>Facebook</Label>
              <Input
                value={profile.facebook}
                onChange={(e) => setProfile({...profile, facebook: e.target.value})}
                disabled={!editing}
                className="mt-1 bg-zinc-800 border-white/10"
                placeholder="https://facebook.com/yourpage"
              />
            </div>
            
            <div>
              <Label>Twitter / X</Label>
              <Input
                value={profile.twitter}
                onChange={(e) => setProfile({...profile, twitter: e.target.value})}
                disabled={!editing}
                className="mt-1 bg-zinc-800 border-white/10"
                placeholder="https://twitter.com/yourhandle"
              />
            </div>
            
            <div>
              <Label>LinkedIn</Label>
              <Input
                value={profile.linkedin}
                onChange={(e) => setProfile({...profile, linkedin: e.target.value})}
                disabled={!editing}
                className="mt-1 bg-zinc-800 border-white/10"
                placeholder="https://linkedin.com/company/yourcompany"
              />
            </div>
            
            <div>
              <Label>Instagram</Label>
              <Input
                value={profile.instagram}
                onChange={(e) => setProfile({...profile, instagram: e.target.value})}
                disabled={!editing}
                className="mt-1 bg-zinc-800 border-white/10"
                placeholder="https://instagram.com/yourhandle"
              />
            </div>
          </div>
        </div>
      </div>
      
      {/* Display current info when not editing */}
      {!editing && (
        <div className="glass-card p-6">
          <h3 className="font-semibold mb-4">Current Organization Stats</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg bg-zinc-800/50 text-center">
              <p className="text-2xl font-bold text-blue-400">{dashboard?.total_staff || 0}</p>
              <p className="text-sm text-zinc-500">Staff Members</p>
            </div>
            <div className="p-4 rounded-lg bg-zinc-800/50 text-center">
              <p className="text-2xl font-bold text-emerald-400">{dashboard?.total_participants || 0}</p>
              <p className="text-sm text-zinc-500">Participants</p>
            </div>
            <div className="p-4 rounded-lg bg-zinc-800/50 text-center">
              <p className="text-2xl font-bold text-violet-400">{dashboard?.total_courses || 0}</p>
              <p className="text-sm text-zinc-500">Courses</p>
            </div>
            <div className="p-4 rounded-lg bg-zinc-800/50 text-center">
              <p className="text-2xl font-bold text-amber-400">${dashboard?.total_revenue?.toFixed(2) || '0.00'}</p>
              <p className="text-sm text-zinc-500">Revenue</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}



// Organization Courses Section Component
function OrgCoursesSection() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  const API = process.env.REACT_APP_BACKEND_URL;
  const getAuth = () => ({ Authorization: `Bearer ${localStorage.getItem('cognify_token')}` });

  useEffect(() => {
    loadCourses();
  }, []);

  const loadCourses = async () => {
    try {
      const { data } = await axios.get(`${API}/api/org/courses`, { headers: getAuth() });
      setCourses(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load courses:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="org-courses-tab">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Organization Courses</h3>
          <p className="text-sm text-zinc-500">{courses.length} course{courses.length !== 1 ? 's' : ''} in your organization</p>
        </div>
      </div>

      {courses.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <BookOpen className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
          <h4 className="font-semibold mb-1">No Courses Yet</h4>
          <p className="text-sm text-zinc-500">Create courses from the Courses section or upload PDFs.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {courses.map((course) => (
            <div key={course.id} className="glass-card p-5 hover:border-violet-500/30 transition-all" data-testid={`org-course-${course.id}`}>
              <div className="flex items-start justify-between mb-3">
                <h4 className="font-semibold text-sm leading-tight">{course.name || course.title}</h4>
                <Badge className={course.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-500/20 text-zinc-400'}>
                  {course.is_active ? 'Active' : 'Draft'}
                </Badge>
              </div>
              <p className="text-xs text-zinc-500 mb-3 line-clamp-2">{course.description || 'No description'}</p>
              <div className="flex items-center justify-between text-xs text-zinc-400">
                <span>{course.category || 'General'}</span>
                <span>${course.price || 0}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
