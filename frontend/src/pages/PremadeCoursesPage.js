import React, { useState, useEffect, useRef, useMemo } from 'react';
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
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription
} from '../components/ui/dialog';
import {
  FileText, Upload, Trash2, Search, Loader2,
  BookOpen, Plus, Eye, Calendar, User, FolderOpen
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';
import { renderAsync as renderDocxAsync } from 'docx-preview';

// Configure pdf.js worker — most robust strategy:
//   Wrap the worker bytes in a Blob URL. Browsers always serve Blob URLs with the
//   right MIME, bypassing any static-server misconfiguration on production.
//   We try the local /pdf.worker.min.js first, then fall back to a CDN.
const _WORKER_LOCAL = `${process.env.PUBLIC_URL || ''}/pdf.worker.min.js`;
const _WORKER_CDN = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;
// Set a synchronous default so PDF.js doesn't bail before our async setup completes
pdfjs.GlobalWorkerOptions.workerSrc = _WORKER_LOCAL;

if (typeof window !== 'undefined' && !window.__pdfWorkerBlobUrl) {
  (async () => {
    for (const src of [_WORKER_LOCAL, _WORKER_CDN]) {
      try {
        const r = await fetch(src);
        if (!r.ok) continue;
        const blob = await r.blob();
        // Force application/javascript MIME on the blob URL
        const jsBlob = new Blob([await blob.text()], { type: 'application/javascript' });
        const blobUrl = URL.createObjectURL(jsBlob);
        window.__pdfWorkerBlobUrl = blobUrl;
        pdfjs.GlobalWorkerOptions.workerSrc = blobUrl;
        return;
      } catch (e) {
        // try next
      }
    }
  })();
}

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
  const [viewBlobUrl, setViewBlobUrl] = useState(null);
  const [viewLoading, setViewLoading] = useState(false);
  const [viewError, setViewError] = useState(null);
  const [pdfNumPages, setPdfNumPages] = useState(null);
  const pdfContainerRef = useRef(null);
  const [pdfContainerWidth, setPdfContainerWidth] = useState(800);
  const docxContainerRef = useRef(null);
  const [viewBlob, setViewBlob] = useState(null);
  const [slidesJson, setSlidesJson] = useState(null); // {title, slides, total_slides}

  useEffect(() => { loadDocuments(); }, [selectedCategory]);

  // Fetch and stream the original document as a blob URL for in-iframe rendering.
  useEffect(() => {
    let cancelled = false;
    async function loadView() {
      setPdfNumPages(null);
      setSlidesJson(null);
      if (!viewDoc) {
        setViewBlobUrl((prev) => { if (prev) URL.revokeObjectURL(prev); return null; });
        setViewBlob(null);
        setViewError(null);
        return;
      }
      setViewLoading(true);
      setViewError(null);
      try {
        const { data, headers } = await axios.get(
          `${API}/api/premade-courses/${viewDoc.id}/view`,
          { headers: getAuth(), responseType: 'blob' }
        );
        if (cancelled) return;

        const fname = (viewDoc.filename || '').toLowerCase();
        const respCT = (headers && headers['content-type']) || data.type || '';

        // Backend may return JSON slides for PPTX when LibreOffice is unavailable
        if (respCT.includes('application/json')) {
          const txt = await data.text();
          try {
            const parsed = JSON.parse(txt);
            if (parsed && parsed.type === 'slides_json' && Array.isArray(parsed.slides)) {
              setSlidesJson(parsed);
              setViewBlob(null);
              setViewBlobUrl((prev) => { if (prev) URL.revokeObjectURL(prev); return null; });
              return;
            }
          } catch (_) { /* fall through */ }
        }

        const isImg = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].some(e => fname.endsWith('.' + e));
        const isTxt = fname.endsWith('.txt');
        const isDocx = fname.endsWith('.docx');
        let mime;
        if (isImg) mime = data.type || 'image/png';
        else if (isTxt) mime = 'text/plain';
        else if (isDocx) mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
        else mime = 'application/pdf';
        const blob = new Blob([data], { type: mime });
        const url = URL.createObjectURL(blob);
        setViewBlob(blob);
        setViewBlobUrl((prev) => { if (prev) URL.revokeObjectURL(prev); return url; });
      } catch (e) {
        if (!cancelled) {
          // Try to read detail from blob error body
          let detail = 'Could not load document';
          try {
            if (e.response?.data && e.response.data.text) {
              const txt = await e.response.data.text();
              try { detail = JSON.parse(txt).detail || detail; } catch (_) { detail = txt || detail; }
            } else if (e.response?.data?.detail) {
              detail = e.response.data.detail;
            }
          } catch (_) {}
          setViewError(detail);
        }
      } finally {
        if (!cancelled) setViewLoading(false);
      }
    }
    loadView();
    return () => { cancelled = true; };
  }, [viewDoc]);

  // Track container width so pdf pages scale responsively
  useEffect(() => {
    const el = pdfContainerRef.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const w = Math.max(320, Math.floor(entry.contentRect.width) - 24);
        setPdfContainerWidth(w);
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [viewBlobUrl]);

  // Stable file source for react-pdf so it doesn't re-fetch on every render.
  // Use the raw blob's ArrayBuffer so PDF.js parses bytes directly (most reliable on production).
  const [pdfArrayBuffer, setPdfArrayBuffer] = useState(null);
  useEffect(() => {
    let cancelled = false;
    if (!viewBlob) { setPdfArrayBuffer(null); return; }
    const fname = (viewDoc?.filename || '').toLowerCase();
    const isImg = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].some(e => fname.endsWith('.' + e));
    const isDocx = fname.endsWith('.docx');
    const isTxt = fname.endsWith('.txt');
    if (isImg || isDocx || isTxt) { setPdfArrayBuffer(null); return; }
    viewBlob.arrayBuffer().then((buf) => {
      if (!cancelled) setPdfArrayBuffer(buf);
    }).catch(() => {
      if (!cancelled) setPdfArrayBuffer(null);
    });
    return () => { cancelled = true; };
  }, [viewBlob, viewDoc]);

  const pdfFileSource = useMemo(() => {
    if (pdfArrayBuffer) return { data: pdfArrayBuffer };
    if (viewBlobUrl) return { url: viewBlobUrl };
    return null;
  }, [pdfArrayBuffer, viewBlobUrl]);

  // Render DOCX into its container using docx-preview (preserves Word styling)
  useEffect(() => {
    const fname = (viewDoc?.filename || '').toLowerCase();
    const isDocx = fname.endsWith('.docx');
    const container = docxContainerRef.current;
    if (!isDocx || !viewBlob || !container) return;
    container.innerHTML = '';
    renderDocxAsync(viewBlob, container, null, {
      className: 'docx-preview',
      inWrapper: true,
      ignoreWidth: false,
      ignoreHeight: false,
      ignoreFonts: false,
      breakPages: true,
      experimental: true,
      useBase64URL: true,
    }).catch((err) => {
      console.error('docx-preview render failed', err);
      container.innerHTML = '<div style="padding:24px;color:#a1a1aa;text-align:center">Could not render Word document.</div>';
    });
  }, [viewBlob, viewDoc]);

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
    // Client-side size guard
    if (selectedFile.size > 100 * 1024 * 1024) {
      toast.error(`File too large (${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB). Max 100MB.`);
      return;
    }
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('title', uploadForm.title);
      formData.append('description', uploadForm.description);
      formData.append('category', uploadForm.category);

      // IMPORTANT: DO NOT set Content-Type manually for multipart/form-data.
      // Axios MUST be allowed to set the boundary parameter automatically,
      // otherwise some proxies (including K8s ingress) reject the body.
      const { data } = await axios.post(`${API}/api/premade-courses/upload`, formData, {
        headers: { ...getAuth() },
        timeout: 300000, // 5 minutes for large files
        maxContentLength: Infinity,
        maxBodyLength: Infinity,
      });
      toast.success(data.message || 'Document uploaded!');
      setShowUploadDialog(false);
      setSelectedFile(null);
      setUploadForm({ title: '', description: '', category: 'general' });
      loadDocuments();
    } catch (err) {
      const detail = err.response?.data?.detail;
      const status = err.response?.status;
      let msg;
      if (status === 413) msg = 'File too large for the server. Try a smaller file.';
      else if (status === 401) msg = 'Session expired. Please log in again.';
      else if (status === 403) msg = 'Not authorized to upload documents.';
      else if (err.code === 'ECONNABORTED') msg = 'Upload timed out. The file may be too large or your connection is slow.';
      else if (detail) msg = typeof detail === 'string' ? detail : JSON.stringify(detail);
      else if (err.message) msg = err.message;
      else msg = 'Upload failed. Please try again.';
      toast.error(msg);
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
          <DialogContent className="bg-zinc-900 border-white/10 w-[95vw] max-w-6xl h-[90vh] p-0 flex flex-col">
            <DialogHeader className="px-6 pt-5 pb-3 border-b border-white/10">
              <DialogTitle className="flex items-center gap-2">
                <Eye className="w-5 h-5 text-violet-400" />
                <span className="truncate">{viewDoc?.title}</span>
              </DialogTitle>
              <DialogDescription className="sr-only">
                View-only document preview. Downloading, copying and printing are disabled.
              </DialogDescription>
              <div className="flex gap-2 flex-wrap pt-2">
                <Badge>{viewDoc?.category}</Badge>
                <Badge className="bg-zinc-700/50">{viewDoc?.filename}</Badge>
                <Badge className="bg-zinc-700/50">{formatFileSize(viewDoc?.file_size || 0)}</Badge>
                <Badge className="bg-emerald-500/20 text-emerald-300">View Only</Badge>
              </div>
            </DialogHeader>

            <div
              className="flex-1 relative overflow-hidden bg-zinc-950"
              onContextMenu={(e) => e.preventDefault()}
              data-testid="premade-view-content"
            >
              {viewLoading && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <Loader2 className="w-10 h-10 animate-spin text-violet-400" />
                </div>
              )}
              {viewError && !viewLoading && (
                <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center">
                  <FileText className="w-12 h-12 text-zinc-500 mb-3" />
                  <p className="text-zinc-300 font-medium">{viewError}</p>
                  {viewDoc?.preview_text && (
                    <div className="mt-4 max-w-2xl w-full text-left bg-zinc-800/60 rounded-lg p-4 max-h-[55vh] overflow-y-auto">
                      <p className="text-xs font-semibold text-zinc-500 mb-2 uppercase tracking-wide">Text fallback</p>
                      <p className="text-sm text-zinc-300 whitespace-pre-wrap leading-relaxed select-none">{viewDoc.preview_text}</p>
                    </div>
                  )}
                </div>
              )}
              {!viewLoading && !viewError && (slidesJson || viewBlobUrl) && (() => {
                // python-pptx structured slides fallback (when LibreOffice isn't on the server)
                if (slidesJson) {
                  return (
                    <div className="w-full h-full overflow-y-auto bg-zinc-950 select-none px-4 py-4 space-y-6" data-testid="premade-view-slides-json">
                      {slidesJson.slides.map((s) => (
                        <div
                          key={s.index}
                          className="mx-auto bg-white text-zinc-900 rounded-lg shadow-xl"
                          style={{ width: '90%', maxWidth: 960, aspectRatio: '16/9', padding: '40px 56px', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start' }}
                        >
                          <h2 className="text-3xl font-bold mb-6 text-zinc-900 border-b-2 border-violet-400 pb-3" style={{ fontFamily: 'Georgia, serif' }}>
                            {s.title}
                          </h2>
                          {s.bullets && s.bullets.length > 0 && (
                            <ul className="space-y-3 flex-1">
                              {s.bullets.map((b, i) => (
                                <li
                                  key={i}
                                  className="text-zinc-700 leading-relaxed"
                                  style={{
                                    paddingLeft: `${(b.level || 0) * 24}px`,
                                    fontSize: (b.level || 0) === 0 ? '1.25rem' : '1.05rem',
                                  }}
                                >
                                  {(b.level || 0) === 0 ? '• ' : '◦ '} {b.text}
                                </li>
                              ))}
                            </ul>
                          )}
                          {s.images && s.images.length > 0 && (
                            <div className="grid grid-cols-2 gap-3 mt-4">
                              {s.images.slice(0, 4).map((img, idx) => (
                                <img
                                  key={idx}
                                  src={img.data}
                                  alt=""
                                  className="max-h-32 object-contain"
                                  draggable={false}
                                />
                              ))}
                            </div>
                          )}
                          <div className="mt-auto text-right text-xs text-zinc-400 pt-3">
                            Slide {s.index} / {slidesJson.total_slides}
                          </div>
                        </div>
                      ))}
                    </div>
                  );
                }

                const fname = (viewDoc?.filename || '').toLowerCase();
                const isImg = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].some(e => fname.endsWith('.' + e));
                const isTxt = fname.endsWith('.txt');
                const isDocx = fname.endsWith('.docx');

                if (isImg) {
                  return (
                    <div className="w-full h-full flex items-center justify-center p-4 select-none">
                      <img
                        src={viewBlobUrl}
                        alt={viewDoc?.title}
                        className="max-w-full max-h-full object-contain pointer-events-none"
                        draggable={false}
                      />
                    </div>
                  );
                }

                if (isTxt) {
                  return (
                    <iframe
                      title={viewDoc?.title}
                      src={viewBlobUrl}
                      className="w-full h-full border-0 bg-white"
                      data-testid="premade-view-iframe"
                    />
                  );
                }

                if (isDocx) {
                  // Word document rendered with docx-preview (preserves original Word styling)
                  return (
                    <div
                      ref={docxContainerRef}
                      className="w-full h-full overflow-y-auto bg-white text-zinc-900 px-6 py-4 select-none"
                      data-testid="premade-view-docx"
                      style={{ userSelect: 'none' }}
                    />
                  );
                }

                // PDF (native PDFs and PPT/PPTX/XLS/XLSX/DOC after conversion) — react-pdf
                return (
                  <div ref={pdfContainerRef} className="w-full h-full overflow-y-auto bg-zinc-900 select-none">
                    <Document
                      file={pdfFileSource}
                      loading={
                        <div className="flex items-center justify-center py-20">
                          <Loader2 className="w-10 h-10 animate-spin text-violet-400" />
                        </div>
                      }
                      error={
                        <div className="text-center py-20 px-6">
                          <FileText className="w-12 h-12 text-zinc-500 mx-auto mb-3" />
                          <p className="text-zinc-300 font-medium">Could not render this document.</p>
                          <p className="text-xs text-zinc-500 mt-2 max-w-md mx-auto">
                            The PDF viewer failed to load. Please refresh the page and try again. If the problem persists, the document may be corrupted.
                          </p>
                          <Button
                            size="sm"
                            variant="outline"
                            className="mt-4 border-white/10"
                            onClick={() => window.location.reload()}
                            data-testid="pdf-reload-btn"
                          >
                            Reload page
                          </Button>
                        </div>
                      }
                      onLoadSuccess={({ numPages }) => { setPdfNumPages(numPages); }}
                      onLoadError={(err) => { console.error('react-pdf load error:', err); }}
                      onSourceError={(err) => { console.error('react-pdf source error:', err); }}
                      onContextMenu={(e) => e.preventDefault()}
                    >
                      {pdfNumPages && Array.from({ length: pdfNumPages }, (_, i) => (
                        <div
                          key={`page_${i + 1}`}
                          className="flex justify-center py-3 border-b border-white/5"
                        >
                          <Page
                            pageNumber={i + 1}
                            width={pdfContainerWidth}
                            renderTextLayer={false}
                            renderAnnotationLayer={false}
                          />
                        </div>
                      ))}
                    </Document>
                  </div>
                );
              })()}
            </div>

            <div className="px-6 py-3 border-t border-white/10 text-[11px] text-zinc-500 flex items-center justify-between gap-4">
              <span>
                {slidesJson ? `${slidesJson.total_slides} slide${slidesJson.total_slides > 1 ? 's' : ''}` :
                  pdfNumPages ? `${pdfNumPages} page${pdfNumPages > 1 ? 's' : ''}` : 'View only'}
              </span>
              <span className="text-center flex-1">
                This document is view-only. Downloading, copying and printing are disabled.
              </span>
              <span className="opacity-0">.</span>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
