import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useParams, useNavigate, Link, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import {
  Sparkles, ArrowLeft, Headphones, Video, Lock, Loader2, FileText, LogIn, Play, Pause
} from 'lucide-react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Reuse the same PDF worker config as PremadeCoursesPage
const _WORKER_LOCAL = `${process.env.PUBLIC_URL || ''}/pdf.worker.min.js`;
const _WORKER_CDN = `https://unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;
pdfjs.GlobalWorkerOptions.workerSrc = _WORKER_LOCAL;
if (typeof window !== 'undefined' && !window.__pdfWorkerBlobUrl) {
  (async () => {
    for (const src of [_WORKER_LOCAL, _WORKER_CDN]) {
      try {
        const r = await fetch(src);
        if (!r.ok) continue;
        const txt = await r.text();
        const blob = new Blob([txt], { type: 'application/javascript' });
        const u = URL.createObjectURL(blob);
        window.__pdfWorkerBlobUrl = u;
        pdfjs.GlobalWorkerOptions.workerSrc = u;
        return;
      } catch (_) { /* ignore and continue */ }
    }
  })();
}

const API = process.env.REACT_APP_BACKEND_URL;

export default function PublicContentViewPage() {
  const { docId } = useParams();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewBlobUrl, setViewBlobUrl] = useState(null);
  const [pdfArrayBuffer, setPdfArrayBuffer] = useState(null);
  const [pdfNumPages, setPdfNumPages] = useState(null);
  const pdfContainerRef = useRef(null);
  const [pdfContainerWidth, setPdfContainerWidth] = useState(800);
  const [mediaInfo, setMediaInfo] = useState(null);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const audioRef = useRef(null);
  const isLoggedIn = typeof window !== 'undefined' && !!localStorage.getItem('cognify_token');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        // Document metadata: parse from the listing endpoint search
        const listResp = await axios.get(`${API}/api/public/content`);
        const found = (listResp.data?.documents || []).find((d) => d.id === docId);
        if (cancelled) return;
        if (!found) {
          toast.error('Document not found');
          navigate('/public');
          return;
        }
        setDoc(found);

        // Fetch the document blob
        const { data, headers } = await axios.get(`${API}/api/public/content/${docId}/view`, {
          responseType: 'blob',
        });
        const respCT = (headers && headers['content-type']) || data.type || '';
        if (respCT.includes('application/json')) {
          const txt = await data.text();
          const parsed = JSON.parse(txt);
          setDoc((prev) => ({ ...prev, slidesJson: parsed }));
        } else {
          const fname = (found.filename || '').toLowerCase();
          const isImg = ['png','jpg','jpeg','gif','webp'].some(e => fname.endsWith('.'+e));
          const mime = isImg ? (data.type || 'image/png') : 'application/pdf';
          const blob = new Blob([data], { type: mime });
          const buf = await blob.arrayBuffer();
          setPdfArrayBuffer(buf);
          setViewBlobUrl(URL.createObjectURL(blob));
        }

        // If logged in, fetch media URLs (audio/video)
        if (isLoggedIn) {
          try {
            const token = localStorage.getItem('cognify_token');
            const mi = await axios.get(`${API}/api/public/content/${docId}/media-info`, {
              headers: { Authorization: `Bearer ${token}` },
            });
            setMediaInfo(mi.data);
          } catch (_) { /* ignore and continue */ }
        }
      } catch (e) {
        toast.error('Failed to load document');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [docId, navigate, isLoggedIn]);

  useEffect(() => {
    if (!pdfContainerRef.current) return;
    const ro = new ResizeObserver((entries) => {
      for (const e of entries) {
        setPdfContainerWidth(Math.max(320, Math.floor(e.contentRect.width) - 32));
      }
    });
    ro.observe(pdfContainerRef.current);
    return () => ro.disconnect();
  }, [viewBlobUrl]);

  const pdfFileSource = useMemo(() => {
    if (pdfArrayBuffer) return { data: pdfArrayBuffer };
    if (viewBlobUrl) return { url: viewBlobUrl };
    return null;
  }, [pdfArrayBuffer, viewBlobUrl]);

  const toggleAudio = () => {
    if (!mediaInfo?.audio_url) return;
    if (!audioRef.current) {
      const token = localStorage.getItem('cognify_token');
      // Audio URL needs auth header — use fetch + blob to bypass header-on-Audio limitation
      fetch(`${API}${mediaInfo.audio_url}`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.blob();
        })
        .then(b => {
          if (!b || b.size < 256) throw new Error('Empty audio file');
          const url = URL.createObjectURL(b);
          const a = new Audio(url);
          audioRef.current = a;
          a.onended = () => setAudioPlaying(false);
          a.onerror = () => {
            toast.error('This audio file is invalid or unsupported. Please ask the admin to regenerate it.');
            setAudioPlaying(false);
            audioRef.current = null;
          };
          a.play().then(() => setAudioPlaying(true)).catch((err) => {
            toast.error('Audio playback failed: ' + (err?.message || 'unsupported format'));
            setAudioPlaying(false);
            audioRef.current = null;
          });
        })
        .catch((err) => {
          toast.error('Audio unavailable: ' + (err?.message || 'unknown error'));
        });
      return;
    }
    if (audioPlaying) { audioRef.current.pause(); setAudioPlaying(false); }
    else {
      audioRef.current.play().then(() => setAudioPlaying(true)).catch(() => {
        toast.error('Audio playback failed');
        setAudioPlaying(false);
      });
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-zinc-100">
      <nav className="border-b border-white/5 bg-zinc-950/90 backdrop-blur sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <Link to="/public" className="flex items-center gap-2 text-zinc-400 hover:text-white">
            <ArrowLeft className="w-4 h-4" /> Back to Public Library
          </Link>
          <div className="flex items-center gap-2">
            {!isLoggedIn ? (
              <Button onClick={() => navigate(`/login?next=/public/${docId}`)} className="bg-violet-500 hover:bg-violet-600">
                <LogIn className="w-4 h-4 mr-2" />
                Sign in for audio/video
              </Button>
            ) : (
              <Badge className="bg-emerald-500/20 text-emerald-300">Signed in</Badge>
            )}
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {loading || !doc ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-10 h-10 animate-spin text-violet-400" />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Main viewer */}
            <div className="lg:col-span-3">
              <div className="mb-4">
                <Badge className="bg-violet-500/20 text-violet-300 mb-2">{doc.category || 'public'}</Badge>
                <h1 className="text-3xl font-bold">{doc.title}</h1>
                {doc.description && <p className="text-zinc-400 mt-2">{doc.description}</p>}
              </div>
              <div ref={pdfContainerRef} className="glass-card overflow-hidden h-[78vh]">
                {doc.slidesJson ? (
                  <div className="w-full h-full overflow-y-auto p-4 bg-zinc-950 space-y-6">
                    {doc.slidesJson.slides.map((s) => (
                      <div
                        key={s.index}
                        className="mx-auto bg-white text-zinc-900 rounded-lg shadow-xl"
                        style={{ width: '90%', maxWidth: 960, aspectRatio: '16/9', padding: '40px 56px', display: 'flex', flexDirection: 'column' }}
                      >
                        <h2 className="text-3xl font-bold mb-6 text-zinc-900 border-b-2 border-violet-400 pb-3">{s.title}</h2>
                        {s.bullets?.length > 0 && (
                          <ul className="space-y-3 flex-1">
                            {s.bullets.map((b, i) => (
                              <li key={i} className="text-zinc-700" style={{ paddingLeft: `${(b.level||0)*24}px`, fontSize: (b.level||0)===0?'1.25rem':'1.05rem' }}>
                                {(b.level||0)===0?'• ':'◦ '}{b.text}
                              </li>
                            ))}
                          </ul>
                        )}
                        <div className="mt-auto text-right text-xs text-zinc-400 pt-3">
                          Slide {s.index} / {doc.slidesJson.total_slides}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : pdfFileSource ? (
                  <div className="h-full overflow-y-auto">
                    <Document
                      file={pdfFileSource}
                      loading={<div className="flex items-center justify-center py-20"><Loader2 className="w-10 h-10 animate-spin text-violet-400" /></div>}
                      error={<div className="text-center py-20"><FileText className="w-12 h-12 text-zinc-500 mx-auto mb-3" /><p className="text-zinc-300">Could not render this document.</p></div>}
                      onLoadSuccess={({ numPages }) => setPdfNumPages(numPages)}
                    >
                      {pdfNumPages && Array.from({ length: pdfNumPages }, (_, i) => (
                        <div key={i} className="flex justify-center py-3 border-b border-white/5">
                          <Page pageNumber={i+1} width={pdfContainerWidth} renderTextLayer={false} renderAnnotationLayer={false} />
                        </div>
                      ))}
                    </Document>
                  </div>
                ) : null}
              </div>
            </div>

            {/* Sidebar with media access */}
            <aside className="lg:col-span-1 space-y-4">
              <div className="glass-card p-5">
                <h3 className="font-semibold mb-3">Media versions</h3>
                {!isLoggedIn ? (
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 p-3 rounded-lg bg-zinc-900 border border-white/5">
                      <Lock className="w-4 h-4 text-zinc-500" />
                      <span className="text-zinc-400">Audio narration</span>
                    </div>
                    <div className="flex items-center gap-2 p-3 rounded-lg bg-zinc-900 border border-white/5">
                      <Lock className="w-4 h-4 text-zinc-500" />
                      <span className="text-zinc-400">Video presentation</span>
                    </div>
                    <Button className="w-full mt-3 bg-violet-500 hover:bg-violet-600" onClick={() => navigate(`/login?next=/public/${docId}`)}>
                      <LogIn className="w-4 h-4 mr-2" /> Sign in to unlock
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3 text-sm">
                    {mediaInfo?.audio_url ? (
                      <Button onClick={toggleAudio} className="w-full bg-violet-500 hover:bg-violet-600">
                        {audioPlaying ? <Pause className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                        {audioPlaying ? 'Pause audio' : 'Listen to audio'}
                      </Button>
                    ) : (
                      <div className="p-3 rounded-lg bg-zinc-900 border border-white/5 text-zinc-500 flex items-center gap-2">
                        <Headphones className="w-4 h-4" /> No audio yet
                      </div>
                    )}
                    {mediaInfo?.video_url ? (
                      <Button
                        onClick={async () => {
                          const token = localStorage.getItem('cognify_token');
                          try {
                            const r = await fetch(`${API}${mediaInfo.video_url}`, { headers: { Authorization: `Bearer ${token}` } });
                            if (!r.ok) throw new Error(`HTTP ${r.status}`);
                            const b = await r.blob();
                            if (!b || b.size < 1024) throw new Error('Empty video file');
                            const u = URL.createObjectURL(b);
                            const w = window.open(u, '_blank');
                            if (!w) toast.info('Pop-up blocked — allow pop-ups for video playback');
                          } catch (err) {
                            toast.error('Video unavailable: ' + (err?.message || 'unsupported format'));
                          }
                        }}
                        className="w-full bg-blue-500 hover:bg-blue-600"
                      >
                        <Video className="w-4 h-4 mr-2" /> Watch video
                      </Button>
                    ) : (
                      <div className="p-3 rounded-lg bg-zinc-900 border border-white/5 text-zinc-500 flex items-center gap-2">
                        <Video className="w-4 h-4" /> No video yet
                      </div>
                    )}
                  </div>
                )}
              </div>
              <div className="glass-card p-5">
                <h3 className="font-semibold mb-2">About</h3>
                <p className="text-xs text-zinc-500">Uploaded by: {doc.uploader_name || '—'}</p>
                <p className="text-xs text-zinc-500">{doc.filename}</p>
              </div>
            </aside>
          </div>
        )}
      </main>
    </div>
  );
}
