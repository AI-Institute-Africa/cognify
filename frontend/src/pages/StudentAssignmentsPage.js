import React, { useState, useEffect } from 'react';
import { Sidebar } from '../components/Sidebar';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { 
  FileText, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Send,
  BookOpen,
  Calendar,
  Award,
  Loader2
} from 'lucide-react';
import { toast } from 'sonner';
import { getStudentAssignments, submitAndGradeAssignment } from '../services/api';

export default function StudentAssignmentsPage() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAssignment, setSelectedAssignment] = useState(null);
  const [submissionContent, setSubmissionContent] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchAssignments();
  }, []);

  const fetchAssignments = async () => {
    try {
      const data = await getStudentAssignments();
      setAssignments(data);
    } catch (error) {
      console.error('Failed to fetch assignments:', error);
      toast.error('Failed to load assignments');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!submissionContent.trim()) {
      toast.error('Please enter your answer');
      return;
    }

    setSubmitting(true);
    try {
      const result = await submitAndGradeAssignment(selectedAssignment.id, submissionContent);
      toast.success(`Assignment submitted! Score: ${result.score}/${result.max_score}`);
      setSelectedAssignment(null);
      setSubmissionContent('');
      fetchAssignments();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Submission failed');
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

  return (
    <div className="min-h-screen bg-[#09090B] flex">
      <Sidebar />
      
      <main className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <FileText className="w-8 h-8 text-blue-400" />
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
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        {getStatusIcon(assignment)}
                        <h3 className="text-xl font-semibold">{assignment.title}</h3>
                      </div>
                      
                      <p className="text-zinc-400 mb-4">{assignment.description}</p>
                      
                      <div className="flex flex-wrap gap-4 text-sm text-zinc-500">
                        <span className="flex items-center gap-2">
                          <BookOpen className="w-4 h-4" />
                          {assignment.course_title}
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
                      </div>
                      
                      {assignment.submitted && assignment.submission?.feedback && (
                        <div className="mt-4 p-4 bg-zinc-900/50 rounded-lg border border-white/5">
                          <h4 className="text-sm font-semibold text-zinc-300 mb-2">Feedback:</h4>
                          <p className="text-zinc-400 text-sm">{assignment.submission.feedback}</p>
                        </div>
                      )}
                    </div>
                    
                    {!assignment.submitted && (
                      <Button
                        onClick={() => setSelectedAssignment(assignment)}
                        className="bg-blue-500 hover:bg-blue-600"
                      >
                        <Send className="w-4 h-4 mr-2" />
                        {t('submit')}
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Submission Modal */}
      {selectedAssignment && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="glass-card p-8 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-2xl font-bold mb-2">{selectedAssignment.title}</h2>
            <p className="text-zinc-400 mb-6">{selectedAssignment.description}</p>
            
            <div className="space-y-4">
              <div>
                <Label>Your Answer</Label>
                <textarea
                  value={submissionContent}
                  onChange={(e) => setSubmissionContent(e.target.value)}
                  className="w-full h-64 mt-2 p-4 bg-zinc-900/50 border border-white/10 rounded-lg focus:border-blue-500/50 outline-none resize-none"
                  placeholder="Type your answer here..."
                />
              </div>
              
              <div className="flex gap-4 justify-end">
                <Button
                  variant="outline"
                  onClick={() => {
                    setSelectedAssignment(null);
                    setSubmissionContent('');
                  }}
                >
                  {t('cancel')}
                </Button>
                <Button
                  onClick={handleSubmit}
                  disabled={submitting}
                  className="bg-blue-500 hover:bg-blue-600"
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
  );
}
