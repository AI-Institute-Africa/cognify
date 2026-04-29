import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import {
  BookOpen, Upload, Trash2, Save, Loader2,
  FileText, Plus, ChevronDown, ChevronRight,
  Edit2, Eye, ArrowLeft
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;
const getAuth = () => ({ Authorization: `Bearer ${localStorage.getItem('cognify_token')}` });

export default function CourseManagePage() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const fileInputRef = useRef(null);

  const [course, setCourse] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [expandedLesson, setExpandedLesson] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [generatingAssignment, setGeneratingAssignment] = useState(false);

  useEffect(() => { loadCourse(); }, [courseId]);

  const loadCourse = async () => {
    try {
      const [courseRes, lessonsRes] = await Promise.all([
        axios.get(`${API}/api/courses/${courseId}`, { headers: getAuth() }),
        axios.get(`${API}/api/courses/${courseId}/lessons`, { headers: getAuth() })
      ]);
      setCourse(courseRes.data);
      setLessons(Array.isArray(lessonsRes.data) ? lessonsRes.data : []);
      setEditForm({
        title: courseRes.data.title || courseRes.data.name || '',
        description: courseRes.data.description || '',
        category: courseRes.data.category || '',
        price: courseRes.data.price || 0,
        is_active: courseRes.data.is_active !== false
      });
    } catch (err) {
      toast.error('Failed to load course');
      navigate('/courses');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveCourse = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/api/courses/${courseId}`, editForm, { headers: getAuth() });
      toast.success('Course updated!');
      setEditMode(false);
      loadCourse();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update course');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCourse = async () => {
    if (!window.confirm('Are you sure you want to delete this course? This cannot be undone.')) return;
    try {
      await axios.delete(`${API}/api/courses/${courseId}`, { headers: getAuth() });
      toast.success('Course deleted');
      navigate('/courses');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete course');
    }
  };

  const handleGenerateAssignment = async () => {
    if (lessons.length === 0) {
      toast.error('No lessons available. Upload content first.');
      return;
    }
    setGeneratingAssignment(true);
    try {
      const { data } = await axios.post(
        `${API}/api/courses/${courseId}/generate-assignment-from-lessons`,
        { title: `${course?.title || course?.name} - Assignment` },
        { headers: getAuth(), timeout: 90000 }
      );
      toast.success(data.message || 'Assignment generated!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to generate assignment');
    } finally {
      setGeneratingAssignment(false);
    }
  };


  const handleUploadContent = async (file) => {
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await axios.post(
        `${API}/api/courses/${courseId}/generate-lessons-from-content`,
        formData,
        { headers: { ...getAuth(), 'Content-Type': 'multipart/form-data' }, timeout: 90000 }
      );
      toast.success(data.message || 'Lessons generated from document!');
      setLessons(data.lessons || []);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message;
      if (msg.includes('timeout') || msg.includes('504')) {
        toast.error('Generation timed out. Try a smaller document.');
      } else {
        toast.error(msg || 'Failed to generate lessons');
      }
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-screen">
          <Loader2 className="w-12 h-12 animate-spin text-violet-500" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header
        title="Manage Course"
        subtitle={course?.title || course?.name || 'Course'}
      />

      <div className="p-6 max-w-5xl mx-auto space-y-6">
        {/* Back button */}
        <Button variant="ghost" onClick={() => navigate('/courses')} className="mb-2" data-testid="back-to-courses">
          <ArrowLeft className="w-4 h-4 mr-2" /> Back to Courses
        </Button>

        {/* Course Details Card */}
        <div className="glass-card p-6" data-testid="course-details-card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">{course?.title || course?.name}</h2>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={() => setEditMode(!editMode)} data-testid="edit-course-btn">
                <Edit2 className="w-4 h-4 mr-1" /> {editMode ? 'Cancel' : 'Edit'}
              </Button>
              <Button variant="outline" size="sm" className="text-red-400 border-red-500/30" onClick={handleDeleteCourse} data-testid="delete-course-btn">
                <Trash2 className="w-4 h-4 mr-1" /> Delete
              </Button>
            </div>
          </div>

          {editMode ? (
            <div className="space-y-4">
              <div>
                <Label>Title</Label>
                <Input value={editForm.title} onChange={(e) => setEditForm({...editForm, title: e.target.value})}
                  className="bg-zinc-800 border-white/10 mt-1" data-testid="edit-title" />
              </div>
              <div>
                <Label>Description</Label>
                <Textarea value={editForm.description} onChange={(e) => setEditForm({...editForm, description: e.target.value})}
                  className="bg-zinc-800 border-white/10 mt-1 min-h-[100px]" data-testid="edit-description" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Category</Label>
                  <Input value={editForm.category} onChange={(e) => setEditForm({...editForm, category: e.target.value})}
                    className="bg-zinc-800 border-white/10 mt-1" />
                </div>
                <div>
                  <Label>Price ($)</Label>
                  <Input type="number" value={editForm.price} onChange={(e) => setEditForm({...editForm, price: parseFloat(e.target.value) || 0})}
                    className="bg-zinc-800 border-white/10 mt-1" />
                </div>
              </div>
              <Button onClick={handleSaveCourse} disabled={saving} className="bg-blue-600 hover:bg-blue-700" data-testid="save-course-btn">
                {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
                Save Changes
              </Button>
            </div>
          ) : (
            <div className="space-y-2 text-sm text-zinc-400">
              <p>{course?.description || 'No description'}</p>
              <div className="flex gap-4 pt-2">
                <Badge>{course?.category || 'General'}</Badge>
                <Badge className={course?.is_active ? 'bg-emerald-500/20 text-emerald-400' : 'bg-zinc-500/20'}>
                  {course?.is_active ? 'Active' : 'Draft'}
                </Badge>
                <span>${course?.price || 0}</span>
                <span>{lessons.length} lessons</span>
              </div>
            </div>
          )}
        </div>

        {/* Upload Content to Generate Lessons */}
        <div className="glass-card p-6 border-amber-500/20" data-testid="upload-content-section">
          <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
            <Upload className="w-5 h-5 text-amber-400" />
            Generate Lessons from Document
          </h3>
          <p className="text-sm text-zinc-400 mb-4">
            Upload a PDF, DOCX, or TXT file. AI will analyze the content and create real, structured lessons with actual text from your document.
          </p>
          <input
            type="file"
            ref={fileInputRef}
            className="hidden"
            accept=".pdf,.docx,.doc,.txt,.pptx"
            onChange={(e) => e.target.files?.[0] && handleUploadContent(e.target.files[0])}
          />
          <Button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            className="bg-amber-600 hover:bg-amber-700"
            data-testid="upload-content-btn"
          >
            {uploading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating lessons from document...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4 mr-2" />
                Upload Document & Generate Lessons
              </>
            )}
          </Button>
        </div>

        {/* Lessons List */}
        <div className="glass-card p-6" data-testid="lessons-section">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-violet-400" />
              Lessons ({lessons.length})
            </h3>
            {lessons.length > 0 && (
              <Button
                onClick={handleGenerateAssignment}
                disabled={generatingAssignment}
                className="bg-emerald-600 hover:bg-emerald-700"
                data-testid="generate-assignment-btn"
              >
                {generatingAssignment ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Generating...</>
                ) : (
                  <><Plus className="w-4 h-4 mr-2" /> Generate Assignment from Lessons</>
                )}
              </Button>
            )}
          </div>

          {lessons.length === 0 ? (
            <div className="text-center py-10 text-zinc-500">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="font-medium">No lessons yet</p>
              <p className="text-sm">Upload a document above to auto-generate structured lessons.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {lessons.map((lesson, idx) => (
                <div key={lesson.id || idx} className="border border-white/5 rounded-xl overflow-hidden" data-testid={`lesson-${idx}`}>
                  <button
                    className="w-full p-4 flex items-center justify-between hover:bg-white/5 transition-colors text-left"
                    onClick={() => setExpandedLesson(expandedLesson === idx ? null : idx)}
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-8 h-8 rounded-lg bg-violet-500/20 flex items-center justify-center text-sm font-bold text-violet-400">
                        {idx + 1}
                      </span>
                      <div>
                        <p className="font-medium text-sm">{lesson.title}</p>
                        <p className="text-xs text-zinc-500">{lesson.duration || '30 min'}</p>
                      </div>
                    </div>
                    {expandedLesson === idx ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                  </button>
                  {expandedLesson === idx && (
                    <div className="px-4 pb-4 border-t border-white/5">
                      {lesson.description && (
                        <p className="text-sm text-zinc-400 mt-3 mb-2 italic">{lesson.description}</p>
                      )}
                      {lesson.content && (
                        <div className="text-sm text-zinc-300 mt-2 whitespace-pre-wrap bg-zinc-800/50 rounded-lg p-4">
                          {lesson.content}
                        </div>
                      )}
                      {lesson.key_points && lesson.key_points.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs font-semibold text-zinc-400 mb-1">Key Points:</p>
                          <ul className="list-disc list-inside text-sm text-zinc-400 space-y-1">
                            {lesson.key_points.map((kp, i) => <li key={i}>{kp}</li>)}
                          </ul>
                        </div>
                      )}
                      {lesson.source_filename && (
                        <p className="text-xs text-zinc-600 mt-2">Source: {lesson.source_filename}</p>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
