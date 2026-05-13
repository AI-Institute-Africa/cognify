import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { DashboardLayout } from '../components/DashboardLayout';
import { Header } from '../components/Header';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '../components/ui/select';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger
} from '../components/ui/dialog';
import {
  FileText, Upload, Trash2, Search, Loader2,
  BookOpen, Plus, Eye, Calendar, User, FolderOpen
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;
const getAuth = () => ({ Authorization: `Bearer ${localStorage.getItem('cognify_token')}` });

const CATEGORIES = [
  { value: 'all', label: 'All Categories' },
  { value: 'general', label: 'General' },
  { value: 'science', label: 'Science' },
  { value: 'mathematics', label: 'Mathematics' },
  { value: 'language', label: 'Language & Literature' },
  { value: 'technology', label: 'Technology' },
  { value: 'business', label: 'Business' },
  { value: 'arts', label: 'Arts & Humanities' },
  { value: 'health', label: 'Health & Medicine' },
  { value: 'other', label: 'Other' }
];

export default function PremadeCoursesPage() {
  const { user } = useAuth();
  const fileInputRef = useRef(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  const [uploadForm, setUploadForm] = useState({ title: '', description: '', category: 'general' });
  const [selectedFile, setSelectedFile] = useState(null);
  const [viewDoc, setViewDoc] = useState(null);

  useEffect(() => { loadDocuments(); }, [selectedCategory]);

  const loadDocuments = async () => {
    try {
      const params = selectedCategory !== 'all' ? `?category=${selectedCategory}` : '';
      const { data } = await axios.get(`${API}/api/premade-courses${params}`, { headers: getAuth() });
      setDocuments(data.documents || []);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !uploadForm.title) {
      toast.error('Please select a file and enter a title');
      return;
    }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('title', uploadForm.title);
      formData.append('description', uploadForm.description);
      formData.append('category', uploadForm.category);
      
      const { data } = await axios.post(`${API}/api/premade-courses/upload`, formData, {
        headers: { ...getAuth(), 'Content-Type': 'multipart/form-data' },
        timeout: 60000
      });
      toast.success(data.message || 'Document uploaded!');
      setShowUploadDialog(false);
      setSelectedFile(null);
      setUploadForm({ title: '', description: '', category: 'general' });
      loadDocuments();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId) => {
    if (!window.confirm('Delete this document?')) return;
    try {
      await axios.delete(`${API}/api/premade-courses/${docId}`, { headers: getAuth() });
      toast.success('Document deleted');
      loadDocuments();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete');
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const filtered = documents.filter(d =>
    d.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.filename?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
      <Header title="Premade Courses" subtitle="Shared document library — upload and access course materials" />

      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Actions Bar */}
        <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
          <div className="flex gap-3 flex-1 w-full md:w-auto">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <Input placeholder="Search documents..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-zinc-900/50 border-white/10" data-testid="premade-search" />
            </div>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-[160px] bg-zinc-900/50 border-white/10" data-testid="category-filter">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent className="bg-zinc-900 border-white/10">
                {CATEGORIES.map(c => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>

          <Dialog open={showUploadDialog} onOpenChange={setShowUploadDialog}>
            <DialogTrigger asChild>
              <Button className="bg-violet-600 hover:bg-violet-700" data-testid="upload-premade-btn">
                <Plus className="w-4 h-4 mr-2" /> Upload Document
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-zinc-900 border-white/10 max-w-md">
              <DialogHeader>
                <DialogTitle>Upload to Premade Courses</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 mt-4">
                <div>
                  <Label>Title</Label>
                  <Input value={uploadForm.title} onChange={(e) => setUploadForm({...uploadForm, title: e.target.value})}
                    placeholder="Document title" className="bg-zinc-800 border-white/10 mt-1" data-testid="upload-title" />
                </div>
                <div>
                  <Label>Description</Label>
                  <Textarea value={uploadForm.description} onChange={(e) => setUploadForm({...uploadForm, description: e.target.value})}
                    placeholder="Brief description" className="bg-zinc-800 border-white/10 mt-1" rows={2} />
                </div>
                <div>
                  <Label>Category</Label>
                  <Select value={uploadForm.category} onValueChange={(v) => setUploadForm({...uploadForm, category: v})}>
                    <SelectTrigger className="bg-zinc-800 border-white/10 mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-800 border-white/10">
                      {CATEGORIES.filter(c => c.value !== 'all').map(c => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>File</Label>
                  <input type="file" ref={fileInputRef} className="hidden" accept=".pdf,.docx,.doc,.txt,.pptx,.xlsx"
                    onChange={(e) => { setSelectedFile(e.target.files[0]); if (!uploadForm.title && e.target.files[0]) setUploadForm({...uploadForm, title: e.target.files[0].name.replace(/\.[^.]+$/, '')}); }} />
                  <Button variant="outline" onClick={() => fileInputRef.current?.click()}
                    className="w-full border-dashed border-white/20 h-16 mt-1 flex-col gap-1" data-testid="select-file-btn">
                    <Upload className="w-5 h-5" />
                    <span className="text-xs">{selectedFile ? selectedFile.name : 'Click to select PDF, DOCX, TXT, PPTX'}</span>
                  </Button>
                </div>
                <Button onClick={handleUpload} disabled={uploading} className="w-full bg-violet-600 hover:bg-violet-700" data-testid="submit-upload-btn">
                  {uploading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Uploading...</> : <><Upload className="w-4 h-4 mr-2" /> Upload Document</>}
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-card p-4 text-center">
            <p className="text-2xl font-bold">{documents.length}</p>
            <p className="text-xs text-zinc-500">Total Documents</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="text-2xl font-bold text-violet-400">{documents.filter(d => d.filename?.endsWith('.pdf')).length}</p>
            <p className="text-xs text-zinc-500">PDFs</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="text-2xl font-bold text-blue-400">{new Set(documents.map(d => d.category)).size}</p>
            <p className="text-xs text-zinc-500">Categories</p>
          </div>
          <div className="glass-card p-4 text-center">
            <p className="text-2xl font-bold text-emerald-400">{documents.filter(d => d.is_view_only !== false).length}</p>
            <p className="text-xs text-zinc-500">View-Only Documents</p>
          </div>
        </div>

        {/* Documents Grid */}
        {filtered.length === 0 ? (
          <div className="glass-card p-16 text-center" data-testid="empty-state">
            <FolderOpen className="w-16 h-16 text-zinc-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Documents Found</h3>
            <p className="text-sm text-zinc-500 mb-4">
              {searchQuery ? 'Try a different search term' : 'Upload documents to build your course library.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="documents-grid">
            {filtered.map((doc) => (
              <div key={doc.id} className="glass-card p-5 hover:border-violet-500/30 transition-all group" data-testid={`doc-${doc.id}`}>
                <div className="flex items-start gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-violet-500/20 flex items-center justify-center shrink-0">
                    <FileText className="w-5 h-5 text-violet-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-sm truncate">{doc.title}</h4>
                    <p className="text-xs text-zinc-500 truncate">{doc.filename}</p>
                  </div>
                </div>
                
                {doc.description && (
                  <p className="text-xs text-zinc-400 line-clamp-2 mb-3">{doc.description}</p>
                )}

                <div className="flex items-center justify-between text-xs text-zinc-500 mb-3">
                  <Badge className="bg-zinc-700/50 text-zinc-400 text-[10px]">{doc.category}</Badge>
                  <span>{formatFileSize(doc.file_size || 0)}</span>
                </div>

                <div className="flex items-center justify-between text-xs text-zinc-500">
                  <span className="flex items-center gap-1">
                    <User className="w-3 h-3" />{doc.uploader_name || 'Unknown'}
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {doc.created_at ? new Date(doc.created_at).toLocaleDateString('en-US', {month:'short',day:'numeric'}) : 'N/A'}
                  </span>
                </div>

                <div className="flex gap-2 mt-4 pt-3 border-t border-white/5">
                  <Button size="sm" variant="ghost" className="flex-1 h-8 text-xs" onClick={() => setViewDoc(doc)} data-testid={`view-${doc.id}`}>
                    <Eye className="w-3 h-3 mr-1" /> View
                  </Button>
                  {(doc.uploaded_by === user?.id || user?.role === 'org_admin' || user?.role === 'admin') && (
                    <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-red-400" onClick={() => handleDelete(doc.id)}>
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Preview Dialog - view only, no download */}
        <Dialog open={!!viewDoc} onOpenChange={() => setViewDoc(null)}>
          <DialogContent className="bg-zinc-900 border-white/10 max-w-3xl max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Eye className="w-5 h-5 text-violet-400" />
                {viewDoc?.title}
              </DialogTitle>
            </DialogHeader>
            <div
              className="space-y-3 mt-4"
              onContextMenu={(e) => e.preventDefault()}
              onCopy={(e) => e.preventDefault()}
              style={{ userSelect: 'none', WebkitUserSelect: 'none' }}
              data-testid="premade-view-content"
            >
              <div className="flex gap-2 flex-wrap">
                <Badge>{viewDoc?.category}</Badge>
                <Badge className="bg-zinc-700/50">{viewDoc?.filename}</Badge>
                <Badge className="bg-zinc-700/50">{formatFileSize(viewDoc?.file_size || 0)}</Badge>
                <Badge className="bg-emerald-500/20 text-emerald-300">View Only</Badge>
              </div>
              {viewDoc?.description && <p className="text-sm text-zinc-400">{viewDoc.description}</p>}
              {viewDoc?.preview_text ? (
                <div className="bg-zinc-800/50 rounded-lg p-4 max-h-[55vh] overflow-y-auto select-none">
                  <p className="text-xs font-semibold text-zinc-500 mb-2 uppercase tracking-wide">Document Content (View Only)</p>
                  <p className="text-sm text-zinc-300 whitespace-pre-wrap leading-relaxed">{viewDoc.preview_text}</p>
                </div>
              ) : (
                <div className="bg-zinc-800/50 rounded-lg p-6 text-center">
                  <FileText className="w-12 h-12 text-violet-400 mx-auto mb-2" />
                  <p className="text-sm text-zinc-400">No preview text available for this document</p>
                </div>
              )}
              <p className="text-[11px] text-zinc-500 text-center pt-2">
                This document is view-only. Downloading, copying and printing are disabled.
              </p>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
