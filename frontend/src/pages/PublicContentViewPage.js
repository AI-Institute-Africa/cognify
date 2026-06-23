import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Sidebar } from '../components/Sidebar';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '../components/ui/select';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs';
import { toast } from 'sonner';
import {
  Sparkles, ArrowLeft, Headphones, Video, Lock, Loader2, FileText, LogIn,
  Play, Pause, Languages, Wand2, Bot, BookOpen, Menu, Image as ImageIcon,
} from 'lucide-react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// PDF worker config (mirrors PremadeCoursesPage)
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
      } catch (_) { /* try next */ }
    }
  })();
}

const API = process.env.REACT_APP_BACKEND_URL;
const TOKEN_HEADER = () => ({ Authorization: `Bearer ${localStorage.getItem('cognify_token')}` });

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'sn', label: 'Shona' },
  { code: 'nd', label: 'Ndebele' },
  { code: 'zu', label: 'isiZulu' },
  { code: 'fr', label: 'Français' },
  { code: 'es', label: 'Español' },
  { code: 'pt', label: 'Português' },
  { code: 'sw', label: 'Kiswahili' },
  { code: 'ar', label: 'العربية' },
  { code: 'zh', label: '中文' },
];

export default function PublicContentViewPage() {
  const { docId } = useParams();
  const navigate = useNavigate();
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const isLoggedIn = isAuthenticated && !!user;
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  useEffect(() => {
    const r = () => setIsMobile(window.innerWidth < 1024);
    r(); window.addEventListener('resize', r);
    return () => window.removeEventListener('resize', r);
  }, []);

  // Doc state
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewBlobUrl, setViewBlobUrl] = useState(null);
  const [pdfArrayBuffer, setPdfArrayBuffer] = useState(null);
  const [pdfNumPages, setPdfNumPages] = useState(null);
  const pdfContainerRef = useRef(null);
  const [pdfContainerWidth, setPdfContainerWidth] = useState(800);

  // Logged-in extras
  const [mediaInfo, setMediaInfo] = useState(null); // {audio_url, video_url, preview_text, ...}
  const [mode, setMode] = useState('read');
  const [language, setLanguage] = useState('en');
  const [translated, setTranslated] = useState('');
  const [translating, setTranslating] = useState(false);
  const [genAudioBusy, setGenAudioBusy] = useState(false);
  const [generatedAudioUrl, setGeneratedAudioUrl] = useState(null);
  const [audioPlaying, setAudioPlaying] = useState(false);
  const audioRef = useRef(null);
  const [slidesJob, setSlidesJob] = useState(null); // {id, status, slides[]}
  const [slidesBusy, setSlidesBusy] = useState(false);
  const [avatarText, setAvatarText] = useState('');
  const [avatarBusy, setAvatarBusy] = useState(false);

  // Load doc metadata + PDF blob
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const listResp = await axios.get(`${API}/api/public/content`);
        const found = (listResp.data?.documents || []).find((d) => d.id === docId);
        if (cancelled) return;
        if (!found) { toast.error('Document not found'); navigate('/public'); return; }
        setDoc(found);

        const { data, headers } = await axios.get(`${API}/api/public/content/${docId}/view`, { responseType: 'blob' });
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

        if (isLoggedIn) {
          try {
            const mi = await axios.get(`${API}/api/public/content/${docId}/media-info`, { headers: TOKEN_HEADER() });
            setMediaInfo(mi.data);
          } catch (_) { /* skip */ }
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
  }, [viewBlobUrl, mode]);

  const pdfFileSource = useMemo(() => {
    if (pdfArrayBuffer) return { data: pdfArrayBuffer };
    if (viewBlobUrl) return { url: viewBlobUrl };
    return null;
  }, [pdfArrayBuffer, viewBlobUrl]);

  // ---------- multi-modal handlers ----------
  const text = translated || mediaInfo?.preview_text || doc?.preview_text || '';

  const handleTranslate = useCallback(async (lang) => {
    setLanguage(lang);
    if (lang === 'en') { setTranslated(''); return; }
    const source = mediaInfo?.preview_text || doc?.preview_text || '';
    if (!source.trim()) { toast.error('No text available to translate'); return; }
    setTranslating(true);
    try {
      const params = new URLSearchParams({ text: source.slice(0, 8000), target_language: lang, source_language: 'en' });
      const { data } = await axios.post(`${API}/api/language/translate?${params}`, {}, { headers: TOKEN_HEADER() });
      setTranslated(data.translated || data.translated_text || source);
      toast.success(`Translated to ${LANGUAGES.find(l => l.code === lang)?.label || lang}`);
    } catch (e) {
      toast.error('Translation failed: ' + (e.response?.data?.detail || e.message));
    } finally { setTranslating(false); }
  }, [doc, mediaInfo]);

  const stopAudio = () => {
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    setAudioPlaying(false);
  };

  const playAudioFromUrl = async (url, isPublicMedia = false) => {
    stopAudio();
    try {
      let blobUrl = url;
      // If it's an authenticated /api/public/.../audio/... endpoint, fetch with auth header first
      if (isPublicMedia && url.startsWith('/api/')) {
        const r = await fetch(`${API}${url}`, { headers: TOKEN_HEADER() });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const b = await r.blob();
        if (!b || b.size < 256) throw new Error('Empty audio file');
        blobUrl = URL.createObjectURL(b);
      }
      const a = new Audio(blobUrl);
      audioRef.current = a;
      a.onended = () => setAudioPlaying(false);
      a.onerror = () => {
        toast.error('Audio file is invalid or unsupported.');
        setAudioPlaying(false);
        audioRef.current = null;
      };
      await a.play();
      setAudioPlaying(true);
    } catch (e) {
      toast.error('Audio playback failed: ' + (e?.message || 'unsupported'));
    }
  };

  const handleListen = async () => {
    // Priority: super-admin uploaded/generated audio > on-demand TTS > browser SpeechSynthesis
    if (audioPlaying) { stopAudio(); return; }
    if (mediaInfo?.audio_url) {
      return playAudioFromUrl(mediaInfo.audio_url, true);
    }
    if (generatedAudioUrl) {
      return playAudioFromUrl(generatedAudioUrl, false);
    }
    // Generate fresh TTS using the source text
    const source = (translated || mediaInfo?.preview_text || doc?.preview_text || '').trim();
    if (!source) { toast.error('No text available to narrate'); return; }
    setGenAudioBusy(true);
    try {
      const { data } = await axios.post(`${API}/api/advanced/tts`,
        { text: source.slice(0, 8000), voice: 'nova', speed: 1.0 },
        { headers: TOKEN_HEADER() });
      const url = data.audio_url;
      setGeneratedAudioUrl(url);
      if (url) {
        await playAudioFromUrl(url, false);
      } else {
        throw new Error('TTS returned no audio');
      }
    } catch (e) {
      // Fallback: browser SpeechSynthesis
      if ('speechSynthesis' in window) {
        try {
          const utter = new SpeechSynthesisUtterance(source.slice(0, 8000));
          utter.lang = language === 'en' ? 'en-US' : language;
          utter.onend = () => setAudioPlaying(false);
          utter.onerror = () => setAudioPlaying(false);
          window.speechSynthesis.cancel();
          window.speechSynthesis.speak(utter);
          setAudioPlaying(true);
          toast.info('Using browser narration (AI audio quota unavailable)');
        } catch (_) { toast.error('Audio unavailable'); }
      } else {
        toast.error('Audio generation failed: ' + (e.response?.data?.detail || e.message));
      }
    } finally { setGenAudioBusy(false); }
  };

  const handleWatch = async () => {
    if (!mediaInfo?.video_url) {
      toast.info('No video version yet. Ask the admin to generate or upload one.');
      return;
    }
    try {
      const r = await fetch(`${API}${mediaInfo.video_url}`, { headers: TOKEN_HEADER() });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const b = await r.blob();
      if (!b || b.size < 1024) throw new Error('Empty video file');
      const u = URL.createObjectURL(b);
      const w = window.open(u, '_blank');
      if (!w) toast.info('Pop-up blocked — allow pop-ups to watch the video');
    } catch (e) {
      toast.error('Video unavailable: ' + (e?.message || 'unsupported'));
    }
  };

  const handleGenerateSlides = async () => {
    setSlidesBusy(true);
    setSlidesJob(null);
    try {
      const source = mediaInfo?.preview_text || doc?.preview_text || '';
      const topic = `${doc?.title || 'Summit Presentation'} — ${source.slice(0, 400)}`;
      const params = new URLSearchParams({ topic, slide_count: '5' });
      const { data } = await axios.post(`${API}/api/content/generate-slides?${params}`, {}, { headers: TOKEN_HEADER() });
      const id = data.slideshow_id;
      toast.success('Generating pictorial slides…');
      // Poll
      const poll = async () => {
        try {
          const { data: j } = await axios.get(`${API}/api/content/slides-status/${id}`, { headers: TOKEN_HEADER() });
          setSlidesJob(j);
          if (j.status === 'completed') {
            setSlidesBusy(false);
            toast.success('Slides ready!');
          } else if (j.status === 'failed') {
            setSlidesBusy(false);
            toast.error(j.error || 'Slide generation failed');
          } else {
            setTimeout(poll, 4000);
          }
        } catch (_) {
          setSlidesBusy(false);
        }
      };
      setTimeout(poll, 4000);
    } catch (e) {
      setSlidesBusy(false);
      toast.error('Failed to start slides: ' + (e.response?.data?.detail || e.message));
    }
  };

  const handleAvatarTeach = async () => {
    const source = (translated || mediaInfo?.preview_text || doc?.preview_text || '').trim();
    if (!source) { toast.error('No text available for avatar teaching'); return; }
    setAvatarBusy(true);
    setAvatarText('');
    try {
      // Use the lesson generator to produce a structured avatar-style explanation
      const params = new URLSearchParams({ topic: doc?.title || 'Public talk', duration_minutes: '5' });
      ['Understand the key points', 'Apply the main ideas', 'Reflect on takeaways']
        .forEach(o => params.append('learning_objectives', o));
      const { data } = await axios.post(`${API}/api/advanced/lesson/generate?${params}`, {}, { headers: TOKEN_HEADER() });
      const script = data.lesson?.script || data.lesson?.content || data.script || JSON.stringify(data).slice(0, 2000);
      setAvatarText(script);
      // Auto-narrate the avatar script using browser TTS as a fallback experience
      if ('speechSynthesis' in window) {
        const utter = new SpeechSynthesisUtterance(script.slice(0, 6000));
        utter.lang = 'en-US';
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utter);
        setAudioPlaying(true);
      }
    } catch (e) {
      toast.error('Avatar teaching unavailable: ' + (e.response?.data?.detail || e.message));
    } finally { setAvatarBusy(false); }
  };

  // ---------- render ----------
  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-[#09090B] flex items-center justify-center">
        <Loader2 className="w-10 h-10 animate-spin text-violet-400" />
      </div>
    );
  }
  if (!doc) return null;

  // GUEST VIEW (no login) — minimal read-only with sign-in CTA
  if (!isLoggedIn) {
    return (
      <GuestPublicView
        doc={doc}
        docId={docId}
        navigate={navigate}
        pdfContainerRef={pdfContainerRef}
        pdfContainerWidth={pdfContainerWidth}
        pdfFileSource={pdfFileSource}
        pdfNumPages={pdfNumPages}
        setPdfNumPages={setPdfNumPages}
      />
    );
  }

  // LOGGED-IN VIEW — full multi-modal experience
  return (
    <div className="min-h-screen bg-[#09090B] text-zinc-100">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} isMobile={isMobile} />
      <main className={`min-h-screen ${isMobile ? '' : 'ml-64'}`}>
        <header className="border-b border-white/5 sticky top-0 z-20 bg-[#09090B]/90 backdrop-blur">
          <div className="px-6 py-4 flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3">
              {isMobile && (
                <button onClick={() => setSidebarOpen(true)} className="p-2 rounded-lg hover:bg-white/5" data-testid="open-sidebar-btn">
                  <Menu className="w-5 h-5" />
                </button>
              )}
              <Link to="/public" className="flex items-center gap-2 text-zinc-400 hover:text-white text-sm" data-testid="back-to-public">
                <ArrowLeft className="w-4 h-4" /> Back
              </Link>
              <div>
                <Badge className="bg-violet-500/20 text-violet-300 mb-1">{doc.category || 'public'}</Badge>
                <h1 className="text-lg sm:text-xl font-semibold">{doc.title}</h1>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Select value={language} onValueChange={handleTranslate}>
                <SelectTrigger className="bg-zinc-900 border-white/10 w-40" data-testid="lang-select">
                  <Languages className="w-4 h-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-zinc-900 border-white/10 text-zinc-100">
                  {LANGUAGES.map((l) => (
                    <SelectItem key={l.code} value={l.code}>{l.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {translating && <Loader2 className="w-4 h-4 animate-spin text-violet-400" />}
            </div>
          </div>
        </header>

        <div className="px-6 py-6 max-w-6xl mx-auto">
          <Tabs value={mode} onValueChange={setMode} className="w-full">
            <TabsList className="bg-zinc-900 border border-white/10 mb-6 flex flex-wrap h-auto">
              <TabsTrigger value="read" data-testid="learner-tab-read"><FileText className="w-4 h-4 mr-2" />Read</TabsTrigger>
              <TabsTrigger value="text" data-testid="learner-tab-text"><BookOpen className="w-4 h-4 mr-2" />Text Summary</TabsTrigger>
              <TabsTrigger value="audio" data-testid="learner-tab-audio"><Headphones className="w-4 h-4 mr-2" />Audio</TabsTrigger>
              <TabsTrigger value="video" data-testid="learner-tab-video"><Video className="w-4 h-4 mr-2" />Video</TabsTrigger>
              <TabsTrigger value="slides" data-testid="learner-tab-slides"><ImageIcon className="w-4 h-4 mr-2" />Pictorial Slides</TabsTrigger>
              <TabsTrigger value="avatar" data-testid="learner-tab-avatar"><Bot className="w-4 h-4 mr-2" />Avatar Teach</TabsTrigger>
            </TabsList>

            {/* READ — original document */}
            <TabsContent value="read" className="mt-0">
              <div ref={pdfContainerRef} className="glass-card overflow-hidden h-[78vh]">
                {doc.slidesJson ? (
                  <SlidesJSONViewer slides={doc.slidesJson.slides} total={doc.slidesJson.total_slides} />
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
            </TabsContent>

            {/* TEXT SUMMARY (with translation) */}
            <TabsContent value="text" className="mt-0">
              <div className="glass-card p-6 min-h-[60vh]">
                <h3 className="font-semibold mb-3 text-zinc-300">
                  {translated ? `Translated to ${LANGUAGES.find(l => l.code === language)?.label}` : 'Original text'}
                </h3>
                {text ? (
                  <div className="prose prose-invert max-w-none whitespace-pre-wrap text-zinc-200 leading-relaxed" data-testid="learner-text-content">
                    {text}
                  </div>
                ) : (
                  <p className="text-zinc-500 text-sm">No extractable text from this document.</p>
                )}
              </div>
            </TabsContent>

            {/* AUDIO */}
            <TabsContent value="audio" className="mt-0">
              <div className="glass-card p-8 min-h-[60vh] flex flex-col items-center justify-center text-center">
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-emerald-500/30 to-blue-500/30 flex items-center justify-center mb-6">
                  <Headphones className="w-12 h-12 text-emerald-300" />
                </div>
                <h3 className="text-2xl font-bold mb-2">Audio Narration</h3>
                <p className="text-zinc-400 text-sm mb-6 max-w-md">
                  {mediaInfo?.audio_url
                    ? 'Pre-recorded narration is available for this presentation.'
                    : 'Generate AI narration on-demand using the document text.'}
                </p>
                <Button
                  size="lg"
                  onClick={handleListen}
                  disabled={genAudioBusy}
                  className="bg-emerald-500 hover:bg-emerald-600"
                  data-testid="learner-audio-btn"
                >
                  {genAudioBusy ? <Loader2 className="w-5 h-5 mr-2 animate-spin" /> :
                    audioPlaying ? <Pause className="w-5 h-5 mr-2" /> : <Play className="w-5 h-5 mr-2" />}
                  {genAudioBusy ? 'Generating…' : audioPlaying ? 'Pause' : (mediaInfo?.audio_url ? 'Play narration' : 'Generate & play')}
                </Button>
                {audioPlaying && (
                  <Button variant="outline" className="mt-3 border-white/10" onClick={stopAudio} data-testid="learner-audio-stop">
                    Stop
                  </Button>
                )}
              </div>
            </TabsContent>

            {/* VIDEO */}
            <TabsContent value="video" className="mt-0">
              <div className="glass-card p-8 min-h-[60vh] flex flex-col items-center justify-center text-center">
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500/30 to-violet-500/30 flex items-center justify-center mb-6">
                  <Video className="w-12 h-12 text-blue-300" />
                </div>
                <h3 className="text-2xl font-bold mb-2">Video Presentation</h3>
                <p className="text-zinc-400 text-sm mb-6 max-w-md">
                  {mediaInfo?.video_url
                    ? 'Watch the full video version of this presentation.'
                    : 'A video version is not yet available. Ask the admin to generate or upload one.'}
                </p>
                <Button
                  size="lg"
                  onClick={handleWatch}
                  disabled={!mediaInfo?.video_url}
                  className="bg-blue-500 hover:bg-blue-600 disabled:opacity-50"
                  data-testid="learner-video-btn"
                >
                  <Play className="w-5 h-5 mr-2" />
                  {mediaInfo?.video_url ? 'Watch video' : 'Not available yet'}
                </Button>
              </div>
            </TabsContent>

            {/* PICTORIAL SLIDES */}
            <TabsContent value="slides" className="mt-0">
              <div className="glass-card p-6 min-h-[60vh]">
                <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                  <div>
                    <h3 className="font-semibold text-lg">Pictorial Slides</h3>
                    <p className="text-xs text-zinc-500">AI-generated visual summary using Gemini Nano Banana</p>
                  </div>
                  <Button
                    onClick={handleGenerateSlides}
                    disabled={slidesBusy}
                    className="bg-violet-500 hover:bg-violet-600"
                    data-testid="learner-slides-btn"
                  >
                    {slidesBusy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Wand2 className="w-4 h-4 mr-2" />}
                    {slidesBusy ? 'Generating…' : 'Generate slides'}
                  </Button>
                </div>
                {slidesJob ? (
                  slidesJob.status === 'completed' ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {(slidesJob.slides || []).map((s, i) => (
                        <div key={i} className="rounded-xl overflow-hidden border border-white/5 bg-zinc-950">
                          {s.image_url && (
                            <img src={`${API}${s.image_url}`} alt={s.title || `Slide ${i+1}`} className="w-full" />
                          )}
                          <div className="p-3">
                            <p className="text-sm font-medium text-zinc-200">{s.title || `Slide ${i+1}`}</p>
                            {s.caption && <p className="text-xs text-zinc-500 mt-1">{s.caption}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <Loader2 className="w-10 h-10 animate-spin text-violet-400 mx-auto mb-4" />
                      <p className="text-sm text-zinc-400">Generating slides ({slidesJob.progress || 0}/{slidesJob.total || 5})…</p>
                    </div>
                  )
                ) : (
                  <div className="text-center py-16">
                    <ImageIcon className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                    <p className="text-sm text-zinc-500">Click &quot;Generate slides&quot; to create a visual summary of this presentation.</p>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* AVATAR TEACHING */}
            <TabsContent value="avatar" className="mt-0">
              <div className="glass-card p-6 min-h-[60vh]">
                <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
                  <div>
                    <h3 className="font-semibold text-lg">Avatar-led Lesson</h3>
                    <p className="text-xs text-zinc-500">AI builds a structured 5-min lesson around this presentation</p>
                  </div>
                  <Button
                    onClick={handleAvatarTeach}
                    disabled={avatarBusy}
                    className="bg-gradient-to-r from-violet-500 to-blue-500 hover:from-violet-600 hover:to-blue-600"
                    data-testid="learner-avatar-btn"
                  >
                    {avatarBusy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Bot className="w-4 h-4 mr-2" />}
                    {avatarBusy ? 'Preparing…' : 'Start avatar teaching'}
                  </Button>
                </div>
                {avatarText ? (
                  <div className="prose prose-invert max-w-none whitespace-pre-wrap text-zinc-200 leading-relaxed">
                    {avatarText}
                  </div>
                ) : (
                  <div className="text-center py-16">
                    <Bot className="w-12 h-12 text-zinc-600 mx-auto mb-3" />
                    <p className="text-sm text-zinc-500">Click &quot;Start avatar teaching&quot; to have your AI tutor walk you through this presentation.</p>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
}

// ---------- Slides JSON viewer (re-used) ----------
function SlidesJSONViewer({ slides, total }) {
  return (
    <div className="w-full h-full overflow-y-auto p-4 bg-zinc-950 space-y-6">
      {(slides || []).map((s) => (
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
            Slide {s.index} / {total}
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------- Guest (no auth) view ----------
function GuestPublicView({ doc, docId, navigate, pdfContainerRef, pdfContainerWidth, pdfFileSource, pdfNumPages, setPdfNumPages }) {
  return (
    <div className="min-h-screen bg-[#0a0a0b] text-zinc-100">
      <nav className="border-b border-white/5 bg-zinc-950/90 backdrop-blur sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <Link to="/public" className="flex items-center gap-2 text-zinc-400 hover:text-white">
            <ArrowLeft className="w-4 h-4" /> Back to Public Library
          </Link>
          <Button onClick={() => navigate(`/login?next=/public/${docId}`)} className="bg-violet-500 hover:bg-violet-600" data-testid="guest-signin-cta">
            <LogIn className="w-4 h-4 mr-2" />
            Sign in for full experience
          </Button>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3">
            <div className="mb-4">
              <Badge className="bg-violet-500/20 text-violet-300 mb-2">{doc.category || 'public'}</Badge>
              <h1 className="text-3xl font-bold">{doc.title}</h1>
              {doc.description && <p className="text-zinc-400 mt-2">{doc.description}</p>}
            </div>
            <div ref={pdfContainerRef} className="glass-card overflow-hidden h-[78vh]">
              {doc.slidesJson ? (
                <SlidesJSONViewer slides={doc.slidesJson.slides} total={doc.slidesJson.total_slides} />
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
          <aside className="lg:col-span-1 space-y-4">
            <div className="glass-card p-5">
              <Sparkles className="w-8 h-8 text-violet-400 mb-3" />
              <h3 className="font-semibold mb-2">Unlock the full experience</h3>
              <p className="text-sm text-zinc-400 mb-4">
                Sign in to get audio narration, video version, AI pictorial slides, avatar teaching, and 10+ languages.
              </p>
              <div className="space-y-2 text-sm">
                {[
                  { icon: Headphones, label: 'Audio narration' },
                  { icon: Video, label: 'Video presentation' },
                  { icon: ImageIcon, label: 'Pictorial slides' },
                  { icon: Bot, label: 'Avatar teaching' },
                  { icon: Languages, label: 'Multi-language' },
                ].map((f, i) => (
                  <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-zinc-900 border border-white/5">
                    <Lock className="w-3 h-3 text-zinc-500" />
                    <f.icon className="w-4 h-4 text-zinc-400" />
                    <span className="text-zinc-300">{f.label}</span>
                  </div>
                ))}
              </div>
              <Button className="w-full mt-4 bg-violet-500 hover:bg-violet-600" onClick={() => navigate(`/login?next=/public/${docId}`)} data-testid="guest-unlock-btn">
                <LogIn className="w-4 h-4 mr-2" /> Sign in to unlock
              </Button>
              <p className="text-xs text-zinc-500 mt-3 text-center">
                Don&apos;t have an account? <Link to="/register" className="text-violet-400 hover:underline">Create one free</Link>
              </p>
            </div>
            <div className="glass-card p-5">
              <h3 className="font-semibold mb-2 text-sm">About</h3>
              <p className="text-xs text-zinc-500">Uploaded by: {doc.uploader_name || '—'}</p>
              <p className="text-xs text-zinc-500">{doc.filename}</p>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}
