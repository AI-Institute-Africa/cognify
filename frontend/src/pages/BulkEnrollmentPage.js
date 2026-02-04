import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { 
  Users,
  Upload,
  Mail,
  FileText,
  Send,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Download,
  Trash2,
  UserPlus,
  Building2,
  Link2
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui/tabs';
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

export default function BulkEnrollmentPage() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [emails, setEmails] = useState('');
  const [csvFile, setCsvFile] = useState(null);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [enrollmentResults, setEnrollmentResults] = useState([]);
  const [courses, setCourses] = useState([]);
  const [pendingEnrollments, setPendingEnrollments] = useState([]);

  const API = process.env.REACT_APP_BACKEND_URL;

  // Load organization courses
  React.useEffect(() => {
    loadCourses();
    loadPendingEnrollments();
  }, []);

  const loadCourses = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/courses`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setCourses(data.filter(c => c.course_branch === 'customized' || c.created_by === user?.id));
      }
    } catch (error) {
      console.error('Failed to load courses:', error);
    }
  };

  const loadPendingEnrollments = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/org/pending-enrollments`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setPendingEnrollments(data);
      }
    } catch (error) {
      console.error('Failed to load pending enrollments:', error);
    }
  };

  // Parse emails from text area
  const parseEmails = (text) => {
    return text
      .split(/[\n,;]/)
      .map(e => e.trim().toLowerCase())
      .filter(e => e && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e));
  };

  // Handle CSV file upload
  const handleCsvUpload = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      toast.error('Please upload a CSV file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result;
      if (typeof text === 'string') {
        // Parse CSV - assume first column is email
        const lines = text.split('\n');
        const extractedEmails = [];
        
        lines.forEach((line, idx) => {
          if (idx === 0 && line.toLowerCase().includes('email')) return; // Skip header
          const columns = line.split(',');
          const email = columns[0]?.trim().toLowerCase();
          if (email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            extractedEmails.push(email);
          }
        });

        setEmails(prev => {
          const existingEmails = parseEmails(prev);
          const allEmails = [...new Set([...existingEmails, ...extractedEmails])];
          return allEmails.join('\n');
        });

        toast.success(`Extracted ${extractedEmails.length} emails from CSV`);
      }
    };
    reader.readAsText(file);
    setCsvFile(file);
  };

  // Handle bulk enrollment
  const handleBulkEnroll = async () => {
    const emailList = parseEmails(emails);
    
    if (emailList.length === 0) {
      toast.error('Please enter at least one valid email address');
      return;
    }

    if (!selectedCourse) {
      toast.error('Please select a course');
      return;
    }

    setLoading(true);
    setEnrollmentResults([]);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/org/bulk-enroll`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          emails: emailList,
          course_id: selectedCourse
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Enrollment failed');
      }

      const results = await response.json();
      setEnrollmentResults(results.results || []);
      
      const successCount = results.results?.filter(r => r.success).length || 0;
      const failCount = results.results?.filter(r => !r.success).length || 0;

      if (successCount > 0) {
        toast.success(`Successfully sent invitations to ${successCount} participants`);
      }
      if (failCount > 0) {
        toast.warning(`${failCount} emails failed to send`);
      }

      // Refresh pending enrollments
      loadPendingEnrollments();

    } catch (error) {
      console.error('Bulk enrollment error:', error);
      toast.error(error.message || 'Failed to enroll participants');
    } finally {
      setLoading(false);
    }
  };

  // Download sample CSV
  const downloadSampleCsv = () => {
    const csv = 'email,name\njohn@example.com,John Doe\njane@example.com,Jane Smith\n';
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'enrollment_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  // Resend invitation
  const resendInvitation = async (enrollmentId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API}/org/resend-invitation/${enrollmentId}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success('Invitation resent successfully');
        loadPendingEnrollments();
      } else {
        toast.error('Failed to resend invitation');
      }
    } catch (error) {
      toast.error('Failed to resend invitation');
    }
  };

  const emailCount = parseEmails(emails).length;

  return (
    <DashboardLayout>
      <Header 
        title="Bulk Enrollment"
        subtitle="Enroll participants in your organization's courses"
      />
      
      <div className="p-8">
        <div className="max-w-5xl mx-auto">
          {/* Info Banner */}
          <div className="glass-card p-6 mb-8 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 border-blue-500/20">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-xl bg-blue-500/20 flex items-center justify-center">
                <Building2 className="w-6 h-6 text-blue-400" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-1">Organization Enrollment</h3>
                <p className="text-zinc-400 text-sm">
                  Add participants by entering their email addresses or uploading a CSV file. 
                  Each participant will receive a magic link to set up their account and access the course.
                </p>
              </div>
            </div>
          </div>

          <Tabs defaultValue="enroll">
            <TabsList className="bg-zinc-900/50 border border-white/10 mb-6">
              <TabsTrigger value="enroll">
                <UserPlus className="w-4 h-4 mr-2" />
                Enroll Participants
              </TabsTrigger>
              <TabsTrigger value="pending">
                <Mail className="w-4 h-4 mr-2" />
                Pending Invitations
                {pendingEnrollments.length > 0 && (
                  <Badge className="ml-2 bg-amber-500/20 text-amber-400">{pendingEnrollments.length}</Badge>
                )}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="enroll">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Email Input Section */}
                <div className="glass-card p-6 space-y-4">
                  <h3 className="font-semibold flex items-center gap-2">
                    <Mail className="w-5 h-5 text-blue-400" />
                    Add Participants
                  </h3>

                  <div>
                    <Label htmlFor="emails">Email Addresses</Label>
                    <Textarea
                      id="emails"
                      placeholder="Enter email addresses (one per line, comma, or semicolon separated)&#10;&#10;example1@company.com&#10;example2@company.com"
                      value={emails}
                      onChange={(e) => setEmails(e.target.value)}
                      className="mt-1 min-h-[200px] bg-zinc-800 border-white/10 font-mono text-sm"
                      data-testid="bulk-emails-input"
                    />
                    <p className="text-xs text-zinc-500 mt-1">
                      {emailCount} valid email{emailCount !== 1 ? 's' : ''} detected
                    </p>
                  </div>

                  <div className="border-t border-white/10 pt-4">
                    <Label>Or Upload CSV File</Label>
                    <div className="mt-2 flex gap-2">
                      <label className="flex-1 p-4 rounded-lg border border-dashed border-white/20 hover:border-blue-500/50 cursor-pointer transition-colors text-center">
                        <Upload className="w-6 h-6 mx-auto mb-2 text-zinc-500" />
                        <span className="text-sm text-zinc-400">
                          {csvFile ? csvFile.name : 'Click to upload CSV'}
                        </span>
                        <input
                          type="file"
                          accept=".csv"
                          className="hidden"
                          onChange={handleCsvUpload}
                        />
                      </label>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={downloadSampleCsv}
                        className="border-white/10"
                      >
                        <Download className="w-4 h-4 mr-1" />
                        Template
                      </Button>
                    </div>
                  </div>
                </div>

                {/* Course Selection & Actions */}
                <div className="glass-card p-6 space-y-4">
                  <h3 className="font-semibold flex items-center gap-2">
                    <FileText className="w-5 h-5 text-violet-400" />
                    Course Selection
                  </h3>

                  <div>
                    <Label>Select Course</Label>
                    <Select value={selectedCourse} onValueChange={setSelectedCourse}>
                      <SelectTrigger className="mt-1 bg-zinc-800 border-white/10">
                        <SelectValue placeholder="Choose a course to enroll participants" />
                      </SelectTrigger>
                      <SelectContent className="bg-zinc-900 border-white/10">
                        {courses.map(course => (
                          <SelectItem key={course.id} value={course.id}>
                            {course.title || course.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {selectedCourse && (
                    <div className="p-4 rounded-lg bg-zinc-800/50">
                      <p className="text-sm text-zinc-400">
                        Selected: <span className="text-white font-medium">
                          {courses.find(c => c.id === selectedCourse)?.title}
                        </span>
                      </p>
                    </div>
                  )}

                  <div className="pt-4 border-t border-white/10">
                    <h4 className="text-sm font-medium mb-2">What happens next?</h4>
                    <ul className="space-y-2 text-sm text-zinc-400">
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5" />
                        Each participant receives an email with a magic link
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5" />
                        They click the link to set their password
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5" />
                        Automatically enrolled in the selected course
                      </li>
                    </ul>
                  </div>

                  <Button
                    onClick={handleBulkEnroll}
                    disabled={loading || emailCount === 0 || !selectedCourse}
                    className="w-full bg-blue-500 hover:bg-blue-600"
                    data-testid="send-invitations-btn"
                  >
                    {loading ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Sending Invitations...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        Send Invitations ({emailCount})
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {/* Results Section */}
              {enrollmentResults.length > 0 && (
                <div className="glass-card p-6 mt-6">
                  <h3 className="font-semibold mb-4">Enrollment Results</h3>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {enrollmentResults.map((result, idx) => (
                      <div 
                        key={idx}
                        className={`p-3 rounded-lg flex items-center justify-between ${
                          result.success ? 'bg-emerald-500/10' : 'bg-red-500/10'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          {result.success ? (
                            <CheckCircle className="w-4 h-4 text-emerald-400" />
                          ) : (
                            <AlertCircle className="w-4 h-4 text-red-400" />
                          )}
                          <span className="text-sm">{result.email}</span>
                        </div>
                        <span className={`text-xs ${result.success ? 'text-emerald-400' : 'text-red-400'}`}>
                          {result.success ? 'Invitation Sent' : result.error || 'Failed'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="pending">
              <div className="glass-card p-6">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Mail className="w-5 h-5 text-amber-400" />
                  Pending Invitations
                </h3>

                {pendingEnrollments.length === 0 ? (
                  <div className="text-center py-8 text-zinc-500">
                    <Users className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No pending invitations</p>
                    <p className="text-sm">Enrolled participants will appear here until they accept</p>
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow className="border-white/10">
                        <TableHead>Email</TableHead>
                        <TableHead>Course</TableHead>
                        <TableHead>Sent</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {pendingEnrollments.map((enrollment) => (
                        <TableRow key={enrollment.id} className="border-white/5">
                          <TableCell className="font-mono text-sm">{enrollment.email}</TableCell>
                          <TableCell>{enrollment.course_name}</TableCell>
                          <TableCell className="text-zinc-400 text-sm">
                            {new Date(enrollment.created_at).toLocaleDateString()}
                          </TableCell>
                          <TableCell>
                            <Badge className="bg-amber-500/20 text-amber-400">Pending</Badge>
                          </TableCell>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => resendInvitation(enrollment.id)}
                            >
                              <RefreshCw className="w-4 h-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </DashboardLayout>
  );
}
