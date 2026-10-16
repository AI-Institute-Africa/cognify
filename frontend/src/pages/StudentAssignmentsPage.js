import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { 
  FileText, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Send,
  BookOpen,
  Calendar,
  Award,
  Loader2,
  Upload,
  FileUp,
  X,
  Eye,
  Download,
  Lock,
  CreditCard
} from 'lucide-react';
import { toast } from 'sonner';
import { getStudentAssignments, getAssignments, submitAndGradeAssignment, getErrorMessage } from '../services/api';

const API = process.env.REACT_APP_BACKEND_URL;

export default function StudentAssignmentsPage() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAssignment, setSelectedAssignment] = useState(null);
  const [submissionContent, setSubmissionContent] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (user) {
      fetchAssignments();
    }
  }, [user]);

  const fetchAssignments = async () => {
    try {
      // Use different API based on user role
      const isTeacherOrAdmin = user?.role === 'teacher' || user?.role === 'org_admin' || user?.role === 'admin';
      const data = isTeacherOrAdmin ? await getAssignments() : await getStudentAssignments();
      setAssignments(data);
    } catch (error) {
      console.error('Failed to fetch assignments:', error);
      toast.error('Failed to load assignments');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'text/markdown'
    ];
    const allowedExtensions = ['.pdf', '.doc', '.docx', '.txt', '.md'];
    
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
      toast.error('Please upload a PDF, Word document, or text file');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const token = localStorage.getItem('cognify_token');
      const response = await fetch(`${API}/api/assignments/upload-submission`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        setUploadedFile({
          name: file.name,
          id: data.file_id,
          url: data.file_url,
          extracted_text: data.extracted_text
        });
        
        // If text was extracted, set it as the submission content
        if (data.extracted_text) {
          setSubmissionContent(data.extracted_text);
        }
        
        toast.success('File uploaded successfully');
      } else {
        toast.error('Failed to upload file');
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async () => {
    if (!submissionContent.trim() && !uploadedFile) {
      toast.error('Please enter your answer or upload a file');
      return;
    }

    setSubmitting(true);
    try {
      const result = await submitAndGradeAssignment(
        selectedAssignment.id, 
        submissionContent,
        uploadedFile?.id
      );
      toast.success(`Assignment submitted! Score: ${result.score}/${result.max_score}`);
      setSelectedAssignment(null);
      setSubmissionContent('');
      setUploadedFile(null);
      fetchAssignments();
    } catch (error) {
      toast.error(getErrorMessage(error, 'Submission failed'));
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusIcon = (assignment) => {
    if (assignment.submitted) {
      return <CheckCircle className="w-5 h-5 text-green-400" />;
    }
    const dueDate = new Date(assignment.due_date);
    if (dueDate < new Date()) {
      return <AlertCircle className="w-5 h-5 text-red-400" />;
    }
    return <Clock className="w-5 h-5 text-yellow-400" />;
  };

  const getStatusText = (assignment) => {
    if (assignment.submitted) {
      return `Submitted - Score: ${assignment.submission?.score || 0}/${assignment.max_score}`;
    }
    const dueDate = new Date(assignment.due_date);
    if (dueDate < new Date()) {
      return 'Overdue';
    }
    return 'Pending';
  };

  const renderAssignmentQuestions = (assignment) => {
    const content = assignment.content;
    if (!content) return null;

    return (
      <div className="mt-4 p-4 bg-zinc-900/50 rounded-lg border border-white/5">
        <h4 className="font-semibold text-violet-400 mb-3 flex items-center gap-2">
          <FileText className="w-4 h-4" />
          Assignment Questions
        </h4>
        
        {/* Main questions */}
        {content.questions && content.questions.length > 0 && (
          <div className="space-y-3">
            {content.questions.map((q, idx) => (
              <div key={idx} className="p-3 bg-zinc-800/50 rounded-lg">
                <p className="font-medium">Q{idx + 1}: {typeof q === 'string' ? q : q.question}</p>
                {q.points && <span className="text-xs text-zinc-500">({q.points} points)</span>}
              </div>
            ))}
          </div>
        )}

        {/* Reflection prompts */}
        {content.reflection_prompts && content.reflection_prompts.length > 0 && (
          <div className="mt-4">
            <h5 className="text-sm font-medium text-zinc-400 mb-2">Reflection Prompts:</h5>
            <ul className="space-y-2">
              {content.reflection_prompts.map((prompt, idx) => (
                <li key={idx} className="text-sm text-zinc-400 pl-4 border-l-2 border-violet-500/30">
                  {prompt}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Coding challenges */}
        {content.coding_challenge && (
          <div className="mt-4 p-3 bg-zinc-800/50 rounded-lg">
            <h5 className="text-sm font-medium text-amber-400 mb-2">Coding Challenge:</h5>
            <p className="text-sm">{content.coding_challenge}</p>
          </div>
        )}

        {/* Instructions */}
        {content.instructions && (
          <div className="mt-4">
            <h5 className="text-sm font-medium text-zinc-400 mb-2">Instructions:</h5>
            <p className="text-sm text-zinc-400">{content.instructions}</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <DashboardLayout>
      <Header title={t('assignments')} subtitle="View and submit your assignments" />
      
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-2xl sm:text-3xl font-bold flex items-center gap-3">
              <FileText className="w-6 h-6 sm:w-8 sm:h-8 text-blue-400" />
              {t('assignments')}
            </h1>
            <p className="text-zinc-400 mt-2">View and submit your course assignments</p>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
            </div>
          ) : assignments.length === 0 ? (
            <div className="glass-card p-12 text-center">
              <FileText className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">No Assignments Yet</h3>
              <p className="text-zinc-400">Assignments from your enrolled courses will appear here.</p>
            </div>
          ) : (
            <div className="grid gap-6">
              {assignments.map((assignment) => (
                <div 
                  key={assignment.id}
                  className="glass-card p-6 hover:border-white/20 transition-all"
                  data-testid={`assignment-card-${assignment.id}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        {getStatusIcon(assignment)}
                        <h3 className="text-xl font-semibold">{assignment.title}</h3>
                        <Badge className="bg-blue-500/20 text-blue-400">
                          {assignment.type || 'Essay'}
                        </Badge>
                      </div>
                      
                      <p className="text-zinc-400 mb-4">{assignment.description}</p>
                      
                      <div className="flex flex-wrap gap-4 text-sm text-zinc-500">
                        <span className="flex items-center gap-2">
                          <BookOpen className="w-4 h-4" />
                          {assignment.course_title || 'Course'}
                        </span>
                        {assignment.due_date && (
                          <span className="flex items-center gap-2">
                            <Calendar className="w-4 h-4" />
                            Due: {new Date(assignment.due_date).toLocaleDateString()}
                          </span>
                        )}
                        <span className="flex items-center gap-2">
                          <Award className="w-4 h-4" />
                          Max Score: {assignment.max_score}
                        </span>
                      </div>

                      {/* Assessment Restriction Banner */}
                      {assignment.assessment_eligible === false && (
                        <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-center justify-between text-amber-300 text-sm">
                          <div className="flex items-center gap-2">
                            <Lock className="w-4 h-4 text-amber-400 flex-shrink-0" />
                            <span>{assignment.assessment_lock_message || 'Assessment locked. Payment required.'}</span>
                          </div>
                          {assignment.course_id && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => navigate(`/payment?course_id=${assignment.course_id}`)}
                              className="ml-3 border-amber-500/40 text-amber-300 hover:bg-amber-500/20 text-xs shrink-0"
                            >
                              <CreditCard className="w-3.5 h-3.5 mr-1" />
                              Pay Now
                            </Button>
                          )}
                        </div>
                      )}

                      <div className="mt-4 flex items-center gap-2">
                        <span className={`px-3 py-1 rounded-full text-sm ${
                          assignment.submitted 
                            ? 'bg-green-500/20 text-green-400' 
                            : 'bg-yellow-500/20 text-yellow-400'
                        }`}>
                          {getStatusText(assignment)}
                        </span>
                        {assignment.auto_grade && (
                          <span className="px-3 py-1 rounded-full text-sm bg-blue-500/20 text-blue-400">
                            Auto-Graded
                          </span>
                        )}
                        <span className="px-3 py-1 rounded-full text-sm bg-violet-500/20 text-violet-400">
                          {assignment.difficulty || 'Standard'}
                        </span>
                      </div>
                      
                      {assignment.submitted && assignment.submission?.feedback && (
                        <div className="mt-4 p-4 bg-zinc-900/50 rounded-lg border border-white/5">
                          <h4 className="text-sm font-semibold text-zinc-300 mb-2">Feedback:</h4>
                          <p className="text-zinc-400 text-sm">{assignment.submission.feedback}</p>
                        </div>
                      )}
                    </div>
                    
                    {!assignment.submitted && (
                      assignment.assessment_eligible === false ? (
                        <Button
                          disabled
                          className="bg-zinc-800 text-zinc-400 border border-amber-500/30 cursor-not-allowed opacity-80"
                          data-testid={`locked-btn-${assignment.id}`}
                        >
                          <Lock className="w-4 h-4 mr-2 text-amber-400" />
                          Locked (Payment Due)
                        </Button>
                      ) : (
                        <Button
                          onClick={() => setSelectedAssignment(assignment)}
                          className="bg-blue-500 hover:bg-blue-600"
                          data-testid={`submit-btn-${assignment.id}`}
                        >
                          <Send className="w-4 h-4 mr-2" />
                          {t('submit')}
                        </Button>
                      )
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Submission Modal */}
        {selectedAssignment && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="glass-card p-8 w-full max-w-3xl max-h-[90vh] overflow-y-auto">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <Badge className="mb-2 bg-violet-500/20 text-violet-400">
                    {selectedAssignment.course_title || 'Course'}
                  </Badge>
                  <h2 className="text-2xl font-bold">{selectedAssignment.title}</h2>
                </div>
                <Button 
                  variant="ghost" 
                  size="icon"
                  onClick={() => {
                    setSelectedAssignment(null);
                    setSubmissionContent('');
                    setUploadedFile(null);
                  }}
                >
                  <X className="w-5 h-5" />
                </Button>
              </div>
              
              <p className="text-zinc-400 mb-4">{selectedAssignment.description}</p>
              
              {/* Show questions in modal too */}
              {renderAssignmentQuestions(selectedAssignment)}
              
              <div className="space-y-6 mt-6">
                {/* File Upload */}
                <div>
                  <Label className="flex items-center gap-2 mb-2">
                    <Upload className="w-4 h-4" />
                    Upload Your Work (Optional)
                  </Label>
                  <p className="text-xs text-zinc-500 mb-3">
                    Supported formats: PDF, Word (.doc, .docx), Text (.txt, .md)
                  </p>
                  
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    accept=".pdf,.doc,.docx,.txt,.md"
                    className="hidden"
                  />
                  
                  {uploadedFile ? (
                    <div className="flex items-center gap-3 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
                      <FileText className="w-5 h-5 text-emerald-400" />
                      <span className="flex-1 truncate">{uploadedFile.name}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setUploadedFile(null)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ) : (
                    <Button
                      variant="outline"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploading}
                      className="w-full border-dashed border-white/20 hover:border-blue-500/50"
                    >
                      {uploading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Uploading...
                        </>
                      ) : (
                        <>
                          <FileUp className="w-4 h-4 mr-2" />
                          Click to upload file
                        </>
                      )}
                    </Button>
                  )}
                </div>

                {/* Text Answer */}
                <div>
                  <Label className="mb-2 block">Your Answer</Label>
                  <Textarea
                    value={submissionContent}
                    onChange={(e) => setSubmissionContent(e.target.value)}
                    className="w-full min-h-[200px] bg-zinc-900/50 border-white/10"
                    placeholder="Type your answer here or upload a file above..."
                  />
                </div>
                
                <div className="flex gap-4 justify-end pt-4 border-t border-white/10">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setSelectedAssignment(null);
                      setSubmissionContent('');
                      setUploadedFile(null);
                    }}
                    className="border-white/10"
                  >
                    {t('cancel')}
                  </Button>
                  <Button
                    onClick={handleSubmit}
                    disabled={submitting || (!submissionContent.trim() && !uploadedFile)}
                    className="bg-blue-500 hover:bg-blue-600"
                    data-testid="submit-assignment-btn"
                  >
                    {submitting ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Submitting...
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4 mr-2" />
                        Submit & Grade
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
